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
import logging

# 🟢 THÊM DÒNG NÀY: import form tiếp đón khám
from forms.tiep_don_kham import TiepDonKham
from forms.chi_dinh_dich_vu import ChiDinhDichVu
from forms.tao_phieu_kham import TaoPhieuKham
from forms.quan_ly_thuoc import QuanLyThuoc
from forms.don_thuoc_bo_sung import DonThuocKhac
from forms.dat_lich_kham_form import DatLichKhamForm
from forms.ai_chat import AIChatDialog
from forms.quan_ly_nhan_su import QuanLyNhanSu
from forms.quan_ly_lich_hen import QuanLyLichHen
from forms.quan_ly_xuat_thuoc import QuanLyXuatThuoc
from forms.xem_lich_su_xuat_thuoc import XemLichSuXuatThuoc


class MainApp(QMainWindow):
    def __init__(self, username, session_id=None):
        super().__init__()
        # Ensure application-level font is set so widgets use a readable size
        try:
            app = QApplication.instance()
            if app:
                app.setFont(QFont("Arial", 11))
        except Exception:
            pass
        self.username = username
        self.role = get_user_role(username)  # lấy role từ DB
        # Optional session id passed by LoginWindow
        self.session_id = session_id
        self.setWindowTitle("Phần mềm quản lý phòng khám")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(900, 600)

        self.initUI()

    def initUI(self):
        # ----- MENU BAR TRÊN CÙNG -----
        menubar = self.menuBar()
        # Make the menubar slightly more compact and prevent menu text wrapping
        menubar.setFont(QFont("Arial", 10))
        try:
            # Force a compact height and item padding to avoid visual overflow
            menubar.setFixedHeight(40)
        except Exception:
            pass
        menubar.setStyleSheet(r"""
            QMenuBar {
                background-color: #1976d2;
                color: white;
                spacing: 6px;
                padding: 0px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 6px 10px; /* left/right padding */
                margin: 0px;
            }
            QMenuBar::item:selected { background: #1565c0; }
            QMenu {
                background-color: white; color: black;
            }
        """)

        hethong_menu = menubar.addMenu("Hệ thống")

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
        # Sidebar base styles. Use a subtle, modern look: buttons are white by
        # default; when active they get a left accent bar + light blue tint so
        # the highlight doesn't 'spill' across the whole sidebar.
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-right: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: white;
                color: #1565c0;
                border: none;
                text-align: left;
                padding: 10px 20px;
                font-size: 11pt;
                margin: 0;
                border-radius: 0;
                min-height: 36px;
            }
            /* inactive hover */
            QPushButton:hover {
                background-color: #f6f8fb;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        # Hiển thị username và role ở đầu sidebar
        user_info_label = QLabel(f"👤 {self.username}")
        user_info_label.setFont(QFont("Arial", 10, QFont.Bold))
        user_info_label.setStyleSheet("color: #1565c0; padding-left: 15px; padding-bottom: 5px;")
        sidebar_layout.addWidget(user_info_label)
        
        role_label = QLabel(f"Vai trò: {self.role or 'user'}")
        role_label.setFont(QFont("Arial", 9))
        role_label.setStyleSheet("color: #666; padding-left: 15px; padding-bottom: 10px;")
        sidebar_layout.addWidget(role_label)
        
        # Dòng phân cách
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(separator)

        title = QLabel("TIẾP ĐÓN")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setStyleSheet("color: #1565c0; padding-left: 15px;")
        sidebar_layout.addWidget(title)

        # ----- NÚT CHỨC NĂNG -----
        self.btn_tiepdon = QPushButton("Tiếp đón khám")
        self.btn_chidinh = QPushButton("Chỉ định dịch vụ")
        self.btn_lapphieu = QPushButton("Lập phiếu khám")
        self.btn_quanly_thuoc = QPushButton("Quản lý thuốc")
        self.btn_xuat_thuoc = QPushButton("Thông tin đơn thuốc")
        self.btn_quanly_dat_lich = QPushButton("Quản lý đặt lịch")

        # Hiển thị nút dựa trên role
        # Tiếp tân, Bác sĩ, Admin đều có nút Tiếp đón khám
        if self.role in ['admin', 'bac_si', 'tiep_tan']:
            sidebar_layout.addWidget(self.btn_tiepdon)

        # Thêm nút Quản lý đặt lịch
        if self.role in ['admin', 'bac_si', 'tiep_tan']:
            sidebar_layout.addWidget(self.btn_quanly_dat_lich)
        
        # Bác sĩ và Admin có nút Chỉ định dịch vụ và Lập phiếu khám
        if self.role in ['bac_si', 'admin']:
            sidebar_layout.addWidget(self.btn_chidinh)
            sidebar_layout.addWidget(self.btn_lapphieu)

        # If user is pharmacist, show Xuất thuốc
        if self.role in ['duoc_si', 'admin']:         
            sidebar_layout.addWidget(self.btn_xuat_thuoc)
        
        # Chỉ Admin có nút Quản lý thuốc
        if self.role == 'admin':
            sidebar_layout.addWidget(self.btn_quanly_thuoc)
            # Admin panel (patient/session management)
            self.btn_admin_panel = QPushButton("Quản lý chung")
            sidebar_layout.addWidget(self.btn_admin_panel)
            # New admin buttons for staff and appointment management
            self.btn_quanly_nhan_su = QPushButton("Quản lý Nhân Sự")
            sidebar_layout.addWidget(self.btn_quanly_nhan_su)
            self.btn_quanly_lich_hen = QPushButton("Quản lý Lịch Hẹn")
            sidebar_layout.addWidget(self.btn_quanly_lich_hen)
            # Admin button for viewing xuat thuoc history
            self.btn_lich_su_xuat_thuoc = QPushButton("Lịch sử xuất thuốc")
            sidebar_layout.addWidget(self.btn_lich_su_xuat_thuoc)
        

        # --- THU TIỀN - BÁO CÁO ---
        if self.role == 'admin':
            sidebar_layout.addSpacing(10)

            title2 = QLabel("THU TIỀN - BÁO CÁO")
            title2.setFont(QFont("Arial", 10, QFont.Bold))
            title2.setStyleSheet("color: #1565c0; padding-left: 15px;")
            sidebar_layout.addWidget(title2)

            self.btn_thutien = QPushButton("Thu tiền dịch vụ")
            sidebar_layout.addWidget(self.btn_thutien)

            self.btn_doanhthu = QPushButton("Doanh thu tổng hợp")
            sidebar_layout.addWidget(self.btn_doanhthu)


        # AI chat button
        self.btn_ai = QPushButton("AI Hỏi đáp")
        sidebar_layout.addWidget(self.btn_ai)
        sidebar_layout.addStretch()

        # ----- KHU VỰC HIỂN THỊ NỘI DUNG -----
        self.content = QStackedWidget()
        self.content.setStyleSheet("background-color: white;")

        # Trang mặc định
        default_page = QWidget()
        layout = QVBoxLayout(default_page)
        layout.setAlignment(Qt.AlignCenter)
        welcome_label = QLabel(f"Chào mừng {self.username} đến với phòng khám!")
        welcome_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(welcome_label)
        self.content.addWidget(default_page)
        # keep reference to default page to detect 'exit' back to home
        self.default_page = default_page

        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "TIẾP ĐÓN KHÁM"
        self.btn_tiepdon.clicked.connect(self.show_tiepdon_form)

        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "CHỈ ĐỊNH DỊCH VỤ"
        self.btn_chidinh.clicked.connect(self.show_chidinh_form)
        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "LẬP PHIẾU KHÁM"
        self.btn_lapphieu.clicked.connect(self.show_lapphieu_form)
        # 🟢 THÊM SỰ KIỆN NHẤN NÚT "QUẢN LÝ THUỐC"
        self.btn_quanly_thuoc.clicked.connect(self.show_quanly_thuoc_form)
        # Kết nối các nút thu tiền / doanh thu để mở tab tương ứng trong QuanLyThuoc
        try:
            if hasattr(self, 'btn_thutien'):
                self.btn_thutien.clicked.connect(self.show_thutien_tab)
            if hasattr(self, 'btn_doanhthu'):
                self.btn_doanhthu.clicked.connect(self.show_doanhthu_tab)
            self.btn_ai.clicked.connect(self.show_ai_dialog)
            if hasattr(self, 'btn_xuat_thuoc'):
                self.btn_xuat_thuoc.clicked.connect(self.show_xuat_thuoc_form)
        except Exception:
            pass

        # Admin panel connect
        try:
            if hasattr(self, 'btn_admin_panel'):
                self.btn_admin_panel.clicked.connect(self.show_admin_panel)
            # Kết nối nút Quản lý đặt lịch
            if hasattr(self, 'btn_quanly_dat_lich'):
                self.btn_quanly_dat_lich.clicked.connect(self.show_quanly_dat_lich)
            # Kết nối nút Quản lý Nhân Sự
            if hasattr(self, 'btn_quanly_nhan_su'):
                self.btn_quanly_nhan_su.clicked.connect(self.show_quanly_nhan_su_form)
            # Kết nối nút Quản lý Lịch Hẹn
            if hasattr(self, 'btn_quanly_lich_hen'):
                self.btn_quanly_lich_hen.clicked.connect(self.show_quanly_lich_hen_form)
            # Kết nối nút Lịch sử xuất thuốc
            if hasattr(self, 'btn_lich_su_xuat_thuoc'):
                self.btn_lich_su_xuat_thuoc.clicked.connect(self.show_lich_su_xuat_thuoc_form)
            if hasattr(self, 'btn_xuat_thuoc'):
                self.btn_xuat_thuoc.clicked.connect(self.show_xuat_thuoc_form)
        except Exception:
            pass

        # Gắn vào layout chính
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)

        # Sidebar button list for easy state management (include new revenue buttons)
        self._sidebar_buttons = [
            self.btn_tiepdon, self.btn_chidinh, self.btn_lapphieu, self.btn_quanly_thuoc
        ]
        # include admin buttons (only if they exist)
        if hasattr(self, 'btn_thutien'):
            self._sidebar_buttons.append(self.btn_thutien)
        if hasattr(self, 'btn_doanhthu'):
            self._sidebar_buttons.append(self.btn_doanhthu)
        # include AI button in sidebar management
        self._sidebar_buttons.append(self.btn_ai)
        if hasattr(self, 'btn_admin_panel'):
            self._sidebar_buttons.append(self.btn_admin_panel)
        if hasattr(self, 'btn_quanly_dat_lich'):
            self._sidebar_buttons.append(self.btn_quanly_dat_lich)
        if hasattr(self, 'btn_quanly_nhan_su'):
            self._sidebar_buttons.append(self.btn_quanly_nhan_su)
        if hasattr(self, 'btn_quanly_lich_hen'):
            self._sidebar_buttons.append(self.btn_quanly_lich_hen)
            self._sidebar_buttons.append(self.btn_quanly_dat_lich)
        if hasattr(self, 'btn_lich_su_xuat_thuoc'):
            self._sidebar_buttons.append(self.btn_lich_su_xuat_thuoc)
        if hasattr(self, 'btn_xuat_thuoc'):
            self._sidebar_buttons.append(self.btn_xuat_thuoc)

        # Initialize sidebar buttons to inactive (white)
        for b in self._sidebar_buttons:
            self._set_sidebar_inactive(b)

        # Update active state when content changes (e.g., child form closes and returns to default)
        self.content.currentChanged.connect(self._on_content_changed) 

    def _set_sidebar_inactive(self, btn):
        """Set button to inactive (white background)."""
        try:
            # lightweight inactive style: white background, blue text
            btn.setStyleSheet(
                "QPushButton { background-color: white; color: #1565c0; border: none; text-align: left; padding: 10px 20px; font-size: 11pt; margin: 0; border-radius: 0; }"
                "QPushButton:hover { background-color: #f6f8fb; }"
            )
            btn.setChecked(False)
        except Exception:
            pass

    def _set_sidebar_active(self, btn):
        """Set button to active (left accent + light blue tint)."""
        try:
            # Accent style: left border + subtle background, blue text and bold
            # Active: use a darker blue background so white text is readable.
            btn.setStyleSheet(
                "QPushButton { background-color: #0078D7; color: white; border: none; text-align: left; padding: 10px 20px; font-size: 11pt; margin: 0; border-radius: 0; border-left: 6px solid #005ea6; font-weight: 600; }"
                "QPushButton:hover { background-color: #0065b8; }"
            )
            btn.setChecked(True)
        except Exception:
            pass

    def _activate_only(self, btn_to_activate):
        """Make only the provided button active; others inactive."""
        for b in self._sidebar_buttons:
            if b is btn_to_activate:
                self._set_sidebar_active(b)
            else:
                self._set_sidebar_inactive(b)

    def _on_content_changed(self, index):
        """Reset sidebar buttons when content returns to default page."""
        try:
            current = self.content.widget(index)
            if current is self.default_page:
                for b in self._sidebar_buttons:
                    self._set_sidebar_inactive(b)
        except Exception:
            pass

    # 🟢 HÀM MỞ FORM TIẾP ĐÓN KHÁM
    def show_tiepdon_form(self):
        """Hiển thị form tiếp đón trong vùng nội dung chính"""
        # TiepDonKham currently accepts role; avoid passing session_id to prevent signature mismatch
        try:
            tiepdon_page = TiepDonKham(role=self.role)  # gọi class trong tiep_don_kham.py, truyền role
            self.content.addWidget(tiepdon_page)
            self.content.setCurrentWidget(tiepdon_page)
            try:
                self._activate_only(self.btn_tiepdon)
            except Exception:
                pass
        except KeyboardInterrupt:
            # User cancelled (Ctrl+C) - propagate so the application can exit cleanly
            raise
        except Exception as e:
            # Log and show a friendly message rather than crashing
            logging.exception("Không thể mở form Tiếp đón:")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Tiếp đón khám:\n{e}")

    # 🟢 HÀM MỞ FORM CHỈ ĐỊNH DỊCH VỤ
    def show_chidinh_form(self):
        """Hiển thị form Chỉ định dịch vụ"""
        # Role check: only bác sĩ and admin may open Chỉ định dịch vụ
        if self.role not in ['bac_si', 'admin']:
            QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền mở trang 'Chỉ định dịch vụ'.")
            return
        chidinh_page = ChiDinhDichVu() # gọi class trong chi_dinh_dich_vu.py
        self.content.addWidget(chidinh_page)
        self.content.setCurrentWidget(chidinh_page)
        
        # Kết nối signal để cập nhật form quản lý khi lưu
        try:
            chidinh_page.data_saved.connect(lambda: self.refresh_quan_ly_form())
        except Exception:
            pass
        
        try:
            self._activate_only(self.btn_chidinh)
        except Exception:
            pass

    def show_lapphieu_form(self):
        """Hiển thị trang Lập phiếu khám trong vùng nội dung chính."""
        try:
            # Role check: only bác sĩ and admin may open Lập phiếu khám
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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Lập phiếu khám:\n{e}")

    def show_quanly_thuoc_form(self):
        """Hiển thị form Quản lý thuốc trong vùng nội dung chính."""
        try:
            # Role check: only admin may open Quản lý thuốc
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Chỉ admin mới có quyền mở 'Quản lý thuốc'.")
                return
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                # Hiển thị chỉ tab Ghi nhận thanh toán khi mở từ mục Quản lý thuốc
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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Quản lý thuốc:\n{e}")

    def show_xuat_thuoc_form(self):
        """Hiển thị form Xuất thuốc cho dược sĩ hoặc admin."""
        try:
            if self.role not in ['duoc_si', 'admin']:
                QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền mở trang 'Xuất thuốc'.")
                return
            page = QuanLyXuatThuoc(username=self.username)
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_xuat_thuoc)
            except Exception:
                pass
        except Exception as e:
            logging.exception("Không thể mở form Xuất thuốc:")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Xuất thuốc:\n{e}")

    def show_lich_su_xuat_thuoc_form(self):
        """Hiển thị form Lịch sử xuất thuốc cho admin."""
        try:
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Bạn không có quyền mở trang 'Lịch sử xuất thuốc'.")
                return
            page = XemLichSuXuatThuoc(username=self.username)
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_lich_su_xuat_thuoc)
            except Exception:
                pass
        except Exception as e:
            logging.exception("Không thể mở form Lịch sử xuất thuốc:")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở trang Lịch sử xuất thuốc:\n{e}")

    def _get_or_create_quan_ly_thuoc(self):
        """Create QuanLyThuoc page if not exists and return it (doesn't change sidebar active state)."""
        try:
            if hasattr(self, 'quan_ly_thuoc_page') and self.quan_ly_thuoc_page:
                return self.quan_ly_thuoc_page
            page = QuanLyThuoc()
            self.content.addWidget(page)
            self.quan_ly_thuoc_page = page
            return page
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo trang Quản lý thuốc:\n{e}")
            return None

    def show_doanhthu_tab(self):
        """Open QuanLyThuoc and switch to the 'Tổng hợp doanh thu' tab."""
        try:
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                # Hiển thị chỉ tab Tổng hợp doanh thu cho mục Doanh thu tổng hợp
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
        """Open QuanLyThuoc and switch to the 'Chi tiết dịch vụ/thuốc' tab (used by Thu tiền dịch vụ)."""
        try:
            page = self._get_or_create_quan_ly_thuoc()
            if page:
                # Hiển thị chỉ tab Chi tiết dịch vụ/thuốc cho mục Thu tiền dịch vụ
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
        """Cập nhật dữ liệu trong form quản lý thuốc khi nhân liệu thay đổi."""
        try:
            if hasattr(self, 'quan_ly_thuoc_page') and self.quan_ly_thuoc_page:
                self.quan_ly_thuoc_page.on_data_updated()
        except Exception:
            pass
    
    def create_don_thuoc_form(self, is_bo_sung=False):
        """Tạo form đơn thuốc (hoặc đơn bổ sung) và kết nối signal."""
        try:
            if is_bo_sung:
                page = DonThuocKhac()
                # Kết nối signal từ form đơn bổ sung
                try:
                    page.medicine_exported.connect(lambda: self.refresh_quan_ly_form())
                except Exception:
                    pass
            else:
                from forms.don_thuoc import KeDonThuoc
                page = KeDonThuoc()
                # Kết nối signal từ form đơn thuốc
                try:
                    page.medicine_exported.connect(lambda: self.refresh_quan_ly_form())
                except Exception:
                    pass
            return page
        except Exception:
            return None


    def logout(self):
        # Record logout time for current session (if any)
        try:
            if getattr(self, 'session_id', None):
                end_user_session(self.session_id)
        except Exception:
            pass
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def show_admin_panel(self):
        """Open Admin panel (patients + sessions). Admin only."""
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

    def show_quanly_dat_lich(self):
        """Mở form quản lý đặt lịch khám (DatLichKhamForm)."""
        try:
            # Tạo form quản lý đặt lịch
            page = DatLichKhamForm(role=self.role)
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_quanly_dat_lich)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quản lý đặt lịch:\n{e}")

    def show_ai_dialog(self):
        """Mở dialog AI Chat (modal)."""
        try:
            dlg = AIChatDialog(self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở AI Chat:\n{e}")

    def show_quanly_nhan_su_form(self):
        """Mở form Quản lý Nhân Sự."""
        try:
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Chỉ admin mới có quyền truy cập Quản lý Nhân Sự.")
                return
            page = QuanLyNhanSu()
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_quanly_nhan_su)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quản lý Nhân Sự:\n{e}")

    def show_quanly_lich_hen_form(self):
        """Mở form Quản lý Lịch Hẹn."""
        try:
            if self.role != 'admin':
                QMessageBox.warning(self, "Phân quyền", "Chỉ admin mới có quyền truy cập Quản lý Lịch Hẹn.")
                return
            page = QuanLyLichHen()
            self.content.addWidget(page)
            self.content.setCurrentWidget(page)
            try:
                self._activate_only(self.btn_quanly_lich_hen)
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Quản lý Lịch Hẹn:\n{e}")


if __name__ == "__main__":
    # Khởi tạo DB và hiển thị màn hình đăng nhập thay vì tự động đăng nhập admin
    initialize_database()
    from login import LoginWindow
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    # Global stylesheet: ensure table row selection uses solid colors and text
    # remains readable even when the table/widget loses focus.
    app.setStyleSheet(r"""
        /* Table selection: active (focused) */
        /* Table base styling */
        QTableView, QTableWidget {
            background-color: white;
            gridline-color: #ddd;
            border: 1px solid #ddd;
            selection-background-color: #0078D7;
            selection-color: white;
        }

        /* Table item styling */
        QTableView::item, QTableWidget::item {
            border: none;
            background-color: transparent;
            color: #000000;
            padding: 4px;
        }

        /* Selected item styling - both active and inactive */
        QTableView::item:selected, QTableWidget::item:selected,
        QTableView::item:selected:active, QTableWidget::item:selected:active,
        QTableView::item:selected:!active, QTableWidget::item:selected:!active {
            background-color: #0078D7;
            color: white;
        }

        /* Header styling */
        QHeaderView::section {
            background-color: #0078D7;
            color: white;
            padding: 4px;
            border: none;
            font-weight: bold;
        }
    """)
    # Mặc định: mở màn hình đăng nhập để người dùng nhập tài khoản
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
