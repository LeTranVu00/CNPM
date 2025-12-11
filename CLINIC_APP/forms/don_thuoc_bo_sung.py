import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDateEdit,
    QSpinBox, QTableWidget, QTableWidgetItem, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QHeaderView, QDialog, QTableView, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QSortFilterProxyModel, pyqtSignal, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from database import get_connection
from signals import app_signals
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog


class ChonThuocDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn Thuốc")
        self.setGeometry(300, 200, 600, 400)
        self.selected_drug = None
        self.initUI()
        self.load_drugs()

    def initUI(self):
        layout = QVBoxLayout()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Mã thuốc", "Tên sản phẩm", "Tồn kho", "Đơn vị"])
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Tìm kiếm thuốc...")
        self.search_box.textChanged.connect(self.filter_drugs)
        layout.addWidget(self.search_box)
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table_view)
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Chọn")
        select_btn.clicked.connect(self.accept_selection)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_drugs(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ma_thuoc, ten_thuoc, ton_kho, don_vi FROM danh_muc_thuoc")
        drugs = cursor.fetchall()
        conn.close()
        for drug in drugs:
            ma_thuoc = QStandardItem(str(drug[0]))
            ten_thuoc = QStandardItem(str(drug[1]))
            ton_kho = QStandardItem(str(drug[2]))
            don_vi = QStandardItem(str(drug[3]) if len(drug) > 3 and drug[3] is not None else "")
            self.model.appendRow([ma_thuoc, ten_thuoc, ton_kho, don_vi])

    def filter_drugs(self, text):
        self.proxy_model.setFilterFixedString(text)

    def accept_selection(self):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            self.selected_drug = {
                'ma_thuoc': self.proxy_model.data(self.proxy_model.index(row, 0)),
                'ten_thuoc': self.proxy_model.data(self.proxy_model.index(row, 1)),
                'don_vi': self.proxy_model.data(self.proxy_model.index(row, 3))
            }
            self.accept()


class ChonLieuDungDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn Liều Dùng")
        self.setGeometry(300, 200, 600, 500)
        self.selected_dosage = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.model = QStandardItemModel()
        # 18 common Vietnamese dosage options
        common_doses = [
            "Ngày uống 1/2V sau ăn sáng",
            "Ngày uống 1/2V sau ăn tối",
            "Ngày uống 1/2V trước ăn sáng",
            "Ngày uống 1/2V trước ăn tối",
            "Ngày uống 1V sau ăn sáng",
            "Ngày uống 1V sau ăn tối",
            "Ngày uống 1V sau ăn trưa",
            "Ngày uống 1V trước ăn sáng",
            "Ngày uống 1V trước ăn tối",
            "Ngày uống 1V trước ăn trưa",
            "Ngày uống 2 lần sau ăn sáng và tối",
            "Ngày uống 2 lần trước ăn sáng và tối",
            "Ngày uống 3 lần sau ăn",
            "Ngày uống 3 lần trước ăn",
            "Dùng khi cần thiết",
            "Ngày 1 lần sau ăn sáng",
            "Ngày 1 lần sau ăn tối",
            "Ngày 1 lần trước khi ngủ"
        ]
        for d in common_doses:
            self.model.appendRow([QStandardItem(d)])

        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.horizontalHeader().hide()
        self.view.verticalHeader().hide()
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.SingleSelection)
        self.view.doubleClicked.connect(self.accept_selection)
        self.view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.view)

        btns = QHBoxLayout()
        ok = QPushButton("Chọn")
        ok.clicked.connect(self.accept_selection)
        cancel = QPushButton("Hủy")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def accept_selection(self):
        idxs = self.view.selectedIndexes()
        if idxs:
            text = self.model.data(idxs[0])
            self.selected_dosage = text
            self.accept()


class NhapGhiChuDialog(QDialog):
    def __init__(self, parent=None, current_text=""):
        super().__init__(parent)
        self.setWindowTitle("Nhập Ghi Chú")
        self.setGeometry(350, 250, 420, 220)
        self.note = None
        self.current_text = current_text
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Nhập ghi chú...")
        if self.current_text and self.current_text != "Nhấn để chọn":
            self.text_edit.setText(self.current_text)
        layout.addWidget(self.text_edit)

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept_note)
        cancel = QPushButton("Hủy")
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def accept_note(self):
        self.note = self.text_edit.toPlainText()
        # Chấp nhận ngay cả khi rỗng để người dùng có thể xóa ghi chú theo ý
        if self.note is not None:
            self.accept()


class PrescriptionDetailDialog(QDialog):
    def __init__(self, parent=None, don_thuoc_id=None, open_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Chi tiết đơn thuốc")
        self.setMinimumSize(700, 400)
        self.don_thuoc_id = don_thuoc_id
        self.open_callback = open_callback
        self.initUI()
        if don_thuoc_id:
            self.load_details(don_thuoc_id)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.info_label = QLabel("")
        self.layout.addWidget(self.info_label)
        self.detail_table = QTableWidget(0, 6)
        self.detail_table.setHorizontalHeaderLabels(["Mã", "Tên", "SL", "ĐV", "Liều dùng", "Ghi chú"])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.detail_table)
        btns = QHBoxLayout()
        self.open_btn = QPushButton("Mở vào form")
        self.open_btn.clicked.connect(self.open_in_form)
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.reject)
        btns.addWidget(self.open_btn)
        btns.addWidget(close_btn)
        self.layout.addLayout(btns)
        self.setLayout(self.layout)

    def load_details(self, don_thuoc_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ngay_ke, bac_si, nguoi_lap_phieu, loi_dan, phieu_kham_id, chan_doan FROM don_thuoc WHERE id = ?", (don_thuoc_id,))
            dt = cursor.fetchone()
            ngay_ke = bac_si = nguoilap = loi_dan = phieu_kham = chan_doan = None
            if dt:
                ngay_ke, bac_si, nguoilap, loi_dan, phieu_kham, chan_doan = dt
            # Cố gắng lấy số phiếu
            so_phieu = ''
            if phieu_kham:
                cursor.execute("SELECT so_phieu FROM phieu_kham WHERE id = ?", (phieu_kham,))
                p = cursor.fetchone()
                if p:
                    so_phieu = str(p[0])
            info = f"Ngày kê: {ngay_ke or ''}    Số phiếu: {so_phieu}    Bác sĩ: {bac_si or ''}    Người lập: {nguoilap or ''}"
            if loi_dan:
                info += f"\nLời dặn: {loi_dan}"
            if chan_doan:
                info += f"\nChẩn đoán: {chan_doan}"
            self.info_label.setText(info)
            # tải chi tiết
            cursor.execute("""
                SELECT ct.ma_thuoc, dm.ten_thuoc, ct.so_luong, ct.don_vi, ct.lieu_dung, ct.ghi_chu
                FROM chi_tiet_don_thuoc ct
                LEFT JOIN danh_muc_thuoc dm ON ct.ma_thuoc = dm.ma_thuoc
                WHERE ct.don_thuoc_id = ?
                ORDER BY ct.id
            """, (don_thuoc_id,))
            details = cursor.fetchall()
            conn.close()
            self.detail_table.setRowCount(0)
            for r, d in enumerate(details):
                self.detail_table.insertRow(r)
                ma, ten, soluong, donvi, lieudung, ghichu = d
                self.detail_table.setItem(r, 0, QTableWidgetItem(str(ma) if ma else ""))
                self.detail_table.setItem(r, 1, QTableWidgetItem(str(ten) if ten else ""))
                self.detail_table.setItem(r, 2, QTableWidgetItem(str(soluong) if soluong is not None else ""))
                self.detail_table.setItem(r, 3, QTableWidgetItem(str(donvi) if donvi else ""))
                self.detail_table.setItem(r, 4, QTableWidgetItem(str(lieudung) if lieudung else ""))
                self.detail_table.setItem(r, 5, QTableWidgetItem(str(ghichu) if ghichu else ""))
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải chi tiết: {e}")

    def open_in_form(self):
        if callable(self.open_callback):
            self.open_callback(self.don_thuoc_id)
        self.accept()


class DonThuocKhac(QWidget):
    def show_chandoan_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết chẩn đoán")
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(self.chandoan.text() if hasattr(self, 'chandoan') else "")
        layout.addWidget(text_edit)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec_()

    def show_diung_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết dị ứng")
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(self.diung.text() if hasattr(self, 'diung') else "")
        layout.addWidget(text_edit)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec_()
    # Signal để thông báo khi dữ liệu được xuất
    medicine_exported = pyqtSignal()
    
    def __init__(self, phieu_kham_id=None, benh_nhan_id=None):
        super().__init__()
        self.setWindowTitle("ĐƠN THUỐC KHÁC")
        self.setGeometry(200, 100, 1200, 750)
        self._suppress_item_changed = False
        self.phieu_kham_id = phieu_kham_id
        self.benh_nhan_id = benh_nhan_id
        self.last_don_thuoc_id = None
        self.initUI()
        self.load_patients()
        self.load_bacsi_list()
        self.load_nguoilap_list()
        # Đăng ký nhận sự kiện chọn bệnh nhân toàn ứng dụng để các form khác có thể cập nhật
        try:
            app_signals.patient_selected.connect(self.auto_select_patient)
        except Exception:
            pass
        if self.benh_nhan_id:
            try:
                self.auto_select_patient(self.benh_nhan_id)
            except Exception:
                pass

    def initUI(self):
        main_layout = QVBoxLayout()

        # ======= THÔNG TIN ĐƠN THUỐC =======
        group_info = QGroupBox("THÔNG TIN ĐƠN THUỐC")
        # Dùng màu đen mặc định cho tiêu đề nhóm để văn bản trông chuẩn và trung tính
        group_info.setStyleSheet("QGroupBox { font-weight: bold; color: #000000; }")
        grid = QGridLayout()

        self.benhnhan = QComboBox()
        self.benhnhan.currentIndexChanged.connect(self.on_patient_selected)
        # Also load on editingFinished for manual input
        if hasattr(self.benhnhan, 'lineEdit') and self.benhnhan.lineEdit():
            self.benhnhan.lineEdit().editingFinished.connect(self.on_patient_manual_select)
        self.ngaysinh = QDateEdit(QDate.currentDate())
        self.ngaysinh.setCalendarPopup(True)
        self.ngaysinh.setReadOnly(True)
        self.gioitinh = QLineEdit()
        self.gioitinh.setReadOnly(True)
        self.dienthoai = QLineEdit()
        self.dienthoai.setReadOnly(True)
        self.tuoi = QLineEdit("20 tuổi")
        self.tuoi.setReadOnly(True)
        self.diachi = QLineEdit()
        self.diachi.setReadOnly(True)
        self.chandoan = QLineEdit()
        self.diung = QLineEdit()
        self.diung.setReadOnly(True)
        self.sohoso = QLineEdit()
        self.sohoso.setReadOnly(True)
        self.sophieukham = QLineEdit()
        self.sophieukham.setReadOnly(True)
        self.ngaykedon = QDateEdit(QDate.currentDate())
        self.ngaykedon.setCalendarPopup(True)
        self.songay = QSpinBox()
        self.songay.setMinimum(1)
        self.loaithuoc = QComboBox()
        self.loaithuoc.addItems(["Thuốc khác", "Thuốc cơ bản"])
        self.bacsi = QComboBox()
        self.bacsi.addItems(["Bác sĩ"])
        self.nguoilap = QComboBox()
        self.nguoilap.addItems(["Bác sĩ"])
        self.doncu = QComboBox()
        self.doncu.currentIndexChanged.connect(self.on_doncu_changed)
        self.donmau = QComboBox()

        # Hàng 1
        grid.addWidget(QLabel("Bệnh nhân"), 0, 0)
        grid.addWidget(self.benhnhan, 0, 1)
        grid.addWidget(QLabel("Ngày sinh"), 0, 2)
        grid.addWidget(self.ngaysinh, 0, 3)
        grid.addWidget(QLabel("Giới tính"), 0, 4)
        grid.addWidget(self.gioitinh, 0, 5)
        grid.addWidget(QLabel("BS kê đơn"), 0, 6)
        grid.addWidget(self.bacsi, 0, 7)

        # Hàng 2
        grid.addWidget(QLabel("Điện thoại"), 1, 0)
        grid.addWidget(self.dienthoai, 1, 1)
        grid.addWidget(QLabel("Tuổi"), 1, 2)
        grid.addWidget(self.tuoi, 1, 3)
        grid.addWidget(QLabel("Số hồ sơ"), 1, 4)
        grid.addWidget(self.sohoso, 1, 5)
        grid.addWidget(QLabel("Người lập"), 1, 6)
        grid.addWidget(self.nguoilap, 1, 7)

        # Hàng 3
        grid.addWidget(QLabel("Địa chỉ"), 2, 0)
        grid.addWidget(self.diachi, 2, 1, 1, 3)
        grid.addWidget(QLabel("Số phiếu"), 2, 4)
        grid.addWidget(self.sophieukham, 2, 5)
        grid.addWidget(QLabel("Đơn mẫu"), 2, 6)
        grid.addWidget(self.donmau, 2, 7)

        # Hàng 4
        grid.addWidget(QLabel("Chẩn đoán"), 3, 0)
        self.chandoan = QLineEdit()
        grid.addWidget(self.chandoan, 3, 1, 1, 2)
        self.btn_chandoan = QPushButton("Xem chi tiết")
        self.btn_chandoan.setMinimumWidth(100)
        self.btn_chandoan.clicked.connect(self.show_chandoan_dialog)
        grid.addWidget(self.btn_chandoan, 3, 3)
        grid.addWidget(QLabel("Ngày kê đơn"), 3, 4)
        grid.addWidget(self.ngaykedon, 3, 5)
        grid.addWidget(QLabel("Đơn cũ"), 3, 6)
        grid.addWidget(self.doncu, 3, 7)

        # Hàng 5
        grid.addWidget(QLabel("Dị ứng"), 4, 0)
        self.diung = QLineEdit()
        grid.addWidget(self.diung, 4, 1, 1, 2)
        self.btn_diung = QPushButton("Xem chi tiết")
        self.btn_diung.setMinimumWidth(100)
        self.btn_diung.clicked.connect(self.show_diung_dialog)
        grid.addWidget(self.btn_diung, 4, 3)
        def show_chandoan_dialog(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Chi tiết chẩn đoán")
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(self.chandoan.text() if hasattr(self, 'chandoan') else "")
            layout.addWidget(text_edit)
            btn_close = QPushButton("Đóng")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.exec_()

        def show_diung_dialog(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Chi tiết dị ứng")
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(self.diung.text() if hasattr(self, 'diung') else "")
            layout.addWidget(text_edit)
            btn_close = QPushButton("Đóng")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.exec_()
        grid.addWidget(QLabel("Số ngày"), 4, 4)
        grid.addWidget(self.songay, 4, 5)
        grid.addWidget(QLabel("Loại đơn"), 4, 6)
        grid.addWidget(self.loaithuoc, 4, 7)

        group_info.setLayout(grid)
        main_layout.addWidget(group_info)

        # ======= BẢNG KÊ THUỐC =======
        self.table_thuoc = QTableWidget(5, 10)
        self.table_thuoc.setHorizontalHeaderLabels([
            "Mã thuốc", "Tên thuốc", "Số lượng", "Đơn vị",
            "Sáng", "Trưa", "Chiều", "Tối", "Liều dùng", "Ghi chú"
        ])
        # Thêm placeholder "Nhấn để chọn" cho các cột tương tác
        for row in range(5):
            ma_thuoc = QTableWidgetItem("Nhấn để chọn")
            ten_thuoc = QTableWidgetItem("Nhấn để chọn")
            lieu_dung = QTableWidgetItem("Nhấn để chọn")
            ghi_chu = QTableWidgetItem("Nhấn để chọn")
            ma_thuoc.setForeground(Qt.gray)
            ten_thuoc.setForeground(Qt.gray)
            lieu_dung.setForeground(Qt.gray)
            ghi_chu.setForeground(Qt.gray)
            self.table_thuoc.setItem(row, 0, ma_thuoc)
            self.table_thuoc.setItem(row, 1, ten_thuoc)
            # Combobox đơn vị cho cột 3 (chỉ hiện mũi tên cho đến khi người dùng chọn)
            unit_combo = self._make_unit_combo()
            self.table_thuoc.setCellWidget(row, 3, unit_combo)
            self.table_thuoc.setItem(row, 8, lieu_dung)
            self.table_thuoc.setItem(row, 9, ghi_chu)
        # Kết nối sự kiện để tự động thêm hàng khi người dùng nhập vào hàng cuối
        self.table_thuoc.itemChanged.connect(self.on_table_thuoc_item_changed)
        header = self.table_thuoc.horizontalHeader()
        # Configure column resize modes so the layout is responsive when zooming/resizing
        # Tên thuốc (1), Liều dùng (8) và Ghi chú (9) sẽ giãn để chiếm không gian chính
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        # Thu nhỏ các cột chỉ cần một số (Sáng->Tối)
        narrow_cols = [4, 5, 6, 7]  # chỉ số cột bắt đầu từ 0
        for c in narrow_cols:
            header.setSectionResizeMode(c, QHeaderView.Fixed)
            self.table_thuoc.setColumnWidth(c, 60)
        # Mã thuốc hơi nhỏ hơn tên thuốc
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_thuoc.setColumnWidth(0, 100)
        # Kéo rộng cột Số lượng và Đơn vị (fixed but wider)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_thuoc.setColumnWidth(2, 110)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table_thuoc.setColumnWidth(3, 140)

        # Cho phép bảng mở rộng theo chiều ngang nhưng giữ chiều cao cố định
        self.table_thuoc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Giữ nguyên hành vi double-click trên ô
        self.table_thuoc.cellDoubleClicked.connect(self.handle_cell_double_click)
        
        # Thêm bảng vào layout chính
        main_layout.addWidget(self.table_thuoc)

        # ======= LỜI DẶN =======
        lbl_loidan = QLabel("Lời dặn")
        self.txt_loidan = QTextEdit()
        self.txt_loidan.setMaximumHeight(50)
        main_layout.addWidget(lbl_loidan)
        main_layout.addWidget(self.txt_loidan)

        # ======= DANH SÁCH ĐƠN THUỐC =======
        lbl_ds = QLabel("DANH SÁCH ĐƠN THUỐC")
        lbl_ds.setStyleSheet("color: #000000; font-weight: bold;")
        main_layout.addWidget(lbl_ds)

        self.table_ds = QTableWidget(3, 4)
        self.table_ds.setHorizontalHeaderLabels([
            "Ngày kê đơn", "Số phiếu", "Trạng thái", "Xem"
        ])
        self.table_ds.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Cột Xem có nút
        for row in range(self.table_ds.rowCount()):
            btn_xem = QPushButton("🔍")
            self.table_ds.setCellWidget(row, 3, btn_xem)

        main_layout.addWidget(self.table_ds)

        # ======= NÚT CHỨC NĂNG =======
        btn_layout = QHBoxLayout()
        # Giữ tham chiếu tới các nút quan trọng để gắn hành vi
        self.btns = {}
        for text in [
            "Nhập mới (F1)", "Lưu (F2)", "In đơn", "Bỏ qua", "Sửa",
            "Xóa", "Gửi cổng dược", "Tải lại", "Thoát"
        ]:
            btn = QPushButton(text)
            btn.setMinimumWidth(100)
            btn.setStyleSheet("background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; }")
            btn_layout.addWidget(btn)
            self.btns[text] = btn
        # Kết nối nút Tải lại
        if "Tải lại" in self.btns:
            self.btns["Tải lại"].clicked.connect(self._handle_reload_clicked)
        # Kết nối các nút chức năng chính
        try:
            if "Nhập mới (F1)" in self.btns:
                self.btns["Nhập mới (F1)"].clicked.connect(self.on_nhapmoi_bo_sung)
            if "Lưu (F2)" in self.btns:
                self.btns["Lưu (F2)"].clicked.connect(self.on_luu_bo_sung)
            if "In đơn" in self.btns:
                self.btns["In đơn"].clicked.connect(self.on_in_bo_sung)
            if "Sửa" in self.btns:
                self.btns["Sửa"].clicked.connect(self.on_sua_bo_sung)
            if "Xóa" in self.btns:
                self.btns["Xóa"].clicked.connect(self.on_xoa_bo_sung)
            if "Gửi cổng dược" in self.btns:
                self.btns["Gửi cổng dược"].clicked.connect(self.on_xuat_thuoc_bo_sung)
            if "Bỏ qua" in self.btns:
                self.btns["Bỏ qua"].clicked.connect(self.on_bo_qua)
            if "Thoát" in self.btns:
                self.btns["Thoát"].clicked.connect(self.on_thoat)
        except Exception:
            pass
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def load_patients(self):
        """Load danh sách bệnh nhân từ database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT 
                    b.id,
                    b.ho_ten,
                    b.ngay_sinh,
                    b.gioi_tinh,
                    b.tuoi,
                    b.dien_thoai,
                    b.so_cccd,
                    b.dia_chi,
                    b.doi_tuong,
                    t.ma_hoso
                FROM benh_nhan b 
                LEFT JOIN tiep_don t ON b.id = t.benh_nhan_id 
                ORDER BY b.ho_ten
            """)
            patients = cursor.fetchall()
            conn.close()
            self.benhnhan.clear()
            self.benhnhan.addItem("--- Chọn bệnh nhân ---")
            for id, name, ngaysinh, gioitinh, tuoi, dienthoai, so_cccd, diachi, doituong, record in patients:
                # Tạo chuỗi hiển thị phân biệt (tên — Mã:HSxxx hoặc ID:nn — điện thoại / cccd / yyyy)
                display_name = name
                extras = []
                if dienthoai:
                    extras.append(str(dienthoai))
                if so_cccd:
                    extras.append(str(so_cccd))
                if ngaysinh:
                    try:
                        yyyy = str(ngaysinh).split("-")[0]
                        extras.append(yyyy)
                    except Exception:
                        pass
                # Ưu tiên hiển thị ma_hoso nếu có vì thân thiện với người dùng
                if record:
                    display_name += f" — Mã:{record}"
                else:
                    display_name += f" — ID:{id}"
                if extras:
                    display_name += f" — {' / '.join(extras)}"
                # Thêm dữ liệu người dùng làm tham số thứ hai để đảm bảo lưu trong Qt.UserRole
                # Giữ metadata bệnh nhân chi tiết trong userData để handler khác có thể dùng
                self.benhnhan.addItem(display_name, {
                    'id': id,
                    'ngaysinh': ngaysinh,
                    'gioi_tinh': gioitinh,
                    'tuoi': tuoi,
                    'dienthoai': dienthoai,
                    'diachi': diachi,
                    'doituong': doituong,
                    'record': record
                })
        except Exception as e:
            print(f"Lỗi load bệnh nhân: {e}")
        
        # Tự động chọn bệnh nhân cuối nếu không truyền ID cụ thể
        if not self.benh_nhan_id:
            try:
                import signals as sig_module
                if sig_module.current_patient_id:
                    self.auto_select_patient(sig_module.current_patient_id)
            except Exception:
                pass

    def load_bacsi_list(self):
        """Load danh sách bác sĩ"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT bac_si FROM don_thuoc WHERE bac_si IS NOT NULL")
            rows = cursor.fetchall()
            # Kiểm tra cột trong don_thuoc để tính trạng thái chính xác trên các schema khác nhau
            try:
                cursor.execute("PRAGMA table_info('don_thuoc')")
                cols_info = cursor.fetchall()
                cols = [c[1] for c in cols_info]
            except Exception:
                cols = []
            conn.close()
            self.bacsi.clear()
            for row in rows:
                if row[0]:
                    self.bacsi.addItem(row[0])
        except Exception:
            pass

    def load_nguoilap_list(self):
        """Load danh sách người lập"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT nguoi_lap_phieu FROM don_thuoc WHERE nguoi_lap_phieu IS NOT NULL")
            rows = cursor.fetchall()
            conn.close()
            self.nguoilap.clear()
            for row in rows:
                if row[0]:
                    self.nguoilap.addItem(row[0])
        except Exception:
            pass

    def on_patient_selected(self, index):
        """Khi chọn bệnh nhân, load thông tin chi tiết"""
        if index <= 0:
            self.clear_form()
            return
        
        # Retrieve stored userData (Qt.UserRole) and accept both dict and QVariant-wrapped dict
        try:
            data = self.benhnhan.itemData(index, Qt.UserRole)
        except Exception:
            # Fallback: try default role
            data = self.benhnhan.itemData(index)

        if not data:
            return
        # If data is a QVariant-like object (PyQt sometimes returns), attempt to extract python dict
        if hasattr(data, 'toPyObject'):
            try:
                data = data.toPyObject()
            except Exception:
                pass
        if not isinstance(data, dict):
            return
        
        patient_id = data.get('id')
        if not patient_id:
            return
        # remember current patient id so other handlers can reload
        self.current_patient_id = patient_id
        
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Load thông tin cơ bản
            cursor.execute("""
                SELECT b.gioi_tinh, b.ngay_sinh, b.tuoi, b.dia_chi, b.dien_thoai
                FROM benh_nhan b
                WHERE b.id = ?
            """, (patient_id,))
            patient = cursor.fetchone()
            if patient:
                gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai = patient
                self.gioitinh.setText(str(gioi_tinh) if gioi_tinh else "")
                    # Thử phân tích nhiều định dạng ngày khác nhau sang QDate
                if ngay_sinh:
                    try:
                                # Nếu đã là chuỗi ngày theo định dạng ISO
                        if isinstance(ngay_sinh, str):
                            # Các định dạng thường gặp: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS
                            parsed = None
                            try:
                                parsed = QDate.fromString(ngay_sinh, "yyyy-MM-dd")
                                if not parsed.isValid():
                                    parsed = QDate.fromString(ngay_sinh.split(' ')[0], "yyyy-MM-dd")
                            except Exception:
                                parsed = None
                            if parsed and parsed.isValid():
                                self.ngaysinh.setDate(parsed)
                        elif isinstance(ngay_sinh, (QDate,)):
                            self.ngaysinh.setDate(ngay_sinh)
                    except Exception:
                        pass
                self.tuoi.setText(str(tuoi) if tuoi else "")
                self.diachi.setText(dia_chi or "")
                self.dienthoai.setText(dien_thoai or "")

            # Load số hồ sơ, số phiếu, chẩn đoán, dị ứng
            # Trước tiên cố gắng lấy ma_hoso từ tiep_don
            ma_hoso = ""
            cursor.execute("""
                SELECT ma_hoso FROM tiep_don 
                WHERE benh_nhan_id = ? AND ma_hoso IS NOT NULL
                ORDER BY id DESC LIMIT 1
            """, (patient_id,))
            r = cursor.fetchone()
            if r:
                ma_hoso = r[0]
                # Đặt text ngay và lặp lại vào cuối vòng lặp sự kiện để tránh bị ghi đè bởi handler khác
                self.sohoso.setText(ma_hoso or "")
                QTimer.singleShot(0, lambda m=ma_hoso: self.sohoso.setText(m or ""))
            
            # Lấy phieu_kham và chi_tiet_phieu_kham mới nhất cho bệnh nhân này
            cursor.execute("""
                SELECT pk.id, pk.so_phieu, ct.chan_doan, ct.di_ung_thuoc
                FROM phieu_kham pk
                LEFT JOIN chi_tiet_phieu_kham ct ON pk.id = ct.phieu_kham_id
                WHERE pk.benh_nhan_id = ?
                ORDER BY pk.id DESC
                LIMIT 1
            """, (patient_id,))
            phieu_row = cursor.fetchone()
            if phieu_row:
                phieu_kham_id, so_phieu, chan_doan, di_ung_thuoc = phieu_row
                self.phieu_kham_id = phieu_kham_id
                self.sophieukham.setText(so_phieu or "")
                self.chandoan.setText(chan_doan or "")
                self.diung.setText(di_ung_thuoc or "")
            else:
                self.phieu_kham_id = None
                self.sophieukham.setText("")
                self.chandoan.setText("")
                self.diung.setText("")

            # Load đơn thuốc cũ
            cursor.execute("""
                SELECT dt.id, dt.ngay_ke, dt.chan_doan 
                FROM don_thuoc dt
                JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                WHERE pk.benh_nhan_id = ?
                ORDER BY dt.ngay_ke DESC, dt.id DESC
            """, (patient_id,))
            prescriptions = cursor.fetchall()
            self.doncu.clear()
            self.doncu.addItem("---Chọn đơn cũ---", None)
            for p in prescriptions:
                display_text = f"{p[1]} - {p[2][:50] + '...' if p[2] and len(p[2]) > 50 else p[2] or 'Không có chẩn đoán'}"
                self.doncu.addItem(display_text, p[0])
            # Load danh sách đơn thuốc vào bảng bên dưới
            try:
                self.load_prescriptions_list(patient_id)
            except Exception:
                pass
        except Exception as e:
            print(f"Lỗi load patient info: {e}")
        finally:
            conn.close()

    def on_patient_manual_select(self):
        """Khi người dùng nhập tên bệnh nhân (manual) hoặc chọn từ list"""
        text = self.benhnhan.currentText().strip()
        if not text or text == "--- Chọn bệnh nhân ---":
            return
        # Tìm item có text khớp và load nó
        for i in range(self.benhnhan.count()):
            if text.lower() in self.benhnhan.itemText(i).lower():
                self.benhnhan.setCurrentIndex(i)
                self.on_patient_selected(i)
                return

    def on_doncu_changed(self, index):
        """When user selects an old prescription, load it into the table below."""
        try:
            if index <= 0:
                return
            don_id = self.doncu.itemData(index)
            if don_id:
                # reuse existing loader to populate the form
                self.load_prescription_into_form(don_id)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải đơn cũ: {e}")

    def clear_form(self):
        """Xóa sạch dữ liệu form"""
        self.gioitinh.clear()
        self.ngaysinh.setDate(QDate.currentDate())
        self.tuoi.clear()
        self.diachi.clear()
        self.dienthoai.clear()
        self.sohoso.clear()
        self.sophieukham.clear()
        self.chandoan.clear()
        self.diung.clear()
        self.doncu.clear()

    def load_prescriptions_list(self, patient_id=None):
        """Load danh sách đơn thuốc cho bệnh nhân vào `table_ds`"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # inspect table columns so we can compute status reliably across schemas
            cursor.execute("PRAGMA table_info('don_thuoc')")
            # Kiểm tra cấu trúc bảng để tính trạng thái một cách đáng tin cậy giữa các schema
            cols_info = cursor.fetchall()
            # Robustly load latest ma_hoso and phieu_kham/so_phieu for this patient.
            try:
                # latest tiep_don with a ma_hoso
                cursor.execute("SELECT ma_hoso FROM tiep_don WHERE benh_nhan_id = ? AND ma_hoso IS NOT NULL ORDER BY id DESC LIMIT 1", (patient_id,))
                r = cursor.fetchone()
                if r and r[0]:
                    self.sohoso.setText(r[0])
                    QTimer.singleShot(0, lambda m=r[0]: self.sohoso.setText(m or ""))
                else:
                    self.sohoso.setText("")

                # latest phieu_kham (id, so_phieu)
                cursor.execute("SELECT id, so_phieu FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (patient_id,))
                p = cursor.fetchone()
                phieu_kham_id = None
                if p:
                    phieu_kham_id = p[0]
                    self.phieu_kham_id = phieu_kham_id
                    self.sophieukham.setText(str(p[1]) if p[1] is not None else "")
                else:
                    self.sophieukham.setText("")

                # prefer latest chi_tiet_phieu_kham for chan_doan and allergy (di_ung_thuoc or di_ung)
                if phieu_kham_id:
                    cursor.execute("SELECT chan_doan, COALESCE(di_ung_thuoc, di_ung, '') FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_kham_id,))
                    det = cursor.fetchone()
                    if det:
                        if det[0]:
                            self.chandoan.setText(det[0])
                        else:
                            self.chandoan.setText("")
                        if det[1]:
                            self.diung.setText(det[1])
                        else:
                            self.diung.setText("")
                    else:
                        self.chandoan.setText("")
                        self.diung.setText("")
                else:
                    # no phieu_kham found
                    self.chandoan.setText("")
                    self.diung.setText("")
            except Exception:
                # fallback to empty fields on any error
                self.sohoso.setText("")
                self.sophieukham.setText("")
                self.chandoan.setText("")
                self.diung.setText("")
            # Load prescriptions for the patient
            # inspect don_thuoc columns so we can compute status reliably across schemas
            cols = []
            try:
                cursor.execute("PRAGMA table_info('don_thuoc')")
                cols_info = cursor.fetchall()
                cols = [c[1] for c in cols_info]
            except Exception:
                cols = []
            
            cursor.execute("""
                SELECT dt.id, dt.ngay_ke, dt.ngay_ke as so_phieu
                FROM don_thuoc dt
                WHERE dt.phieu_kham_id IN (SELECT id FROM phieu_kham WHERE benh_nhan_id = ?)
                ORDER BY dt.ngay_ke DESC, dt.id DESC
            """, (patient_id,))
            rows = cursor.fetchall()
            self.table_ds.setRowCount(0)
            for r, rec in enumerate(rows):
                # Bản ghi có thể chứa các cột phụ thuộc vào schema
                dt_id = rec[0]
                ngay_ke = rec[1]
                so_phieu = rec[2] if len(rec) > 2 else ''
                # Tính trạng thái
                status_parts = []
                extra_vals = rec[3:]
                extra_names = []
                if 'trang_thai' in cols:
                    extra_names.append('trang_thai')
                if 'xuat_thuoc' in cols:
                    extra_names.append('xuat_thuoc')
                if 'da_luu' in cols:
                    extra_names.append('da_luu')
                extra_map = dict(zip(extra_names, extra_vals)) if extra_names else {}
                # Any existing don_thuoc row means it was saved -> Đã kê đơn
                status_parts.append('Đã kê đơn')
                # trang_thai may already indicate saved or exported
                if extra_map.get('trang_thai'):
                    st = str(extra_map.get('trang_thai'))
                    l = st.lower()
                    # Kiểm tra xem trang_thai có đề cập tới việc đã xuất thuốc hay không
                    if any(x in l for x in ('xuất', 'xuat', 'đã xuất', 'da xuat')):
                        if 'Đã xuất thuốc' not in status_parts:
                            status_parts.append('Đã xuất thuốc')
                    elif any(x in l for x in ('kê', 'ke', 'đã', 'da')):
                        if 'Đã kê đơn' not in status_parts:
                            status_parts.append('Đã kê đơn')
                    else:
                        status_parts.append(st)
                # xuat_thuoc -> Đã xuất thuốc (explicit flag)
                if extra_map.get('xuat_thuoc') not in (None, 0, '', '0'):
                    if 'Đã xuất thuốc' not in status_parts:
                        status_parts.append('Đã xuất thuốc')
                trang_thai = ', '.join(status_parts) if status_parts else ''
                self.table_ds.insertRow(r)
                item_ngay = QTableWidgetItem(str(ngay_ke) if ngay_ke is not None else "")
                item_so = QTableWidgetItem(str(so_phieu) if so_phieu is not None else "")
                item_trangthai = QTableWidgetItem(str(trang_thai))
                self.table_ds.setItem(r, 0, item_ngay)
                self.table_ds.setItem(r, 1, item_so)
                self.table_ds.setItem(r, 2, item_trangthai)
                btn = QPushButton("Xem")
                # Lưu callback mà không dùng closure đệ quy để tránh lỗi đệ quy
                btn.prescription_id = dt_id
                btn.clicked.connect(lambda: self.on_view_prescription(btn.prescription_id))
                self.table_ds.setCellWidget(r, 3, btn)
        except Exception as e:
            print(f"Lỗi populate table_ds: {e}")

    def on_view_prescription(self, don_thuoc_id):
        """Handler khi nhấn nút Xem: show chi tiết dialog với option mở vào form"""
        try:
            dialog = PrescriptionDetailDialog(self, don_thuoc_id, self.load_prescription_into_form)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải đơn thuốc: {e}")

    def _handle_reload_clicked(self):
        """Reload prescription list for the currently selected patient."""
        try:
            pid = getattr(self, 'current_patient_id', None)
            if pid:
                self.load_prescriptions_list(pid)
            else:
                # Không có bệnh nhân được chọn, xóa danh sách
                self.table_ds.setRowCount(0)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải lại danh sách: {e}")

    def load_prescription_into_form(self, don_thuoc_id):
        """Load một đơn thuốc (don_thuoc + chi_tiet_don_thuoc) vào form hiện tại"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ngay_ke, bac_si, nguoi_lap_phieu, loi_dan, phieu_kham_id, chan_doan FROM don_thuoc WHERE id = ?", (don_thuoc_id,))
            dt = cursor.fetchone()
            if not dt:
                conn.close()
                raise ValueError("Đơn thuốc không tồn tại")
            ngay_ke, bac_si, nguoilap, loi_dan, phieu_kham_id, chan_doan = dt
            # Cập nhật các trường cơ bản
            try:
                if ngay_ke:
                    # assume format 'YYYY-MM-DD' or similar
                    try:
                        self.ngaykedon.setDate(QDate.fromString(str(ngay_ke), "yyyy-MM-dd"))
                    except Exception:
                        pass
                if chan_doan:
                    self.chandoan.setText(chan_doan)
                if bac_si:
                    if self.bacsi.findText(bac_si) == -1:
                        self.bacsi.addItem(bac_si)
                    self.bacsi.setCurrentText(bac_si)
                if nguoilap:
                    if self.nguoilap.findText(nguoilap) == -1:
                        self.nguoilap.addItem(nguoilap)
                    self.nguoilap.setCurrentText(nguoilap)
                if loi_dan:
                    self.txt_loidan.setText(loi_dan)
                # load so phieu from phieu_kham
                if phieu_kham_id:
                    cursor.execute("SELECT so_phieu FROM phieu_kham WHERE id = ?", (phieu_kham_id,))
                    p = cursor.fetchone()
                    if p:
                        self.sophieukham.setText(str(p[0]))

                # Prefer latest diagnosis and allergy values from chi_tiet_phieu_kham
                try:
                    if phieu_kham_id:
                        cursor.execute("SELECT chan_doan, di_ung_thuoc FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_kham_id,))
                        det = cursor.fetchone()
                        if det:
                            self.chandoan.setText(det[0] or "")
                            self.diung.setText(det[1] or "")
                except Exception:
                    pass

            except Exception:
                pass

            # Load chi tiết đơn thuốc
            cursor.execute("""
                SELECT ct.ma_thuoc, dm.ten_thuoc, ct.so_luong, ct.don_vi, ct.sang, ct.trua, ct.chieu, ct.toi, ct.lieu_dung, ct.ghi_chu
                FROM chi_tiet_don_thuoc ct
                LEFT JOIN danh_muc_thuoc dm ON ct.ma_thuoc = dm.ma_thuoc
                WHERE ct.don_thuoc_id = ?
                ORDER BY ct.id
            """, (don_thuoc_id,))
            details = cursor.fetchall()
            # Clear and populate table_thuoc
            self.table_thuoc.setRowCount(0)
            for r, d in enumerate(details):
                self.table_thuoc.insertRow(r)
                ma, ten, soluong, donvi, sang, trua, chieu, toi, lieudung, ghichu = d
                ma_item = QTableWidgetItem(str(ma) if ma else "")
                ten_item = QTableWidgetItem(str(ten) if ten else "")
                soluong_item = QTableWidgetItem(str(soluong) if soluong is not None else "")
                # set units as combo
                unit_combo = self._make_unit_combo()
                if donvi:
                    if unit_combo.findText(donvi) == -1:
                        unit_combo.addItem(donvi)
                    unit_combo.setCurrentText(donvi)
                # dosing columns: show the raw stored value as entered (no ✓ conversion)
                sang_item = QTableWidgetItem(str(sang) if sang is not None else "")
                trua_item = QTableWidgetItem(str(trua) if trua is not None else "")
                chieu_item = QTableWidgetItem(str(chieu) if chieu is not None else "")
                toi_item = QTableWidgetItem(str(toi) if toi is not None else "")
                lieudung_item = QTableWidgetItem(str(lieudung) if lieudung else "")
                ghichu_item = QTableWidgetItem(str(ghichu) if ghichu else "")
                # make non-editable where appropriate
                for it in (ma_item, ten_item, sang_item, trua_item, chieu_item, toi_item, lieudung_item, ghichu_item):
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                    it.setForeground(Qt.black)
                self.table_thuoc.setItem(r, 0, ma_item)
                self.table_thuoc.setItem(r, 1, ten_item)
                self.table_thuoc.setItem(r, 2, soluong_item)
                self.table_thuoc.setCellWidget(r, 3, unit_combo)
                self.table_thuoc.setItem(r, 4, sang_item)
                self.table_thuoc.setItem(r, 5, trua_item)
                self.table_thuoc.setItem(r, 6, chieu_item)
                self.table_thuoc.setItem(r, 7, toi_item)
                self.table_thuoc.setItem(r, 8, lieudung_item)
                self.table_thuoc.setItem(r, 9, ghichu_item)
            # add one empty row at the end
            self._append_empty_row_main()
        finally:
            conn.close()

    def handle_cell_double_click(self, row, col):
        """Xử lý double-click trên bảng để chọn thuốc, liều dùng, hoặc nhập ghi chú"""
        # Mã/Tên thuốc (col 0 hoặc 1): mở dialog chọn thuốc
        if col in (0, 1):
            dialog = ChonThuocDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_drug:
                self._suppress_item_changed = True
                try:
                    ma_item = QTableWidgetItem(dialog.selected_drug['ma_thuoc'])
                    ten_item = QTableWidgetItem(dialog.selected_drug['ten_thuoc'])
                    ma_item.setForeground(Qt.black)
                    ten_item.setForeground(Qt.black)
                    # Make items non-editable to match original behavior
                    ma_item.setFlags(ma_item.flags() & ~Qt.ItemIsEditable)
                    ten_item.setFlags(ten_item.flags() & ~Qt.ItemIsEditable)
                    self.table_thuoc.setItem(row, 0, ma_item)
                    self.table_thuoc.setItem(row, 1, ten_item)
                    # If the chosen drug has a stored unit, apply it to the unit combo
                    try:
                        unit_w = self.table_thuoc.cellWidget(row, 3)
                        don_vi = dialog.selected_drug.get('don_vi') if dialog.selected_drug else None
                        if unit_w and don_vi:
                            if unit_w.findText(don_vi) == -1:
                                unit_w.addItem(don_vi)
                            unit_w.setCurrentText(don_vi)
                    except Exception:
                        pass
                finally:
                    self._suppress_item_changed = False
        # Liều dùng (col 8): mở dialog chọn liều dùng
        elif col == 8:
            dialog = ChonLieuDungDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_dosage:
                self._suppress_item_changed = True
                try:
                    ld_item = QTableWidgetItem(dialog.selected_dosage)
                    ld_item.setForeground(Qt.black)
                    ld_item.setFlags(ld_item.flags() & ~Qt.ItemIsEditable)
                    self.table_thuoc.setItem(row, col, ld_item)
                finally:
                    self._suppress_item_changed = False
        # Ghi chú (col 9): mở dialog nhập ghi chú
        elif col == 9:
            current_text = ""
            current_item = self.table_thuoc.item(row, col)
            if current_item and current_item.text() != "Nhấn để chọn":
                current_text = current_item.text()
            dialog = NhapGhiChuDialog(self, current_text)
            if dialog.exec_() == QDialog.Accepted and dialog.note is not None:
                self._suppress_item_changed = True
                try:
                    note_item = QTableWidgetItem(dialog.note)
                    note_item.setForeground(Qt.black)
                    self.table_thuoc.setItem(row, col, note_item)
                finally:
                    self._suppress_item_changed = False

    def on_table_thuoc_item_changed(self, item):
        """Khi chỉnh sửa hàng cuối, tự động thêm hàng mới"""
        if self._suppress_item_changed or item is None:
            return
        
        last_row = self.table_thuoc.rowCount() - 1
        if item.row() == last_row and item.text().strip():
            self._append_empty_row_main()

    def _append_empty_row_main(self):
        """Thêm hàng trống mới"""
        self._suppress_item_changed = True
        try:
            r = self.table_thuoc.rowCount()
            self.table_thuoc.insertRow(r)
            for col in [0, 1, 8, 9]:
                item = QTableWidgetItem("Nhấn để chọn")
                item.setForeground(Qt.gray)
                self.table_thuoc.setItem(r, col, item)
            unit_combo = self._make_unit_combo()
            self.table_thuoc.setCellWidget(r, 3, unit_combo)
        finally:
            self._suppress_item_changed = False

    def _make_unit_combo(self, initial_value=None):
        """Tạo combobox đơn vị"""
        unit_options = ["viên", "lọ", "chai", "ống", "gói", "tuýp", "tuýp nhỏ", "ống nhỏ"]
        combo = QComboBox()
        combo.addItems(unit_options)
        combo.setEditable(True)
        combo.setCurrentIndex(-1)
        combo.clearEditText()
        return combo

    def auto_select_patient(self, patient_id):
        """Tự động chọn bệnh nhân và load dữ liệu"""
        try:
            for i in range(self.benhnhan.count()):
                try:
                    data = self.benhnhan.itemData(i, Qt.UserRole)
                except Exception:
                    data = self.benhnhan.itemData(i)
                # handle QVariant wrappers
                if hasattr(data, 'toPyObject'):
                    try:
                        data = data.toPyObject()
                    except Exception:
                        pass
                if isinstance(data, dict) and data.get('id') == patient_id:
                    # Set current index (this will trigger on_patient_selected signal)
                    self.benhnhan.setCurrentIndex(i)
                    # Also call the handler directly to ensure fields are populated
                    try:
                        self.on_patient_selected(i)
                    except Exception:
                        pass
                    return
        except Exception:
            pass

    def _detect_detail_fk_col(self, cur):
        """Detect which FK column name chi_tiet_don_thuoc_bo_sung uses.
        Returns the column name string or None if table doesn't exist or no known FK found.
        """
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chi_tiet_don_thuoc_bo_sung'")
            if not cur.fetchone():
                return None
            cur.execute("PRAGMA table_info(chi_tiet_don_thuoc_bo_sung)")
            cols = [c[1] for c in cur.fetchall()]
            if 'don_thuoc_id' in cols:
                return 'don_thuoc_id'
            if 'don_thuoc_bo_sung_id' in cols:
                return 'don_thuoc_bo_sung_id'
            return None
        except Exception:
            return None

    # ---------------- Button handlers ----------------
    def on_nhapmoi_bo_sung(self):
        """Reset only medicine tables and note for supplementary form."""
        try:
            self._suppress_item_changed = True
            # reset main table to 5 placeholder rows
            self.table_thuoc.clearContents()
            self.table_thuoc.setRowCount(0)
            for _ in range(5):
                self._append_empty_row_main()
            # if a 'thuốc khác' table exists in this form, reset it
            if hasattr(self, 'table_thuoc_khac'):
                try:
                    self.table_thuoc_khac.clearContents()
                    self.table_thuoc_khac.setRowCount(0)
                except Exception:
                    pass
            # clear note
            try:
                self.txt_loidan.clear()
            except Exception:
                pass
        finally:
            self._suppress_item_changed = False

    def on_luu_bo_sung(self):
        """Save supplementary prescription to DB and lock editing."""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            # ensure header table
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='don_thuoc_bo_sung'")
            if not cur.fetchone():
                cur.execute(
                    "CREATE TABLE don_thuoc_bo_sung (id INTEGER PRIMARY KEY, phieu_kham_id INTEGER, ngay_ke TEXT, nguoi_lap_phieu TEXT, chan_doan TEXT, loi_dan TEXT, tong_tien REAL)"
                )
            phieu_kham_id = getattr(self, 'phieu_kham_id', None)
            ngay = self.ngaykedon.date().toString("yyyy-MM-dd") if hasattr(self, 'ngaykedon') else QDate.currentDate().toString("yyyy-MM-dd")
            nguoi = self.nguoilap.currentText() if hasattr(self, 'nguoilap') else ''
            chan = self.chandoan.text() if hasattr(self, 'chandoan') else ''
            loi = self.txt_loidan.toPlainText() if hasattr(self, 'txt_loidan') else ''
            try:
                tong = float(self.tongtien.text()) if hasattr(self, 'tongtien') and self.tongtien.text() else 0
            except Exception:
                tong = 0
            cur.execute("INSERT INTO don_thuoc_bo_sung (phieu_kham_id, ngay_ke, nguoi_lap_phieu, chan_doan, loi_dan, tong_tien) VALUES (?, ?, ?, ?, ?, ?)", (
                phieu_kham_id, ngay, nguoi, chan, loi, tong
            ))
            don_id = cur.lastrowid
            # ensure detail table exists and choose the correct FK column name
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chi_tiet_don_thuoc_bo_sung'")
            if not cur.fetchone():
                cur.execute(
                    "CREATE TABLE chi_tiet_don_thuoc_bo_sung (id INTEGER PRIMARY KEY, don_thuoc_id INTEGER, ma_thuoc TEXT, ten_thuoc TEXT, so_luong INTEGER, don_vi TEXT, sang TEXT, trua TEXT, chieu TEXT, toi TEXT, lieu_dung TEXT, ghi_chu TEXT)"
                )

            # Determine which FK column the table uses (some schemas use don_thuoc_bo_sung_id)
            cur.execute("PRAGMA table_info(chi_tiet_don_thuoc_bo_sung)")
            detail_cols = [c[1] for c in cur.fetchall()]
            if 'don_thuoc_id' in detail_cols:
                fk_col = 'don_thuoc_id'
            elif 'don_thuoc_bo_sung_id' in detail_cols:
                fk_col = 'don_thuoc_bo_sung_id'
            else:
                # If neither column exists (very old schema), try to add don_thuoc_id
                try:
                    cur.execute("ALTER TABLE chi_tiet_don_thuoc_bo_sung ADD COLUMN don_thuoc_id INTEGER DEFAULT 0")
                    fk_col = 'don_thuoc_id'
                except Exception:
                    # fallback to don_thuoc_id if add failed
                    fk_col = 'don_thuoc_id'

            insert_sql = f"INSERT INTO chi_tiet_don_thuoc_bo_sung ({fk_col}, ma_thuoc, ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

            for r in range(self.table_thuoc.rowCount()):
                ma = self.table_thuoc.item(r, 0)
                if not ma or not ma.text() or ma.text() == 'Nhấn để chọn':
                    continue
                ten = self.table_thuoc.item(r, 1).text() if self.table_thuoc.item(r, 1) else ''
                qty = int(self.table_thuoc.item(r, 2).text()) if self.table_thuoc.item(r, 2) and self.table_thuoc.item(r, 2).text() else 0
                unit_w = self.table_thuoc.cellWidget(r, 3)
                unit = unit_w.currentText() if unit_w else ''
                sang = self.table_thuoc.item(r, 4).text() if self.table_thuoc.item(r, 4) else ''
                trua = self.table_thuoc.item(r, 5).text() if self.table_thuoc.item(r, 5) else ''
                chieu = self.table_thuoc.item(r, 6).text() if self.table_thuoc.item(r, 6) else ''
                toi = self.table_thuoc.item(r, 7).text() if self.table_thuoc.item(r, 7) else ''
                lieu = self.table_thuoc.item(r, 8).text() if self.table_thuoc.item(r, 8) else ''
                ghi = self.table_thuoc.item(r, 9).text() if self.table_thuoc.item(r, 9) else ''
                cur.execute(insert_sql, (
                    don_id, ma.text(), ten, qty, unit, sang, trua, chieu, toi, lieu, ghi
                ))
            # try add da_luu flag
            try:
                cur.execute("PRAGMA table_info(don_thuoc_bo_sung)")
                cols = [c[1] for c in cur.fetchall()]
                if 'da_luu' not in cols:
                    cur.execute("ALTER TABLE don_thuoc_bo_sung ADD COLUMN da_luu INTEGER DEFAULT 0")
                cur.execute("UPDATE don_thuoc_bo_sung SET da_luu = 1 WHERE id = ?", (don_id,))
            except Exception:
                pass
            conn.commit()
            QMessageBox.information(self, "Thành công", "Đã lưu đơn thuốc bổ sung.")
            # lock editing
            try:
                self.table_thuoc.setEnabled(False)
                if hasattr(self, 'table_thuoc_khac'):
                    try:
                        self.table_thuoc_khac.setEnabled(False)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")
        finally:
            if conn:
                conn.close()

    def on_in_bo_sung(self):
        """Print / preview supplementary prescription."""
        try:
            html = self.build_print_html_bo_sung()
            try:
                from PyQt5.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(html)
            except Exception:
                doc = None
            mb = QMessageBox(self)
            mb.setWindowTitle("In đơn bổ sung")
            mb.setText("Bạn muốn Xem trước, In trực tiếp hay Lưu ra file PDF?")
            btn_preview = mb.addButton("Xem trước", QMessageBox.ActionRole)
            btn_print = mb.addButton("In trực tiếp", QMessageBox.AcceptRole)
            btn_pdf = mb.addButton("Lưu ra PDF", QMessageBox.DestructiveRole)
            btn_cancel = mb.addButton("Hủy", QMessageBox.RejectRole)
            mb.exec_()
            clicked = mb.clickedButton()
            if clicked == btn_cancel:
                return
            if clicked == btn_preview:
                printer = QPrinter(QPrinter.HighResolution)
                preview = QPrintPreviewDialog(printer, self)
                def _render(p):
                    try:
                        if doc:
                            doc.print_(p)
                    except Exception:
                        pass
                preview.paintRequested.connect(_render)
                preview.exec_()
                return
            if clicked == btn_pdf:
                fn, _ = QFileDialog.getSaveFileName(self, "Lưu PDF", "don_thuoc_bo_sung.pdf", "PDF Files (*.pdf)")
                if not fn:
                    return
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(fn)
                try:
                    if doc:
                        doc.print_(printer)
                    else:
                        from PyQt5.QtGui import QTextDocument as _TD
                        _d = _TD()
                        _d.setHtml(html)
                        _d.print_(printer)
                    QMessageBox.information(self, "Hoàn tất", f"Đã lưu PDF: {fn}")
                    # Emit signal để cập nhật form quản lý xuất thuốc
                    if self.benh_nhan_id:
                        app_signals.don_bo_sung_printed.emit(self.benh_nhan_id)
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể lưu PDF: {e}")
                return
            if clicked == btn_print:
                printer = QPrinter(QPrinter.HighResolution)
                dlg = QPrintDialog(printer, self)
                if dlg.exec_() == QDialog.Accepted:
                    try:
                        if doc:
                            doc.print_(printer)
                        else:
                            from PyQt5.QtGui import QTextDocument as _TD
                            _d = _TD()
                            _d.setHtml(html)
                            _d.print_(printer)
                        QMessageBox.information(self, "Hoàn tất", "Lệnh in đã được gửi.")
                        # Emit signal để cập nhật form quản lý xuất thuốc
                        if self.benh_nhan_id:
                            app_signals.don_bo_sung_printed.emit(self.benh_nhan_id)
                    except Exception as e:
                        QMessageBox.critical(self, "Lỗi", f"Lỗi khi in: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi in đơn bổ sung: {e}")

    def on_sua_bo_sung(self):
        try:
            self.table_thuoc.setEnabled(True)
            if hasattr(self, 'table_thuoc_khac'):
                try:
                    self.table_thuoc_khac.setEnabled(True)
                except Exception:
                    pass
            QMessageBox.information(self, "Sửa", "Đã bật chế độ sửa. Hãy chỉnh sửa các trường rồi chọn Lưu.")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể bật chế độ sửa: {e}")

    def on_xoa_bo_sung(self):
        try:
            sel = self.table_thuoc.selectedIndexes()
            if sel:
                row = sel[0].row()
                self.table_thuoc.removeRow(row)
                return
            if hasattr(self, 'table_thuoc_khac'):
                sel2 = self.table_thuoc_khac.selectedIndexes()
                if sel2:
                    row = sel2[0].row()
                    self.table_thuoc_khac.removeRow(row)
                    return
            QMessageBox.information(self, "Lưu ý", "Hãy chọn một hàng để xóa.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")

    def on_xuat_thuoc_bo_sung(self):
        """Gửi tới cổng dược: chỉ gửi đơn, không trừ tồn kho"""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            # 1. Lấy ID đơn bổ sung mới nhất
            cur.execute("SELECT id FROM don_thuoc_bo_sung ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng lưu đơn trước khi gửi tới cổng dược.")
                return

            don_id = row[0]

            # 2. Kiểm tra có thuốc trong đơn không
            medicines = []
            try:
                fk_col = self._detect_detail_fk_col(cur)
                if fk_col:
                    sql = f"SELECT ma_thuoc, ten_thuoc, so_luong FROM chi_tiet_don_thuoc_bo_sung WHERE {fk_col} = ?"
                    cur.execute(sql, (don_id,))
                    medicines = cur.fetchall()
                else:
                    try:
                        cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong FROM chi_tiet_don_thuoc_bo_sung WHERE don_thuoc_id = ?", (don_id,))
                        medicines = cur.fetchall()
                    except Exception:
                        try:
                            cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong FROM chi_tiet_don_thuoc_bo_sung WHERE don_thuoc_bo_sung_id = ?", (don_id,))
                            medicines = cur.fetchall()
                        except Exception:
                            medicines = []
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi đọc chi tiết đơn thuốc: {e}")
                return

            # 3. Nếu không có chi tiết → chỉ đánh dấu gửi
            if not medicines:
                try:
                    cur.execute("PRAGMA table_info(don_thuoc_bo_sung)")
                    cols = [c[1] for c in cur.fetchall()]
                    if 'da_gui_cong_duoc' not in cols:
                        cur.execute("ALTER TABLE don_thuoc_bo_sung ADD COLUMN da_gui_cong_duoc INTEGER DEFAULT 0")

                    cur.execute("UPDATE don_thuoc_bo_sung SET da_gui_cong_duoc = 1 WHERE id = ?", (don_id,))
                    conn.commit()
                    QMessageBox.information(self, "Hoàn tất", "Đã gửi đơn bổ sung tới cổng dược.")
                    # Phát tín hiệu để cập nhật form quản lý
                    self.medicine_exported.emit()
                    return

                except Exception as e:
                    conn.rollback()
                    QMessageBox.critical(self, "Lỗi", f"Không thể gửi tới cổng dược: {e}")
                    return

            # 4. Đánh dấu đơn đã gửi tới cổng dược
            try:
                cur.execute("PRAGMA table_info(don_thuoc_bo_sung)")
                cols = [c[1] for c in cur.fetchall()]

                if 'da_gui_cong_duoc' not in cols:
                    cur.execute("ALTER TABLE don_thuoc_bo_sung ADD COLUMN da_gui_cong_duoc INTEGER DEFAULT 0")
                    conn.commit()

                cur.execute("UPDATE don_thuoc_bo_sung SET da_gui_cong_duoc = 1 WHERE id = ?", (don_id,))
                conn.commit()
                
                QMessageBox.information(self, "Hoàn tất", "Đã gửi đơn bổ sung tới cổng dược!")
                # Phát tín hiệu để cập nhật form quản lý
                self.medicine_exported.emit()

            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Lỗi", f"Không thể gửi tới cổng dược: {e}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi: {e}")

        finally:
            if conn:
                conn.close()

    def build_print_html_bo_sung(self):
        try:
            clinic_name = "Phòng khám ABC"
            title = "ĐƠN THUỐC BỔ SUNG"
            patient = self.benhnhan.currentText() if hasattr(self, 'benhnhan') else ''
            dob = self.ngaysinh.date().toString("yyyy-MM-dd") if hasattr(self, 'ngaysinh') else ''
            sohoso = self.sohoso.text() if hasattr(self, 'sohoso') else ''
            sophieu = self.sophieukham.text() if hasattr(self, 'sophieukham') else ''
            bacsi = self.bacsi.currentText() if hasattr(self, 'bacsi') else ''
            ngay = self.ngaykedon.date().toString("yyyy-MM-dd") if hasattr(self, 'ngaykedon') else ''
            chan_doan = self.chandoan.text() if hasattr(self, 'chandoan') else ''
            loi_dan = self.txt_loidan.toPlainText() if hasattr(self, 'txt_loidan') else ''

            html = []
            html.append(f"<h2 style='text-align:center'>{clinic_name}</h2>")
            html.append(f"<h3 style='text-align:center'>{title}</h3>")
            html.append("<hr />")
            html.append("<table width='100%'>")
            html.append(f"<tr><td><b>Bệnh nhân:</b> {patient}</td><td><b>Ngày sinh:</b> {dob}</td></tr>")
            html.append(f"<tr><td><b>Số hồ sơ:</b> {sohoso}</td><td><b>Số phiếu:</b> {sophieu}</td></tr>")
            html.append(f"<tr><td><b>Bác sĩ:</b> {bacsi}</td><td><b>Ngày kê:</b> {ngay}</td></tr>")
            html.append(f"<tr><td colspan='2'><b>Chẩn đoán:</b> {chan_doan}</td></tr>")
            html.append("</table>")
            html.append("<h4>Thuốc kê</h4>")
            html.append("<table border='1' cellspacing='0' cellpadding='4' width='100%'>")
            html.append("<tr style='background:#eee'><th>Mã</th><th>Tên</th><th>Số lượng</th><th>Đơn vị</th><th>Liều dùng</th></tr>")
            for r in range(self.table_thuoc.rowCount()):
                ma_item = self.table_thuoc.item(r, 0)
                if not ma_item:
                    continue
                text = ma_item.text().strip()
                if not text or text == 'Nhấn để chọn':
                    continue
                ten = self.table_thuoc.item(r, 1).text() if self.table_thuoc.item(r, 1) else ''
                qty = self.table_thuoc.item(r, 2).text() if self.table_thuoc.item(r, 2) else ''
                unit_w = self.table_thuoc.cellWidget(r, 3)
                unit = unit_w.currentText() if unit_w else ''
                ld = self.table_thuoc.item(r, 8).text() if self.table_thuoc.item(r, 8) else ''
                note = self.table_thuoc.item(r, 9).text() if self.table_thuoc.item(r, 9) else ''
                html.append(f"<tr><td>{text}</td><td>{ten}</td><td>{qty}</td><td>{unit}</td><td>{ld}</td></tr>")
                if note and note.strip():
                    safe_note = note.replace('\n', '<br/>')
                    html.append(f"<tr><td colspan='5' style='background:#fafafa'><b>Ghi chú:</b> {safe_note}</td></tr>")
            html.append("</table>")
            # thuốc khác (only if present in this form)
            other_rows = []
            if hasattr(self, 'table_thuoc_khac'):
                for r in range(self.table_thuoc_khac.rowCount()):
                    name_item = self.table_thuoc_khac.item(r, 0)
                    if not name_item:
                        continue
                    name = name_item.text().strip()
                    if not name:
                        continue
                    qty = self.table_thuoc_khac.item(r, 1).text() if self.table_thuoc_khac.item(r, 1) else ''
                    unit_w = self.table_thuoc_khac.cellWidget(r, 2)
                    unit = unit_w.currentText() if unit_w else ''
                    ld = self.table_thuoc_khac.item(r, 3).text() if self.table_thuoc_khac.item(r, 3) else ''
                    other_rows.append((name, qty, unit, ld))
            if other_rows:
                html.append("<h4>Thuốc khác</h4>")
                html.append("<table border='1' cellspacing='0' cellpadding='4' width='100%'>")
                html.append("<tr style='background:#eee'><th>Tên</th><th>Số lượng</th><th>Đơn vị</th><th>Liều dùng</th></tr>")
                for name, qty, unit, ld in other_rows:
                    html.append(f"<tr><td>{name}</td><td>{qty}</td><td>{unit}</td><td>{ld}</td></tr>")
                html.append("</table>")
            html.append("<h4>Lời dặn</h4>")
            html.append(f"<div>{loi_dan.replace('\n', '<br/>')}</div>")
            html.append("<br/><div style='text-align:right'>Ngày kê: " + ngay + "</div>")
            return '\n'.join(html)
        except Exception as e:
            return f"<p>Lỗi khi tạo nội dung in: {e}</p>"

    def on_bo_qua(self):
        """Skip / cancel current operation; typically resets form."""
        try:
            self._suppress_item_changed = True
            self.clear_form()
            self.table_thuoc.clearContents()
            self.table_thuoc.setRowCount(0)
            for _ in range(5):
                self._append_empty_row_main()
            if hasattr(self, 'table_thuoc_khac'):
                try:
                    self.table_thuoc_khac.clearContents()
                    self.table_thuoc_khac.setRowCount(0)
                except Exception:
                    pass
            try:
                self.txt_loidan.clear()
            except Exception:
                pass
            QMessageBox.information(self, "Bỏ qua", "Đã hủy bỏ.")
        finally:
            self._suppress_item_changed = False

    def on_thoat(self):
        """Close the supplementary form window."""
        try:
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể đóng cửa sổ: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DonThuocKhac()
    win.show()
    sys.exit(app.exec_())
