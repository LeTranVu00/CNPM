# login.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QMessageBox, QCheckBox, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from database import (
    verify_user,
    get_user_role,
    start_user_session,
    create_user,
    get_user_fullname,
    update_user_fullname,
    add_bac_si,
    bac_si_exists,
)
from PyQt5.QtWidgets import QInputDialog

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Đăng nhập hệ thống')
        self.setFixedSize(450, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Title
        title_label = QLabel("CHÀO MỪNG TRỞ LẠI")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        subtitle_label = QLabel("Phần Mềm Quản Lý Phòng Khám")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 11))
        
        # Tab widget for Login/Register
        self.tabs = QTabWidget()
        
        # Tab 1: Login
        login_tab = QWidget()
        self.init_login_tab(login_tab)
        self.tabs.addTab(login_tab, "Đăng Nhập")
        
        # Tab 2: Register (disabled for security)
        # register_tab = QWidget()
        # self.init_register_tab(register_tab)
        # self.tabs.addTab(register_tab, "Tạo Tài Khoản")
        
        # Add all to main layout
        layout.addWidget(title_label)
        layout.addSpacing(5)
        layout.addWidget(subtitle_label)
        layout.addSpacing(15)
        layout.addWidget(self.tabs)
    
    def init_login_tab(self, tab):
        """Khởi tạo tab đăng nhập."""
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFixedWidth(120)
        username_label.setFont(QFont("Arial", 10))
        self.username_input = QLineEdit()
        self.username_input.setFont(QFont("Arial", 10))
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Mật khẩu:")
        password_label.setFixedWidth(120)
        password_label.setFont(QFont("Arial", 10))
        self.password_input = QLineEdit()
        self.password_input.setFont(QFont("Arial", 10))
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        
        # Remember me checkbox
        self.remember_check = QCheckBox("Nhớ tài khoản, mật khẩu")
        self.remember_check.setFont(QFont("Arial", 10))
        self.remember_check.setChecked(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        login_button = QPushButton("Đăng nhập")
        login_button.setFont(QFont("Arial", 10, QFont.Bold))
        login_button.clicked.connect(self.handle_login)
        
        exit_button = QPushButton("Thoát")
        exit_button.setFont(QFont("Arial", 10))
        exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(login_button)
        button_layout.addWidget(exit_button)
        
        # Add to layout
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addWidget(self.remember_check)
        layout.addSpacing(10)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Set button styles
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
    
    def init_register_tab(self, tab):
        """Khởi tạo tab tạo tài khoản."""
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info label
        info_label = QLabel("Tạo Tài Khoản Mới")
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(info_label)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFixedWidth(120)
        username_label.setFont(QFont("Arial", 10))
        self.reg_username_input = QLineEdit()
        self.reg_username_input.setFont(QFont("Arial", 10))
        self.reg_username_input.setPlaceholderText("Ít nhất 3 ký tự")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.reg_username_input)
        
        # Full name (for doctors)
        fullname_layout = QHBoxLayout()
        fullname_label = QLabel("Họ và tên:")
        fullname_label.setFixedWidth(120)
        fullname_label.setFont(QFont("Arial", 10))
        self.reg_fullname_input = QLineEdit()
        self.reg_fullname_input.setFont(QFont("Arial", 10))
        self.reg_fullname_input.setPlaceholderText("Họ và tên")
        fullname_layout.addWidget(fullname_label)
        fullname_layout.addWidget(self.reg_fullname_input)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Mật khẩu:")
        password_label.setFixedWidth(120)
        password_label.setFont(QFont("Arial", 10))
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setFont(QFont("Arial", 10))
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        self.reg_password_input.setPlaceholderText("Ít nhất 6 ký tự")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.reg_password_input)
        
        # Confirm Password
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("Xác nhận MK:")
        confirm_label.setFixedWidth(120)
        confirm_label.setFont(QFont("Arial", 10))
        self.reg_confirm_input = QLineEdit()
        self.reg_confirm_input.setFont(QFont("Arial", 10))
        self.reg_confirm_input.setEchoMode(QLineEdit.Password)
        self.reg_confirm_input.setPlaceholderText("Nhập lại mật khẩu")
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.reg_confirm_input)
        
        # Role selection
        role_layout = QHBoxLayout()
        role_label = QLabel("Vai trò:")
        role_label.setFixedWidth(120)
        role_label.setFont(QFont("Arial", 10))
        self.reg_role_combo = QComboBox()
        self.reg_role_combo.addItems(["Tiếp Tân", "Bác Sĩ", "Dược Sĩ"])
        self.reg_role_combo.setFont(QFont("Arial", 10))
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.reg_role_combo)
        role_layout.addStretch()
        
        # Add fullname input (above role)
        layout.addLayout(fullname_layout)

        # Buttons
        button_layout = QHBoxLayout()
        register_button = QPushButton("Tạo Tài Khoản")
        register_button.setFont(QFont("Arial", 10, QFont.Bold))
        register_button.clicked.connect(self.handle_register)
        
        clear_button = QPushButton("Xóa")
        clear_button.setFont(QFont("Arial", 10))
        clear_button.clicked.connect(self.clear_register_form)
        
        button_layout.addWidget(register_button)
        button_layout.addWidget(clear_button)
        
        # Add to layout
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(confirm_layout)
        layout.addLayout(role_layout)
        layout.addSpacing(10)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Set button styles
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
    
    def handle_login(self):
        """Xử lý đăng nhập."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        
        # Xử lý đăng nhập
        if self.authenticate(username, password):
            # Start a user session and remember the session id to pass to MainApp
            try:
                session_id = start_user_session(username)
            except Exception:
                session_id = None
            # store for use in open_main_app
            try:
                self._started_session_id = session_id
            except Exception:
                pass
            # If user is a doctor, ensure their name is stored in bac_si
            try:
                role = get_user_role(username)
                if role == 'bac_si':
                    # Try to get fullname from users table
                    fullname = get_user_fullname(username)
                    if fullname:
                        # create bac_si record if not exists
                        try:
                            if not bac_si_exists(fullname):
                                add_bac_si(fullname)
                        except Exception:
                            pass
                    else:
                        # Ask for full name once
                        try:
                            text, ok = QInputDialog.getText(self, "Lưu tên Bác Sĩ", "Vui lòng nhập Họ và tên của Bác Sĩ:")
                            if ok and text.strip():
                                fullname = text.strip()
                                try:
                                    update_user_fullname(username, fullname)
                                except Exception:
                                    pass
                                try:
                                    add_bac_si(fullname)
                                except Exception:
                                    pass
                        except Exception:
                            pass
            except Exception:
                pass

            QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
            self.open_main_app()
        else:
            QMessageBox.critical(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")
    
    def handle_register(self):
        """Xử lý tạo tài khoản mới."""
        username = self.reg_username_input.text().strip()
        password = self.reg_password_input.text().strip()
        confirm = self.reg_confirm_input.text().strip()
        full_name = self.reg_fullname_input.text().strip()
        role_text = self.reg_role_combo.currentText()
        
        # Validation
        if not username or not password or not confirm:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        
        if len(username) < 3:
            QMessageBox.warning(self, "Lỗi", "Tên đăng nhập phải ít nhất 3 ký tự!")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu phải ít nhất 6 ký tự!")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp!")
            return
        
        # Map display text to role value
        role_map = {
            "Tiếp Tân": "tiep_tan",
            "Bác Sĩ": "bac_si",
            "Dược Sĩ": "duoc_si"
        }
        role = role_map.get(role_text, "tiep_tan")

        # Require full_name for receptionist and doctor
        if role in ("tiep_tan", "bac_si", "duoc_si") and not full_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Họ và tên khi đăng ký vai trò Tiếp Tân, Bác Sĩ hoặc Dược Sĩ.")
            return
        
        # Try to create user (include full_name)
        try:
            result = create_user(username, password, role=role, full_name=full_name if full_name else None)
            if result:
                # If doctor, create bac_si record as well
                if role == 'bac_si' and full_name:
                    try:
                        add_bac_si(full_name)
                    except Exception:
                        pass

                QMessageBox.information(self, "Thành công", 
                    f"Tạo tài khoản thành công!\n\nTên: {username}\nVai trò: {role_text}\n\nBạn có thể đăng nhập ngay.")
                self.clear_register_form()
                self.tabs.setCurrentIndex(0)  # Switch to login tab
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể tạo tài khoản!")
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                QMessageBox.critical(self, "Lỗi", f"Tên đăng nhập '{username}' đã tồn tại!")
            else:
                QMessageBox.critical(self, "Lỗi", f"Lỗi tạo tài khoản: {e}")
    
    def clear_register_form(self):
        """Xóa dữ liệu trong form tạo tài khoản."""
        self.reg_username_input.clear()
        self.reg_password_input.clear()
        self.reg_confirm_input.clear()
        try:
            self.reg_fullname_input.clear()
        except Exception:
            pass
        self.reg_role_combo.setCurrentIndex(0)
    
    def authenticate(self, username, password):
        """Xác thực tài khoản."""
        try:
            return verify_user(username, password)
        except Exception:
            return False
    
    def open_main_app(self):
        """Mở ứng dụng chính."""
        from main_app import MainApp
        try:
            session_id = getattr(self, '_started_session_id', None)
        except Exception:
            session_id = None
        
        if session_id is None:
            self.main_app = MainApp(self.username_input.text())
        else:
            self.main_app = MainApp(self.username_input.text(), session_id=session_id)
        self.main_app.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Đặt font mặc định
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
