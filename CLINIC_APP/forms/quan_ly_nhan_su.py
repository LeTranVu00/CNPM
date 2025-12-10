from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QHeaderView, QSizePolicy, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from database import get_connection
from app_signals import app_signals


class QuanLyNhanSu(QWidget):
    """Form quản lý nhân sự (bác sĩ, tiếp tân, dược sĩ) - thêm/sửa/xóa thông tin nhân viên."""
    
    data_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Nhân Sự")
        self.init_ui()
        self.load_staff()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        lbl_title = QLabel("QUẢN LÝ NHÂN SỰ")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14pt; color: #1565c0;")
        layout.addWidget(lbl_title)
        
        # Search bar
        search_layout = QHBoxLayout()
        lbl_search = QLabel("Tìm kiếm:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên hoặc chức vụ...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.filter_staff)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.search_input)
        # Role filter
        self.role_filter = QComboBox()
        self.role_filter.addItem("Tất cả")
        self.role_filter.addItem("Bác sĩ")
        self.role_filter.addItem("Tiếp tân")
        self.role_filter.addItem("Dược sĩ")
        self.role_filter.currentIndexChanged.connect(self.load_staff)
        search_layout.addWidget(self.role_filter)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm nhân viên")
        btn_add.clicked.connect(self.open_add_dialog)
        btn_edit = QPushButton("✏️ Sửa")
        btn_edit.clicked.connect(self.open_edit_dialog)
        btn_delete = QPushButton("🗑️ Xóa")
        btn_delete.clicked.connect(self.delete_staff)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Tên", "Chức Vụ", "Phòng Khám"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setMinimumHeight(400)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 120)
        
        layout.addWidget(self.table)
        # Listen for global user_created signal to refresh staff list when accounts are created
        try:
            app_signals.user_created.connect(lambda u, r, f: self.load_staff())
        except Exception:
            pass
    
    def load_staff(self):
        """Tải danh sách nhân sự từ database, hỗ trợ lọc theo chức vụ."""
        # Ensure users table is synced into nhan_su so accounts appear here
        try:
            from database import sync_users_to_nhan_su
            sync_users_to_nhan_su()
        except Exception:
            pass
        self.table.setRowCount(0)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            role = self.role_filter.currentText() if hasattr(self, 'role_filter') else 'Tất cả'
            if role and role != 'Tất cả':
                cursor.execute("SELECT id, ten, chuc_vu, phong_kham FROM nhan_su WHERE chuc_vu = ? ORDER BY ten", (role,))
            else:
                cursor.execute("SELECT id, ten, chuc_vu, phong_kham FROM nhan_su ORDER BY ten")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                # Name column stores ID in UserRole
                name_item = QTableWidgetItem(row[1] or "")
                name_item.setData(Qt.UserRole, row[0])
                self.table.setItem(row_pos, 0, name_item)

                self.table.setItem(row_pos, 1, QTableWidgetItem(row[2] or ""))
                self.table.setItem(row_pos, 2, QTableWidgetItem(row[3] or ""))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách: {e}")
    
    def filter_staff(self):
        """Lọc nhân sự theo tên hoặc chức vụ."""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().lower() if self.table.item(row, 0) else ''
            role = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ''
            show = search_text in name or search_text in role
            self.table.setRowHidden(row, not show)
    
    def open_add_dialog(self):
        """Mở dialog thêm nhân viên mới."""
        dialog = StaffDialog(self, mode="add")
        if dialog.exec_():
            ten, chuc_vu, phong_kham = dialog.get_data()
            self.add_staff(ten, chuc_vu, phong_kham)
    
    def open_edit_dialog(self):
        """Mở dialog sửa thông tin nhân viên."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một nhân viên để sửa")
            return

        row = selected_rows[0].row()
        ns_id = self.table.item(row, 0).data(Qt.UserRole)
        ten = self.table.item(row, 0).text()
        chuc_vu = self.table.item(row, 1).text()
        phong_kham = self.table.item(row, 2).text()

        dialog = StaffDialog(self, mode="edit", ten=ten, chuc_vu=chuc_vu, phong_kham=phong_kham)
        if dialog.exec_():
            new_ten, new_chuc_vu, new_phong_kham = dialog.get_data()
            self.update_staff(ns_id, new_ten, new_chuc_vu, new_phong_kham)
    
    def add_staff(self, ten, chuc_vu, phong_kham):
        """Thêm nhân viên mới vào database."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, ?, ?)",
                          (ten, chuc_vu, phong_kham))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Thành công", f"Đã thêm nhân viên {ten}")
            self.load_staff()
            self.data_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm nhân viên: {e}")
    
    def update_staff(self, ns_id, ten, chuc_vu, phong_kham):
        """Cập nhật thông tin nhân viên."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE nhan_su SET ten = ?, chuc_vu = ?, phong_kham = ? WHERE id = ?",
                          (ten, chuc_vu, phong_kham, ns_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Thành công", f"Đã cập nhật nhân viên {ten}")
            self.load_staff()
            self.data_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")
    
    def delete_staff(self):
        """Xóa nhân viên từ database."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một nhân viên để xóa")
            return

        row = selected_rows[0].row()
        ns_id = self.table.item(row, 0).data(Qt.UserRole)
        ten = self.table.item(row, 0).text()

        reply = QMessageBox.question(self, "Xác nhận", 
                                     f"Bạn chắc chắn muốn xóa nhân viên {ten}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM nhan_su WHERE id = ?", (ns_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Thành công", f"Đã xóa nhân viên {ten}")
                self.load_staff()
                self.data_saved.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")


class StaffDialog(QDialog):
    """Dialog để thêm/sửa nhân viên (chức vụ, chuyên khoa)."""

    def __init__(self, parent=None, mode="add", ten="", chuc_vu="Bác sĩ", phong_kham=""):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("Thêm Nhân Viên" if mode == "add" else "Sửa Nhân Viên")
        self.setGeometry(100, 100, 420, 220)
        self.init_ui(ten, chuc_vu, phong_kham)

    def init_ui(self, ten, chuc_vu, phong_kham):
        layout = QFormLayout(self)

        lbl_title = QLabel("Thông tin Nhân Viên")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #1565c0;")
        layout.addRow(lbl_title)

        # Input fields
        self.input_ten = QLineEdit()
        self.input_ten.setText(ten)
        self.input_ten.setPlaceholderText("Ví dụ: Nguyễn Văn A")
        layout.addRow("Tên:", self.input_ten)

        self.input_chuc_vu = QComboBox()
        self.input_chuc_vu.addItems(["Bác sĩ", "Tiếp tân", "Dược sĩ"]) 
        if chuc_vu:
            idx = self.input_chuc_vu.findText(chuc_vu)
            if idx >= 0:
                self.input_chuc_vu.setCurrentIndex(idx)
        layout.addRow("Chức vụ:", self.input_chuc_vu)

        self.input_phong_kham = QLineEdit()
        self.input_phong_kham.setText(phong_kham)
        self.input_phong_kham.setPlaceholderText("Ví dụ: Phòng khám số 1")
        layout.addRow("Phòng Khám:", self.input_phong_kham)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Lưu")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

    def get_data(self):
        """Lấy dữ liệu nhập vào: trả về (ten, chuc_vu, phong_kham)."""
        ten = self.input_ten.text().strip()
        chuc_vu = self.input_chuc_vu.currentText()
        phong_kham = self.input_phong_kham.text().strip()

        if not ten:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên nhân viên")
            return None, None, None

        return ten, chuc_vu, phong_kham
