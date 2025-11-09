import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QAction, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import initialize_database
initialize_database()

# 🟢 THÊM DÒNG NÀY: import form tiếp đón khám
from forms.tiep_don_kham import TiepDonKham
from forms.chi_dinh_dich_vu import ChiDinhDichVu
from forms.form_thong_ke_thu_chi import ThongKeThuChi
from forms.form_thu_tien_dich_vu import ThuTienDichVu


class MainApp(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Phần mềm quản lý phòng khám")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(900, 600)

        self.initUI()

    def initUI(self):
        # ----- MENU BAR TRÊN CÙNG -----
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 10))
        menubar.setStyleSheet("background-color: #1976d2; color: white;")

        hethong_menu = menubar.addMenu("Hệ thống")
        danhmuc_menu = menubar.addMenu("Danh mục")
        khambenh_menu = menubar.addMenu("Khám bệnh")
        dichvu_menu = menubar.addMenu("Dịch vụ")
        thuoc_menu = menubar.addMenu("Thuốc - VTYT")
        thuchi_menu = menubar.addMenu("Thu chi")
        baocao_menu = menubar.addMenu("Báo cáo")
# Them action cho menu thu chi
        thutien_action = QAction("💰 Thu tiền dịch vụ", self)
        thutien_action.triggered.connect(self.show_thutien_dichvu)

        thongke_action = QAction("📊 Thống kê thu chi", self)
        thongke_action.triggered.connect(self.show_thongke_thu_chi)

        thuchi_menu.addAction(thutien_action)
        thuchi_menu.addAction(thongke_action)

        # Thêm action mẫu
        logout_action = QAction("Đăng xuất", self)
        logout_action.triggered.connect(self.logout)
        hethong_menu.addAction(logout_action)

        # ----- CENTRAL WIDGET -----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ----- SIDEBAR BÊN TRÁI -----
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

        # ----- NÚT CHỨC NĂNG -----
        self.btn_tiepdon = QPushButton("➕ Tiếp đón khám")
        self.btn_chidinh = QPushButton("🧾 Chỉ định dịch vụ")
        self.btn_lapphieu = QPushButton("📋 Lập phiếu khám")

        for btn in [self.btn_tiepdon, self.btn_chidinh, self.btn_lapphieu]:
            sidebar_layout.addWidget(btn)

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
        welcome_label = QLabel(f"Chào mừng {self.username} đến với phần mềm quả lý phòng khám vippro nhất lịch sử!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        self.content.addWidget(default_page)

        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "TIẾP ĐÓN KHÁM"
        self.btn_tiepdon.clicked.connect(self.show_tiepdon_form)

        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "CHỈ ĐỊNH DỊCH VỤ"
        self.btn_chidinh.clicked.connect(self.show_chidinh_form)

        

        # Gắn vào layout chính
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)

    # 🟢 HÀM MỞ FORM TIẾP ĐÓN KHÁM
    def show_tiepdon_form(self):
       """ Hiển thị form tiếp đón trong vùng nội dung chính
        tiepdon_page = TiepDonKham()  # gọi class trong tiep_don_kham.py
        self.content.addWidget(tiepdon_page)
        self.content.setCurrentWidget(tiepdon_page)
        """
       if not hasattr(self, 'tiepdon_page'):
           self.tiepdon_page = TiepDonKham()  #class trong tiep_don_kham
           self.content.addWidget(self.tiepdon_page)
       else:
           #Cap nhat lai du lieu truoc khi hien thi
            self.tiepdon_page.load_thongke_luottiepdon()
            self.tiepdon_page.load_danhsach_tiepdon()
       self.content.setCurrentWidget(self.tiepdon_page)   

    # 🟢 HÀM MỞ FORM CHỈ ĐỊNH DỊCH VỤ
    def show_chidinh_form(self):
        """Hiển thị form Chỉ định dịch vụ"""
        chidinh_page = ChiDinhDichVu() # gọi class trong chi_dinh_dich_vu.py
        self.content.addWidget(chidinh_page)
        self.content.setCurrentWidget(chidinh_page)

    def show_thongke_thu_chi(self):
        # Hien thi form thong ke thu chi
        thongkethuchi_page = ThongKeThuChi()
        self.content.addWidget(thongkethuchi_page)
        self.content.setCurrentWidget(thongkethuchi_page)

    def show_thutien_dichvu(self):
        # Hien thi form thu tien dich vu
        thutien_page = ThuTienDichVu()
        self.content.addWidget(thutien_page)
        self.content.setCurrentWidget(thutien_page)
    

    def logout(self):
            from login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()


if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = MainApp("admin")
    window.showMaximized()
    sys.exit(app.exec_())
