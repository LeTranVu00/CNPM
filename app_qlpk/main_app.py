#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QAction, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Giả sử database.py tồn tại và có hàm này
try:
    from database import initialize_database

    initialize_database()
except ImportError:
    print("Bỏ qua initialize_database (chỉ chạy demo)")

# Import các form
from forms.tiep_don_kham import TiepDonKham
from forms.chi_dinh_dich_vu import ChiDinhDichVu

# ## NÂNG CẤP: Import 3 form mới
from forms.lap_phieu_kham import LapPhieuKham
from forms.ke_don_thuoc import KeDonThuoc
from forms.phieu_nhap import PhieuNhap


class MainApp(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Phần mềm quản lý phòng khám")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(900, 600)

        # Cache các trang để không phải tạo lại
        self.pages = {}

        self.initUI()

    def initUI(self):
        # ----- MENU BAR TRÊN CÙNG -----
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 10))
        # ## NÂNG CẤP: Bỏ style ở đây để dùng style của HĐH
        # menubar.setStyleSheet("background-color: #1976d2; color: white;")

        hethong_menu = menubar.addMenu("Hệ thống")
        danhmuc_menu = menubar.addMenu("Danh mục")
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
            QPushButton:focus {
                background-color: #d0e0f0; /* Màu khi được chọn */
                border-left: 3px solid #1976d2;
                font-weight: bold;
            }
            QLabel.SidebarTitle {
                font-family: "Arial";
                font-size: 10pt;
                font-weight: bold;
                color: #1565c0; 
                padding-left: 15px;
                margin-top: 10px;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        title = QLabel("TIẾP ĐÓN & KHÁM BỆNH")
        title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title)

        # ----- NÚT CHỨC NĂNG -----
        self.btn_tiepdon = QPushButton("➕ Tiếp đón khám")
        self.btn_chidinh = QPushButton("🧾 Chỉ định dịch vụ")
        self.btn_lapphieu = QPushButton("📋 Lập phiếu khám")
        self.btn_kedon = QPushButton("💊 Kê đơn thuốc")  # ## MỚI

        sidebar_layout.addWidget(self.btn_tiepdon)
        sidebar_layout.addWidget(self.btn_chidinh)
        sidebar_layout.addWidget(self.btn_lapphieu)
        sidebar_layout.addWidget(self.btn_kedon)  # ## MỚI

        # ## MỚI: Nhóm Thuốc
        title_thuoc = QLabel("THUỐC - KHO")
        title_thuoc.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_thuoc)
        self.btn_phieunhap = QPushButton("🚚 Phiếu nhập kho")  # ## MỚI
        sidebar_layout.addWidget(self.btn_phieunhap)  # ## MỚI

        title2 = QLabel("THU TIỀN - BÁO CÁO")
        title2.setObjectName("SidebarTitle")
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
        welcome_label = QLabel(f"Chào mừng {self.username} đến với phần mềm!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        self.content.addWidget(default_page)
        self.pages["default"] = default_page

        # Kết nối sự kiện
        self.btn_tiepdon.clicked.connect(lambda: self.show_form("tiepdon", TiepDonKham))
        self.btn_chidinh.clicked.connect(lambda: self.show_form("chidinh", ChiDinhDichVu))

        # ## NÂNG CẤP: Kết nối 3 nút mới
        self.btn_lapphieu.clicked.connect(lambda: self.show_form("lapphieukham", LapPhieuKham))
        self.btn_kedon.clicked.connect(lambda: self.show_form("kedonthuoc", KeDonThuoc))
        self.btn_phieunhap.clicked.connect(lambda: self.show_form("phieunhap", PhieuNhap))

        # Gắn vào layout chính
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)
        main_layout.setStretch(0, 1)  # Sidebar
        main_layout.setStretch(1, 5)  # Vùng nội dung (rộng hơn)

    # ## NÂNG CẤP: Hàm chung để mở Form
    def show_form(self, key, form_class):
        """
        Hiển thị form trong QStackedWidget.
        Sử dụng cache để tránh tạo lại form đã mở.
        """
        # Nếu form chưa có trong cache, tạo mới và thêm vào
        if key not in self.pages:
            print(f"Đang tạo trang mới: {key}")
            form_page = form_class()
            self.pages[key] = form_page
            self.content.addWidget(form_page)

        # Lấy form từ cache và hiển thị
        page_to_show = self.pages[key]
        self.content.setCurrentWidget(page_to_show)

        # Nếu là form Tiếp đón, gọi hàm load lại
        if key == "tiepdon":
            try:
                page_to_show.load_data_benh_nhan()
            except Exception as e:
                print(f"Lỗi khi load lại dữ liệu Tiêp Đón: {e}")

    def logout(self):
        # Cẩn thận với import vòng
        try:
            from login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()
        except ImportError:
            QMessageBox.critical(self, "Lỗi", "Không thể tải lại cửa sổ Đăng nhập.")
            self.close()


if __name__ == "__main__":
    # Bỏ qua initialize_database() nếu không có
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = MainApp("admin")
    window.showMaximized()
    sys.exit(app.exec_())