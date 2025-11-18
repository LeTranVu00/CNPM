# login.py <--- [LỖI CŨ] Tên file trong code. Đã xóa/comment.

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from database import verify_user, get_user_role, start_user_session


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Đăng nhập hệ thống')
        self.setFixedSize(400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        title_label = QLabel("Đăng nhập hệ thống")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))

        subtitle_label = QLabel("Phần Mềm Quản Lý Phòng Khám")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 11))

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        username_layout = QHBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFixedWidth(120)
        username_label.setFont(QFont("Arial", 10))
        self.username_input = QLineEdit()
        self.username_input.setFont(QFont("Arial", 10))
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        password_layout = QHBoxLayout()
        password_label = QLabel("Mật khẩu:")
        password_label.setFixedWidth(120)
        password_label.setFont(QFont("Arial", 10))
        self.password_input = QLineEdit()
        self.password_input.setFont(QFont("Arial", 10))
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        self.remember_check = QCheckBox("Nhớ tài khoản, mật khẩu")
        self.remember_check.setFont(QFont("Arial", 10))
        self.remember_check.setChecked(True)

        button_layout = QHBoxLayout()
        login_button = QPushButton("Đăng nhập")
        login_button.setFont(QFont("Arial", 10, QFont.Bold))
        login_button.clicked.connect(self.handle_login)

        exit_button = QPushButton("Thoát")
        exit_button.setFont(QFont("Arial", 10))
        exit_button.clicked.connect(self.close)

        button_layout.addWidget(login_button)
        button_layout.addWidget(exit_button)

        form_layout.addLayout(username_layout)
        form_layout.addLayout(password_layout)
        form_layout.addWidget(self.remember_check)
        form_layout.addSpacing(10)
        form_layout.addLayout(button_layout)

        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(subtitle_label)
        layout.addSpacing(20)
        layout.addLayout(form_layout)

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

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        if self.authenticate(username, password):
            try:
                session_id = start_user_session(username)
            except Exception:
                session_id = None

            try:
                self._started_session_id = session_id
            except Exception:
                pass
            QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
            self.open_main_app()
        else:
            QMessageBox.critical(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")

    def authenticate(self, username, password):
        try:
            return verify_user(username, password)
        except Exception:
            return False

    def open_main_app(self):
        # [QUAN TRỌNG] Import MainApp bên trong hàm để tránh lỗi "Circular Import"
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
    font = QFont("Arial", 10)
    app.setFont(font)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())