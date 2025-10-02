import sys
import os
# --- BẮT ĐẦU SỬA LỖI IMPORT ---
# Thêm thư mục gốc của dự án vào sys.path để Python nhận ra 'app_qlpk' là package
# Lấy đường dẫn thư mục hiện tại của file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Lấy đường dẫn thư mục cha (chính là thư mục gốc của dự án)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- KẾT THÚC SỬA LỖI IMPORT ---


from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# Bây giờ import sẽ hoạt động vì đường dẫn đã được thêm vào
from app_qlpk.database import initialize_database 

# Khởi tạo cơ sở dữ liệu
initialize_database()

# 🟢 Import các form
from app_qlpk.forms.tiep_don_kham import TiepDonKham
from app_qlpk.forms.lap_phieu_kham import LapPhieuKham
from app_qlpk.forms.phieu_nhap import PhieuNhap  
# ✅ THÊM: Import form DonThuoc
from app_qlpk.forms.don_thuoc import DonThuoc

class MainApp(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Phần mềm quản lý phòng khám")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(900, 600)
        self.initUI()

    def initUI(self):
        # ----- MENU BAR -----
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 10))
        menubar.setStyleSheet("background-color: #1976d2; color: white;")

        hethong_menu = menubar.addMenu("Hệ thống")
        danhmuc_menu = menubar.addMenu("Danh mục")
        # 🔥 ĐÃ SỬA LỖI TYPO: menmenubar -> menubar
        khambenh_menu = menubar.addMenu("Khám bệnh")
        dichvu_menu = menubar.addMenu("Dịch vụ")
        thuoc_menu = menubar.addMenu("Thuốc - VTYT")
        thuchi_menu = menubar.addMenu("Thu chi")
        baocao_menu = menubar.addMenu("Báo cáo")

        logout_action = QAction("Đăng xuất", self)
        logout_action.triggered.connect(self.logout)
        hethong_menu.addAction(logout_action)

        # ----- CENTRAL WIDGET -----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ----- SIDEBAR -----
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-right: 1px solid #ccc;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        title = QLabel("TIẾP ĐÓN")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title)

        # ----- NÚT CHỨC NĂNG (TIẾP ĐÓN - KHÁM BỆNH) -----
        self.btn_tiepdon = QPushButton("➕ Tiếp đón khám")
        self.btn_chidinh = QPushButton("🧾 Chỉ định dịch vụ")
        self.btn_lapphieu = QPushButton("📋 Lập phiếu khám")
        # ✅ THÊM NÚT ĐƠN THUỐC
        self.btn_donthuoc = QPushButton("💊 Kê đơn thuốc")


        for btn in [self.btn_tiepdon, self.btn_chidinh, self.btn_lapphieu, self.btn_donthuoc]: # Đã thêm btn_donthuoc
            sidebar_layout.addWidget(btn)

        # Thêm khu vực THUỐC - VẬT TƯ Y TẾ
        sidebar_layout.addSpacing(10)
        title_thuoc = QLabel("QUẢN LÝ KHO")
        title_thuoc.setFont(QFont("Arial", 10, QFont.Bold))
        title_thuoc.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title_thuoc)
        
        # ✅ NÚT PHIẾU NHẬP
        self.btn_phieunhap = QPushButton("📦 Phiếu nhập")
        sidebar_layout.addWidget(self.btn_phieunhap)
        
        # Khu vực THU TIỀN - BÁO CÁO (giữ nguyên)
        sidebar_layout.addSpacing(10)
        title2 = QLabel("THU TIỀN - BÁO CÁO")
        title2.setFont(QFont("Arial", 10, QFont.Bold))
        title2.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title2)

        btn_thutien = QPushButton("💰 Thu tiền dịch vụ")
        btn_doanhthu = QPushButton("📊 Doanh thu tổng hợp")
        sidebar_layout.addWidget(btn_thutien)
        sidebar_layout.addWidget(btn_doanhthu)
        sidebar_layout.addStretch()

        # ----- KHU VỰC HIỂN THỊ NỘI DUNG -----
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: white;")

        # Trang mặc định
        default_page = QWidget()
        layout = QVBoxLayout(default_page)
        layout.setAlignment(Qt.AlignCenter)
        welcome_label = QLabel(f"Chào mừng {self.username} đến với phần mềm quản lý phòng khám!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        self.content.addWidget(default_page)

        # ----- GẮN SỰ KIỆN -----
        self.btn_tiepdon.clicked.connect(self.show_tiepdon_form)
        self.btn_lapphieu.clicked.connect(self.show_lapphieu_form)
        self.btn_phieunhap.clicked.connect(self.show_phieunhap_form) 
        # ✅ GẮN SỰ KIỆN CHO NÚT ĐƠN THUỐC
        self.btn_donthuoc.clicked.connect(self.show_donthuoc_form)


        # ----- BỐ CỤC CHÍNH -----
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)

    # ----- CÁC HÀM HIỂN THỊ FORM -----
    def show_tiepdon_form(self):
        """Hiển thị form Tiếp đón khám"""
        tiepdon_page = TiepDonKham()
        self.content.addWidget(tiepdon_page)
        self.content.setCurrentWidget(tiepdon_page)

    def show_lapphieu_form(self):
        """Hiển thị form Lập phiếu khám"""
        lapphieu_page = LapPhieuKham()
        self.content.addWidget(lapphieu_page)
        self.content.setCurrentWidget(lapphieu_page)

    def show_phieunhap_form(self):
        """Hiển thị form Phiếu nhập"""
        phieunhap_page = PhieuNhap()
        self.content.addWidget(phieunhap_page)
        self.content.setCurrentWidget(phieunhap_page)
        
    def show_donthuoc_form(self):
        """Hiển thị form Kê đơn thuốc"""
        donthuoc_page = DonThuoc()
        self.content.addWidget(donthuoc_page)
        self.content.setCurrentWidget(donthuoc_page)

    def logout(self):
        from app_qlpk.login import LoginWindow 
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = MainApp("admin")
    window.showMaximized()
    sys.exit(app.exec_())