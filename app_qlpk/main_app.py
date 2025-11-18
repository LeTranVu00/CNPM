# main_app.py <--- [LỖI CŨ] Đã xóa dòng tên file gây lỗi SyntaxError.

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QAction, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import initialize_database

initialize_database()

from database import get_user_role, end_user_session

# Import các form con
from forms.tiep_don_kham import TiepDonKham
from forms.chi_dinh_dich_vu import ChiDinhDichVu
from forms.tao_phieu_kham import TaoPhieuKham
from forms.quan_ly_thuoc import QuanLyThuoc
from forms.don_thuoc_bo_sung import DonThuocKhac


class MainApp(QMainWindow):
    def __init__(self, username, session_id=None):
        super().__init__()
        try:
            app = QApplication.instance()
            if app:
                app.setFont(QFont("Arial", 11))
        except Exception:
            pass
        self.username = username
        self.role = get_user_role(username)  # lấy role từ DB
        self.session_id = session_id
        self.setWindowTitle("Phần mềm quản lý phòng khám")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(900, 600)

        self.initUI()

    def initUI(self):
        # ----- MENU BAR -----
        menubar = self.menuBar()
        menubar.setFont(QFont("Arial", 10))
        try:
            menubar.setFixedHeight(40)
        except Exception:
            pass
        menubar.setStyleSheet(r"""
            QMenuBar { background-color: #1976d2; color: white; spacing: 6px; padding: 0px; }
            QMenuBar::item { background: transparent; padding: 6px 10px; margin: 0px; }
            QMenuBar::item:selected { background: #1565c0; }
            QMenu { background-color: white; color: black; }
        """)

        hethong_menu = menubar.addMenu("Hệ thống")
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
            QFrame { background-color: #f5f5f5; border-right: 1px solid #e0e0e0; }
            QPushButton { background-color: white; color: #1565c0; border: none; text-align: left; padding: 10px 20px; font-size: 11pt; margin: 0; border-radius: 0; min-height: 36px; }
            QPushButton:hover { background-color: #f6f8fb; }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        # User Info
        user_info_label = QLabel(f"👤 {self.username}")
        user_info_label.setFont(QFont("Arial", 10, QFont.Bold))
        user_info_label.setStyleSheet("color: #1565c0; padding-left: 15px; padding-bottom: 5px;")
        sidebar_layout.addWidget(user_info_label)

        role_label = QLabel(f"Vai trò: {self.role or 'user'}")
        role_label.setFont(QFont("Arial", 9))
        role_label.setStyleSheet("color: #666; padding-left: 15px; padding-bottom: 10px;")
        sidebar_layout.addWidget(role_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(separator)

        # Buttons
        title = QLabel("TIẾP ĐÓN")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title)

        self.btn_tiepdon = QPushButton("Tiếp đón khám")
        self.btn_chidinh = QPushButton("Chỉ định dịch vụ")
        self.btn_lapphieu = QPushButton("Lập phiếu khám")
        self.btn_quanly_thuoc = QPushButton("Quản lý thuốc")

        sidebar_layout.addWidget(self.btn_tiepdon)

        if self.role in ['bac_si', 'admin']:
            sidebar_layout.addWidget(self.btn_chidinh)
            sidebar_layout.addWidget(self.btn_lapphieu)

        if self.role == 'admin':
            sidebar_layout.addWidget(self.btn_quanly_thuoc)
            self.btn_admin_panel = QPushButton("Admin - Quản lý")
            sidebar_layout.addWidget(self.btn_admin_panel)

        sidebar_layout.addSpacing(10)
        title2 = QLabel("THU TIỀN - BÁO CÁO")
        title2.setFont(QFont("Arial", 10, QFont.Bold))
        title2.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title2)

        self.btn_thutien = QPushButton("Thu tiền dịch vụ")
        self.btn_doanhthu = QPushButton("Doanh thu tổng hợp")
        sidebar_layout.addWidget(self.btn_thutien)
        sidebar_layout.addWidget(self.btn_doanhthu)
        sidebar_layout.addStretch()

        # ----- CONTENT -----
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: white;")

        default_page = QWidget()
        layout = QVBoxLayout(default_page)
        layout.setAlignment(Qt.AlignCenter)
        welcome_label = QLabel(f"Chào mừng {self.username} đến với phần mềm quản lý phòng khám!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        self.content.addWidget(default_page)
        self.default_page = default_page

        # Connections
        self.btn_tiepdon.clicked.connect(self.show_tiepdon_form)
        self.btn_chidinh.clicked.connect(self.show_chidinh_form)
        self.btn_lapphieu.clicked.connect(self.show_lapphieu_form)
        self.btn_quanly_thuoc.clicked.connect(self.show_quanly_thuoc_form)

        try:
            self.btn_thutien.clicked.connect(self.show_thutien_tab)
            self.btn_doanhthu.clicked.connect(self.show_doanhthu_tab)
        except Exception:
            pass

        try:
            if hasattr(self, 'btn_admin_panel'):
                self.btn_admin_panel.clicked.connect(self.show_admin_panel)
        except Exception:
            pass

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)

        # Sidebar button list management
        self._sidebar_buttons = [
            self.btn_tiepdon, self.btn_chidinh, self.btn_lapphieu, self.btn_quanly_thuoc,
            self.btn_thutien, self.btn_doanhthu
        ]
        if hasattr(self, 'btn_admin_panel'):
            self._sidebar_buttons.append(self.btn_admin_panel)

        for b in self._sidebar_buttons:
            self._set_sidebar_inactive(b)

        self.content.currentChanged.connect(self._on_content_changed)

    def _set_sidebar_inactive(self, btn):
        try:
            btn.setStyleSheet(
                "QPushButton { background-color: white; color: #1565c0; border: none; text-align: left; padding: 10px 20px; font-size: 11pt; margin: 0; border-radius: 0; }"
                "QPushButton:hover { background-color: #f6f8fb; }"
            )
            btn.setChecked(False)
        except Exception:
            pass

    def _set_sidebar_active(self, btn):
        try:
            btn.setStyleSheet(
                "QPushButton { background-color: #0078D7; color: white; border: none; text-align: left; padding: 10px 20px; font-size: 11pt; margin: 0; border-radius: 0; border-left: 6px solid #005ea6; font-weight: 600; }"
                "QPushButton:hover { background-color: #0065b8; }"
            )
            btn.setChecked(True)
        except Exception:
            pass

    def _activate_only(self, btn_to_activate):
        for b in self._sidebar_buttons:
            if b is btn_to_activate:
                self._set_sidebar_active(b)
            else:
                self._set_sidebar_inactive(b)

    def _on_content_changed(self, index):
        try:
            current = self.content.widget(index)
            if current is self.default_page:
                for b in self._sidebar_buttons:
                    self._set_sidebar_inactive(b)
        except Exception:
            pass

    def show_tiepdon_form(self):
        tiepdon_page = TiepDonKham(role=self.role)
        self.content.addWidget(tiepdon_page)
        self.content.setCurrentWidget(tiepdon_page)
        try:
            self._activate_only(self.btn_tiepdon)
        except Exception:
            pass

    def show_chidinh_form(self):
        if self.role not in ['bac_si', 'admin']:
            QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền mở trang 'Chỉ định dịch vụ'.")
            return
        chidinh_page = ChiDinhDichVu()
        self.content.addWidget(chidinh_page)
        self.content.setCurrentWidget(chidinh_page)
        try:
            chidinh_page.data_saved.connect(lambda: self.refresh_quan_ly_form())
        except Exception:
            pass
        try:
            self._activate_only(self.btn_chidinh)
        except Exception:
            pass

    def show_lapphieu_form(self):
        try:
            if self.role not in ['bac_si', 'admin']:
                QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền mở trang 'Lập phiếu khám'.")
                return
            page = TaoPhieuKham()
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_lapphieu)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Lập phiếu khám:\n{e}")

    def show_quanly_thuoc_form(self):
        try:
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Chỉ admin mới có quyền mở 'Quản lý thuốc'.")
                return
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                try:
                    page.set_mode('quanly')
                except Exception:
                    pass
                self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_quanly_thuoc)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Quản lý thuốc:\n{e}")

    def _get_or_create_quan_ly_thuoc(self):
        try:
            if hasattr(self, 'quan_ly_thuoc_page') and self.quan_ly_thuoc_page:
                return self.quan_ly_thuoc_page
            page = QuanLyThuoc()
            self.content.addWidget(page)
            self.quan_ly_thuoc_page = page
            return page
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo trang Quản lý thuốc:\n{e}")
            return None

    def show_doanhthu_tab(self):
        try:
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                try:
                    page.set_mode('doanhthu')
                except Exception:
                    pass
                self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_doanhthu)
            except Exception:
                pass
        except Exception:
            pass

    def show_thutien_tab(self):
        try:
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                try:
                    page.set_mode('thutien')
                except Exception:
                    pass
                self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_thutien)
            except Exception:
                pass
        except Exception:
            pass

    def refresh_quan_ly_form(self):
        try:
            if hasattr(self, 'quan_ly_thuoc_page') and self.quan_ly_thuoc_page:
                self.quan_ly_thuoc_page.on_data_updated()
        except Exception:
            pass

    def create_don_thuoc_form(self, is_bo_sung=False):
        try:
            if is_bo_sung:
                page = DonThuocKhac()
                try:
                    page.medicine_exported.connect(lambda: self.refresh_quan_ly_form())
                except Exception:
                    pass
            else:
                from forms.don_thuoc import KeDonThuoc
                page = KeDonThuoc()
                try:
                    page.medicine_exported.connect(lambda: self.refresh_quan_ly_form())
                except Exception:
                    pass
            return page
        except Exception:
            return None

    def logout(self):
        try:
            if getattr(self, 'session_id', None):
                end_user_session(self.session_id)
        except Exception:
            pass

        # [QUAN TRỌNG] Import LoginWindow bên trong hàm để tránh lỗi "Circular Import" (Vòng lặp)
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def show_admin_panel(self):
        try:
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền truy cập Admin Panel.")
                return
            from forms.admin_panel import AdminPanel
            page = AdminPanel()
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_admin_panel)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Admin Panel:\n{e}")


if __name__ == "__main__":
    initialize_database()

    # [LƯU Ý] Import LoginWindow ở đây cũng là cách tránh import vòng lặp
    from login import LoginWindow

    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    app.setStyleSheet(r"""
        QTableView, QTableWidget {
            background-color: white;
            gridline-color: #ddd;
            border: 1px solid #ddd;
            selection-background-color: #0078D7;
            selection-color: white;
        }
        QTableView::item, QTableWidget::item {
            border: none;
            background-color: transparent;
            color: #000000;
            padding: 4px;
        }
        QTableView::item:selected, QTableWidget::item:selected,
        QTableView::item:selected:active, QTableWidget::item:selected:active,
        QTableView::item:selected:!active, QTableWidget::item:selected:!active {
            background-color: #0078D7;
            color: white;
        }
        QHeaderView::section {
            background-color: #0078D7;
            color: white;
            padding: 4px;
            border: none;
            font-weight: bold;
        }
    """)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())