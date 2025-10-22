# login.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Đăng nhập hệ thống')
        self.setFixedSize(400, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Title
        title_label = QLabel("Đăng nhập hệ thống")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        
        subtitle_label = QLabel("Phần Mềm Quản Lý Phòng Khám")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 11))
        
        # Form fields
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFixedWidth(120)
        username_label.setFont(QFont("Arial", 10))
        self.username_input = QLineEdit()
        self.username_input.setFont(QFont("Arial", 10))
        self.username_input.setText("pacsi")  # Default value
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
        self.password_input.setText("123")  # Default value
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
        
        # Add all to form layout
        form_layout.addLayout(username_layout)
        form_layout.addLayout(password_layout)
        form_layout.addWidget(self.remember_check)
        form_layout.addSpacing(10)
        form_layout.addLayout(button_layout)
        
        # Add all to main layout
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(subtitle_label)
        layout.addSpacing(20)
        layout.addLayout(form_layout)
        
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
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
        
        # Xử lý đăng nhập
        if self.authenticate(username, password):
            QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
            self.open_main_app()
        else:
            QMessageBox.critical(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu!")
    
    def authenticate(self, username, password):
        users = {
            "tieptan": "123",
            "bacsi": "123", 
            "pacsi": "123",
            "admin": "123"
        }
        
        return username in users and users[username] == password
    
    def open_main_app(self):
        from main_app import MainApp
        self.main_app = MainApp(self.username_input.text())
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