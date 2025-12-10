import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QSpinBox, QHeaderView, QDialog, QTableView, QSizePolicy, QMessageBox,
    QInputDialog, QFileDialog
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtCore import Qt, QDate, QSortFilterProxyModel, pyqtSignal
from app_signals import app_signals
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from database import get_connection


class NoPopupComboBox(QComboBox):
    """A QComboBox variant that displays the current text but does not
    show a popup when clicked and hides the drop-down arrow.

    This keeps existing code that uses currentIndex/currentData working
    while removing the visual dropdown affordance and preventing user
    interaction via the popup.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # hide the drop-down arrow and minimize the drop-down area
        try:
            self.setStyleSheet(
                "QComboBox::drop-down { width: 0px; border: none; }"
                "QComboBox::down-arrow { image: none; }"
            )
        except Exception:
            pass

    def showPopup(self):
        # Prevent the popup from opening
        return


class NhapGhiChuDialog(QDialog):
    def __init__(self, parent=None, current_text=""):
        super().__init__(parent)
        self.setWindowTitle("Nhập Ghi Chú")
        self.setGeometry(300, 200, 400, 200)
        self.note = None
        self.current_text = current_text
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Add text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Nhập ghi chú vào đây...")
        if self.current_text and self.current_text != "Nhấn để nhập":
            self.text_edit.setText(self.current_text)
        layout.addWidget(self.text_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_note)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def accept_note(self):
        self.note = self.text_edit.toPlainText()
        if self.note.strip():  # Only accept if note is not empty
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

        # Danh sách các liều dùng phổ biến
        self.model = QStandardItemModel()
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
        
        for dose in common_doses:
            self.model.appendRow([QStandardItem(dose)])
        
        self.list_view = QTableView()
        self.list_view.setModel(self.model)
        self.list_view.horizontalHeader().hide()
        self.list_view.verticalHeader().hide()
        self.list_view.setSelectionBehavior(QTableView.SelectRows)
        self.list_view.setSelectionMode(QTableView.SingleSelection)
        self.list_view.doubleClicked.connect(self.accept_selection)
        # Set column width to fill the dialog
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # Set alternating row colors for better readability
        self.list_view.setAlternatingRowColors(True)
        # Set a minimum size for better appearance
        self.list_view.setMinimumSize(580, 400)
        layout.addWidget(self.list_view)

        # Buttons
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Chọn")
        select_btn.clicked.connect(self.accept_selection)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def accept_selection(self):
        indexes = self.list_view.selectedIndexes()
        if indexes:
            self.selected_dosage = self.model.data(indexes[0])
            self.accept()

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

        # Tạo model cho table view
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Mã thuốc", "Tên sản phẩm", "Đơn vị", "Tồn kho"])

        # Tạo proxy model để filter
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)  # Search all columns
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Tìm kiếm thuốc...")
        self.search_box.textChanged.connect(self.filter_drugs)
        layout.addWidget(self.search_box)

        # Table view
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
    # Kéo dài các cột để chiếm toàn bộ chiều rộng dialog
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table_view)

        # Buttons
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
        # include don_vi so we can auto-fill unit when a drug is selected
        cursor.execute("SELECT ma_thuoc, ten_thuoc, don_vi, ton_kho FROM danh_muc_thuoc")
        drugs = cursor.fetchall()
        conn.close()

        for drug in drugs:
            ma_thuoc = QStandardItem(str(drug[0]))
            ten_thuoc = QStandardItem(str(drug[1]))
            don_vi = QStandardItem(str(drug[2] or ""))
            ton_kho = QStandardItem(str(drug[3]))
            self.model.appendRow([ma_thuoc, ten_thuoc, don_vi, ton_kho])

    def filter_drugs(self, text):
        self.proxy_model.setFilterFixedString(text)

    def accept_selection(self):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            # read ma, ten, don_vi from proxy model
            ma = self.proxy_model.data(self.proxy_model.index(row, 0))
            ten = self.proxy_model.data(self.proxy_model.index(row, 1))
            don_vi = self.proxy_model.data(self.proxy_model.index(row, 2))
            self.selected_drug = {
                'ma_thuoc': ma,
                'ten_thuoc': ten,
                'don_vi': don_vi
            }
            self.accept()

class KeDonThuoc(QWidget):
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

    def show_diungthuoc_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Chi tiết dị ứng thuốc")
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(self.diungthuoc.text() if hasattr(self, 'diungthuoc') else "")
        layout.addWidget(text_edit)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec_()
    # Signal để thông báo khi dữ liệu được xuất
    medicine_exported = pyqtSignal()

    def __init__(self, phieu_kham_id=None, benh_nhan_id=None):
        super().__init__()
        self.phieu_kham_id = phieu_kham_id
        self.benh_nhan_id = benh_nhan_id
        self.setWindowTitle("KÊ ĐƠN THUỐC")
        self.setGeometry(200, 100, 1250, 750)
        # Flag to suppress itemChanged handlers during programmatic updates
        self._suppress_item_changed = False
        self.initUI()

        # If a patient ID was provided, auto-select that patient after initializing
        if self.benh_nhan_id:
            self.auto_select_patient(self.benh_nhan_id)

    def initUI(self):
        self.main_layout = QVBoxLayout()
        # Minimize spacing/margins for a more compact form, especially when zoomed
        self.main_layout.setSpacing(4)
        self.main_layout.setContentsMargins(6, 6, 6, 6)

        # ======== TIÊU ĐỀ ========
        title = QLabel("ĐƠN THUỐC")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0066cc;")
        self.main_layout.addWidget(title)

        # ======== THÔNG TIN BỆNH NHÂN ========
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        group_bn.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
        grid_bn = QGridLayout()
        grid_bn.setSpacing(6)
        grid_bn.setContentsMargins(6, 6, 6, 6)

        # Initialize widgets
        # Use a non-popup combobox for patient display: show selected name
        # but prevent the user from opening the dropdown (no arrow)
        self.hoten = NoPopupComboBox()
        self.hoten.setEditable(False)
        # currentIndexChanged is still used when programmatically selecting patients
        self.hoten.currentIndexChanged.connect(self.on_patient_selected)
        
        self.ngaysinh = QDateEdit(QDate.currentDate())
        self.ngaysinh.setCalendarPopup(True)
        self.ngaysinh.setReadOnly(True)
        
        self.gioitinh = QLineEdit()
        self.gioitinh.setReadOnly(True)
        
        self.dienthoai = QLineEdit()
        self.dienthoai.setReadOnly(True)
        
        self.tuoi = QLineEdit()
        self.tuoi.setReadOnly(True)
        
        self.sohoso = QLineEdit()
        self.sohoso.setReadOnly(True)
        
        self.sophieukham = QLineEdit()
        self.sophieukham.setReadOnly(True)
        self.sophieukham = QLineEdit()
        self.diachi = QLineEdit()
        self.diachi.setReadOnly(True)
        
        self.chandoan = QLineEdit()
        self.chandoan.setReadOnly(True)
        
        self.diungthuoc = QLineEdit()
        self.diungthuoc.setReadOnly(True)
        
        self.songay = QSpinBox()
        self.songay.setMinimum(1)
        self.songay.setMaximum(100)
        self.taikham = QDateEdit(QDate.currentDate())
        self.taikham.setCalendarPopup(True)
        self.tongtien = QLineEdit("0")
        self.doituong = QLineEdit()
        self.doituong.setReadOnly(True)
        
        self.loaithuoc = QComboBox()
        self.loaithuoc.addItems(["Thuốc cơ bản", "Thuốc khác"])
        self.ngaykedon = QDateEdit(QDate.currentDate())
        self.ngaykedon.setCalendarPopup(True)
        self.bacsi = QComboBox()
        self.bacsi.addItems(["Bác sĩ"])
        self.quaythuoc = QComboBox()
        self.quaythuoc.addItems(["Kho thuốc"])
        self.nguoilapphieu = QLineEdit()
        self.donmau = QComboBox()
        # Đơn mẫu: will populate from DB; keep special items
        self.donmau.addItem("--Chọn mẫu--", None)
        self.donmau.addItem("Xóa đơn mẫu", "delete")
        self.donmau.currentIndexChanged.connect(self.on_donmau_changed)
        # Buttons for saving/deleting templates
        self.btn_save_template = QPushButton("Lưu mẫu")
        self.btn_save_template.setMinimumWidth(80)
        self.btn_save_template.clicked.connect(self.on_save_template)
        try:
            self._style_button(self.btn_save_template, primary=False)
        except Exception:
            pass
        self.btn_delete_template = QPushButton("Xóa mẫu")
        self.btn_delete_template.setMinimumWidth(80)
        self.btn_delete_template.clicked.connect(self.on_delete_template)
        try:
            self._style_button(self.btn_delete_template, primary=False)
        except Exception:
            pass
        # Load templates from DB
        try:
            self.load_templates()
        except Exception:
            pass
        # Ensure custom 'thuốc khác' table exists for persisting user-entered items
        try:
            self.ensure_thuoc_khac_table()
        except Exception:
            pass
        self.doncu = QComboBox()
        self.doncu.currentIndexChanged.connect(self.on_doncu_changed)
        
        # Load patients into combobox
        self.load_patients()

        # --- Hàng 1 ---
        grid_bn.addWidget(QLabel("Bệnh nhân "), 0, 0)
        grid_bn.addWidget(self.hoten, 0, 1)
        grid_bn.addWidget(QLabel("Ngày sinh"), 0, 2)
        grid_bn.addWidget(self.ngaysinh, 0, 3)
        grid_bn.addWidget(QLabel("Giới tính"), 0, 4)
        grid_bn.addWidget(self.gioitinh, 0, 5)
        grid_bn.addWidget(QLabel("Bác sĩ kê đơn "), 0, 6)
        grid_bn.addWidget(self.bacsi, 0, 7)

        # --- Hàng 2 ---
        grid_bn.addWidget(QLabel("Điện thoại"), 1, 0)
        grid_bn.addWidget(self.dienthoai, 1, 1)
        grid_bn.addWidget(QLabel("Tuổi"), 1, 2)
        grid_bn.addWidget(self.tuoi, 1, 3)
        grid_bn.addWidget(QLabel("Số hồ sơ"), 1, 4)
        grid_bn.addWidget(self.sohoso, 1, 5)
        grid_bn.addWidget(QLabel("Quầy thuốc"), 1, 6)
        grid_bn.addWidget(self.quaythuoc, 1, 7)

        # --- Hàng 3 ---
        grid_bn.addWidget(QLabel("Địa chỉ"), 2, 0)
        grid_bn.addWidget(self.diachi, 2, 1, 1, 3)
        grid_bn.addWidget(QLabel("Số phiếu khám"), 2, 4)
        grid_bn.addWidget(self.sophieukham, 2, 5)
        grid_bn.addWidget(QLabel("Người lập phiếu"), 2, 6)
        grid_bn.addWidget(self.nguoilapphieu, 2, 7)

        # --- Hàng 4 ---
        grid_bn.addWidget(QLabel("Chẩn đoán"), 3, 0)
        self.chandoan = QLineEdit()
        grid_bn.addWidget(self.chandoan, 3, 1, 1, 2)
        self.btn_chandoan = QPushButton("Xem chi tiết")
        self.btn_chandoan.setMinimumWidth(100)
        self.btn_chandoan.clicked.connect(self.show_chandoan_dialog)
        grid_bn.addWidget(self.btn_chandoan, 3, 3)
        grid_bn.addWidget(QLabel("Ngày kê đơn"), 3, 4)
        grid_bn.addWidget(self.ngaykedon, 3, 5)
        grid_bn.addWidget(QLabel("Đơn mẫu"), 3, 6)
        # Place combobox and template buttons together in a container widget
        tmp_container = QWidget()
        tmp_h = QHBoxLayout()
        tmp_h.setContentsMargins(0, 0, 0, 0)
        tmp_h.setSpacing(4)
        tmp_h.addWidget(self.donmau)
        tmp_h.addWidget(self.btn_save_template)
        tmp_h.addWidget(self.btn_delete_template)
        tmp_container.setLayout(tmp_h)
        grid_bn.addWidget(tmp_container, 3, 7)

        # --- Hàng 5 ---
        grid_bn.addWidget(QLabel("Dị ứng thuốc"), 4, 0)
        self.diungthuoc = QLineEdit()
        grid_bn.addWidget(self.diungthuoc, 4, 1, 1, 2)
        self.btn_diungthuoc = QPushButton("Xem chi tiết")
        self.btn_diungthuoc.setMinimumWidth(100)
        self.btn_diungthuoc.clicked.connect(self.show_diungthuoc_dialog)
        grid_bn.addWidget(self.btn_diungthuoc, 4, 3)
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

        def show_diungthuoc_dialog(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Chi tiết dị ứng thuốc")
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(self.diungthuoc.text() if hasattr(self, 'diungthuoc') else "")
            layout.addWidget(text_edit)
            btn_close = QPushButton("Đóng")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.exec_()
        grid_bn.addWidget(QLabel("Đối tượng"), 4, 4)
        grid_bn.addWidget(self.doituong, 4, 5)
        grid_bn.addWidget(QLabel("Đơn cũ"), 4, 6)
        grid_bn.addWidget(self.doncu, 4, 7)

        # --- Hàng 6 ---
        grid_bn.addWidget(QLabel("Số ngày"), 5, 0)
        grid_bn.addWidget(self.songay, 5, 1)
        grid_bn.addWidget(QLabel("Hẹn tái khám"), 5, 2)
        grid_bn.addWidget(self.taikham, 5, 3)
        grid_bn.addWidget(QLabel("Tổng tiền"), 5, 4)
        grid_bn.addWidget(self.tongtien, 5, 5)
        grid_bn.addWidget(QLabel("Loại đơn"), 5, 6)
        grid_bn.addWidget(self.loaithuoc, 5, 7)

        group_bn.setLayout(grid_bn)
        self.main_layout.addWidget(group_bn)

        # ======== BẢNG THUỐC ========
        # Bỏ cột STT; các cột sẽ là: Mã thuốc, Tên thuốc, Số lượng, Đơn vị, Sáng, Trưa, Chiều, Tối, Liều dùng, Ghi chú
        group_danhmuc = QGroupBox("DANH MỤC THUỐC")
        group_danhmuc.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
        vbox_danhmuc = QVBoxLayout()
        vbox_danhmuc.setSpacing(4)
        vbox_danhmuc.setContentsMargins(6, 6, 6, 6)
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
            # Unit combo for column 3 (arrow-only until a choice is made)
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

        # Make table expand horizontally but keep vertical size fixed to the calculated
        # maximum so it doesn't push content down when zooming.
        self.table_thuoc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Keep cell double-click behavior
        self.table_thuoc.cellDoubleClicked.connect(self.handle_cell_double_click)

        # Put the main medicines table inside the GroupBox's layout so it's visually grouped
        vbox_danhmuc.addWidget(self.table_thuoc)
        group_danhmuc.setLayout(vbox_danhmuc)
        self.main_layout.addWidget(group_danhmuc)

        # ======== THUỐC KHÁC ========
        group_khac = QGroupBox("THUỐC KHÁC")
        group_khac.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
        vbox_khac = QVBoxLayout()
        vbox_khac.setSpacing(4)
        vbox_khac.setContentsMargins(6, 6, 6, 6)

        # Bảng thuốc khác (4 cột: Tên, Số lượng, Đơn vị, Liều dùng)
        self.table_thuoc_khac = QTableWidget(3, 4)
        self.table_thuoc_khac.setHorizontalHeaderLabels([
            "Tên thuốc ngoài", "Số lượng", "Đơn vị", "Liều dùng"
        ])
        # First column (Tên thuốc ngoài) should take available width, others fixed
        self.table_thuoc_khac.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # Thêm placeholder cho bảng thuốc khác
        for r in range(self.table_thuoc_khac.rowCount()):
            name = QTableWidgetItem("")
            qty = QTableWidgetItem("")
            unit = QTableWidgetItem("")
            dose = QTableWidgetItem("Nhấn để chọn")
            dose.setForeground(Qt.gray)
            # Unit combo for thuốc khác col 2 (arrow-only until a choice is made)
            unit_combo = self._make_unit_combo()
            self.table_thuoc_khac.setItem(r, 0, name)
            self.table_thuoc_khac.setItem(r, 1, qty)
            self.table_thuoc_khac.setCellWidget(r, 2, unit_combo)
            self.table_thuoc_khac.setItem(r, 3, dose)
        # Kết nối sự kiện để tự động thêm hàng khi người dùng nhập vào hàng cuối của bảng thuốc khác
        self.table_thuoc_khac.itemChanged.connect(self.on_table_thuoc_khac_item_changed)
        # Kết nối double click để mở dialog liều dùng cho thuốc khác
        self.table_thuoc_khac.cellDoubleClicked.connect(self.handle_table_thuoc_khac_double_clicked)

        vbox_khac.addWidget(self.table_thuoc_khac)
        group_khac.setLayout(vbox_khac)
        self.main_layout.addWidget(group_khac)

        # Adjust column widths for THUỐC KHÁC table
        # Make "Tên thuốc ngoài" column shorter and fixed width
        self.table_thuoc_khac.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_thuoc_khac.setColumnWidth(0, 350)
        
        # Keep "Số lượng" and "Đơn vị" the same
        self.table_thuoc_khac.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table_thuoc_khac.setColumnWidth(1, 110)
        self.table_thuoc_khac.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table_thuoc_khac.setColumnWidth(2, 140)
        
        # Make "Liều dùng" column stretch to take remaining space
        self.table_thuoc_khac.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        # Set size policy so the thuốc khác table won't expand vertically and create a
        # large gap before 'LỜI DẶN'. Vertical size is fixed; horizontal expands.
        self.table_thuoc_khac.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # We'll adjust both tables' maximum heights to show N visible rows in a responsive
        # way by recalculating sizes on resize. Call adjustment once now after creation.
        try:
            self.adjust_table_heights()
        except Exception:
            pass


        # ======== LỜI DẶN ========
        self.main_layout.addWidget(QLabel("LỜI DẶN"))
        self.loidan = QTextEdit()
        self.main_layout.addWidget(self.loidan)
        # Make the 'LỜI DẶN' box smaller so it doesn't take too much space
        try:
            self.loidan.setMaximumHeight(70)
            self.loidan.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        except Exception:
            pass

        # ======== NÚT CHỨC NĂNG ========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(2, 2, 2, 2)

        # Left-aligned buttons
        left_btn_layout = QHBoxLayout()
        self.btn_nhapmoi = QPushButton("Nhập mới (F1)")
        self.btn_nhapmoi.setMinimumWidth(100)
        self.btn_nhapmoi.clicked.connect(self.on_nhapmoi)
        try:
            self._style_button(self.btn_nhapmoi, primary=True)
        except Exception:
            pass
        left_btn_layout.addWidget(self.btn_nhapmoi)

        self.btn_luu = QPushButton("Lưu (F2)")
        self.btn_luu.setMinimumWidth(100)
        self.btn_luu.clicked.connect(self.on_luu)
        try:
            self._style_button(self.btn_luu, primary=True)
        except Exception:
            pass
        left_btn_layout.addWidget(self.btn_luu)

        self.btn_sua = QPushButton("Sửa")
        self.btn_sua.setMinimumWidth(100)
        self.btn_sua.clicked.connect(self.on_sua)
        try:
            self._style_button(self.btn_sua, primary=True)
        except Exception:
            pass
        left_btn_layout.addWidget(self.btn_sua)

        self.btn_xoa = QPushButton("Xóa")
        self.btn_xoa.setMinimumWidth(100)
        self.btn_xoa.clicked.connect(self.on_xoa)
        try:
            self._style_button(self.btn_xoa, primary=True)
        except Exception:
            pass
        left_btn_layout.addWidget(self.btn_xoa)

        btn_layout.addLayout(left_btn_layout)
        btn_layout.addStretch()  # Add space between left and right buttons

        # Right-aligned buttons
        right_btn_layout = QHBoxLayout()
        self.btn_in_don = QPushButton("In đơn")
        self.btn_in_don.setMinimumWidth(100)
        self.btn_in_don.clicked.connect(self.on_in_don)
        try:
            self._style_button(self.btn_in_don, primary=True)
        except Exception:
            pass
        right_btn_layout.addWidget(self.btn_in_don)

        self.btn_xuat_thuoc = QPushButton("Gửi cổng dược")
        self.btn_xuat_thuoc.setMinimumWidth(100)
        self.btn_xuat_thuoc.clicked.connect(self.on_xuat_thuoc)
        try:
            self._style_button(self.btn_xuat_thuoc, primary=True)
        except Exception:
            pass
        right_btn_layout.addWidget(self.btn_xuat_thuoc)

        self.btn_thoat = QPushButton("Thoát")
        self.btn_thoat.setMinimumWidth(100)
        self.btn_thoat.clicked.connect(self.on_thoat)
        try:
            self._style_button(self.btn_thoat, primary=False)
        except Exception:
            pass
        right_btn_layout.addWidget(self.btn_thoat)

        btn_layout.addLayout(right_btn_layout)
        self.main_layout.addLayout(btn_layout)

        self.setLayout(self.main_layout)

    def _make_unit_combo(self, initial_value=None):
        """Create a unit QComboBox that hides its text until the user picks or types one.

        initial_value: optional string to pre-select or pre-fill the combo.
        """
        unit_options = ["viên", "lọ", "chai", "ống", "gói", "tuýp", "tuýp nhỏ", "ống nhỏ"]
        combo = QComboBox()
        combo.addItems(unit_options)
        combo.setEditable(True)
        # Always clear the text initially
        combo.setCurrentIndex(-1)
        combo.clearEditText()

        # Hide the line edit text until user enters/selects something
        le = combo.lineEdit()
        le.setStyleSheet("color: rgba(0,0,0,0);")
        le.clear()  # ensure text is cleared

        def reveal_if_not_empty(txt):
            if txt and str(txt).strip():
                try:
                    le.setStyleSheet("color: black;")
                except Exception:
                    pass
            else:
                try:
                    le.setStyleSheet("color: rgba(0,0,0,0);")
                except Exception:
                    pass

        # When the current text or the lineedit changes, reveal the text if non-empty
        combo.currentTextChanged.connect(reveal_if_not_empty)
        le.textChanged.connect(reveal_if_not_empty)

        # If an initial value is provided AND it's not empty, select or set it and reveal
        if initial_value and str(initial_value).strip():
            if initial_value in unit_options:
                combo.setCurrentIndex(unit_options.index(initial_value))
            else:
                combo.setCurrentText(str(initial_value))
            try:
                le.setStyleSheet("color: black;")
            except Exception:
                pass
        else:
            # No initial value or empty - ensure combo is cleared
            combo.setCurrentIndex(-1)
            combo.clearEditText()
            le.clear()
            try:
                le.setStyleSheet("color: rgba(0,0,0,0);")
            except Exception:
                pass

        return combo

    def _style_button(self, btn, primary=True):
        """Apply consistent flat/tab-like styling to buttons.

        primary: if True use stronger blue; otherwise use a lighter outline style.
        """
        if primary:
            style = (
                "QPushButton {"
                "background-color: #0078D7;"
                "color: white;"
                "border: 1px solid #0078D7;"
                "border-radius: 4px;"
                "padding: 6px 12px;"
                "}"
                "QPushButton:hover {"
                "background-color: #005a9e;"
                "color: white;"
                "}"
                "QPushButton:pressed {"
                "background-color: #004a87;"
                "}"
                "QPushButton:disabled {"
                "background-color: #d6e6fb;"
                "color: #9aaecf;"
                "}"
            )
        else:
            style = (
                "QPushButton {"
                "background-color: transparent;"
                "color: #0078D7;"
                "border: 1px solid #0078D7;"
                "border-radius: 4px;"
                "padding: 4px 10px;"
                "}"
                "QPushButton:hover {"
                "background-color: #e6f0fb;"
                "color: #005a9e;"
                "}"
                "QPushButton:pressed {"
                "background-color: #cfe6fb;"
                "}"
            )
        try:
            btn.setStyleSheet(style)
            # keep text visible on hover by ensuring color rules are set above
            btn.setCursor(Qt.PointingHandCursor)
        except Exception:
            pass

    def handle_cell_double_click(self, row, col):
        # Open drug chooser when user double-clicks on Mã thuốc (col 0) or Tên thuốc (col 1)
        if col in (0, 1):
            dialog = ChonThuocDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_drug:
                # Cập nhật mã thuốc (col 0) và tên thuốc (col 1) with black text
                ma_item = QTableWidgetItem(dialog.selected_drug['ma_thuoc'])
                ten_item = QTableWidgetItem(dialog.selected_drug['ten_thuoc'])
                ma_item.setForeground(Qt.black)
                # Make entered items non-editable so user cannot overwrite by typing
                try:
                    ma_item.setFlags(ma_item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                ten_item.setForeground(Qt.black)
                try:
                    ten_item.setFlags(ten_item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                self.table_thuoc.setItem(row, 0, ma_item)
                self.table_thuoc.setItem(row, 1, ten_item)
                # If the selected drug includes a unit, apply it to the unit combo cell
                try:
                    don_vi = dialog.selected_drug.get('don_vi')
                    if don_vi:
                        unit_widget = self.table_thuoc.cellWidget(row, 3)
                        if unit_widget:
                            try:
                                unit_widget.setCurrentText(don_vi)
                            except Exception:
                                # fallback: try setting the edit text
                                try:
                                    unit_widget.lineEdit().setText(don_vi)
                                except Exception:
                                    pass
                except Exception:
                    pass
        # Open dosage chooser when user double-clicks on Liều dùng (col 8)
        elif col == 8:
            dialog = ChonLieuDungDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_dosage:
                ld_item = QTableWidgetItem(dialog.selected_dosage)
                ld_item.setForeground(Qt.black)
                try:
                    ld_item.setFlags(ld_item.flags() & ~Qt.ItemIsEditable)
                except Exception:
                    pass
                self.table_thuoc.setItem(row, col, ld_item)
        # Open note input dialog when user double-clicks on Ghi chú (col 9)
        elif col == 9:
            current_text = ""
            current_item = self.table_thuoc.item(row, col)
            if current_item and current_item.text() != "Nhấn để chọn":
                current_text = current_item.text()
            
            dialog = NhapGhiChuDialog(self, current_text)
            if dialog.exec_() == QDialog.Accepted and dialog.note:
                self.table_thuoc.setItem(row, col, QTableWidgetItem(dialog.note))

    def on_doncu_changed(self, index):
        """Xử lý khi người dùng chọn một đơn cũ từ combobox."""
        if index <= 0:  # Bỏ qua item đầu tiên (-- Chọn đơn cũ --)
            return
            
        don_cu_id = self.doncu.currentData()
        if don_cu_id == "new":
            # Người dùng chọn tạo đơn mới: chỉ reset phần đơn thuốc (không xóa
            # thông tin bệnh nhân). Điều này giữ nguyên các trường bệnh nhân
            # hiện tại và chỉ làm sạch bảng thuốc + lời dặn để nhập đơn mới.
            self.reset_prescription_content()
            return
            
        if don_cu_id:
            # Load đơn thuốc đã chọn
            self.load_prescription(don_cu_id)
            # Disable form sau khi load
            self.disable_form_editing()

    def load_templates(self):
        """Load templates (don_mau) from DB into self.donmau combobox."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, ten_mau, ngay_tao FROM don_mau ORDER BY ngay_tao DESC")
            rows = cur.fetchall()
            conn.close()
        except Exception:
            rows = []

        # Clear current template items but keep first two special items
        try:
            # Remove all items and re-add fixed ones
            self.donmau.clear()
            self.donmau.addItem("--Chọn mẫu--", None)
            self.donmau.addItem("Xóa đơn mẫu", "delete")
            for r in rows:
                tid, name, ngay = r
                label = f"{name} - {ngay}" if name else f"Mẫu {tid} - {ngay}"
                self.donmau.addItem(label, tid)
        except Exception:
            pass

    def ensure_thuoc_khac_table(self):
        """Create `thuoc_khac` table if it does not exist. Used to persist custom 'thuốc khác' entries."""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Desired schema: id, ten_thuoc, don_vi, ghi_chu, don_thuoc_id
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='thuoc_khac'")
            exists = cur.fetchone()
            if not exists:
                cur.execute(
                    """
                    CREATE TABLE thuoc_khac (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ten_thuoc TEXT NOT NULL,
                        don_vi TEXT,
                        ghi_chu TEXT,
                        don_thuoc_id INTEGER
                    )
                    """
                )
            else:
                # Table exists; verify columns and migrate if necessary
                cur.execute("PRAGMA table_info('thuoc_khac')")
                cols = [r[1] for r in cur.fetchall()]
                # If created_by/created_at exist or don_thuoc_id missing, migrate to new schema
                if ('created_by' in cols) or ('created_at' in cols) or ('don_thuoc_id' not in cols):
                    # create new table
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS thuoc_khac_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ten_thuoc TEXT NOT NULL,
                            don_vi TEXT,
                            ghi_chu TEXT,
                            don_thuoc_id INTEGER
                        )
                        """
                    )
                    # copy data: map ten_thuoc, don_vi, ghi_chu where possible
                    copy_cols = []
                    if 'ten_thuoc' in cols:
                        copy_cols.append('ten_thuoc')
                    if 'don_vi' in cols:
                        copy_cols.append('don_vi')
                    if 'ghi_chu' in cols:
                        copy_cols.append('ghi_chu')
                    if copy_cols:
                        src_cols = ', '.join(copy_cols)
                        dst_cols = src_cols
                        cur.execute(f"INSERT INTO thuoc_khac_new ({dst_cols}) SELECT {src_cols} FROM thuoc_khac")
                    # drop old and rename
                    cur.execute("DROP TABLE thuoc_khac")
                    cur.execute("ALTER TABLE thuoc_khac_new RENAME TO thuoc_khac")
            conn.commit()
        except Exception:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
        finally:
            if conn:
                conn.close()

    def on_save_template(self):
        """Save current prescription content as a template into don_mau and chi_tiet_don_mau."""
        # Ask for template name
        name, ok = QInputDialog.getText(self, "Lưu mẫu", "Tên mẫu:")
        if not ok or not name.strip():
            return
        name = name.strip()

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            # insert into don_mau
            cur.execute("INSERT INTO don_mau (ten_mau, ngay_tao, chan_doan, loi_dan, bac_si, quay_thuoc, nguoi_lap_phieu) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                name,
                QDate.currentDate().toString("yyyy-MM-dd"),
                self.chandoan.text(),
                self.loidan.toPlainText(),
                self.bacsi.currentText(),
                self.quaythuoc.currentText(),
                self.nguoilapphieu.text()
            ))
            don_mau_id = cur.lastrowid

            # save main table items
            for r in range(self.table_thuoc.rowCount()):
                ma = self.table_thuoc.item(r, 0)
                if not ma or not ma.text() or ma.text() == "Nhấn để chọn":
                    continue
                ten = self.table_thuoc.item(r, 1)
                qty = self.table_thuoc.item(r, 2)
                unit_widget = self.table_thuoc.cellWidget(r, 3)
                unit = unit_widget.currentText() if unit_widget else None
                sang = self.table_thuoc.item(r, 4)
                trua = self.table_thuoc.item(r, 5)
                chieu = self.table_thuoc.item(r, 6)
                toi = self.table_thuoc.item(r, 7)
                lieu = self.table_thuoc.item(r, 8)
                ghi = self.table_thuoc.item(r, 9)

                cur.execute("INSERT INTO chi_tiet_don_mau (don_mau_id, ma_thuoc, ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    don_mau_id,
                    ma.text(),
                    ten.text() if ten else None,
                    int(qty.text()) if qty and qty.text() else 0,
                    unit or None,
                    sang.text() if sang else None,
                    trua.text() if trua else None,
                    chieu.text() if chieu else None,
                    toi.text() if toi else None,
                    lieu.text() if lieu else None,
                    ghi.text() if ghi else None
                ))

            # save thuốc khác
            for r in range(self.table_thuoc_khac.rowCount()):
                ten = self.table_thuoc_khac.item(r, 0)
                if not ten or not ten.text():
                    continue
                qty = self.table_thuoc_khac.item(r, 1)
                unit_widget = self.table_thuoc_khac.cellWidget(r, 2)
                unit = unit_widget.currentText() if unit_widget else None
                lieu = self.table_thuoc_khac.item(r, 3)
                cur.execute("INSERT INTO chi_tiet_don_mau (don_mau_id, ma_thuoc, ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu) VALUES (?, NULL, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL)", (
                    don_mau_id,
                    ten.text(),
                    int(qty.text()) if qty and qty.text() else 0,
                    unit or None,
                    lieu.text() if lieu else None
                ))

            conn.commit()
            QMessageBox.information(self, "Thành công", "Đã lưu mẫu thành công.")
            # reload templates
            try:
                self.load_templates()
            except Exception:
                pass

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu mẫu: {e}")
        finally:
            if conn:
                conn.close()

    def on_delete_template(self):
        """Delete selected template from DB."""
        data = self.donmau.currentData()
        if not data or data == "delete":
            QMessageBox.information(self, "Lưu ý", "Hãy chọn một mẫu để xóa.")
            return
        template_id = data
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xóa mẫu này?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM chi_tiet_don_mau WHERE don_mau_id = ?", (template_id,))
            cur.execute("DELETE FROM don_mau WHERE id = ?", (template_id,))
            conn.commit()
            QMessageBox.information(self, "Thành công", "Đã xóa mẫu.")
            try:
                self.load_templates()
            except Exception:
                pass
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa mẫu: {e}")
        finally:
            if conn:
                conn.close()

    def load_template(self, template_id):
        """Load a template (don_mau) by id into the form (fill fields and tables)."""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT chan_doan, loi_dan, bac_si, quay_thuoc, nguoi_lap_phieu FROM don_mau WHERE id = ?", (template_id,))
            row = cur.fetchone()
            if row:
                chan_doan, loi_dan, bac_si, quay, nguoi = row
                try:
                    self.chandoan.setText(chan_doan or "")
                    self.loidan.setPlainText(loi_dan or "")
                    try:
                        self.bacsi.setCurrentText(bac_si or self.bacsi.currentText())
                    except Exception:
                        pass
                    try:
                        self.quaythuoc.setCurrentText(quay or self.quaythuoc.currentText())
                    except Exception:
                        pass
                    self.nguoilapphieu.setText(nguoi or "")
                except Exception:
                    pass

            # Load template details
            cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu FROM chi_tiet_don_mau WHERE don_mau_id = ?", (template_id,))
            details = cur.fetchall()

            self._suppress_item_changed = True
            try:
                if details:
                    self.table_thuoc.setRowCount(len(details))
                    for r, d in enumerate(details):
                        ma, ten, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu = d
                        ma_item = QTableWidgetItem(str(ma or ""))
                        ma_item.setForeground(Qt.black)
                        self.table_thuoc.setItem(r, 0, ma_item)

                        ten_item = QTableWidgetItem(str(ten or ""))
                        ten_item.setForeground(Qt.black)
                        self.table_thuoc.setItem(r, 1, ten_item)

                        qty_item = QTableWidgetItem(str(so_luong or ""))
                        self.table_thuoc.setItem(r, 2, qty_item)

                        unit_combo = self._make_unit_combo(initial_value=don_vi)
                        self.table_thuoc.setCellWidget(r, 3, unit_combo)

                        for ci, val in enumerate((sang, trua, chieu, toi), start=4):
                            self.table_thuoc.setItem(r, ci, QTableWidgetItem(str(val or "")))

                        ld_item = QTableWidgetItem(str(lieu_dung or ""))
                        ld_item.setForeground(Qt.black)
                        self.table_thuoc.setItem(r, 8, ld_item)

                        note_item = QTableWidgetItem(str(ghi_chu or ""))
                        note_item.setForeground(Qt.black)
                        self.table_thuoc.setItem(r, 9, note_item)
                else:
                    self.reset_tables()
            finally:
                self._suppress_item_changed = False

        except Exception as e:
            QMessageBox.warning(self, "Lỗi tải mẫu", f"Không thể tải mẫu: {e}")
        finally:
            if conn:
                conn.close()

    def on_donmau_changed(self, index):
        """Load dữ liệu khi chọn một đơn mẫu từ combo box `Đơn mẫu`."""
        # Nếu chọn mục mặc định (index 0) thì không làm gì
        if index <= 0:
            return

        data = self.donmau.itemData(index)
        if data == "delete":
            # Reset combobox về trạng thái chọn mẫu
            self.donmau.setCurrentIndex(0)
            return

        # Nếu item có id template -> load từ DB
        template_id = data
        if template_id:
            try:
                self.load_template(template_id)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể load mẫu: {e}")

    def _append_empty_row_main(self, force_count=5):
        """Append a new empty row to the main medicines table with placeholders.
        
        Args:
            force_count: if provided, ensure table has exactly this many rows by adding
                       empty rows or removing excess rows.
        """
        def _make_empty_row(row_idx):
            """Helper to create an empty row with proper placeholders"""
            # Block signals while setting up the row to prevent any auto-fill
            old_state = self.table_thuoc.signalsBlocked()
            self.table_thuoc.blockSignals(True)
            try:
                ma = QTableWidgetItem("Nhấn để chọn")
                ten = QTableWidgetItem("Nhấn để chọn")
                lieu = QTableWidgetItem("Nhấn để chọn")
                ghi = QTableWidgetItem("Nhấn để chọn")
                # Ensure placeholders are gray
                ma.setForeground(Qt.gray)
                ten.setForeground(Qt.gray)
                lieu.setForeground(Qt.gray)
                ghi.setForeground(Qt.gray)
                
                # Set data to distinguish placeholder text
                for item in (ma, ten, lieu, ghi):
                    item.setData(Qt.UserRole, "placeholder")
                    
                self.table_thuoc.setItem(row_idx, 0, ma)
                self.table_thuoc.setItem(row_idx, 1, ten)
                
                # Quantity must be an empty QTableWidgetItem (not None)
                qty = QTableWidgetItem()
                qty.setData(Qt.UserRole, "empty")  # mark as intentionally empty
                self.table_thuoc.setItem(row_idx, 2, qty)
                
                # Unit combo must be properly cleared
                unit_combo = self._make_unit_combo()
                self.table_thuoc.setCellWidget(row_idx, 3, unit_combo)
                
                # Time columns must be empty QTableWidgetItems (not None)
                for ci in range(4, 8):
                    time_item = QTableWidgetItem()
                    time_item.setData(Qt.UserRole, "empty")
                    self.table_thuoc.setItem(row_idx, ci, time_item)
                    
                self.table_thuoc.setItem(row_idx, 8, lieu)
                self.table_thuoc.setItem(row_idx, 9, ghi)
                
                # Clear any cached data/properties that might cause auto-fill
                for col in range(self.table_thuoc.columnCount()):
                    item = self.table_thuoc.item(row_idx, col)
                    if item:
                        item.setToolTip("")
                        item.setStatusTip("")
            finally:
                self.table_thuoc.blockSignals(old_state)
            
        if force_count:
            # Remove excess rows or add missing rows to match force_count
            current = self.table_thuoc.rowCount()
            if current > force_count:
                for _ in range(current - force_count):
                    self.table_thuoc.removeRow(self.table_thuoc.rowCount() - 1)
            elif current < force_count:
                for _ in range(force_count - current):
                    r = self.table_thuoc.rowCount()
                    self.table_thuoc.insertRow(r)
                    _make_empty_row(r)
            
            # Now ensure all empty rows have proper placeholders
            for r in range(self.table_thuoc.rowCount()):
                item0 = self.table_thuoc.item(r, 0)
                if not item0 or not item0.text().strip() or item0.data(Qt.UserRole) == "placeholder":
                    _make_empty_row(r)
            return

        # Normal append mode - just add one row
        r = self.table_thuoc.rowCount()
        self.table_thuoc.insertRow(r)
        _make_empty_row(r)  # Use the helper to ensure consistent empty row format

    def _append_empty_row_khac(self):
        """Append a new empty row to the 'thuốc khác' table with placeholders."""
        r = self.table_thuoc_khac.rowCount()
        self.table_thuoc_khac.insertRow(r)
        # name and qty empty by default
        name = QTableWidgetItem("")
        qty = QTableWidgetItem("")
        dose = QTableWidgetItem("Nhấn để chọn")
        dose.setForeground(Qt.gray)
        # add unit combo for thuốc khác (arrow-only until selection)
        unit_combo = self._make_unit_combo()
        self.table_thuoc_khac.setItem(r, 0, name)
        self.table_thuoc_khac.setItem(r, 1, qty)
        self.table_thuoc_khac.setCellWidget(r, 2, unit_combo)
        self.table_thuoc_khac.setItem(r, 3, dose)

    def on_table_thuoc_item_changed(self, item):
        """Handler: when user edits last row in main table, append a new empty row."""
        if self._suppress_item_changed:
            return
        if item is None:
            return
        
        # Clear any residual data when placeholder text is edited
        if item.data(Qt.UserRole) == "placeholder" and item.text() != "Nhấn để chọn":
            # User edited a placeholder cell - remove placeholder status
            item.setData(Qt.UserRole, None)
            item.setForeground(Qt.black)
            # After user provides a value for mã thuốc / tên thuốc / liều dùng,
            # make that cell non-editable to prevent accidental deletion/overwrite
            try:
                if item.column() in (0, 1, 8):
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            except Exception:
                pass
            
        last_row = self.table_thuoc.rowCount() - 1
        # If edited item is in the last row and not empty, append a new row
        if item.row() == last_row and item.text().strip():
            self._suppress_item_changed = True
            self._append_empty_row_main()
            self._suppress_item_changed = False

    def on_table_thuoc_khac_item_changed(self, item):
        """Handler: when user edits last row in thuốc khác table, append a new empty row."""
        if self._suppress_item_changed:
            return
        if item is None:
            return
        last_row = self.table_thuoc_khac.rowCount() - 1
        if item.row() == last_row and item.text().strip():
            self._suppress_item_changed = True
            self._append_empty_row_khac()
            self._suppress_item_changed = False

    def handle_table_thuoc_khac_double_clicked(self, row, col):
        """Handle double-clicks on the 'thuốc khác' table.
        Open the dosage chooser when user double-clicks column 3 (Liều dùng).
        """
        # Liều dùng is column index 3 in table_thuoc_khac
        if col == 3:
            dialog = ChonLieuDungDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_dosage:
                item = QTableWidgetItem(dialog.selected_dosage)
                item.setForeground(Qt.black)
                self.table_thuoc_khac.setItem(row, col, item)

    def adjust_table_heights(self):
        """Adjust maximum heights of the tables so they show a fixed number
        of visible rows (5 for main, 3 for 'thuốc khác') while remaining
        responsive to DPI/zoom and row height changes.
        """
        def _calc(table, visible_rows):
            header_h = table.horizontalHeader().height()
            if table.rowCount() > 0:
                row_h = table.rowHeight(0)
            else:
                row_h = table.verticalHeader().defaultSectionSize()
            # Add a small margin for gridlines
            total_h = header_h + row_h * visible_rows + 6
            table.setMaximumHeight(total_h)

        try:
            if hasattr(self, 'table_thuoc'):
                _calc(self.table_thuoc, 5)
            if hasattr(self, 'table_thuoc_khac'):
                _calc(self.table_thuoc_khac, 3)
        except Exception:
            # Non-fatal: best-effort sizing
            pass

    def resizeEvent(self, event):
        # Keep table heights recalculated when the window is resized or DPI changes
        try:
            self.adjust_table_heights()
        except Exception:
            pass
        return super().resizeEvent(event)
        
    def clear_form(self):
        """Clear all form fields"""
        self.ngaysinh.setDate(QDate.currentDate())
        self.gioitinh.clear()
        self.dienthoai.clear()
        self.tuoi.clear()
        self.sohoso.clear()
        self.sophieukham.clear()
        self.diachi.clear()
        self.chandoan.clear()
        self.diungthuoc.clear()
        self.doituong.clear()

    def reset_tables(self):
        """Reset main and 'thuốc khác' tables to placeholder state."""
        # Main table -> exactly 5 empty rows with placeholders
        self._suppress_item_changed = True
        try:
            # Clear the table completely first
            self.table_thuoc.clearContents()
            self.table_thuoc.setRowCount(0)
            # Then use _append_empty_row_main with force_count to add 5 properly initialized rows
            self._append_empty_row_main(force_count=5)
        finally:
            self._suppress_item_changed = False

        # Thuốc khác table -> 3 rows
        self._suppress_item_changed = True
        try:
            self.table_thuoc_khac.setRowCount(3)
            for r in range(self.table_thuoc_khac.rowCount()):
                name = QTableWidgetItem("")
                qty = QTableWidgetItem("")
                unit_combo = self._make_unit_combo()
                dose = QTableWidgetItem("Nhấn để chọn")
                dose.setForeground(Qt.gray)
                self.table_thuoc_khac.setItem(r, 0, name)
                self.table_thuoc_khac.setItem(r, 1, qty)
                self.table_thuoc_khac.setCellWidget(r, 2, unit_combo)
                self.table_thuoc_khac.setItem(r, 3, dose)
        finally:
            self._suppress_item_changed = False

    def on_nhapmoi(self):
        """Reset only medicine tables and note, keeping all patient info."""
        # Get current patient info before reset
        current_patient_data = self.hoten.currentData()
        
        # Reset only prescription content
        self.reset_prescription_content()
        
        try:
            # Update old prescriptions combobox if a patient is selected
            if isinstance(current_patient_data, dict):
                benh_nhan_id = current_patient_data.get('id')
                if benh_nhan_id:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT dt.id, dt.ngay_ke, dt.chan_doan 
                        FROM don_thuoc dt
                        JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                        WHERE pk.benh_nhan_id = ?
                        ORDER BY dt.ngay_ke DESC, dt.id DESC
                    """, (benh_nhan_id,))
                    prescriptions = cursor.fetchall()
                    conn.close()

                    self.doncu.clear()
                    self.doncu.addItem("-- Chọn đơn cũ --", None)
                    self.doncu.addItem(">>> Tạo đơn mới <<<", "new")
                    for p in prescriptions:
                        display_text = f"{p[1]} - {p[2][:50] + '...' if p[2] and len(p[2]) > 50 else p[2] or 'Không có chẩn đoán'}"
                        self.doncu.addItem(display_text, p[0])
            else:
                self.doncu.clear()
                self.doncu.addItem("-- Chọn đơn cũ --", None)
        except Exception:
            pass
        
        # Reload templates in case they were modified
        try:
            self.load_templates()
        except Exception:
            pass

    def reset_prescription_content(self):
        """Reset only the prescription tables and note, keeping all other info intact."""
        try:
            # Reset tables to placeholders
            self.reset_tables()
        except Exception:
            pass

        try:
            # Reset only prescription-specific fields
            self.loidan.clear()
            self.songay.setValue(1)
            self.tongtien.setText("0")
            try:
                self.donmau.setCurrentIndex(0)
            except Exception:
                pass
            
            # Reset dates to current date
            current_date = QDate.currentDate()
            self.ngaykedon.setDate(current_date)
            self.taikham.setDate(current_date)
            
            # reset last saved id because we are creating a new unsaved prescription
            self.last_don_thuoc_id = None
            # enable editing so user can start typing immediately
            self.enable_form_editing()
        except Exception:
            pass

    def disable_form_editing(self):
        """Disable editing of form fields"""
        # Disable tables
        self.table_thuoc.setEnabled(False)
        self.table_thuoc_khac.setEnabled(False)
        
        # Disable other editable fields
        fields_to_disable = [
            self.chandoan, self.diungthuoc, self.nguoilapphieu, self.tongtien,
            self.songay, self.taikham, self.ngaykedon, self.loidan
        ]
        for field in fields_to_disable:
            try:
                field.setReadOnly(True)
            except:
                field.setEnabled(False)
                
        # Disable comboboxes
        combos_to_disable = [
            self.bacsi, self.quaythuoc, self.loaithuoc, self.donmau
        ]
        for combo in combos_to_disable:
            combo.setEnabled(False)
            
    def enable_form_editing(self):
        """Enable editing of form fields"""
        # Enable tables
        self.table_thuoc.setEnabled(True)
        self.table_thuoc_khac.setEnabled(True)
        
        # Enable other editable fields
        fields_to_enable = [
            self.chandoan, self.diungthuoc, self.nguoilapphieu, self.tongtien,
            self.songay, self.taikham, self.ngaykedon, self.loidan
        ]
        for field in fields_to_enable:
            try:
                field.setReadOnly(False)
            except:
                field.setEnabled(True)
                
        # Enable comboboxes
        combos_to_enable = [
            self.bacsi, self.quaythuoc, self.loaithuoc, self.donmau
        ]
        for combo in combos_to_enable:
            combo.setEnabled(True)

        # When enabling editing, also make existing entered cells editable again
        try:
            for r in range(self.table_thuoc.rowCount()):
                for c in (0, 1, 8):
                    item = self.table_thuoc.item(r, c)
                    if item and item.data(Qt.UserRole) != 'placeholder':
                        try:
                            item.setFlags(item.flags() | Qt.ItemIsEditable)
                        except Exception:
                            pass
        except Exception:
            pass

    def on_luu(self):
        ok, msg = self.save_prescription()
        if ok:
            QMessageBox.information(self, "Thành công", msg)
            self.disable_form_editing()  # Disable editing after successful save
            # Clear table selection to remove blue highlight
            try:
                self.table_thuoc.clearSelection()
                self.table_thuoc_khac.clearSelection()
            except Exception:
                pass
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def on_in_don(self):
        try:
            html = self.build_print_html()

            # prefer QTextDocument for consistent rendering
            try:
                from PyQt5.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(html)
            except Exception:
                doc = None

            # Show a choice: Preview, Print, Save PDF, Cancel
            mb = QMessageBox(self)
            mb.setWindowTitle("In đơn")
            mb.setText("Bạn muốn Xem trước, In trực tiếp hay Lưu ra file PDF?")
            btn_preview = mb.addButton("Xem trước", QMessageBox.ActionRole)
            btn_print = mb.addButton("In trực tiếp", QMessageBox.AcceptRole)
            btn_pdf = mb.addButton("Lưu ra PDF", QMessageBox.DestructiveRole)
            btn_cancel = mb.addButton("Hủy", QMessageBox.RejectRole)
            mb.exec_()
            clicked = mb.clickedButton()

            # Cancel
            if clicked == btn_cancel:
                return

            # Preview
            if clicked == btn_preview:
                printer = QPrinter(QPrinter.HighResolution)
                preview = QPrintPreviewDialog(printer, self)
                def _render_preview(p):
                    try:
                        if doc:
                            doc.print_(p)
                        else:
                            from PyQt5.QtGui import QTextDocument as _TD
                            _d = _TD()
                            _d.setHtml(html)
                            _d.print_(p)
                    except Exception:
                        pass
                preview.paintRequested.connect(_render_preview)
                preview.exec_()
                return

            # Save to PDF
            if clicked == btn_pdf:
                fn, _ = QFileDialog.getSaveFileName(self, "Lưu PDF", "don_thuoc.pdf", "PDF Files (*.pdf)")
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
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể lưu PDF: {e}")
                return

            # Print directly
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
                    except Exception as e:
                        QMessageBox.critical(self, "Lỗi", f"Lỗi khi in: {e}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi in đơn: {e}")

    def build_print_html(self):
        """Build an HTML representation of the prescription suitable for printing.

        This collects patient info and table rows (main medicines and 'thuốc khác')
        and returns a simple, printable HTML string.
        """
        try:
            clinic_name = "Phòng khám ABC"
            title = "ĐƠN THUỐC"
            patient = self.hoten.currentText() or ""
            dob = self.ngaysinh.date().toString("yyyy-MM-dd") if self.ngaysinh else ""
            sohoso = self.sohoso.text() if hasattr(self, 'sohoso') else ""
            sophieu = self.sophieukham.text() if hasattr(self, 'sophieukham') else ""
            bacsi = self.bacsi.currentText() if hasattr(self, 'bacsi') else ""
            ngay = self.ngaykedon.date().toString("yyyy-MM-dd") if hasattr(self, 'ngaykedon') else ""
            chan_doan = self.chandoan.text() if hasattr(self, 'chandoan') else ""
            loi_dan = self.loidan.toPlainText() if hasattr(self, 'loidan') else ""

            html = []
            html.append(f"<h2 style='text-align:center'>{clinic_name}</h2>")
            html.append(f"<h3 style='text-align:center'>{title}</h3>")
            html.append("<hr />")
            # Patient block
            html.append("<table width='100%'>")
            html.append(f"<tr><td><b>Bệnh nhân:</b> {patient}</td><td><b>Ngày sinh:</b> {dob}</td></tr>")
            html.append(f"<tr><td><b>Số hồ sơ:</b> {sohoso}</td><td><b>Số phiếu:</b> {sophieu}</td></tr>")
            html.append(f"<tr><td><b>Bác sĩ:</b> {bacsi}</td><td><b>Ngày kê:</b> {ngay}</td></tr>")
            html.append(f"<tr><td colspan='2'><b>Chẩn đoán:</b> {chan_doan}</td></tr>")
            html.append("</table>")

            # Main medicines
            html.append("<h4>Thuốc kê</h4>")
            # Table without Ghi chú column; long notes are printed on a full-width row below each item
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
                # main row
                html.append(f"<tr><td>{text}</td><td>{ten}</td><td>{qty}</td><td>{unit}</td><td>{ld}</td></tr>")
                # if note exists, add a full-width row below the item for the note (allows wrapping)
                if note and note.strip():
                    safe_note = note.replace('\n', '<br/>')
                    html.append(f"<tr><td colspan='5' style='background:#fafafa'><b>Ghi chú:</b> {safe_note}</td></tr>")
            html.append("</table>")

            # Thuốc khác
            # Collect non-empty 'thuốc khác' rows first; only render section when there's data
            other_rows = []
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

            # Notes / instructions
            html.append("<h4>Lời dặn</h4>")
            html.append(f"<div>{loi_dan.replace('\n', '<br/>')}</div>")

            # Footer
            html.append("<br/><div style='text-align:right'>Ngày kê: " + ngay + "</div>")

            return '\n'.join(html)
        except Exception as e:
            return f"<p>Lỗi khi tạo nội dung in: {e}</p>"

    def on_sua(self):
        try:
            if not hasattr(self, 'last_don_thuoc_id') or not self.last_don_thuoc_id:
                QMessageBox.warning(self, "Cảnh báo", "Không có đơn thuốc nào để sửa.")
                return
                
            self.enable_form_editing()
            QMessageBox.information(self, "Sửa", "Đã bật chế độ sửa. Hãy chỉnh sửa các trường rồi chọn Lưu.")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể bật chế độ sửa: {e}")

    def on_xoa(self):
        # If a row in the main table is selected, delete that detail row only
        try:
            sel = self.table_thuoc.selectedIndexes()
            if sel:
                row = sel[0].row()
                item = self.table_thuoc.item(row, 0)
                # If this row corresponds to a saved detail (has UserRole id) and the prescription is saved, delete it from DB
                detail_id = None
                try:
                    if item:
                        detail_id = item.data(Qt.UserRole)
                except Exception:
                    detail_id = None

                if detail_id and hasattr(self, 'last_don_thuoc_id') and self.last_don_thuoc_id:
                    reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc chắn muốn xóa hàng thuốc này?", QMessageBox.Yes | QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return
                    conn = None
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM chi_tiet_don_thuoc WHERE id = ?", (int(detail_id),))
                        conn.commit()
                        # remove row from UI
                        self.table_thuoc.removeRow(row)
                        # ensure at least one empty row exists
                        if self.table_thuoc.rowCount() == 0:
                            self._append_empty_row_main()
                        QMessageBox.information(self, "Thành công", "Đã xóa hàng thuốc.")
                        return
                    except Exception as e:
                        if conn:
                            try:
                                conn.rollback()
                            except Exception:
                                pass
                        QMessageBox.critical(self, "Lỗi", f"Không thể xóa hàng thuốc: {e}")
                    finally:
                        if conn:
                            conn.close()
                else:
                    # Unsaved row -> just remove from UI
                    self.table_thuoc.removeRow(row)
                    if self.table_thuoc.rowCount() == 0:
                        self._append_empty_row_main()
                    return

            # If a row in thuốc khác is selected, delete that detail only
            sel_k = self.table_thuoc_khac.selectedIndexes()
            if sel_k:
                row = sel_k[0].row()
                item0 = self.table_thuoc_khac.item(row, 0)
                detail_id = None
                try:
                    if item0:
                        detail_id = item0.data(Qt.UserRole)
                except Exception:
                    detail_id = None

                if detail_id and hasattr(self, 'last_don_thuoc_id') and self.last_don_thuoc_id:
                    reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc chắn muốn xóa hàng thuốc này?", QMessageBox.Yes | QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return
                    conn = None
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM chi_tiet_don_thuoc WHERE id = ?", (int(detail_id),))
                        conn.commit()
                        self.table_thuoc_khac.removeRow(row)
                        if self.table_thuoc_khac.rowCount() == 0:
                            self._append_empty_row_khac()
                        QMessageBox.information(self, "Thành công", "Đã xóa hàng thuốc.")
                        return
                    except Exception as e:
                        if conn:
                            try:
                                conn.rollback()
                            except Exception:
                                pass
                        QMessageBox.critical(self, "Lỗi", f"Không thể xóa hàng thuốc: {e}")
                    finally:
                        if conn:
                            conn.close()
                else:
                    # Unsaved row -> just remove
                    self.table_thuoc_khac.removeRow(row)
                    if self.table_thuoc_khac.rowCount() == 0:
                        self._append_empty_row_khac()
                    return

        except Exception:
            # Fall back to deleting the whole prescription if nothing selected or an error occurred
            pass

        # No specific row selected -> delete the entire prescription as before
        if not hasattr(self, 'last_don_thuoc_id') or not self.last_don_thuoc_id:
            QMessageBox.warning(self, "Cảnh báo", "Không có đơn nào để xóa.")
            return
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc chắn muốn xóa đơn này?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (self.last_don_thuoc_id,))
            cur.execute("DELETE FROM don_thuoc WHERE id = ?", (self.last_don_thuoc_id,))
            conn.commit()
            QMessageBox.information(self, "Thành công", "Đã xoá đơn thuốc.")
            self.on_nhapmoi()
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa đơn: {e}")
        finally:
            if conn:
                conn.close()

    def on_xuat_thuoc(self):
        """Gửi tới cổng dược: chỉ gửi đơn thuốc, không trừ tồn kho"""
        if not hasattr(self, 'last_don_thuoc_id') or not self.last_don_thuoc_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng lưu đơn thuốc trước khi gửi tới cổng dược!")
            return
        
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # Check if medicine details exist
            cur.execute("""
                SELECT COUNT(*) FROM chi_tiet_don_thuoc
                WHERE don_thuoc_id = ? AND ma_thuoc IS NOT NULL
            """, (self.last_don_thuoc_id,))
            medicine_count = cur.fetchone()[0]
            
            if medicine_count == 0:
                QMessageBox.warning(self, "Cảnh báo", "Không có thuốc để gửi!")
                conn.close()
                return
            
            # Mark the don_thuoc as sent to pharmacy (add column if needed)
            try:
                cur.execute("PRAGMA table_info(don_thuoc)")
                cols = [c[1] for c in cur.fetchall()]
                if 'da_gui_cong_duoc' not in cols:
                    cur.execute("ALTER TABLE don_thuoc ADD COLUMN da_gui_cong_duoc INTEGER DEFAULT 0")
                    conn.commit()
                
                cur.execute("UPDATE don_thuoc SET da_gui_cong_duoc = 1 WHERE id = ?", (self.last_don_thuoc_id,))
                conn.commit()
                
                QMessageBox.information(self, "Thành công", "Đã gửi đơn thuốc tới cổng dược!")
                
                # Phát tín hiệu để cập nhật form quản lý
                self.medicine_exported.emit()
                try:
                    app_signals.medicine_exported.emit()
                except Exception:
                    pass
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Lỗi", f"Không thể gửi đơn: {e}")
            finally:
                conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi: {e}")
            # Mark the don_thuoc record as exported (add column if needed)
            try:
                if hasattr(self, 'last_don_thuoc_id') and self.last_don_thuoc_id:
                    conn2 = get_connection()
                    cur2 = conn2.cursor()
                    cur2.execute("PRAGMA table_info('don_thuoc')")
                    cols = [r[1] for r in cur2.fetchall()]
                    if 'xuat_thuoc' not in cols:
                        try:
                            cur2.execute("ALTER TABLE don_thuoc ADD COLUMN xuat_thuoc INTEGER DEFAULT 0")
                            conn2.commit()
                        except Exception:
                            pass
                    try:
                        cur2.execute("UPDATE don_thuoc SET xuat_thuoc = 1 WHERE id = ?", (self.last_don_thuoc_id,))
                        conn2.commit()
                    except Exception:
                        pass
                    finally:
                        conn2.close()
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi xuất thuốc: {e}")

    def on_thoat(self):
        try:
            self.close()
        except Exception:
            pass

    def _find_patient_index_by_id(self, patient_id):
        """Return combobox index for a given patient id, or -1 if not found."""
        try:
            for i in range(self.hoten.count()):
                data = self.hoten.itemData(i)
                if isinstance(data, dict) and data.get('id') == patient_id:
                    return i
        except Exception:
            pass
        return -1
        
    def auto_select_patient(self, patient_id):
        """Automatically select a patient in the combobox by their ID."""
        try:
            idx = self._find_patient_index_by_id(patient_id)
            if idx >= 0:
                self.hoten.setCurrentIndex(idx)
        except Exception:
            pass

    def load_prescription(self, don_thuoc_id, disable_after_load=True):
        """Load a saved prescription (don_thuoc) into the form and show which patient it belongs to.

        Steps:
        - read `don_thuoc` row by id
        - if it references `phieu_kham`, follow to `benh_nhan` to get patient id
        - select the patient in combobox and populate patient fields
        - load chi_tiet_don_thuoc rows into the tables
        - set self.last_don_thuoc_id
        - disable form editing
        """
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT phieu_kham_id, ngay_ke, so_ngay, ngay_tai_kham, tong_tien,
                       loai_don, chan_doan, di_ung_thuoc, loi_dan, bac_si, quay_thuoc, nguoi_lap_phieu
                FROM don_thuoc
                WHERE id = ?
            """, (don_thuoc_id,))
            row = cur.fetchone()
            if not row:
                raise Exception(f"Không tìm thấy đơn thuốc id={don_thuoc_id}")

            phieu_kham_id = row[0]
            # populate top-level fields
            try:
                if row[1]:
                    try:
                        self.ngaykedon.setDate(QDate.fromString(row[1], "yyyy-MM-dd"))
                    except Exception:
                        pass
                self.songay.setValue(int(row[2]) if row[2] is not None else 1)
                if row[3]:
                    try:
                        self.taikham.setDate(QDate.fromString(row[3], "yyyy-MM-dd"))
                    except Exception:
                        pass
                self.tongtien.setText(str(row[4] or 0))
                try:
                    self.loaithuoc.setCurrentText(row[5] or self.loaithuoc.currentText())
                except Exception:
                    pass
                self.chandoan.setText(row[6] or "")
                self.diungthuoc.setText(row[7] or "")
                self.loidan.setPlainText(row[8] or "")
                try:
                    self.bacsi.setCurrentText(row[9] or self.bacsi.currentText())
                except Exception:
                    pass
                try:
                    self.quaythuoc.setCurrentText(row[10] or self.quaythuoc.currentText())
                except Exception:
                    pass
                self.nguoilapphieu.setText(row[11] or "")
            except Exception:
                pass

            patient_id = None
            if phieu_kham_id:
                cur.execute("SELECT benh_nhan_id FROM phieu_kham WHERE id = ?", (phieu_kham_id,))
                t = cur.fetchone()
                if t:
                    patient_id = t[0]

            # Prefer diagnosis from detailed exam info if available
            try:
                if phieu_kham_id:
                    cur.execute("SELECT chan_doan FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_kham_id,))
                    _diag = cur.fetchone()
                    if _diag and _diag[0]:
                        try:
                            self.chandoan.setText(_diag[0])
                        except Exception:
                            pass
            except Exception:
                pass

            # If we have patient_id, select in combobox and populate patient fields
            if patient_id:
                idx = self._find_patient_index_by_id(patient_id)
                if idx >= 0:
                    # block currentIndexChanged while populating
                    try:
                        self.hoten.blockSignals(True)
                        self.hoten.setCurrentIndex(idx)
                    finally:
                        self.hoten.blockSignals(False)

            # Load detail rows
            # include the detail id so we can identify rows for deletion later
            cur.execute("SELECT id, ma_thuoc, ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (don_thuoc_id,))
            details = cur.fetchall()

            # populate main table and 'thuốc khác' table separately
            self._suppress_item_changed = True
            try:
                if details:
                    # Separate rows that have ma_thuoc (main medicines) from those without (thuốc khác)
                    main_rows = []
                    other_rows = []
                    for d in details:
                        detail_id, ma, ten, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu = d
                        if ma is None or str(ma).strip() == "":
                            other_rows.append(d)
                        else:
                            main_rows.append(d)

                    # Populate main medicines table
                    main_count = len(main_rows)
                    # Ensure at least 0 rows; we'll later ensure 5 visible rows using helper
                    self.table_thuoc.setRowCount(main_count)
                    for r, d in enumerate(main_rows):
                        detail_id, ma, ten, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu = d
                        ma_item = QTableWidgetItem(str(ma))
                        ma_item.setForeground(Qt.black)
                        try:
                            ma_item.setData(Qt.UserRole, int(detail_id))
                        except Exception:
                            pass
                        self.table_thuoc.setItem(r, 0, ma_item)

                        if ten:
                            ten_item = QTableWidgetItem(str(ten))
                            ten_item.setForeground(Qt.black)
                        else:
                            ten_item = QTableWidgetItem("Nhấn để chọn")
                            ten_item.setForeground(Qt.gray)
                        self.table_thuoc.setItem(r, 1, ten_item)

                        qty_item = QTableWidgetItem(str(so_luong) if so_luong else "")
                        self.table_thuoc.setItem(r, 2, qty_item)

                        unit_combo = self._make_unit_combo(initial_value=don_vi if don_vi else None)
                        self.table_thuoc.setCellWidget(r, 3, unit_combo)

                        for ci, val in enumerate((sang, trua, chieu, toi), start=4):
                            self.table_thuoc.setItem(r, ci, QTableWidgetItem(str(val or "")))

                        if lieu_dung:
                            ld_item = QTableWidgetItem(str(lieu_dung))
                            ld_item.setForeground(Qt.black)
                        else:
                            ld_item = QTableWidgetItem("Nhấn để chọn")
                            ld_item.setForeground(Qt.gray)
                        self.table_thuoc.setItem(r, 8, ld_item)

                        if ghi_chu and ghi_chu != "Nhấn để chọn":
                            note_item = QTableWidgetItem(str(ghi_chu))
                            note_item.setForeground(Qt.black)
                        else:
                            note_item = QTableWidgetItem("Nhấn để chọn")
                            note_item.setForeground(Qt.gray)
                        self.table_thuoc.setItem(r, 9, note_item)

                    # Ensure the main table shows the expected placeholder rows (min 5 visible)
                    self._append_empty_row_main(force_count=5)

                    # Populate 'thuốc khác' table from other_rows
                    other_count = len(other_rows)
                    if other_count:
                        self.table_thuoc_khac.setRowCount(other_count)
                        for rr, od in enumerate(other_rows):
                            detail_id, ma, ten, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu = od
                            name_item = QTableWidgetItem(str(ten or ""))
                            qty_item = QTableWidgetItem(str(so_luong) if so_luong else "")
                            unit_combo = self._make_unit_combo(initial_value=don_vi if don_vi else None)
                            dose_item = QTableWidgetItem(str(lieu_dung) if lieu_dung else "Nhấn để chọn")
                            if lieu_dung:
                                dose_item.setForeground(Qt.black)
                            else:
                                dose_item.setForeground(Qt.gray)
                            # attach detail id for potential deletion
                            try:
                                name_item.setData(Qt.UserRole, int(detail_id))
                            except Exception:
                                pass
                            self.table_thuoc_khac.setItem(rr, 0, name_item)
                            self.table_thuoc_khac.setItem(rr, 1, qty_item)
                            self.table_thuoc_khac.setCellWidget(rr, 2, unit_combo)
                            self.table_thuoc_khac.setItem(rr, 3, dose_item)
                        # After populating existing 'thuốc khác' rows, append one empty placeholder
                        # so the user always has an empty row to start typing into and the
                        # itemChanged handler will add more rows as needed.
                        try:
                            self._append_empty_row_khac()
                        except Exception:
                            pass
                    else:
                        # No other rows -> ensure default placeholders
                        self.table_thuoc_khac.setRowCount(3)
                        for r in range(self.table_thuoc_khac.rowCount()):
                            name = QTableWidgetItem("")
                            qty = QTableWidgetItem("")
                            unit_combo = self._make_unit_combo()
                            dose = QTableWidgetItem("Nhấn để chọn")
                            dose.setForeground(Qt.gray)
                            self.table_thuoc_khac.setItem(r, 0, name)
                            self.table_thuoc_khac.setItem(r, 1, qty)
                            self.table_thuoc_khac.setCellWidget(r, 2, unit_combo)
                            self.table_thuoc_khac.setItem(r, 3, dose)
                else:
                    # No details -> reset tables to show placeholders
                    self.reset_tables()
            finally:
                self._suppress_item_changed = False

            # set last saved id
            self.last_don_thuoc_id = don_thuoc_id
            # Optionally disable form editing after loading prescription.
            # Caller can request to keep the form editable (e.g., when a patient
            # is selected and we want the user to be able to edit immediately).
            if disable_after_load:
                self.disable_form_editing()
            # Clear table selection to remove blue highlight after loading
            try:
                self.table_thuoc.clearSelection()
                self.table_thuoc_khac.clearSelection()
            except Exception:
                pass

        except Exception as e:
            QMessageBox.warning(self, "Lỗi tải đơn", f"Không thể tải đơn thuốc: {e}")
        finally:
            if conn:
                conn.close()
        
    def on_record_selected(self, index):
        """Handle when user selects a different medical record number"""
        if index < 0:
            return
            
        record_no = self.sohoso.currentText()
        if not record_no:
            return
            
        # Get patient ID from current patient selection
        patient_data = self.hoten.currentData()
        if not patient_data:
            return
            
        patient_id = patient_data.get('id')
        if not patient_id:
            return
            
        # Load the specific medical record data
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pk.so_phieu, COALESCE(ct.chan_doan, '') AS chan_doan, ct.di_ung_thuoc
            FROM tiep_don td
            LEFT JOIN phieu_kham pk ON pk.benh_nhan_id = td.benh_nhan_id
            LEFT JOIN chi_tiet_phieu_kham ct ON pk.id = ct.phieu_kham_id
            WHERE td.benh_nhan_id = ? AND td.ma_hoso = ?
            ORDER BY pk.id DESC LIMIT 1
        """, (patient_id, record_no))
        
        record = cursor.fetchone()
        if record:
            so_phieu, chan_doan, di_ung = record
            self.sophieukham.setText(so_phieu or "")
            self.chandoan.setText(chan_doan or "")
            self.diungthuoc.setText(di_ung or "")

    def load_patients(self):
        """Load all patients into the comboboxes"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get patients with their record numbers and additional info
        cursor.execute("""
            SELECT DISTINCT 
                b.id,
                b.ho_ten,
                b.ngay_sinh,
                b.gioi_tinh,
                b.tuoi,
                b.dien_thoai,
                b.dia_chi,
                b.doi_tuong,
                t.ma_hoso
            FROM benh_nhan b 
            LEFT JOIN tiep_don t ON b.id = t.benh_nhan_id 
            ORDER BY b.ho_ten
        """)
        patients = cursor.fetchall()
        conn.close()

        self.hoten.clear()
        self.hoten.addItem("--- Chọn bệnh nhân ---")  # Empty option
        
        # Group patients by name for cases with duplicate names
        patient_dict = {}
        for id, name, ngaysinh, gioitinh, tuoi, dienthoai, diachi, doituong, record in patients:
            if name in patient_dict:
                patient_dict[name].append((id, ngaysinh, gioitinh, tuoi, dienthoai, diachi, doituong, record))
            else:
                patient_dict[name] = [(id, ngaysinh, gioitinh, tuoi, dienthoai, diachi, doituong, record)]

        # Add patients to combobox, marking duplicates with record number
        for name, patient_records in patient_dict.items():
            if len(patient_records) == 1:
                # Single patient with this name
                patient_data = patient_records[0]
                display_name = f"{name} - {patient_data[7]}" if patient_data[7] else name
                self.hoten.addItem(display_name, userData={
                    'id': patient_data[0],
                    'ngaysinh': patient_data[1],
                    'gioitinh': patient_data[2],
                    'tuoi': patient_data[3],
                    'dienthoai': patient_data[4],
                    'diachi': patient_data[5],
                    'doituong': patient_data[6],
                    'record': patient_data[7]
                })
            else:
                # Multiple patients with same name
                for patient_data in patient_records:
                    display_name = f"{name} - {patient_data[7]}" if patient_data[7] else f"{name} (Chưa có số hồ sơ)"
                    self.hoten.addItem(display_name, userData={
                        'id': patient_data[0],
                        'ngaysinh': patient_data[1],
                        'gioitinh': patient_data[2],
                        'tuoi': patient_data[3],
                        'dienthoai': patient_data[4],
                        'diachi': patient_data[5],
                        'doituong': patient_data[6],
                        'record': patient_data[7]
                    })

    def on_patient_selected(self, index):
        """Handle patient selection"""
        # Clear form first
        self.clear_form()
        
        if index <= 0:  # Skip the "--- Chọn bệnh nhân ---" item
            return
            
        # Get the selected patient data
        data = self.hoten.itemData(index)
        if not data or not isinstance(data, dict):
            return
            
        patient_id = data.get('id')
        if not patient_id:
            return
            
        # Load patient data
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get patient info
            cursor.execute("""
                SELECT b.gioi_tinh, b.ngay_sinh, b.tuoi, b.dia_chi, b.dien_thoai
                FROM benh_nhan b
                WHERE b.id = ?
            """, (patient_id,))
            patient = cursor.fetchone()
            
            if patient:
                gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai = patient
                
                # Update UI fields
                self.gioitinh.setText(gioi_tinh)
                if ngay_sinh:
                    try:
                        self.ngaysinh.setDate(QDate.fromString(ngay_sinh, "yyyy-MM-dd"))
                    except:
                        self.ngaysinh.setDate(QDate.currentDate())
                self.tuoi.setText(str(tuoi) if tuoi else "")
                self.diachi.setText(dia_chi or "")
                self.dienthoai.setText(dien_thoai or "")
                
                # Load số hồ sơ and other info for this patient
                cursor.execute("""
                    SELECT DISTINCT 
                        td.ma_hoso,
                        b.doi_tuong,
                        pk.so_phieu,
                        COALESCE(ct.chan_doan, '') AS chan_doan,
                        ct.di_ung_thuoc,
                        pk.id as phieu_kham_id
                    FROM tiep_don td
                    LEFT JOIN benh_nhan b ON td.benh_nhan_id = b.id
                    LEFT JOIN phieu_kham pk ON pk.benh_nhan_id = td.benh_nhan_id
                    LEFT JOIN chi_tiet_phieu_kham ct ON pk.id = ct.phieu_kham_id
                    WHERE td.benh_nhan_id = ? 
                    AND td.ma_hoso IS NOT NULL
                    ORDER BY pk.id DESC
                """, (patient_id,))
                records = cursor.fetchall()
                
                # Update số hồ sơ combobox and set current record
                self.sohoso.clear()
                if records:
                    # Lấy mã hồ sơ mới nhất
                    first_record = records[0]
                    ma_hoso, doi_tuong, so_phieu, chan_doan, di_ung_thuoc, phieu_kham_id = first_record
                    self.sohoso.setText(ma_hoso or "")
                    # Save phieu_kham_id for later use if needed
                    self.phieu_kham_id = phieu_kham_id
                    # Update other fields từ record mới nhất
                    self.doituong.setText(doi_tuong or "")
                    self.sophieukham.setText(so_phieu or "")
                    # Prefer diagnosis from the detailed exam info (chi_tiet_phieu_kham)
                    try:
                        if phieu_kham_id:
                            cursor.execute("SELECT chan_doan FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_kham_id,))
                            drow = cursor.fetchone()
                            if drow and drow[0]:
                                self.chandoan.setText(drow[0])
                            else:
                                self.chandoan.setText(chan_doan or "")
                    except Exception:
                        self.chandoan.setText(chan_doan or "")
                    self.diungthuoc.setText(di_ung_thuoc or "")

                # Load tất cả đơn thuốc của bệnh nhân
                cursor.execute("""
                    SELECT dt.id, dt.ngay_ke, dt.chan_doan 
                    FROM don_thuoc dt
                    JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                    WHERE pk.benh_nhan_id = ?
                    ORDER BY dt.ngay_ke DESC, dt.id DESC
                """, (patient_id,))
                prescriptions = cursor.fetchall()
                
                # Cập nhật combobox đơn cũ
                self.doncu.clear()
                self.doncu.addItem("---Chọn đơn cũ---", None)
                self.doncu.addItem("---Tạo đơn mới---", "new")
                for p in prescriptions:
                    display_text = f"{p[1]} - {p[2][:50] + '...' if p[2] and len(p[2]) > 50 else p[2] or 'Không có chẩn đoán'}"
                    self.doncu.addItem(display_text, p[0])
                
                if prescriptions:
                    # Load đơn thuốc gần nhất
                    # When selecting a patient and auto-loading their most recent
                    # prescription, keep the form editable so user can immediately
                    # modify/enter a new prescription. Only lock when they press Lưu.
                    self.load_prescription(prescriptions[0][0], disable_after_load=False)
                else:
                    # Reset tables nếu không có đơn thuốc
                    self.reset_tables()
                    
        finally:
            conn.close()

    def save_prescription(self):
        """Save the prescription and its details to database"""
        # Validate required fields
        if not self.hoten.currentText().strip():
            return False, "Vui lòng chọn bệnh nhân"
            
        # Get patient ID
        patient_id = self.hoten.currentData()

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Insert don_thuoc record
            cursor.execute("""
                INSERT INTO don_thuoc (
                    phieu_kham_id,
                    ngay_ke,
                    so_ngay,
                    ngay_tai_kham,
                    tong_tien,
                    loai_don,
                    chan_doan,
                    di_ung_thuoc,
                    loi_dan,
                    bac_si,
                    quay_thuoc,
                    nguoi_lap_phieu
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.phieu_kham_id,
                self.ngaykedon.date().toString("yyyy-MM-dd"),
                self.songay.value(),
                self.taikham.date().toString("yyyy-MM-dd"),
                float(self.tongtien.text() or 0),
                self.loaithuoc.currentText(),
                self.chandoan.text(),
                self.diungthuoc.text(),
                self.loidan.toPlainText(),
                self.bacsi.currentText(),
                self.quaythuoc.currentText(),
                self.nguoilapphieu.text()
            ))

            don_thuoc_id = cursor.lastrowid

            # Save main medicines
            for row in range(self.table_thuoc.rowCount()):
                ma_thuoc_item = self.table_thuoc.item(row, 0)
                if not ma_thuoc_item or not ma_thuoc_item.text() or ma_thuoc_item.text() == "Nhấn để chọn":
                    continue

                ten_thuoc_item = self.table_thuoc.item(row, 1)
                ten_thuoc = ten_thuoc_item.text() if ten_thuoc_item else ""
                so_luong_item = self.table_thuoc.item(row, 2)
                so_luong = int(so_luong_item.text()) if so_luong_item and so_luong_item.text() else 0
                don_vi_widget = self.table_thuoc.cellWidget(row, 3)
                don_vi = don_vi_widget.currentText() if don_vi_widget else ""

                sang_item = self.table_thuoc.item(row, 4)
                sang = sang_item.text() if sang_item else ""
                trua_item = self.table_thuoc.item(row, 5)
                trua = trua_item.text() if trua_item else ""
                chieu_item = self.table_thuoc.item(row, 6)
                chieu = chieu_item.text() if chieu_item else ""
                toi_item = self.table_thuoc.item(row, 7)
                toi = toi_item.text() if toi_item else ""

                lieu_dung_item = self.table_thuoc.item(row, 8)
                lieu_dung = lieu_dung_item.text() if lieu_dung_item and lieu_dung_item.text() != "Nhấn để chọn" else ""

                ghi_chu_item = self.table_thuoc.item(row, 9)
                ghi_chu = ghi_chu_item.text() if ghi_chu_item and ghi_chu_item.text() != "Nhấn để chọn" else ""

                cursor.execute("""
                    INSERT INTO chi_tiet_don_thuoc (
                        don_thuoc_id,
                        ma_thuoc,
                        ten_thuoc,
                        so_luong,
                        don_vi,
                        sang,
                        trua,
                        chieu,
                        toi,
                        lieu_dung,
                        ghi_chu
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    don_thuoc_id,
                    ma_thuoc_item.text(),
                    ten_thuoc,
                    so_luong,
                    don_vi,
                    sang,
                    trua,
                    chieu,
                    toi,
                    lieu_dung,
                    ghi_chu
                ))
                # record the inserted detail id on the row item for later per-row deletion
                try:
                    detail_id = cursor.lastrowid
                    if ma_thuoc_item:
                        try:
                            ma_thuoc_item.setData(Qt.UserRole, int(detail_id))
                        except Exception:
                            pass
                except Exception:
                    pass

            # Save additional medicines
            for row in range(self.table_thuoc_khac.rowCount()):
                ten_thuoc_item = self.table_thuoc_khac.item(row, 0)
                if not ten_thuoc_item or not ten_thuoc_item.text():
                    continue

                so_luong_item = self.table_thuoc_khac.item(row, 1)
                so_luong = int(so_luong_item.text()) if so_luong_item and so_luong_item.text() else 0
                don_vi_widget = self.table_thuoc_khac.cellWidget(row, 2)
                don_vi = don_vi_widget.currentText() if don_vi_widget else ""
                lieu_dung_item = self.table_thuoc_khac.item(row, 3)
                lieu_dung = lieu_dung_item.text() if lieu_dung_item and lieu_dung_item.text() != "Nhấn để chọn" else ""
                # Persist this 'thuốc khác' into thuoc_khac table for future autocomplete/suggestions
                try:
                    name_val = ten_thuoc_item.text().strip()
                    if name_val:
                        cursor.execute("SELECT id FROM thuoc_khac WHERE ten_thuoc = ? LIMIT 1", (name_val,))
                        found = cursor.fetchone()
                        if not found:
                            try:
                                cursor.execute("INSERT INTO thuoc_khac (ten_thuoc, don_vi, ghi_chu, don_thuoc_id) VALUES (?, ?, ?, ?)", (
                                    name_val,
                                    don_vi or None,
                                    lieu_dung or None,
                                    don_thuoc_id
                                ))
                            except Exception:
                                # ignore insertion errors for now
                                pass
                except Exception:
                    pass

                cursor.execute("""
                    INSERT INTO chi_tiet_don_thuoc (
                        don_thuoc_id,
                        ma_thuoc,
                        ten_thuoc,
                        so_luong,
                        don_vi,
                        lieu_dung
                    ) VALUES (?, NULL, ?, ?, ?, ?)
                """, (
                    don_thuoc_id,
                    ten_thuoc_item.text(),
                    so_luong,
                    don_vi,
                    lieu_dung
                ))
                # attach the newly inserted detail id to the thuốc_khac table row for later deletion
                try:
                    detail_id = cursor.lastrowid
                    try:
                        item0 = self.table_thuoc_khac.item(row, 0)
                        if item0:
                            item0.setData(Qt.UserRole, int(detail_id))
                    except Exception:
                        pass
                except Exception:
                    pass

            # Commit once everything saved
            conn.commit()
            # keep reference to the last saved id
            try:
                self.last_don_thuoc_id = don_thuoc_id
            except Exception:
                pass

            # Ensure don_thuoc has a 'da_luu' column and mark this record as saved
            try:
                cursor.execute("PRAGMA table_info('don_thuoc')")
                cols = [r[1] for r in cursor.fetchall()]
                if 'da_luu' not in cols:
                    try:
                        cursor.execute("ALTER TABLE don_thuoc ADD COLUMN da_luu INTEGER DEFAULT 0")
                    except Exception:
                        pass
                try:
                    cursor.execute("UPDATE don_thuoc SET da_luu = 1 WHERE id = ?", (don_thuoc_id,))
                    conn.commit()
                except Exception:
                    pass
            except Exception:
                pass

            return True, "Lưu đơn thuốc thành công"

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return False, f"Lỗi khi lưu đơn thuốc: {str(e)}"
        finally:
            if conn:
                conn.close()

# ======== MAIN ========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = KeDonThuoc()
    win.show()
    sys.exit(app.exec_())
