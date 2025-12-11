# quan_ly_tai_khoan.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QMessageBox, QHeaderView, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from database import (
    get_connection, create_user, get_user_role, 
    verify_user
)
from app_signals import app_signals
import hashlib


class QuanLyTaiKhoan(QWidget):
    """Form quản lý tài khoản cho Admin"""
    account_created = pyqtSignal()
    
    def __init__(self, current_username=None):
        super().__init__()
        self.current_username = current_username  # Username của admin đang đăng nhập
        self.initUI()
        self.load_accounts()
    
    def initUI(self):
        self.setFont(QFont("Arial", 10))
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Tiêu đề
        title = QLabel("Quản Lý Tài Khoản Hệ Thống")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #1976d2;")
        layout.addWidget(title)
        
        # ----- PHẦN FORM TẠO TÀI KHOẢN -----
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)
        
        # Tên đăng nhập
        form_layout.addWidget(QLabel("Tên đăng nhập:"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Nhập tên đăng nhập (ít nhất 3 ký tự)")
        self.input_username.setMinimumWidth(150)
        form_layout.addWidget(self.input_username)
        
        # Mật khẩu
        form_layout.addWidget(QLabel("Mật khẩu:"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setPlaceholderText("Ít nhất 6 ký tự")
        self.input_password.setMinimumWidth(150)
        form_layout.addWidget(self.input_password)
        
        # Họ và tên
        form_layout.addWidget(QLabel("Họ và tên:"))
        self.input_fullname = QLineEdit()
        self.input_fullname.setPlaceholderText("Tên đầy đủ của người dùng")
        self.input_fullname.setMinimumWidth(150)
        form_layout.addWidget(self.input_fullname)
        
        # Phòng khám (tùy chọn) - để lưu vào bảng nhan_su khi tạo nhân sự
        form_layout.addWidget(QLabel("Phòng khám:"))
        self.input_phong_kham = QLineEdit()
        self.input_phong_kham.setPlaceholderText("Tên phòng khám (tùy chọn)")
        self.input_phong_kham.setMinimumWidth(150)
        form_layout.addWidget(self.input_phong_kham)
        
        # Vai trò
        form_layout.addWidget(QLabel("Vai trò:"))
        self.combo_role = QComboBox()
        self.combo_role.addItems(["tiep_tan", "bac_si", "duoc_si", "admin"])
        self.combo_role.setMinimumWidth(120)
        form_layout.addWidget(self.combo_role)
        
        # Nút
        btn_create = QPushButton("Tạo Tài Khoản")
        btn_create.setMinimumWidth(120)
        btn_create.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_create.clicked.connect(self.create_account)
        form_layout.addWidget(btn_create)
        
        layout.addLayout(form_layout)
        
        # Dòng phân cách
        separator = QLabel("")
        separator.setStyleSheet("border-top: 1px solid #ddd; margin: 10px 0;")
        layout.addWidget(separator)
        
        # ----- DANH SÁCH TÀI KHOẢN -----
        list_label = QLabel("Danh Sách Tài Khoản")
        list_label.setFont(QFont("Arial", 12, QFont.Bold))
        list_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(list_label)
        
        # Bảng
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Tên đăng nhập", "Họ và tên", "Vai trò", "Đổi mật khẩu", "Sửa", "Xóa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ddd;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #1976d2;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }
        """)
        layout.addWidget(self.table)
        
        # Nút tải lại
        btn_refresh = QPushButton("Tải lại")
        btn_refresh.setMaximumWidth(150)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0065b8;
            }
        """)
        btn_refresh.clicked.connect(self.load_accounts)
        layout.addWidget(btn_refresh)
    
    def create_account(self):
        """Tạo tài khoản mới"""
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()
        fullname = self.input_fullname.text().strip()
        role = self.combo_role.currentText()
        
        # Kiểm tra
        if not username or len(username) < 3:
            QMessageBox.warning(self, "Lỗi", "Tên đăng nhập phải có ít nhất 3 ký tự.")
            return
        
        if not password or len(password) < 6:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu phải có ít nhất 6 ký tự.")
            return
        
        if not fullname:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập họ và tên.")
            return
        
        # Kiểm tra username đã tồn tại
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Lỗi", f"Tên đăng nhập '{username}' đã tồn tại.")
                conn.close()
                return
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi kiểm tra tài khoản: {e}")
            return
        
        # Tạo tài khoản
        try:
            # Truyền full_name vào create_user để hàm bên DB có thể tạo bản ghi nhan_su với tên đầy đủ
            create_user(username, password, role, fullname)

            # Cập nhật họ và tên (dự phòng nếu create_user không cập nhật)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET full_name = ? WHERE username = ?", (fullname, username))
            conn.commit()

            # Nếu người dùng thuộc nhóm nhân sự (bác sĩ, tiếp tân, dược sĩ) và admin đã nhập
            # tên phòng khám, cập nhật cột phong_kham trong bảng nhan_su.
            phong_kham = self.input_phong_kham.text().strip()
            if phong_kham:
                try:
                    # Cập nhật theo tên đầy đủ nếu có, nếu không dùng username
                    display_name = fullname if fullname else username
                    cursor.execute("UPDATE nhan_su SET phong_kham = ? WHERE ten = ?", (phong_kham, display_name))
                    conn.commit()
                except Exception:
                    # Không bắt buộc — nếu không tồn tại bản ghi nhan_su thì bỏ qua
                    pass

            conn.close()
            
            QMessageBox.information(self, "Thành công", 
                f"Tài khoản '{username}' đã được tạo thành công.\nVai trò: {role}")
            
            # Xóa các ô nhập
            self.input_username.clear()
            self.input_password.clear()
            self.input_fullname.clear()
            self.input_phong_kham.clear()
            self.combo_role.setCurrentIndex(0)
            
            # Tải lại bảng
            self.load_accounts()
            self.account_created.emit()
            try:
                app_signals.data_changed.emit()
            except Exception:
                pass
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo tài khoản: {e}")
    
    def load_accounts(self):
        """Load danh sách tài khoản từ database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name, role FROM users ORDER BY username")
            accounts = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(0)
            
            for account in accounts:
                account_id, username, full_name, role = account
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Tên đăng nhập
                self.table.setItem(row, 0, QTableWidgetItem(username))
                
                # Họ và tên
                self.table.setItem(row, 1, QTableWidgetItem(full_name or ""))
                
                # Vai trò
                self.table.setItem(row, 2, QTableWidgetItem(role or "user"))
                
                # Nút Đổi mật khẩu
                btn_change_pass = QPushButton("Đổi MK")
                btn_change_pass.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: black;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #ffb300;
                    }
                """)
                btn_change_pass.clicked.connect(lambda checked, uid=account_id, uname=username: 
                    self.change_password(uid, uname))
                self.table.setCellWidget(row, 3, btn_change_pass)

                # Nút Sửa
                btn_edit = QPushButton("Sửa")
                btn_edit.setStyleSheet(btn_change_pass.styleSheet())
                btn_edit.clicked.connect(lambda checked, uid=account_id, uname=username: 
                    self.edit_account(uid, uname))
                self.table.setCellWidget(row, 4, btn_edit)

                # Nút Xóa
                btn_delete = QPushButton("Xóa")
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                btn_delete.clicked.connect(lambda checked, uid=account_id, uname=username: 
                    self.delete_account(uid, uname))
                self.table.setCellWidget(row, 5, btn_delete)
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách tài khoản: {e}")
    
    def change_password(self, user_id, username):
        """Đổi mật khẩu người dùng"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Đổi mật khẩu - {username}")
        dialog.setFixedSize(350, 150)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Mật khẩu hiện tại (xác minh tùy chọn)
        layout.addWidget(QLabel("Mật khẩu mới:"))
        input_new_pass = QLineEdit()
        input_new_pass.setEchoMode(QLineEdit.Password)
        input_new_pass.setPlaceholderText("Nhập mật khẩu mới (ít nhất 6 ký tự)")
        layout.addWidget(input_new_pass)
        
        # Xác nhận mật khẩu
        layout.addWidget(QLabel("Xác nhận mật khẩu:"))
        input_confirm_pass = QLineEdit()
        input_confirm_pass.setEchoMode(QLineEdit.Password)
        input_confirm_pass.setPlaceholderText("Xác nhận mật khẩu")
        layout.addWidget(input_confirm_pass)
        
        # Các nút
        button_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Hủy")
        
        def on_ok():
            new_pass = input_new_pass.text().strip()
            confirm_pass = input_confirm_pass.text().strip()
            
            if not new_pass or len(new_pass) < 6:
                QMessageBox.warning(dialog, "Lỗi", "Mật khẩu phải có ít nhất 6 ký tự.")
                return
            
            if new_pass != confirm_pass:
                QMessageBox.warning(dialog, "Lỗi", "Mật khẩu xác nhận không khớp.")
                return
            
            try:
                # Băm mật khẩu
                hashed_pass = hashlib.sha256(new_pass.encode()).hexdigest()
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                             (hashed_pass, user_id))
                conn.commit()
                conn.close()
                
                QMessageBox.information(dialog, "Thành công", 
                    f"Mật khẩu của '{username}' đã được đổi thành công.")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Lỗi", f"Không thể đổi mật khẩu: {e}")
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)
        
        button_layout.addWidget(btn_ok)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def edit_account(self, user_id, username):
        """Sửa thông tin tài khoản (họ tên, vai trò, phòng khám)"""
        # Lấy dữ liệu hiện tại
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username, full_name, role FROM users WHERE id = ?", (user_id,))
            r = cursor.fetchone()
            conn.close()
            if not r:
                QMessageBox.warning(self, "Lỗi", "Tài khoản không tồn tại.")
                return
            _, cur_fullname, cur_role = r[0], r[1], r[2]
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin tài khoản: {e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa tài khoản - {username}")
        dialog.setFixedSize(400, 220)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Họ và tên
        layout.addWidget(QLabel("Họ và tên:"))
        input_full = QLineEdit()
        input_full.setText(cur_fullname or "")
        layout.addWidget(input_full)

        # Vai trò
        layout.addWidget(QLabel("Vai trò:"))
        combo_role = QComboBox()
        combo_role.addItems(["tiep_tan", "bac_si", "duoc_si", "admin"])
        if cur_role in ["tiep_tan", "bac_si", "duoc_si", "admin"]:
            combo_role.setCurrentText(cur_role)
        layout.addWidget(combo_role)

        # Phòng khám (lấy từ nhan_su nếu có)
        layout.addWidget(QLabel("Phòng Khám:"))
        input_phong = QLineEdit()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Tìm theo full_name trước, nếu không có thử username
            search_name = cur_fullname if cur_fullname else username
            cursor.execute("SELECT phong_kham FROM nhan_su WHERE ten = ?", (search_name,))
            rr = cursor.fetchone()
            if rr and rr[0]:
                input_phong.setText(rr[0])
            conn.close()
        except Exception:
            pass
        layout.addWidget(input_phong)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Lưu")
        btn_cancel = QPushButton("Hủy")

        def on_save():
            new_full = input_full.text().strip()
            new_role = combo_role.currentText()
            new_phong = input_phong.text().strip()

            if not new_full:
                QMessageBox.warning(dialog, "Lỗi", "Họ và tên không được trống.")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                # Cập nhật users
                cursor.execute("UPDATE users SET full_name = ?, role = ? WHERE id = ?", (new_full, new_role, user_id))
                conn.commit()

                # Cập nhật hoặc tạo bản ghi nhan_su nếu role là nhân sự
                role_map = {
                    'tiep_tan': 'Tiếp tân',
                    'bac_si': 'Bác sĩ',
                    'duoc_si': 'Dược sĩ'
                }
                if new_role in role_map:
                    display_role = role_map[new_role]
                    # Kiểm tra tồn tại theo tên
                    cursor.execute("SELECT id FROM nhan_su WHERE ten = ?", (new_full,))
                    found = cursor.fetchone()
                    if found:
                        cursor.execute("UPDATE nhan_su SET chuc_vu = ?, phong_kham = ? WHERE id = ?", (display_role, new_phong if new_phong else None, found[0]))
                    else:
                        # Tạo mới
                        cursor.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, ?, ?)", (new_full, display_role, new_phong if new_phong else None))
                    conn.commit()
                else:
                    # Nếu đổi vai trò sang không phải nhân sự, xóa bản ghi nhan_su nếu có
                    try:
                        cursor.execute("DELETE FROM nhan_su WHERE ten = ?", (new_full,))
                        conn.commit()
                    except Exception:
                        pass

                conn.close()
                QMessageBox.information(dialog, "Thành công", "Thông tin tài khoản đã được cập nhật.")
                dialog.accept()
                self.load_accounts()
                try:
                    app_signals.data_changed.emit()
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(dialog, "Lỗi", f"Không thể lưu thay đổi: {e}")

        btn_ok.clicked.connect(on_save)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        dialog.exec_()
    
    def delete_account(self, user_id, username):
        """Xóa tài khoản"""
        # Không cho xóa admin đang đăng nhập
        if self.current_username and username == self.current_username:
            QMessageBox.warning(self, "Không thể xóa", 
                "Bạn không thể xóa tài khoản của chính mình!\n\nHãy yêu cầu admin khác xóa.")
            return
        
        reply = QMessageBox.warning(self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa tài khoản '{username}'?\n\nHành động này không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Kiểm tra nếu là admin cuối cùng
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user_role = cursor.fetchone()
            
            if user_role and user_role[0] == 'admin' and admin_count <= 1:
                conn.close()
                QMessageBox.warning(self, "Lỗi", "Không thể xóa admin cuối cùng trong hệ thống.")
                return
            
            # Lấy full_name trước khi xóa để cập nhật nhan_su
            cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            full_name = row[0] if row and row[0] else None

            # Thực hiện xóa user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

            # Cập nhật/ xóa bản ghi trong nhan_su nếu tồn tại cùng tên
            try:
                if full_name:
                    cursor.execute("DELETE FROM nhan_su WHERE ten = ?", (full_name,))
                # luôn cố gắng xóa bản ghi có username trùng nếu có
                cursor.execute("DELETE FROM nhan_su WHERE ten = ?", (username,))
                conn.commit()
            except Exception:
                # không bắt buộc thành công
                pass

            conn.close()

            QMessageBox.information(self, "Thành công", 
                f"Tài khoản '{username}' đã được xóa.")

            self.load_accounts()
            try:
                app_signals.data_changed.emit()
            except Exception:
                pass
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa tài khoản: {e}")
