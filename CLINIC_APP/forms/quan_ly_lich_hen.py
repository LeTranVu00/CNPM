from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QHeaderView, QSizePolicy, QComboBox, QDateTimeEdit, QTextEdit
)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
from database import get_connection


class QuanLyLichHen(QWidget):
    """Form quản lý lịch hẹn - xem, hủy, reschedule lịch hẹn khám."""
    
    data_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản Lý Lịch Hẹn")
        self.init_ui()
        self.load_appointments()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        lbl_title = QLabel("QUẢN LÝ LỊCH HẸN KHÁM")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14pt; color: #1565c0;")
        layout.addWidget(lbl_title)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        lbl_search = QLabel("Tìm kiếm:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên bệnh nhân hoặc BS...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.filter_appointments)
        
        lbl_status = QLabel("Trạng thái:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tất cả", "chờ duyệt", "xác nhận", "hoàn thành", "đã hủy"])
        self.status_filter.setMaximumWidth(150)
        self.status_filter.currentTextChanged.connect(self.filter_appointments)
        
        filter_layout.addWidget(lbl_search)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(lbl_status)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        btn_confirm = QPushButton("✓ Xác Nhận")
        btn_confirm.clicked.connect(self.confirm_appointment)
        btn_confirm.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 10px;")
        
        btn_reschedule = QPushButton("📅 Rescheduling")
        btn_reschedule.clicked.connect(self.reschedule_appointment)
        btn_reschedule.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 10px;")
        
        btn_cancel = QPushButton("✗ Hủy Lịch")
        btn_cancel.clicked.connect(self.cancel_appointment)
        btn_cancel.setStyleSheet("background-color: #f44336; color: white; padding: 5px 10px;")
        
        btn_view = QPushButton("👁️ Chi Tiết")
        btn_view.clicked.connect(self.view_appointment)
        btn_view.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 10px;")
        
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_reschedule)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_view)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Bệnh Nhân", "Ngày Giờ", "Bác Sĩ", 
            "Loại Khám", "Trạng Thái", "Ghi Chú", "BN_ID"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setMinimumHeight(400)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Hide BN_ID column (for internal use)
        self.table.setColumnHidden(6, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        
        layout.addWidget(self.table)
    
    def load_appointments(self):
        """Tải danh sách lịch hẹn từ database."""
        self.table.setRowCount(0)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lh.id, lh.ho_ten, lh.ngay_gio, lh.bac_si, lh.loai_kham, 
                       lh.trang_thai, lh.ghi_chu, lh.benh_nhan_id
                FROM lich_hen lh
                ORDER BY lh.ngay_gio DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)
                
                # Store ID in Qt.UserRole of first column (invisible)
                ho_ten_item = QTableWidgetItem(row[1] or "")
                ho_ten_item.setData(Qt.UserRole, row[0])  # Store ID invisibly
                self.table.setItem(row_pos, 0, ho_ten_item)
                
                self.table.setItem(row_pos, 1, QTableWidgetItem(row[2] or ""))
                self.table.setItem(row_pos, 2, QTableWidgetItem(row[3] or ""))
                self.table.setItem(row_pos, 3, QTableWidgetItem(row[4] or ""))
                
                # Status column with color coding
                status_item = QTableWidgetItem(row[5] or "")
                if row[5] == "đã hủy":
                    status_item.setForeground(self.table.palette().color(self.table.palette().Foreground))
                    status_item.setBackground(self.table.palette().color(self.table.palette().HighlightedText))
                self.table.setItem(row_pos, 4, status_item)
                
                self.table.setItem(row_pos, 5, QTableWidgetItem(row[6] or ""))
                self.table.setItem(row_pos, 6, QTableWidgetItem(str(row[7] or "")))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải lịch hẹn: {e}")
    
    def filter_appointments(self):
        """Lọc lịch hẹn theo tìm kiếm và trạng thái."""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            ho_ten = self.table.item(row, 1).text().lower()
            trang_thai = self.table.item(row, 5).text()
            
            show_search = search_text in ho_ten or search_text in self.table.item(row, 3).text().lower()
            show_status = status_filter == "Tất cả" or trang_thai == status_filter
            
            show = show_search and show_status
            self.table.setRowHidden(row, not show)
    
    def get_selected_appointment(self):
        """Lấy lịch hẹn được chọn."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một lịch hẹn")
            return None
        return selected_rows[0].row()
    
    def confirm_appointment(self):
        """Xác nhận lịch hẹn (chuyển từ 'chờ duyệt' -> 'xác nhận')."""
        row = self.get_selected_appointment()
        if row is None:
            return
        
        lh_id = self.table.item(row, 0).data(Qt.UserRole)
        ho_ten = self.table.item(row, 0).text()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE lich_hen SET trang_thai = ? WHERE id = ?",
                          ("xác nhận", lh_id))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Thành công", f"Đã xác nhận lịch hẹn cho {ho_ten}")
            self.load_appointments()
            self.data_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xác nhận: {e}")
    
    def reschedule_appointment(self):
        """Chỉnh lại lịch hẹn."""
        row = self.get_selected_appointment()
        if row is None:
            return
        
        lh_id = self.table.item(row, 0).data(Qt.UserRole)
        ho_ten = self.table.item(row, 0).text()
        ngay_gio_cu = self.table.item(row, 1).text()
        bac_si = self.table.item(row, 2).text()
        loai_kham = self.table.item(row, 3).text()
        ghi_chu = self.table.item(row, 5).text()
        
        dialog = RescheduleDialog(self, ho_ten, ngay_gio_cu, bac_si, loai_kham, ghi_chu)
        if dialog.exec_():
            new_ngay_gio, new_bac_si, new_loai_kham, new_ghi_chu = dialog.get_data()
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE lich_hen 
                    SET ngay_gio = ?, bac_si = ?, loai_kham = ?, ghi_chu = ?
                    WHERE id = ?
                """, (new_ngay_gio, new_bac_si, new_loai_kham, new_ghi_chu, lh_id))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Thành công", f"Đã rescheduling lịch hẹn cho {ho_ten}")
                self.load_appointments()
                self.data_saved.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể reschedule: {e}")
    
    def cancel_appointment(self):
        """Hủy lịch hẹn."""
        row = self.get_selected_appointment()
        if row is None:
            return
        
        lh_id = self.table.item(row, 0).data(Qt.UserRole)
        ho_ten = self.table.item(row, 0).text()
        trang_thai = self.table.item(row, 4).text()
        
        if trang_thai == "đã hủy":
            QMessageBox.warning(self, "Thông báo", "Lịch hẹn này đã bị hủy rồi")
            return
        
        reply = QMessageBox.question(self, "Xác nhận", 
                                     f"Bạn chắc chắn muốn hủy lịch hẹn cho {ho_ten}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE lich_hen SET trang_thai = ? WHERE id = ?",
                              ("đã hủy", lh_id))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Thành công", f"Đã hủy lịch hẹn cho {ho_ten}")
                self.load_appointments()
                self.data_saved.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể hủy: {e}")
    
    def view_appointment(self):
        """Xem chi tiết lịch hẹn."""
        row = self.get_selected_appointment()
        if row is None:
            return
        
        lh_id = self.table.item(row, 0).data(Qt.UserRole)
        ho_ten = self.table.item(row, 0).text()
        ngay_gio = self.table.item(row, 1).text()
        bac_si = self.table.item(row, 2).text()
        loai_kham = self.table.item(row, 3).text()
        trang_thai = self.table.item(row, 4).text()
        ghi_chu = self.table.item(row, 5).text()
        
        msg = f"""
        CHI TIẾT LỊCH HẸN
        ─────────────────
        ID: {lh_id}
        Bệnh nhân: {ho_ten}
        Ngày giờ: {ngay_gio}
        Bác sĩ: {bac_si}
        Loại khám: {loai_kham}
        Trạng thái: {trang_thai}
        Ghi chú: {ghi_chu or "(Không có)"}
        """
        
        QMessageBox.information(self, "Chi Tiết Lịch Hẹn", msg)


class RescheduleDialog(QDialog):
    """Dialog để reschedule lịch hẹn."""
    
    def __init__(self, parent=None, ho_ten="", ngay_gio="", bac_si="", loai_kham="", ghi_chu=""):
        super().__init__(parent)
        self.setWindowTitle("Rescheduling Lịch Hẹn")
        self.setGeometry(100, 100, 450, 350)
        self.init_ui(ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu)
    
    def init_ui(self, ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu):
        layout = QFormLayout(self)
        
        lbl_title = QLabel("Rescheduling Lịch Hẹn")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #1565c0;")
        layout.addRow(lbl_title)
        
        # Display patient name (read-only)
        lbl_bn = QLabel(ho_ten)
        lbl_bn.setStyleSheet("font-weight: bold; color: #1565c0;")
        layout.addRow("Bệnh nhân:", lbl_bn)
        
        # New date/time
        self.input_ngay_gio = QDateTimeEdit()
        self.input_ngay_gio.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.input_ngay_gio.setDateTime(QDateTime.fromString(ngay_gio, "yyyy-MM-dd HH:mm"))
        layout.addRow("Ngày giờ mới:", self.input_ngay_gio)
        
        # Doctor selection (editable - can type new values)
        self.combo_bac_si = QComboBox()
        self.combo_bac_si.setEditable(True)
        self.load_doctors()
        if bac_si:
            idx = self.combo_bac_si.findText(bac_si)
            if idx >= 0:
                self.combo_bac_si.setCurrentIndex(idx)
            else:
                self.combo_bac_si.setEditText(bac_si)
        layout.addRow("Bác sĩ:", self.combo_bac_si)
        
        # Visit type selection (editable - can type new values)
        self.combo_loai_kham = QComboBox()
        self.combo_loai_kham.setEditable(True)
        self.load_loai_kham()
        if loai_kham:
            idx = self.combo_loai_kham.findText(loai_kham)
            if idx >= 0:
                self.combo_loai_kham.setCurrentIndex(idx)
            else:
                self.combo_loai_kham.setEditText(loai_kham)
        layout.addRow("Loại khám:", self.combo_loai_kham)
        
        # Notes
        self.input_ghi_chu = QTextEdit()
        self.input_ghi_chu.setText(ghi_chu)
        self.input_ghi_chu.setMinimumHeight(80)
        layout.addRow("Ghi chú:", self.input_ghi_chu)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Lưu")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
    
    def load_doctors(self):
        """Tải danh sách bác sĩ."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ten FROM bac_si ORDER BY ten")
            doctors = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.combo_bac_si.addItems(doctors)
        except Exception:
            pass
    
    def load_loai_kham(self):
        """Tải danh sách loại khám."""
        try:
            # Predefined visit types
            loai_kham_list = ["Khám tư vấn", "Tái khám", "Khám theo yêu cầu"]
            self.combo_loai_kham.addItems(loai_kham_list)
        except Exception:
            pass
    
    def get_data(self):
        """Lấy dữ liệu reschedule."""
        ngay_gio = self.input_ngay_gio.dateTime().toString("yyyy-MM-dd HH:mm")
        bac_si = self.combo_bac_si.currentText()
        loai_kham = self.combo_loai_kham.currentText()
        ghi_chu = self.input_ghi_chu.toPlainText().strip()
        
        return ngay_gio, bac_si, loai_kham, ghi_chu
