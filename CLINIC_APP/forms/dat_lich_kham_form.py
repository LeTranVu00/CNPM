from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox, QHBoxLayout, QDateTimeEdit, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtCore import Qt
from database import get_connection

class DatLichKhamForm(QWidget):
    def __init__(self, parent=None, role=None):
        super().__init__(parent)
        self.role = role
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Tab 1: Đặt lịch khám (form cũ)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setSpacing(18)

        self.input_ho_ten = QLineEdit()
        self.input_ho_ten.setPlaceholderText("Họ tên bệnh nhân")
        self.input_ho_ten.setMinimumHeight(40)
        self.input_ho_ten.setStyleSheet("font-size: 18px;")

        self.input_ngay_gio = QDateTimeEdit(QDateTime.currentDateTime())
        self.input_ngay_gio.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.input_ngay_gio.setCalendarPopup(True)
        self.input_ngay_gio.setMinimumHeight(40)
        self.input_ngay_gio.setStyleSheet("font-size: 18px;")

        self.combo_bac_si = QComboBox()
        self.combo_bac_si.setMinimumHeight(40)
        self.combo_bac_si.setStyleSheet("font-size: 18px;")
        self.combo_bac_si.addItem("Nhấn để chọn bác sĩ")

        self.combo_loai_kham = QComboBox()
        self.combo_loai_kham.setMinimumHeight(40)
        self.combo_loai_kham.setStyleSheet("font-size: 18px;")
        self.combo_loai_kham.addItem("Nhấn để chọn loại khám")

        self.input_ghi_chu = QLineEdit()
        self.input_ghi_chu.setPlaceholderText("Ghi chú")
        self.input_ghi_chu.setMinimumHeight(40)
        self.input_ghi_chu.setStyleSheet("font-size: 18px;")

        # Các ô nhập SĐT và địa chỉ
        self.input_dien_thoai = QLineEdit()
        self.input_dien_thoai.setPlaceholderText("Số điện thoại (không bắt buộc)")
        self.input_dien_thoai.setMinimumHeight(36)
        self.input_dien_thoai.setStyleSheet("font-size: 16px;")

        self.input_dia_chi = QLineEdit()
        self.input_dia_chi.setPlaceholderText("Địa chỉ (không bắt buộc)")
        self.input_dia_chi.setMinimumHeight(36)
        self.input_dia_chi.setStyleSheet("font-size: 16px;")

        form_layout.addRow("Họ tên bệnh nhân:", self.input_ho_ten)
        form_layout.addRow("Ngày & Giờ:", self.input_ngay_gio)
        form_layout.addRow("Bác sĩ:", self.combo_bac_si)
        form_layout.addRow("Loại khám:", self.combo_loai_kham)
        form_layout.addRow("Ghi chú:", self.input_ghi_chu)
        form_layout.addRow("Số điện thoại:", self.input_dien_thoai)
        form_layout.addRow("Địa chỉ:", self.input_dia_chi)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        self.btn_save = QPushButton("Lưu lịch hẹn")
        self.btn_save.setMinimumHeight(44)
        self.btn_save.setMinimumWidth(180)
        self.btn_save.setStyleSheet("font-size: 18px; background:#1976d2; color:white; border-radius:7px;")
        self.btn_save.clicked.connect(self.save_appointment)
        btn_layout.addWidget(self.btn_save)
        form_layout.addRow(btn_layout)

        tabs.addTab(form_widget, "Đặt lịch khám")

        # Tab 2: Lịch sử bệnh nhân đã đặt
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        # Bộ lọc ngày tháng
        filter_layout = QHBoxLayout()
        self.filter_from = QDateTimeEdit()
        self.filter_from.setCalendarPopup(True)
        self.filter_from.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.filter_to = QDateTimeEdit()
        self.filter_to.setCalendarPopup(True)
        self.filter_to.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.btn_search_history = QPushButton("Tìm kiếm")
        self.btn_search_history.setMinimumWidth(100)
        self.btn_reload_history = QPushButton("Tải lại")
        self.btn_reload_history.setMinimumWidth(100)
        filter_layout.addWidget(QLabel("Từ ngày:"))
        filter_layout.addWidget(self.filter_from)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        filter_layout.addWidget(self.filter_to)
        filter_layout.addWidget(self.btn_search_history)
        filter_layout.addWidget(self.btn_reload_history)
        filter_layout.addStretch()
        history_layout.addLayout(filter_layout)

        # Thêm cột phụ cho nút 'Xem'
        # Các cột: ID, Họ tên, SĐT, Địa chỉ, Ngày & Giờ, Bác sĩ, Loại khám, Ghi chú, Xem
        self.table_history = QTableWidget(0, 9)
        self.table_history.setHorizontalHeaderLabels(["ID", "Họ tên", "SĐT", "Địa chỉ", "Ngày & Giờ", "Bác sĩ", "Loại khám", "Ghi chú", "Xem"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setAlternatingRowColors(True)
        history_layout.addWidget(self.table_history)
        tabs.addTab(history_widget, "Lịch sử đặt lịch")

        self.load_doctors_and_rooms()
        self.load_history_data()

        # Kết nối nút 'Tải lại' với hàm tải lại dữ liệu lịch sử
        self.btn_reload_history.clicked.connect(self.load_history)
        # Kết nối nút 'Tìm kiếm' với hàm lọc theo ngày
        self.btn_search_history.clicked.connect(self.search_history_by_date)

    def search_history_by_date(self):
        from_dt = self.filter_from.dateTime().toString("yyyy-MM-dd HH:mm")
        to_dt = self.filter_to.dateTime().toString("yyyy-MM-dd HH:mm")
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Bao gồm số điện thoại, địa chỉ và nguoi_dat để có thể hiển thị chi tiết
            cur.execute("""
                SELECT id, ho_ten, dien_thoai, dia_chi, ngay_gio, bac_si, loai_kham, ghi_chu, nguoi_dat
                FROM lich_hen
                WHERE ngay_gio >= ? AND ngay_gio <= ?
                ORDER BY id ASC
            """, (from_dt, to_dt))
            rows = cur.fetchall()
        finally:
            conn.close()
        self.table_history.setRowCount(0)
        for r in rows:
            row = self.table_history.rowCount()
            self.table_history.insertRow(row)
            # r mong đợi: (id, ho_ten, dien_thoai, dia_chi, ngay_gio, bac_si, loai_kham, ghi_chu, nguoi_dat)
            for c, v in enumerate(r[:-1]):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_history.setItem(row, c, item)
            # Cột cuối: nút 'Xem' (chỉ số cột 8)
            from PyQt5.QtWidgets import QPushButton
            btn = QPushButton("Xem")
            btn.setProperty('lh_id', r[0])
            btn.clicked.connect(lambda checked, _id=r[0]: self.view_history_detail(_id))
            self.table_history.setCellWidget(row, 8, btn)

    def load_doctors_and_rooms(self):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ten FROM nhan_su WHERE chuc_vu = 'Bác sĩ' ORDER BY ten ASC")
            doctors = [r[0] for r in cur.fetchall()]
            self.combo_bac_si.clear()
            self.combo_bac_si.addItem("Nhấn để chọn bác sĩ")
            self.combo_bac_si.addItems(doctors)

            # Các loại khám định sẵn
            loai_kham_list = ["Khám tư vấn", "Tái khám", "Khám theo yêu cầu"]
            self.combo_loai_kham.clear()
            self.combo_loai_kham.addItem("Nhấn để chọn loại khám")
            self.combo_loai_kham.addItems(loai_kham_list)
        finally:
            conn.close()

    def load_history_data(self):
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Bao gồm số điện thoại, địa chỉ và nguoi_dat để hiển thị trong view chi tiết
            cur.execute("SELECT id, ho_ten, dien_thoai, dia_chi, ngay_gio, bac_si, loai_kham, ghi_chu, nguoi_dat FROM lich_hen ORDER BY id ASC")
            rows = cur.fetchall()
        finally:
            conn.close()
        self.table_history.setRowCount(0)
        for r in rows:
            row = self.table_history.rowCount()
            self.table_history.insertRow(row)
            # r mong đợi: (id, ho_ten, dien_thoai, dia_chi, ngay_gio, bac_si, loai_kham, ghi_chu, nguoi_dat)
            for c, v in enumerate(r[:-1]):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_history.setItem(row, c, item)
            # Thêm nút xem ở cột cuối (index 8)
            from PyQt5.QtWidgets import QPushButton
            btn = QPushButton("Xem")
            btn.setProperty('lh_id', r[0])
            btn.clicked.connect(lambda checked, _id=r[0]: self.view_history_detail(_id))
            self.table_history.setCellWidget(row, 8, btn)

    def load_history(self):
        self.load_history_data()

    def save_appointment(self):
        ho_ten = self.input_ho_ten.text().strip()
        ngay_gio = self.input_ngay_gio.dateTime().toString("yyyy-MM-dd HH:mm")
        bac_si = self.combo_bac_si.currentText().strip()
        loai_kham = self.combo_loai_kham.currentText().strip()
        ghi_chu = self.input_ghi_chu.text().strip()
        if not ho_ten or not ngay_gio or bac_si == "Nhấn để chọn bác sĩ" or loai_kham == "Nhấn để chọn loại khám":
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin và chọn bác sĩ, loại khám!")
            return
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # Xác định người đặt dựa trên role
            nguoi_dat = "Bệnh nhân"  # Mặc định là bệnh nhân
            if self.role == 'tiep_tan':
                nguoi_dat = "Tiếp tân"
            elif self.role == 'bac_si':
                nguoi_dat = "Bác sĩ"
            elif self.role == 'admin':
                nguoi_dat = "Admin"
            
            cur.execute("INSERT INTO lich_hen (ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu, trang_thai, nguoi_dat, dien_thoai, dia_chi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu, "Chưa duyệt", nguoi_dat, self.input_dien_thoai.text().strip(), self.input_dia_chi.text().strip()))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Thành công", "Đã lưu lịch hẹn!")
            self.input_ho_ten.clear()
            self.input_ngay_gio.setDateTime(QDateTime.currentDateTime())
            self.combo_bac_si.setCurrentIndex(0)
            self.combo_loai_kham.setCurrentIndex(0)
            self.input_ghi_chu.clear()
            self.input_dien_thoai.clear()
            self.input_dia_chi.clear()
            self.load_history_data()  # Tải lại dữ liệu lịch sử
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu lịch hẹn:\n{e}")

    def view_history_detail(self, lh_id: int):
        """Show appointment details including who placed it."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, ho_ten, dien_thoai, dia_chi, ngay_gio, bac_si, loai_kham, ghi_chu, nguoi_dat FROM lich_hen WHERE id = ?", (lh_id,))
            r = cur.fetchone()
            conn.close()
            if not r:
                QMessageBox.warning(self, "Không tìm thấy", "Không tìm thấy lịch hẹn này.")
                return
            msg = f"""

ID: {r[0]}
Bệnh nhân: {r[1]}
Số điện thoại: {r[2] or '(Không có)'}
Địa chỉ: {r[3] or '(Không có)'}
Ngày giờ: {r[4]}
Bác sĩ: {r[5]}
Loại khám: {r[6]}
Ghi chú: {r[7] or '(Không có)'}
Người đặt: {r[8] or '(Không xác định)'}
"""
            QMessageBox.information(self, "Chi tiết lịch hẹn", msg)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lấy chi tiết: {e}")
