from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QDateEdit, QDateTimeEdit, QMessageBox, QGroupBox, QGridLayout, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog,
    QListWidget, QListWidgetItem, QSizePolicy
)
from PyQt5.QtCore import QDate, Qt, QStringListModel
from PyQt5.QtGui import QFont
import sys
from database import get_connection
from functools import partial
import logging

# Module logger
logger = logging.getLogger(__name__)


class TaoPhieuKham(QWidget):
    """Form Lập phiếu khám (trang, không phải dialog)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Arial", 10))
        self.parent = parent
        # Khởi tạo các action chính
        self.create_actions()
        # Global stylesheet
        style = """
                QGroupBox {
                    border: 1px solid #0078D7;
                    border-radius: 3px;
                    margin-top: 10px;
                    font-weight: bold;
                    color: #0078D7;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                    background: white;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #1084E3;
                }
                QTabWidget::pane {
                    border: 1px solid #0078D7;
                }
                QTabBar::tab {
                    background: white;
                    border: 1px solid #0078D7;
                    padding: 5px 10px;
                    color: #0078D7;
                }
                QTabBar::tab:selected {
                    background: #0078D7;
                    color: white;
                }
                /* Inputs: neutral by default, green outline on focus */
                QLineEdit, QComboBox, QTextEdit, QDateTimeEdit {
                    border: 1px solid #cfcfcf;
                    background: white;
                    border-radius: 4px;
                    padding: 4px;
                }
                QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateTimeEdit:focus {
                    border: 2px solid #0078D7; /* blue focus */
                    outline: none;
                }
                QLineEdit:read-only {
                    background: #F0F0F0;
                }
                QTableWidget {
                    border: 1px solid #ddd;
                    gridline-color: #ddd;
                    background-color: white;
                }
                /* Table item default + selection styling: only highlight when selected */
                QTableWidget::item {
                    border: none;
                    padding: 4px;
                    background-color: transparent;
                    color: #000000;
                }
                QTableWidget::item:selected {
                    background-color: #0078D7;
                    color: #ffffff;
                }
                QHeaderView::section {
                    background-color: #0078D7;
                    color: white;
                    padding: 4px;
                    border: none;
                }
            """
        self.setStyleSheet(style)
        self.initUI()  # Match tiep_don_kham.py naming
        self.load_benh_nhan_list()  # Match tiep_don_kham.py naming
        
        # Initialize ICD10 data
        self.all_icd10_data = []
        self.selected_icd10_codes = []
        self.load_icd10_list()  # Load ICD10 data

        self.current_phieu_kham_id = None
        self.current_so_phieu = None

    def create_actions(self):
        """Tạo các action cho toolbar"""
        # Nút Nhập mới (F1)
        self.btn_nhapmoi = QPushButton("Nhập mới (F1)")
        self.btn_nhapmoi.setShortcut("F1")
        self.btn_nhapmoi.clicked.connect(self.on_reset)

        # Nút Lưu (F2) 
        self.btn_luu = QPushButton("Lưu (F2)")
        self.btn_luu.setShortcut("F2")
        self.btn_luu.clicked.connect(self.on_save)

        # Nút Bỏ qua
        self.btn_boqua = QPushButton("Bỏ qua")
        self.btn_boqua.clicked.connect(self.on_reset)

        # Nút Sửa
        self.btn_sua = QPushButton("Sửa")
        self.btn_sua.clicked.connect(self.on_edit)

        # Nút Xóa
        self.btn_xoa = QPushButton("Xóa")
        self.btn_xoa.clicked.connect(self.on_delete)

        # Nút In phiếu
        self.btn_inphieu = QPushButton("In phiếu")
        self.btn_inphieu.clicked.connect(self.on_print)

        # Combo Phiếu khám
        self.combo_phieukham = QComboBox()
        self.combo_phieukham.addItems(["Phiếu khám bệnh", "Phiếu chỉ định", "Phiếu tạm ứng", "Phiếu thu"])
        self.combo_phieukham.currentIndexChanged.connect(self.on_phieu_changed)

        # Nút Mời vào khám
        self.btn_moivaokham = QPushButton("Mời vào khám")
        self.btn_moivaokham.clicked.connect(self.on_moi_kham)

        # Nút Kết thúc khám
        self.btn_ketthuckham = QPushButton("Kết thúc khám")
        self.btn_ketthuckham.clicked.connect(self.on_ket_thuc)

        # Nút Hủy kết thúc
        self.btn_huyketthuc = QPushButton("Hủy kết thúc")
        self.btn_huyketthuc.clicked.connect(self.on_huy_ket_thuc)

        # Nút Thoát
        self.btn_thoat = QPushButton("Thoát") 
        self.btn_thoat.clicked.connect(self.close)

        # Style cho các nút: blue theme matching tiep_don_kham.py
        button_style = """
            QPushButton {
                background-color: #0078D7;
                border: 1px solid #0078D7;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #1084E3;
                border-color: #0078D7;
            }
            QPushButton:pressed {
                background-color: #005a9e;
                color: white;
            }
        """
        for btn in [self.btn_nhapmoi, self.btn_luu, self.btn_boqua, self.btn_sua, 
                   self.btn_xoa, self.btn_inphieu, self.btn_moivaokham,
                   self.btn_ketthuckham, self.btn_huyketthuc, self.btn_thoat]:
            btn.setStyleSheet(button_style)

    def initUI(self):  # Match tiep_don_kham.py naming
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)  # Match tiep_don_kham.py layout
        main_layout.setSpacing(8)

        # Top tabs (visual only for now)
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(2)
        tab_style = """
                QPushButton { 
                    background: white; 
                    border: 1px solid #0078D7;
                    color: #0078D7;
                    padding: 6px 12px;
                    border-radius: 0px;
                }
                QPushButton:checked { 
                    background: #0078D7;
                    color: white;
                }
                QPushButton:hover {
                    background: #E5F3FF;
                }
        """
        
        # Add stretch to center the buttons
        tabs_layout.addStretch()
        
        self.tab_chidinh = QPushButton("Chỉ định dịch vụ")
        self.tab_don = QPushButton("Đơn điều trị")
        self.tab_donbosung = QPushButton("Đơn bổ sung")
        # Make all three buttons checkable and styled, and add them to the layout
        for t in (self.tab_chidinh, self.tab_don, self.tab_donbosung):
            t.setCheckable(True)
            t.setStyleSheet(tab_style)
            t.setMinimumHeight(28)
            t.setFixedWidth(150)  # Set fixed width for all buttons
            tabs_layout.addWidget(t)
        
        # Connect tab clicks to activate tab (mutually exclusive) and open forms.
        # Use a small helper to ensure only one tab is active (checked) at a time.
        def _activate_tab(btn_to_activate, btn_to_deactivate, action):
            try:
                btn_to_activate.setChecked(True)
                btn_to_deactivate.setChecked(False)
            except Exception:
                pass
            try:
                action()
            except Exception:
                pass

        self.tab_chidinh.clicked.connect(lambda: _activate_tab(self.tab_chidinh, self.tab_don, self.mo_form_chidinh))
        # Connect Đơn điều trị -> mở form đơn thuốc
        self.tab_don.clicked.connect(lambda: _activate_tab(self.tab_don, self.tab_chidinh, self.mo_form_don))

        # connect Đơn bổ sung -> mở form đơn thuốc bổ sung
        self.tab_donbosung.clicked.connect(lambda: _activate_tab(self.tab_donbosung, self.tab_chidinh, self.mo_form_donbosung))
            
        # Add stretch on the right to center the buttons
        tabs_layout.addStretch()
        # Start with both tabs inactive (white background). Clicking one will
        # set it active and reset the other.
        self.tab_chidinh.setChecked(False)
        self.tab_don.setChecked(False)
        self.tab_donbosung.setChecked(False)
        main_layout.addLayout(tabs_layout)

        # === Patient info group (top of form) ===
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        grid = QGridLayout()
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)
        # Set column stretch so input columns expand and labels stay compact
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 2)
        grid.setColumnStretch(4, 0)
        grid.setColumnStretch(5, 1)
        grid.setColumnStretch(6, 0)
        grid.setColumnStretch(7, 1)

        grid.addWidget(QLabel("Họ và tên"), 0, 0)
        self.hoten = QComboBox()  # Rename combo_bn to hoten to match tiep_don_kham.py
        self.hoten.setEditable(True)
        try:
            from PyQt5.QtWidgets import QCompleter
            self.completer = QCompleter()
            self.completer.setCaseSensitivity(False)
            self.hoten.setCompleter(self.completer)
        except Exception:
            self.completer = None
        grid.addWidget(self.hoten, 0, 1)

        grid.addWidget(QLabel("Giới tính"), 0, 2)
        self.gioitinh = QLineEdit()
        self.gioitinh.setReadOnly(True)
        grid.addWidget(self.gioitinh, 0, 3)

        grid.addWidget(QLabel("Ngày sinh"), 1, 0)
        self.ngaysinh = QLineEdit()
        self.ngaysinh.setReadOnly(True)
        grid.addWidget(self.ngaysinh, 1, 1)

        grid.addWidget(QLabel("Tuổi"), 1, 2)
        self.tuoi = QLineEdit()
        self.tuoi.setReadOnly(True)
        grid.addWidget(self.tuoi, 1, 3)

        grid.addWidget(QLabel("Ngày lập"), 1, 4)
        self.display_ngaylap_top = QLineEdit(QDate.currentDate().toString("dd/MM/yyyy"))
        self.display_ngaylap_top.setReadOnly(True)
        grid.addWidget(self.display_ngaylap_top, 1, 5)

        grid.addWidget(QLabel("Tiền khám"), 1, 6)
        self.tienkham = QLineEdit("0")
        grid.addWidget(self.tienkham, 1, 7)

        grid.addWidget(QLabel("Địa chỉ"), 2, 0)
        self.diachi = QLineEdit()
        self.diachi.setReadOnly(True)
        grid.addWidget(self.diachi, 2, 1, 1, 3)

        grid.addWidget(QLabel("Điện thoại"), 0, 4)
        self.dienthoai = QLineEdit()
        self.dienthoai.setReadOnly(True)
        grid.addWidget(self.dienthoai, 0, 5)

        grid.addWidget(QLabel("Đối tượng"), 2, 4)
        self.doituong = QLineEdit()
        self.doituong.setReadOnly(True)
        grid.addWidget(self.doituong, 2, 5)

        grid.addWidget(QLabel("Loại khám"), 3, 0)
        self.loaikham = QLineEdit()
        self.loaikham.setReadOnly(True)
        grid.addWidget(self.loaikham, 3, 1)

        grid.addWidget(QLabel("Ngày tiếp đón"), 3, 2)
        self.ngaytiepdon = QLineEdit()
        self.ngaytiepdon.setReadOnly(True)
        grid.addWidget(self.ngaytiepdon, 3, 3)

        grid.addWidget(QLabel("Phòng khám"), 3, 4)
        self.phongkham = QLineEdit()
        self.phongkham.setReadOnly(True)
        grid.addWidget(self.phongkham, 3, 5)

        grid.addWidget(QLabel("Bác sĩ khám"), 4, 0)
        self.bacsikham = QLineEdit()
        self.bacsikham.setReadOnly(True)
        grid.addWidget(self.bacsikham, 4, 1)

        grid.addWidget(QLabel("Tình trạng"), 4, 2)
        self.tinhtrang = QLineEdit()
        self.tinhtrang.setReadOnly(True)
        grid.addWidget(self.tinhtrang, 4, 3)

        grid.addWidget(QLabel("Mã hồ sơ"), 4, 4)
        self.mahoso = QLineEdit()
        self.mahoso.setReadOnly(True)
        grid.addWidget(self.mahoso, 4, 5)

        grid.addWidget(QLabel("Số phiếu"), 0, 6)
        self.sophieukham = QLineEdit()
        self.sophieukham.setReadOnly(True)
        grid.addWidget(self.sophieukham, 0, 7)

        # Ghi chú khám: đặt trong cùng group THÔNG TIN TIẾP ĐÓN, chiếm toàn bộ chiều ngang
        grid.addWidget(QLabel("Ghi chú khám"), 6, 0)
        self.ghichu = QTextEdit()
        self.ghichu.setFixedHeight(120)
        grid.addWidget(self.ghichu, 6, 1, 1, 7)

        group_bn.setLayout(grid)
        main_layout.addWidget(group_bn)

        # === Tabs: THÔNG TIN KHÁM | LỊCH SỬ KCB ===
        self.tabs = QTabWidget()

        # Tab 1: Thông tin khám
        tab_thongtin = QWidget()
        t1_layout = QVBoxLayout(tab_thongtin)
        t1_layout.setSpacing(10)  # Increase spacing between sections
        t1_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding

        # Vitals row - Adjust to 3 equal columns
        vitals_grid = QGridLayout()
        vitals_grid.setHorizontalSpacing(15)  # More space between columns
        vitals_grid.setVerticalSpacing(8)
        
        # Create consistent label style
        label_style = "QLabel { min-width: 80px; }"  # Ensure labels have minimum width

        # Column 1: Nhiệt độ
        lbl_nhietdo = QLabel("Nhiệt độ")
        lbl_nhietdo.setStyleSheet(label_style)
        vitals_grid.addWidget(lbl_nhietdo, 0, 0)
        self.nhietdo = QLineEdit()
        self.nhietdo.setPlaceholderText("Nhiệt độ °C")
        self.nhietdo.setMinimumWidth(100)
        vitals_grid.addWidget(self.nhietdo, 0, 1)

        # Column 2: Nhịp tim
        lbl_nhiptim = QLabel("Nhịp tim")
        lbl_nhiptim.setStyleSheet(label_style)
        vitals_grid.addWidget(lbl_nhiptim, 0, 2)
        self.nhiptim = QLineEdit()
        self.nhiptim.setPlaceholderText("Nhịp tim nhịp/phút")
        self.nhiptim.setMinimumWidth(100)
        vitals_grid.addWidget(self.nhiptim, 0, 3)

        # Column 3: Huyết áp
        lbl_huyetap = QLabel("Huyết áp")
        lbl_huyetap.setStyleSheet(label_style)
        vitals_grid.addWidget(lbl_huyetap, 0, 4)
        self.huyetap = QLineEdit()
        self.huyetap.setPlaceholderText("Huyết áp mmHg")
        self.huyetap.setMinimumWidth(100)
        vitals_grid.addWidget(self.huyetap, 0, 5)

        # Set column stretches to make inputs expand evenly
        for i in range(6):
            if i % 2 == 1:  # Input columns
                vitals_grid.setColumnStretch(i, 1)
            else:  # Label columns
                vitals_grid.setColumnStretch(i, 0)

        t1_layout.addLayout(vitals_grid)

        t1_layout.addSpacing(5)  # Small gap between sections
        
        # Additional vitals / measurements - using grid layout for alignment
        meas_grid = QGridLayout()
        meas_grid.setHorizontalSpacing(15)
        meas_grid.setVerticalSpacing(8)

        # Column 1: Nhịp thở
        lbl_nhiptho = QLabel("Nhịp thở")
        lbl_nhiptho.setStyleSheet(label_style)
        meas_grid.addWidget(lbl_nhiptho, 0, 0)
        self.nhiptho = QLineEdit()
        self.nhiptho.setPlaceholderText("Nhịp thở nhịp/phút")
        self.nhiptho.setMinimumWidth(100)
        meas_grid.addWidget(self.nhiptho, 0, 1)

        # Column 2: Cân nặng
        lbl_cannang = QLabel("Cân nặng")
        lbl_cannang.setStyleSheet(label_style)
        meas_grid.addWidget(lbl_cannang, 0, 2)
        self.cannang = QLineEdit()
        self.cannang.setPlaceholderText("Kg")
        self.cannang.setMinimumWidth(100)
        meas_grid.addWidget(self.cannang, 0, 3)

        # Column 3: Chiều cao
        lbl_chieucao = QLabel("Chiều cao")
        lbl_chieucao.setStyleSheet(label_style)
        meas_grid.addWidget(lbl_chieucao, 0, 4)
        self.chieucao = QLineEdit()
        self.chieucao.setPlaceholderText("cm")
        self.chieucao.setMinimumWidth(100)
        meas_grid.addWidget(self.chieucao, 0, 5)

        # Set column stretches to make inputs expand evenly
        for i in range(6):
            if i % 2 == 1:  # Input columns
                meas_grid.setColumnStretch(i, 1)
            else:  # Label columns
                meas_grid.setColumnStretch(i, 0)

        t1_layout.addLayout(meas_grid)

        t1_layout.addSpacing(5)  # Small gap before history section

        # Allergy / histories - using grid layout for better alignment
        hist_grid = QGridLayout()
        hist_grid.setHorizontalSpacing(15)
        hist_grid.setVerticalSpacing(8)

        # Column 1: Dị ứng thuốc
        lbl_diung = QLabel("Dị ứng")
        lbl_diung.setStyleSheet(label_style)
        hist_grid.addWidget(lbl_diung, 0, 0)
        self.diungthuoc = QLineEdit()
        self.diungthuoc.setPlaceholderText("Dị ứng thuốc")
        self.diungthuoc.setMinimumWidth(100)
        hist_grid.addWidget(self.diungthuoc, 0, 1)

        # Column 2: Tiền sử bản thân
        lbl_tiensubt = QLabel("Tiền sử BT")
        lbl_tiensubt.setStyleSheet(label_style)
        hist_grid.addWidget(lbl_tiensubt, 0, 2)
        self.tiensubanthan = QLineEdit()
        self.tiensubanthan.setPlaceholderText("Tiền sử bản thân")
        self.tiensubanthan.setMinimumWidth(100)
        hist_grid.addWidget(self.tiensubanthan, 0, 3)

        # Column 3: Tiền sử gia đình
        lbl_tiensugd = QLabel("Tiền sử GĐ")
        lbl_tiensugd.setStyleSheet(label_style)
        hist_grid.addWidget(lbl_tiensugd, 0, 4)
        self.tiensugiadinh = QLineEdit()
        self.tiensugiadinh.setPlaceholderText("Tiền sử gia đình")
        self.tiensugiadinh.setMinimumWidth(100)
        hist_grid.addWidget(self.tiensugiadinh, 0, 5)

        # Set column stretches to make inputs expand evenly
        for i in range(6):
            if i % 2 == 1:  # Input columns
                hist_grid.setColumnStretch(i, 1)
            else:  # Label columns
                hist_grid.setColumnStretch(i, 0)

        t1_layout.addLayout(hist_grid)

        t1_layout.addSpacing(5)  # Small gap before diagnosis section

        # Bệnh kèm theo + ICD10 - using grid layout for proper alignment with other rows
        extra_grid = QGridLayout()
        extra_grid.setHorizontalSpacing(10)
        extra_grid.setVerticalSpacing(8)
        extra_grid.setContentsMargins(0, 0, 0, 0)

        # Column 0: Bệnh kèm theo label
        lbl_benhkem = QLabel("Bệnh kèm theo")
        lbl_benhkem.setStyleSheet(label_style)
        extra_grid.addWidget(lbl_benhkem, 0, 0)
        
        # Column 1: Bệnh kèm theo input
        self.benhkemtheo = QLineEdit()
        self.benhkemtheo.setPlaceholderText("Bệnh kèm theo")
        extra_grid.addWidget(self.benhkemtheo, 0, 1)

        # Column 2: ICD10 label
        lbl_icd10 = QLabel("ICD 10")
        lbl_icd10.setStyleSheet(label_style)
        extra_grid.addWidget(lbl_icd10, 0, 2)
        
        # Column 3-4: ICD10 input + button
        icd10_hbox = QHBoxLayout()
        icd10_hbox.setSpacing(5)
        icd10_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.icd10_display = QLineEdit()
        self.icd10_display.setReadOnly(True)
        self.icd10_display.setPlaceholderText("Chọn ICD10...")
        icd10_hbox.addWidget(self.icd10_display)
        
        btn_icd10 = QPushButton("...")
        btn_icd10.setMaximumWidth(40)
        btn_icd10.clicked.connect(self.open_icd10_dialog)
        icd10_hbox.addWidget(btn_icd10)
        
        # Store selected ICD10 codes internally
        self.selected_icd10_codes = []
        
        extra_grid.addLayout(icd10_hbox, 0, 3)
        
        # Set column stretches
        extra_grid.setColumnStretch(1, 1)  # Bệnh kèm theo input expands
        extra_grid.setColumnStretch(3, 1)  # ICD10 input expands

        t1_layout.addLayout(extra_grid)

        # Khám lâm sàng (trường lớn nhất vì thường cần ghi nhiều)
        t1_layout.addWidget(QLabel("Khám lâm sàng"))
        self.khamlamsang = QTextEdit()
        self.khamlamsang.setFixedHeight(40)
        t1_layout.addWidget(self.khamlamsang)

        # Chỉ định CLS (ngay dưới Khám lâm sàng)
        t1_layout.addWidget(QLabel("Chỉ định CLS"))
        self.chidinh_cls = QTextEdit()
        self.chidinh_cls.setFixedHeight(40)
        t1_layout.addWidget(self.chidinh_cls)

        # Chẩn đoán
        t1_layout.addWidget(QLabel("Chẩn đoán"))
        self.chandoan = QTextEdit()
        self.chandoan.setFixedHeight(40)
        t1_layout.addWidget(self.chandoan)

        # Kết luận
        t1_layout.addWidget(QLabel("Kết luận"))
        self.ketluan = QTextEdit()
        self.ketluan.setFixedHeight(40)
        t1_layout.addWidget(self.ketluan)

        self.tabs.addTab(tab_thongtin, "THÔNG TIN KHÁM")

        # Tab 2: Lịch sử KCB
        tab_lichsu = QWidget()
        t2_layout = QVBoxLayout(tab_lichsu)
        # History: Ngày khám | Bác sỹ khám | Chẩn đoán | Thuốc | Chi tiết
        self.table_history = QTableWidget(0, 5)
        self.table_history.setHorizontalHeaderLabels(["Ngày khám", "Bác sĩ khám", "Chẩn đoán", "Thuốc", "Xem chi tiết"])
        
        # Cấu hình độ rộng cột
        header = self.table_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Ngày khám
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Bác sỹ khám
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Chẩn đoán co giãn
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Thuốc co giãn
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Xem chi tiết
        
        # Đặt độ rộng cụ thể
        self.table_history.setColumnWidth(0, 120)  # Ngày khám
        self.table_history.setColumnWidth(1, 120)  # Bác sỹ khám
        self.table_history.setColumnWidth(4, 100)  # Xem chi tiết
        
        # Không cho chỉnh sửa trực tiếp, chọn theo hàng và chỉ 1 hàng
        self.table_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSelectionMode(QAbstractItemView.SingleSelection)
        # don't use automatic alternating rows; only highlight when selected
        self.table_history.setAlternatingRowColors(False)
        self.table_history.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                background-color: transparent;
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
            QTableWidget::item:!selected {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #0078D7;
                color: white;
                padding: 4px;
            }
        """)
        t2_layout.addWidget(self.table_history)
        self.tabs.addTab(tab_lichsu, "LỊCH SỬ KCB")

        main_layout.addWidget(self.tabs)
        # Date, doctor, room and actions (moved below tabs)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Ngày hẹn tái khám:"))
        self.ngaylap = QDateTimeEdit(QDate.currentDate())
        self.ngaylap.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.ngaylap.setCalendarPopup(True)
        # balance bottom row - make date/doctor/room fields expand sensibly
        h2.addWidget(self.ngaylap, 1)
        h2.addWidget(QLabel("Bác sĩ:"))
        self.bacsi = QLineEdit()
        self.bacsi.setReadOnly(True)
        self.bacsi.setMinimumWidth(160)
        h2.addWidget(self.bacsi, 1)
        h2.addWidget(QLabel("Phòng:"))
        self.phong = QLineEdit()
        self.phong.setReadOnly(True)
        self.phong.setMinimumWidth(160)
        h2.addWidget(self.phong, 1)
        h2.addStretch()
        main_layout.addLayout(h2)

        # Toolbar buttons at bottom
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        # Left group: Nhập mới, Lưu, Bỏ qua, Sửa, Xóa, In phiếu
        toolbar.addWidget(self.btn_nhapmoi)
        toolbar.addWidget(self.btn_luu)
        toolbar.addWidget(self.btn_boqua)
        toolbar.addWidget(self.btn_sua)
        toolbar.addWidget(self.btn_xoa)
        toolbar.addWidget(self.btn_inphieu)
        toolbar.addStretch()  # Push right group to the right
        # Right group: Mời vào khám, Kết thúc khám, Hủy kết thúc, Thoát
        toolbar.addWidget(self.btn_moivaokham)
        toolbar.addWidget(self.btn_ketthuckham)
        toolbar.addWidget(self.btn_huyketthuc)
        toolbar.addWidget(self.btn_thoat)
        main_layout.addLayout(toolbar)

        # signals
        self.hoten.currentIndexChanged.connect(self.on_select_benh_nhan)
        try:
            if self.completer:
                self.completer.activated.connect(self._on_completer_activated)
            try:
                self.hoten.lineEdit().editingFinished.connect(self._on_hoten_editing_finished)
            except Exception:
                pass
        except Exception:
            pass

    def on_select_benh_nhan(self, idx: int):
        """Khi chọn bệnh nhân: nạp thông tin cơ bản và lịch sử KCB."""
        # Use currentData() which is more robust than itemData(idx)
        # (signals may emit -1 or stale index in some Qt versions)
        # Handler for selecting patient

        benh_nhan_id = self.hoten.currentData()
        # Fallback: nếu currentData() là None (ví dụ người dùng gõ tên thay vì chọn)
        # Chỉ tự chọn khi:
        #  - user nhập full display item (ví dụ 'Họ Tên — Mã:HS005 ...') - exact match
        #  - hoặc text chứa 'Mã:' hoặc 'ID:' mà ta có thể parse
        # Không tự lookup theo tên đơn lẻ để tránh auto-load nhầm khi người dùng đang nhập bệnh nhân mới.
        if not benh_nhan_id:
            name = self.hoten.currentText().strip()
            if name:
                try:
                    # If name contains Mã:HSxxx try to lookup benh_nhan_id via tiep_don
                    if "Mã:" in name:
                        try:
                            ma = name.split("Mã:")[1].split()[0].strip()
                            tmp_conn = get_connection()
                            tmp_cur = tmp_conn.cursor()
                            tmp_cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (ma,))
                            rr = tmp_cur.fetchone()
                            tmp_conn.close()
                            if rr and rr[0]:
                                benh_nhan_id = rr[0]
                        except Exception:
                            benh_nhan_id = None
                    elif "ID:" in name:
                        try:
                            pid = int(name.split("ID:")[1].split()[0].strip())
                            benh_nhan_id = pid
                        except Exception:
                            benh_nhan_id = None
                    else:
                        # match full display text in combobox (exact match) - otherwise do nothing
                        idx_exact = self.hoten.findText(name, Qt.MatchExactly)
                        if idx_exact >= 0:
                            benh_nhan_id = self.hoten.itemData(idx_exact, Qt.UserRole)
                        else:
                            benh_nhan_id = None
                except Exception:
                    benh_nhan_id = None
        if not benh_nhan_id:
            # clear
            self.dienthoai.clear()
            self.ngaysinh.clear()
            self.gioitinh.clear()
            self.diachi.clear()
            self.sophieukham.clear()
            self.table_history.setRowCount(0)
            # Clear vital fields
            self.nhietdo.clear()
            self.nhiptim.clear()
            self.huyetap.clear()
            self.nhiptho.clear()
            self.cannang.clear()
            self.chieucao.clear()
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            # include loai_kham when loading patient record
            cur.execute("SELECT ho_ten, gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai, doi_tuong, so_cccd, loai_kham FROM benh_nhan WHERE id = ?", (benh_nhan_id,))
            bn = cur.fetchone()
            if bn:
                # bn: ho_ten, gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai, doi_tuong, so_cccd, loai_kham
                self.dienthoai.setText(bn[5] or "")
                self.ngaysinh.setText(bn[2] or "")
                self.gioitinh.setText(bn[1] or "")
                self.diachi.setText(bn[4] or "")
                self.tuoi.setText(str(bn[3]) + " tuổi" if bn[3] else "")
                self.doituong.setText(bn[6] or "")
                # so_cccd stored in bn[7] — keep as mã hồ sơ display if present
                self.mahoso.setText(bn[7] or "")
                # loai_kham may be in benh_nhan — populate top Loại khám field
                try:
                    self.loaikham.setText(bn[8] or "")
                except Exception:
                    pass

            # Load latest tiep_don (reception data) to populate vital fields
            try:
                cur.execute("""
                    SELECT nhiet_do, nhip_tim, huyet_ap, nhip_tho, can_nang, chieu_cao
                    FROM tiep_don
                    WHERE benh_nhan_id = ?
                    ORDER BY id DESC LIMIT 1
                """, (benh_nhan_id,))
                td = cur.fetchone()
                
                # Helper function to safely convert number to string
                # Chỉ hiển thị giá trị nếu nó là số hợp lệ
                def safe_str(val):
                    if val is None:
                        return ""
                    try:
                        # Nếu là số (int hoặc float) thì hiển thị
                        if isinstance(val, (int, float)):
                            # If it's a whole number, display without decimal
                            if float(val) == int(val):
                                return str(int(val))
                            return str(val)
                        # Nếu là chuỗi, cố gắng chuyển thành số để kiểm tra hợp lệ
                        str_val = str(val).strip()
                        if not str_val:
                            return ""
                        # Kiểm tra xem chuỗi có thể chuyển thành số không
                        try:
                            num_val = float(str_val)
                            # Nếu là số nguyên, hiển thị không có phần thập phân
                            if num_val == int(num_val):
                                return str(int(num_val))
                            return str(num_val)
                        except ValueError:
                            # Nếu không phải số hợp lệ, trả về chuỗi rỗng
                            return ""
                    except:
                        return ""
                
                if td:
                    # td: nhiet_do, nhip_tim, huyet_ap, nhip_tho, can_nang, chieu_cao
                    self.nhietdo.setText(safe_str(td[0]))
                    self.nhiptim.setText(safe_str(td[1]))
                    self.huyetap.setText(safe_str(td[2]))
                    self.nhiptho.setText(safe_str(td[3]))
                    self.cannang.setText(safe_str(td[4]))
                    self.chieucao.setText(safe_str(td[5]))
                else:
                    # Clear vital fields if no tiep_don data
                    self.nhietdo.clear()
                    self.nhiptim.clear()
                    self.huyetap.clear()
                    self.nhiptho.clear()
                    self.cannang.clear()
                    self.chieucao.clear()
            except Exception:
                # Ignore errors when loading tiep_don
                pass

            # load latest phieu_kham -> display so_phieu and load detail
            cur.execute("SELECT so_phieu, id FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (benh_nhan_id,))
            last = cur.fetchone()
            if last:
                self.sophieukham.setText(last[0] or "")
                # Load chi tiết phiếu khám gần nhất
                try:
                    self.load_chi_tiet_kham(last[1])
                    # Cũng load thêm khám lâm sàng từ chi_dinh để đảm bảo cập nhật mới nhất
                    self.load_kham_lam_sang_from_chi_dinh(benh_nhan_id)
                    self.current_phieu_kham_id = last[1]
                    self.current_so_phieu = last[0]
                    # Kiểm tra xem phiếu khám này có dữ liệu chi tiết không
                    # Nếu chưa có dữ liệu chi tiết (ghi chú, exam info, ...) thì mở form để nhập
                    # Chỉ khóa form khi phiếu đã đầy đủ thông tin
                    conn_check = get_connection()
                    cur_check = conn_check.cursor()
                    try:
                        cur_check.execute("""
                            SELECT COUNT(*) FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ?
                        """, (last[1],))
                        has_detail = cur_check.fetchone()[0] > 0
                        
                        if has_detail:
                            # Phiếu có dữ liệu chi tiết → khóa form
                            self.lock_form()
                        else:
                            # Phiếu chưa có chi tiết → mở form để nhập
                            self.unlock_form()

                    
                    finally:
                        conn_check.close()
                except Exception:
                    logger.exception("Error loading chi tiết khám")
            else:
                # Nếu chưa có phiếu khám -> không tạo số phiếu mới, chờ tạo từ form chỉ định
                # Giữ lại các giá trị vitals đã load từ `tiep_don` (nếu có)
                self.sophieukham.clear()
                # Clear các trường khác trong tab THÔNG TIN KHÁM
                self.clear_chi_tiet_kham()
                # Load khám lâm sàng từ form chỉ định dịch vụ (nếu có)
                self.load_kham_lam_sang_from_chi_dinh(benh_nhan_id)
                # Đảm bảo form mở để nhập dữ liệu mới
                self.unlock_form()

            # load history (phieu_kham)
            cur.execute("""
                SELECT pk.id, pk.ngay_lap, pk.bac_si
                FROM phieu_kham pk
                WHERE pk.benh_nhan_id = ?
                ORDER BY pk.id DESC
                LIMIT 50
            """, (benh_nhan_id,))
            rows = cur.fetchall()

            # load recent tiep_don info (ma_hoso, phong_kham, bac_si_kham, tinh_trang, ngay_tiep_don, tien_kham)
            try:
                cur.execute("SELECT ma_hoso, phong_kham, bac_si_kham, tinh_trang, ngay_tiep_don, tien_kham FROM tiep_don WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (benh_nhan_id,))
                td = cur.fetchone()
                if td:
                    # td: ma_hoso, phong_kham, bac_si_kham, tinh_trang, ngay_tiep_don, tien_kham
                    try:
                        self.mahoso.setText(td[0] or "")
                    except Exception:
                        pass
                    try:
                        self.phongkham.setText(td[1] or "")
                        # also sync bottom editable room field
                        self.phong.setText(td[1] or "")
                    except Exception:
                        pass
                    try:
                        self.bacsikham.setText(td[2] or "")
                        # also sync bottom editable doctor field
                        self.bacsi.setText(td[2] or "")
                    except Exception:
                        pass
                    try:
                        self.tinhtrang.setText(td[3] or "")
                    except Exception:
                        pass
                    try:
                        # display date of reception in top panel
                        self.ngaytiepdon.setText(td[4] or "")
                        # and set bottom editable date (QDateEdit) if possible
                        if td[4]:
                            qd = QDate.fromString(td[4], "yyyy-MM-dd")
                            if qd.isValid():
                                try:
                                    self.ngaylap.setDate(qd)
                                    try:
                                        self.display_ngaylap_top.setText(qd.toString("dd/MM/yyyy"))
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    try:
                        # tiền khám từ tiep_don
                        self.tienkham.setText(str(td[5] or "0"))
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            rows = []
        finally:
            conn.close()

        # populate history table
        self.table_history.setRowCount(0)
        for r in rows:
            # r: id, ngay_lap, bac_si
            phieu_id = r[0]
            # determine diagnosis for history: prefer chi_tiet_phieu_kham.chan_doan then chi_dinh.chan_doan_ban_dau
            diagnosis_text = ""
            try:
                conn_diag = get_connection()
                cur_diag = conn_diag.cursor()
                cur_diag.execute("SELECT chan_doan FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_id,))
                drow = cur_diag.fetchone()
                if drow and drow[0]:
                    diagnosis_text = drow[0]
                else:
                    cur_diag.execute("SELECT chan_doan_ban_dau FROM chi_dinh WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_id,))
                    cdrow = cur_diag.fetchone()
                    if cdrow and cdrow[0]:
                        diagnosis_text = cdrow[0]
            except Exception:
                diagnosis_text = ""
            finally:
                try:
                    conn_diag.close()
                except Exception:
                    pass
            # Lấy thông tin thuốc cho phiếu khám này
            conn_drugs = get_connection()
            cur_drugs = conn_drugs.cursor()
            try:
                cur_drugs.execute("""
                    SELECT ctdt.ten_thuoc, ctdt.so_luong, ctdt.don_vi, ctdt.lieu_dung
                    FROM chi_tiet_don_thuoc ctdt
                    JOIN don_thuoc dt ON ctdt.don_thuoc_id = dt.id
                    WHERE dt.phieu_kham_id = ?
                    ORDER BY ctdt.id
                """, (phieu_id,))
                medicines = cur_drugs.fetchall()
            except Exception:
                medicines = []
            finally:
                conn_drugs.close()
            
            # Tạo chuỗi thuốc
            medicine_text = ""
            if medicines:
                medicine_lines = []
                for med in medicines:
                    ten_thuoc = med[0] or ""
                    so_luong = med[1] or ""
                    don_vi = med[2] or ""
                    lieu_dung = med[3] or ""
                    med_str = f"{ten_thuoc} {so_luong}{don_vi}"
                    if lieu_dung:
                        med_str += f" ({lieu_dung})"
                    medicine_lines.append(med_str)
                medicine_text = "\n".join(medicine_lines)
            
            row = self.table_history.rowCount()
            self.table_history.insertRow(row)
            self.table_history.setItem(row, 0, QTableWidgetItem(str(r[1] or "")))
            self.table_history.setItem(row, 1, QTableWidgetItem(str(r[2] or "")))
            self.table_history.setItem(row, 2, QTableWidgetItem(str(diagnosis_text or "")))
            # Cột thuốc: hiển thị danh sách thuốc
            med_item = QTableWidgetItem(medicine_text)
            self.table_history.setItem(row, 3, med_item)
            # Xem button
            btn = QPushButton("Xem")
            btn.clicked.connect(partial(self.show_phieu_kham_details, phieu_id))
            self.table_history.setCellWidget(row, 4, btn)

    def load_so_phieu_kham(self, benh_nhan_id):
        """Load số phiếu khám từ phiếu đã tạo trong form chỉ định."""
        if not benh_nhan_id:
            return None

        conn = get_connection()
        cur = conn.cursor()
        try:
            # Lấy phiếu khám trong ngày
            today = QDate.currentDate().toString("yyyy-MM-dd")
            cur.execute("""
                SELECT so_phieu, id 
                FROM phieu_kham 
                WHERE benh_nhan_id = ? AND date(ngay_lap) = ?
                ORDER BY id DESC LIMIT 1
            """, (benh_nhan_id, today))
            result = cur.fetchone()
            if result:
                return result[0], result[1]  # Trả về cả số phiếu và ID
            return None
        finally:
            conn.close()

    def on_save(self):
        benh_nhan_id = self.hoten.currentData()  # Updated from combo_bn to hoten
        if not benh_nhan_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn bệnh nhân.")
            return

        ngay_lap = self.ngaylap.date().toString("yyyy-MM-dd")
        bac_si = self.bacsi.text().strip()
        phong_kham = self.phong.text().strip()
        kham_lam_sang = self.khamlamsang.toPlainText().strip()
        chan_doan = self.chandoan.toPlainText().strip()
        # Ghi chú chung trên form (nằm trong group THÔNG TIN BỆNH NHÂN)
        ghi_chu_kham = self.ghichu.toPlainText().strip()

        # Thu thập thông tin chi tiết khám
        try:
            nhiet_do = float(self.nhietdo.text()) if self.nhietdo.text().strip() else None
        except ValueError:
            nhiet_do = None

        try:
            nhip_tim = int(self.nhiptim.text()) if self.nhiptim.text().strip() else None
        except ValueError:
            nhip_tim = None

        try:
            nhip_tho = int(self.nhiptho.text()) if self.nhiptho.text().strip() else None
        except ValueError:
            nhip_tho = None

        try:
            can_nang = float(self.cannang.text()) if self.cannang.text().strip() else None
        except ValueError:
            can_nang = None

        try:
            chieu_cao = float(self.chieucao.text()) if self.chieucao.text().strip() else None
        except ValueError:
            chieu_cao = None

        huyet_ap = self.huyetap.text().strip()
        di_ung_thuoc = self.diungthuoc.text().strip()
        tien_su_ban_than = self.tiensubanthan.text().strip()
        tien_su_gia_dinh = self.tiensugiadinh.text().strip()
        benh_kem_theo = self.benhkemtheo.text().strip()
        icd10 = ",".join(self.selected_icd10_codes)  # Join selected ICD10 codes with comma
        kham_lam_sang = self.khamlamsang.toPlainText().strip()
        ket_luan = self.ketluan.toPlainText().strip()
        
        # DEBUG: log the values being saved for troubleshooting
        logger.debug("[DEBUG on_save] Giá trị lấy từ form:")
        logger.debug("  nhiet_do=%s (từ '%s')", nhiet_do, self.nhietdo.text())
        logger.debug("  nhip_tim=%s (từ '%s')", nhip_tim, self.nhiptim.text())
        logger.debug("  nhip_tho=%s (từ '%s')", nhip_tho, self.nhiptho.text())
        logger.debug("  can_nang=%s (từ '%s')", can_nang, self.cannang.text())
        logger.debug("  chieu_cao=%s (từ '%s')", chieu_cao, self.chieucao.text())
        logger.debug("  huyet_ap='%s' (từ '%s')", huyet_ap, self.huyetap.text())
        logger.debug("  chan_doan='%s'", chan_doan)
        logger.debug("  kham_lam_sang='%s...' (len=%d)", kham_lam_sang[:30], len(kham_lam_sang))
        logger.debug("  Trạng thái các trường:")
        logger.debug("    nhietdo.isReadOnly()=%s", self.nhietdo.isReadOnly())
        logger.debug("    nhiptim.isReadOnly()=%s", self.nhiptim.isReadOnly())
        logger.debug("    nhiptho.isReadOnly()=%s", self.nhiptho.isReadOnly())
        logger.debug("    cannang.isReadOnly()=%s", self.cannang.isReadOnly())
        logger.debug("    chieucao.isReadOnly()=%s", self.chieucao.isReadOnly())
        
        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            # Sử dụng current_phieu_kham_id đã được gán khi chọn bệnh nhân
            phieu_id = self.current_phieu_kham_id
            
            if not phieu_id:
                # Nếu chưa có phiếu khám, kiểm tra xem đã tạo phiếu từ form chỉ định chưa
                today = QDate.currentDate().toString("yyyy-MM-dd")
                cur.execute("""
                    SELECT id, so_phieu FROM phieu_kham 
                    WHERE benh_nhan_id = ? AND date(ngay_lap) = ?
                    ORDER BY id DESC LIMIT 1
                """, (benh_nhan_id, today))
                existing = cur.fetchone()

                if not existing:
                    QMessageBox.warning(self, "Thông báo", 
                        "Vui lòng tạo phiếu khám từ form Chỉ định dịch vụ trước!")
                    return
                phieu_id = existing[0]
                self.current_phieu_kham_id = phieu_id

            # Cập nhật thông tin phiếu khám
            # phieu_kham no longer stores 'chan_doan' (diagnosis is stored in chi_dinh/chi_tiet)
            cur.execute("""
                UPDATE phieu_kham 
                SET ngay_lap = ?, bac_si = ?, phong_kham = ?
                WHERE id = ?
            """, (ngay_lap, bac_si, phong_kham, phieu_id))

            # Cập nhật chi tiết khám (xóa cũ nếu có)
            cur.execute("DELETE FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ?", (phieu_id,))
            
            # Thêm chi tiết khám mới
            cur.execute("""
                INSERT INTO chi_tiet_phieu_kham(
                    phieu_kham_id, nhiet_do, nhip_tim, huyet_ap, nhip_tho,
                    can_nang, chieu_cao, di_ung_thuoc, tien_su_ban_than,
                    tien_su_gia_dinh, benh_kem_theo, icd10, chidinh_cls,
                    kham_lam_sang, chan_doan, ket_luan, ghi_chu_kham
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                phieu_id, nhiet_do, nhip_tim, huyet_ap, nhip_tho,
                can_nang, chieu_cao, di_ung_thuoc, tien_su_ban_than,
                tien_su_gia_dinh, benh_kem_theo, icd10, self.chidinh_cls.toPlainText().strip(),
                kham_lam_sang, chan_doan, ket_luan, ghi_chu_kham
            ))

            # Get the so_phieu for the current phieu_kham
            cur.execute("SELECT so_phieu FROM phieu_kham WHERE id = ?", (phieu_id,))
            so_phieu = cur.fetchone()[0]
            
            conn.commit()
            self.current_so_phieu = so_phieu
            # update displayed so_phieu in patient info panel
            try:
                self.sophieukham.setText(so_phieu)
            except Exception:
                pass
            QMessageBox.information(self, "Thành công", f"Đã lưu phiếu: {so_phieu}")
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu phiếu khám: {e}")
        finally:
            conn.close()

    def clear_chi_tiet_kham(self):
        """Xóa dữ liệu chi tiết khám trên form."""
        # Lưu vital signs hiện tại
        vital_backup = {
            "nhietdo": self.nhietdo.text(),
            "nhiptim": self.nhiptim.text(),
            "huyetap": self.huyetap.text(),
            "nhiptho": self.nhiptho.text(),
            "cannang": self.cannang.text(),
            "chieucao": self.chieucao.text(),
        }
        
        # Clear toàn bộ
        self.nhietdo.clear()
        self.nhiptim.clear()
        self.huyetap.clear()
        self.nhiptho.clear()
        self.cannang.clear()
        self.chieucao.clear()
        self.diungthuoc.clear()
        self.tiensubanthan.clear()
        self.tiensugiadinh.clear()
        self.benhkemtheo.clear()
        self.selected_icd10_codes = []  # Reset selected ICD10 codes
        self.update_icd10_display()
        try:
            self.chidinh_cls.clear()
        except Exception:
            pass
        self.khamlamsang.clear()
        self.chandoan.clear()
        self.ketluan.clear()
        self.ghichu.clear()
        
        # Restore vital signs
        self.nhietdo.setText(vital_backup["nhietdo"])
        self.nhiptim.setText(vital_backup["nhiptim"])
        self.huyetap.setText(vital_backup["huyetap"])
        self.nhiptho.setText(vital_backup["nhiptho"])
        self.cannang.setText(vital_backup["cannang"])
        self.chieucao.setText(vital_backup["chieucao"])

    def load_kham_lam_sang_from_chi_dinh(self, benh_nhan_id):
        """Load khám lâm sàng từ chi_dinh."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            logger.debug("load_kham_lam_sang_from_chi_dinh: benh_nhan_id=%s", benh_nhan_id)

            # Bước 1: Lấy phiếu khám mới nhất của bệnh nhân
            cur.execute("SELECT id FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (benh_nhan_id,))
            pk_result = cur.fetchone()
            logger.debug("Latest phieu_kham: %s", pk_result)

            if not pk_result:
                logger.debug("No phieu_kham found for benh_nhan_id=%s", benh_nhan_id)
                conn.close()
                return

            phieu_kham_id = pk_result[0]

            # Bước 2: Lấy chi_dinh mới nhất của phiếu khám đó
            cur.execute("""
                SELECT kham_lam_sang, id
                FROM chi_dinh
                WHERE phieu_kham_id = ?
                ORDER BY id DESC LIMIT 1
            """, (phieu_kham_id,))
            cd_result = cur.fetchone()
            logger.debug("chi_dinh query result: %s", cd_result)

            if cd_result and cd_result[0]:
                kham_lam_sang = cd_result[0]
                chi_dinh_id = cd_result[1]

                self.khamlamsang.setPlainText(kham_lam_sang)
                try:
                    self._kham_load_source.setText(f"Loaded from: chi_dinh (id={chi_dinh_id})")
                except Exception:
                    pass
                logger.debug("Loaded kham_lam_sang from chi_dinh: %s...", (kham_lam_sang[:50] if len(kham_lam_sang) > 50 else kham_lam_sang))
            else:
                logger.debug("No kham_lam_sang in chi_dinh for phieu_kham_id=%s", phieu_kham_id)

            conn.close()
        except Exception:
            logger.exception("Exception in load_kham_lam_sang_from_chi_dinh")

    def load_chi_tiet_kham(self, phieu_kham_id):
        """Load thông tin chi tiết khám từ CSDL."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT nhiet_do, nhip_tim, huyet_ap, nhip_tho,
                       can_nang, chieu_cao, di_ung_thuoc, tien_su_ban_than,
                       tien_su_gia_dinh, benh_kem_theo, icd10, chidinh_cls,
                       kham_lam_sang, chan_doan, ket_luan, ghi_chu_kham
                FROM chi_tiet_phieu_kham
                WHERE phieu_kham_id = ?
            """, (phieu_kham_id,))
            row = cur.fetchone()
            if row:
                self.nhietdo.setText(str(row[0]) if row[0] is not None else "")
                self.nhiptim.setText(str(row[1]) if row[1] is not None else "")
                self.huyetap.setText(row[2] or "")
                self.nhiptho.setText(str(row[3]) if row[3] is not None else "")
                self.cannang.setText(str(row[4]) if row[4] is not None else "")
                self.chieucao.setText(str(row[5]) if row[5] is not None else "")
                self.diungthuoc.setText(row[6] or "")
                self.tiensubanthan.setText(row[7] or "")
                self.tiensugiadinh.setText(row[8] or "")
                self.benhkemtheo.setText(row[9] or "")
                # Load ICD10 codes (stored as comma-separated string)
                icd10_codes_str = row[10] or ""
                self.selected_icd10_codes = [code.strip() for code in icd10_codes_str.split(",") if code.strip()]
                self.update_icd10_display()
                # row[11] = chidinh_cls, row[12] = kham_lam_sang, row[13] = chan_doan, row[14] = ket_luan, row[15] = ghi_chu_kham
                try:
                    self.chidinh_cls.setPlainText(row[11] or "")
                except Exception:
                    pass
                
                # Priority: Load kham_lam_sang từ chi_dinh
                kham_from_chi_dinh = None
                try:
                    cur.execute("SELECT kham_lam_sang FROM chi_dinh WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_kham_id,))
                    cd = cur.fetchone()
                    if cd and cd[0]:
                        kham_from_chi_dinh = cd[0]
                except Exception as e:
                    logger.exception("Error loading kham_lam_sang from chi_dinh in load_chi_tiet_kham")
                
                # Use chi_dinh data if available, otherwise fall back to chi_tiet_phieu_kham
                self.khamlamsang.setPlainText(kham_from_chi_dinh or row[12] or "")
                # chan_doan giữ nguyên từ chi_tiet_phieu_kham (load từ ICD10, không từ chi_dinh)
                self.chandoan.setPlainText(row[13] or "")
                self.ketluan.setPlainText(row[14] or "")
                self.ghichu.setPlainText(row[15] or "")
            else:
                self.clear_chi_tiet_kham()
        finally:
            conn.close()
            
    def on_reset(self):
        self.hoten.setCurrentIndex(-1)  # Updated from combo_bn to hoten
        self.ngaylap.setDate(QDate.currentDate())
        self.display_ngaylap_top.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        self.tuoi.clear()
        self.ngaysinh.clear()
        self.gioitinh.clear()
        self.diachi.clear()
        self.doituong.clear()
        self.loaikham.clear()
        self.bacsikham.clear()
        self.ngaytiepdon.clear()
        self.tinhtrang.clear()
        self.phongkham.clear()
        self.mahoso.clear()
        self.bacsi.clear()
        self.phong.clear()
        self.chandoan.clear()
        self.current_phieu_kham_id = None
        self.current_so_phieu = None
        self.clear_chi_tiet_kham()

    def show_phieu_kham_details(self, phieu_id):
        """Hiển thị dialog chi tiết cho một phiếu khám."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT so_phieu, benh_nhan_id, ngay_lap, bac_si, phong_kham, tong_tien FROM phieu_kham WHERE id = ?", (phieu_id,))
            pk = cur.fetchone()
            cur.execute("SELECT nhiet_do, nhip_tim, huyet_ap, nhip_tho, can_nang, chieu_cao, di_ung_thuoc, tien_su_ban_than, tien_su_gia_dinh, benh_kem_theo, icd10, chidinh_cls, kham_lam_sang, chan_doan, ket_luan, ghi_chu_kham FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ?", (phieu_id,))
            detail = cur.fetchone()
            # Also collect chi_dinh (danh sách dịch vụ)
            cur.execute("SELECT ten_dich_vu, so_luong, don_gia FROM chi_dinh WHERE phieu_kham_id = ?", (phieu_id,))
            services = cur.fetchall()
            # Lấy thông tin thuốc từ đơn thuốc
            cur.execute("""
                SELECT ctdt.ten_thuoc, ctdt.so_luong, ctdt.don_vi, ctdt.lieu_dung, ctdt.sang, ctdt.trua, ctdt.chieu, ctdt.toi
                FROM chi_tiet_don_thuoc ctdt
                JOIN don_thuoc dt ON ctdt.don_thuoc_id = dt.id
                WHERE dt.phieu_kham_id = ?
                ORDER BY ctdt.id
            """, (phieu_id,))
            medicines = cur.fetchall()
        finally:
            conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Chi tiết phiếu {pk[0] if pk else phieu_id}")
        layout = QVBoxLayout(dlg)
        text = []
        if pk:
            text.append(f"Số phiếu: {pk[0]}")
            text.append(f"Ngày lập: {pk[2]}")
            text.append(f"Bác sĩ: {pk[3]}")
            text.append(f"Phòng: {pk[4]}")
            # Determine diagnosis: prefer detail.chan_doan, then chi_dinh.chan_doan_ban_dau
            diagnosis_text = ""
            if detail and len(detail) > 13 and detail[13]:
                diagnosis_text = detail[13]
            else:
                try:
                    cur2 = get_connection().cursor()
                    cur2.execute("SELECT chan_doan_ban_dau FROM chi_dinh WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (phieu_id,))
                    cdv = cur2.fetchone()
                    if cdv and cdv[0]:
                        diagnosis_text = cdv[0]
                except Exception:
                    diagnosis_text = ""
            text.append(f"Chẩn đoán (phiếu): {diagnosis_text}")
            text.append(f"Tổng tiền: {pk[5]}")
            if detail:
                text.append("--- Dấu hiệu và tiền sử ---")
                text.append(f"Nhiệt độ: {detail[0]}")
                text.append(f"Nhịp tim: {detail[1]}")
                text.append(f"Huyết áp: {detail[2]}")
                text.append(f"Nhịp thở: {detail[3]}")
                text.append(f"Cân nặng: {detail[4]}  Chiều cao: {detail[5]}")
                text.append(f"Dị ứng thuốc: {detail[6]}")
                text.append(f"Tiền sử bản thân: {detail[7]}")
                text.append(f"Tiền sử gia đình: {detail[8]}")
                text.append(f"Bệnh kèm theo: {detail[9]}")
                text.append(f"ICD10: {detail[10]}")
                text.append(f"Chỉ định CLS: {detail[11]}")
                text.append("--- Khám lâm sàng / Kết luận ---")
                text.append(f"Khám lâm sàng: {detail[12]}")
                text.append(f"Chẩn đoán (chi tiết): {detail[13]}")
                text.append(f"Kết luận: {detail[14]}")
                text.append(f"Ghi chú khám: {detail[15]}")
        if services:
            text.append("--- Dịch vụ chỉ định ---")
            for s in services:
                text.append(f"{s[0]} x{s[1]} - {s[2]}")
        if medicines:
            text.append("--- Danh sách thuốc ---")
            for med in medicines:
                ten_thuoc = med[0] or ""
                so_luong = med[1] or ""
                don_vi = med[2] or ""
                lieu_dung = med[3] or ""
                sang = med[4] or ""
                trua = med[5] or ""
                chieu = med[6] or ""
                toi = med[7] or ""
                
                med_str = f"{ten_thuoc} {so_luong}{don_vi}"
                if lieu_dung:
                    med_str += f" ({lieu_dung})"
                
                timing = []
                if sang:
                    timing.append(f"Sáng: {sang}")
                if trua:
                    timing.append(f"Trưa: {trua}")
                if chieu:
                    timing.append(f"Chiều: {chieu}")
                if toi:
                    timing.append(f"Tối: {toi}")
                
                if timing:
                    med_str += " - " + ", ".join(timing)
                
                text.append(med_str)

        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText("\n".join(text))
        # Giảm minimum size để không ép layout khi resize, cho phép mở rộng khi cần
        te.setMinimumSize(400, 300)
        te.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(te)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dlg.accept)
        hb = QHBoxLayout()
        hb.addStretch()
        hb.addWidget(btn_close)
        layout.addLayout(hb)

        dlg.exec_()

    def lock_form(self):
        """Khóa form để không cho chỉnh sửa (nhưng vẫn cho phép chỉnh sửa các vital signs)"""
        # Khóa các trường thông tin chi tiết khám, TRỪ vital signs (nhiệt độ, nhịp tim, nhịp thở, cân nặng, chiều cao)
        # vì những trường này có thể thay đổi mỗi lần khám
        fields_to_lock = [
            self.chandoan, self.khamlamsang, self.ketluan, self.ghichu,
            self.diungthuoc, self.tiensubanthan,
            self.tiensugiadinh, self.benhkemtheo, self.icd10_display, self.chidinh_cls,
            self.bacsi, self.phong, self.huyetap
        ]
        # Các trường vital signs KHÔNG bị khóa để cho phép chỉnh sửa:
        # nhietdo, nhiptim, nhiptho, cannang, chieucao
        for field in fields_to_lock:
            # QComboBox không có setReadOnly, sử dụng setEnabled thay thế
            if isinstance(field, QComboBox):
                field.setEnabled(False)
            else:
                field.setReadOnly(True)

    def unlock_form(self):
        """Mở khóa form để cho phép chỉnh sửa"""
        # Mở khóa các trường thông tin chi tiết khám
        fields_to_unlock = [
            self.chandoan, self.khamlamsang, self.ketluan, self.ghichu,
            self.nhietdo, self.nhiptim, self.huyetap, self.nhiptho,
            self.cannang, self.chieucao, self.diungthuoc, self.tiensubanthan,
            self.tiensugiadinh, self.benhkemtheo, self.icd10_display, self.chidinh_cls,
            self.bacsi, self.phong
        ]
        for field in fields_to_unlock:
            # QComboBox không có setReadOnly, sử dụng setEnabled thay thế
            if isinstance(field, QComboBox):
                field.setEnabled(True)
            else:
                field.setReadOnly(False)

    def on_edit(self):
        """Cho phép chỉnh sửa thông tin phiếu khám"""
        if not self.sophieukham.text():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn bệnh nhân và phiếu khám cần sửa!")
            return
        
        # Mở khóa form để cho phép chỉnh sửa
        self.unlock_form()
        QMessageBox.information(self, "Thông báo", "Đã bật chế độ sửa thông tin phiếu khám.")

    def on_delete(self):
        """Xóa phiếu khám hiện tại"""
        if not self.current_phieu_kham_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn phiếu khám cần xóa!")
            return
        reply = QMessageBox.question(self, "Xác nhận", 
                                   "Bạn có chắc chắn muốn xóa phiếu khám này?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ?", 
                          (self.current_phieu_kham_id,))
                cur.execute("DELETE FROM phieu_kham WHERE id = ?", 
                          (self.current_phieu_kham_id,))
                conn.commit()
                QMessageBox.information(self, "Thành công", "Đã xóa phiếu khám!")
                self.on_reset()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa phiếu khám: {e}")
            finally:
                conn.close()

    def on_print(self):
        """In phiếu khám"""
        if not self.current_phieu_kham_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn phiếu khám cần in!")
            return
            
        try:
            from .print_phieu_kham import print_phieu_kham
            
            # Thu thập dữ liệu cho phiếu in
            phieu_data = {
                'so_phieu': self.sophieukham.text(),
                'ngay_lap': self.display_ngaylap_top.text(),
                'ho_ten': self.hoten.currentText(),
                'gioi_tinh': self.gioitinh.text(),
                'ngay_sinh': self.ngaysinh.text(),
                'tuoi': self.tuoi.text().replace(" tuổi", ""),
                'dia_chi': self.diachi.text(),
                'dien_thoai': self.dienthoai.text(),
                'nhiet_do': self.nhietdo.text(),
                'huyet_ap': self.huyetap.text(),
                'nhip_tim': self.nhiptim.text(),
                'nhip_tho': self.nhiptho.text(),
                'can_nang': self.cannang.text(),
                'chieu_cao': self.chieucao.text(),
                'di_ung_thuoc': self.diungthuoc.text(),
                'tien_su_ban_than': self.tiensubanthan.text(),
                'tien_su_gia_dinh': self.tiensugiadinh.text(),
                'benh_kem_theo': self.benhkemtheo.text(),
                'icd10': ",".join(self.selected_icd10_codes),  # Join selected ICD10 codes
                'kham_lam_sang': self.khamlamsang.toPlainText(),
                'chan_doan': self.chandoan.toPlainText(),
                'ket_luan': self.ketluan.toPlainText(),
                'bac_si': self.bacsi.text()
            }
            
            # Gọi hàm in phiếu
            output_path = print_phieu_kham(phieu_data)
            
            # Mở cửa sổ xem trước PDF
            from .pdf_viewer import PDFViewer
            viewer = PDFViewer(output_path, parent=self)
            viewer.setWindowTitle(f"Xem trước phiếu khám - {self.sophieukham.text()}")
            viewer.resize(800, 900)  # Kích thước cửa sổ xem trước
            viewer.show()
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể in phiếu khám: {e}")

    
    def on_phieu_changed(self, index):
        """Xử lý khi chọn loại phiếu khác nhau"""
        phieu_type = self.combo_phieukham.currentText()
        QMessageBox.information(self, "Thông báo", 
                              f"Đang chuyển sang {phieu_type}...")

    def on_moi_kham(self):
        """Mời bệnh nhân vào khám"""
        if not self.current_phieu_kham_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn phiếu khám!")
            return
        QMessageBox.information(self, "Thông báo", 
                              "Đã mời bệnh nhân vào khám!")

    def on_ket_thuc(self):
        """Kết thúc khám cho bệnh nhân"""
        if not self.current_phieu_kham_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn phiếu khám!")
            return
        # Cập nhật cờ 'da_kham' trong bảng tiep_don
        benh_nhan_id = self.hoten.currentData()
        mahoso = (self.mahoso.text() or "").strip()
        conn = get_connection()
        cur = conn.cursor()
        try:
            td_id = None
            if mahoso:
                cur.execute("SELECT id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (mahoso,))
                r = cur.fetchone()
                if r:
                    td_id = r[0]
            if not td_id and benh_nhan_id:
                cur.execute("SELECT id FROM tiep_don WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (benh_nhan_id,))
                r = cur.fetchone()
                if r:
                    td_id = r[0]

            if td_id:
                cur.execute("UPDATE tiep_don SET da_kham = 1 WHERE id = ?", (td_id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.exception("Lỗi khi cập nhật da_kham")
        finally:
            conn.close()

        QMessageBox.information(self, "Thông báo", "Đã kết thúc khám cho bệnh nhân!")

    def on_huy_ket_thuc(self):
        """Hủy kết thúc khám"""
        if not self.current_phieu_kham_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn phiếu khám!")
            return
        # Cập nhật cờ 'da_kham' trong bảng tiep_don về 0
        benh_nhan_id = self.hoten.currentData()
        mahoso = (self.mahoso.text() or "").strip()
        conn = get_connection()
        cur = conn.cursor()
        try:
            td_id = None
            if mahoso:
                cur.execute("SELECT id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (mahoso,))
                r = cur.fetchone()
                if r:
                    td_id = r[0]
            if not td_id and benh_nhan_id:
                cur.execute("SELECT id FROM tiep_don WHERE benh_nhan_id = ? ORDER BY id DESC LIMIT 1", (benh_nhan_id,))
                r = cur.fetchone()
                if r:
                    td_id = r[0]

            if td_id:
                cur.execute("UPDATE tiep_don SET da_kham = 0 WHERE id = ?", (td_id,))
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.exception("Lỗi khi cập nhật da_kham (hủy)")
        finally:
            conn.close()

        QMessageBox.information(self, "Thông báo", "Đã hủy kết thúc khám!")

    def load_benh_nhan_list(self):
        # Helper handlers for completer and editing finished on the hoten combobox
        # (Kept out of on_select_benh_nhan to avoid nested scopes and alignment issues.)
        def _on_completer_activated_local(text):
            try:
                if not text or not text.strip():
                    return
                if "Mã:" in text:
                    try:
                        ma = text.split("Mã:")[1].split()[0].strip()
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (ma,))
                        r = cur.fetchone()
                        conn.close()
                        if r and r[0]:
                            target_id = r[0]
                            for i in range(self.hoten.count()):
                                if self.hoten.itemData(i, Qt.UserRole) == target_id:
                                    self.hoten.setCurrentIndex(i)
                                    self.on_select_benh_nhan(i)
                                    return
                    except Exception:
                        pass
                idx = self.hoten.findText(text.strip(), Qt.MatchExactly)
                if idx >= 0:
                    self.hoten.setCurrentIndex(idx)
                    self.on_select_benh_nhan(idx)
            except Exception as e:
                logger.exception("_on_completer_activated (local) error: %s", e)

        def _on_hoten_editing_finished_local():
            try:
                text = self.hoten.currentText().strip()
                if not text:
                    return
                if "Mã:" in text:
                    try:
                        ma = text.split("Mã:")[1].split()[0].strip()
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (ma,))
                        r = cur.fetchone()
                        conn.close()
                        if r and r[0]:
                            target_id = r[0]
                            for i in range(self.hoten.count()):
                                if self.hoten.itemData(i, Qt.UserRole) == target_id:
                                    self.hoten.setCurrentIndex(i)
                                    self.on_select_benh_nhan(i)
                                    return
                    except Exception:
                        pass
                idx = self.hoten.findText(text, Qt.MatchExactly)
                if idx >= 0:
                    self.hoten.setCurrentIndex(idx)
                    self.on_select_benh_nhan(idx)
            except Exception as e:
                logger.exception("_on_hoten_editing_finished (local) error: %s", e)

        # Attach local helpers to instance methods so they can be connected; using
        # attributes avoids defining methods at class scope and keeps them close to load flow.
        try:
            # only set if not already present to avoid double connects
            if not hasattr(self, '_on_completer_activated'):
                self._on_completer_activated = _on_completer_activated_local
            if not hasattr(self, '_on_hoten_editing_finished'):
                self._on_hoten_editing_finished = _on_hoten_editing_finished_local
        except Exception:
            pass
        """Load danh sách bệnh nhân vào combobox."""
        conn = get_connection()
        cur = conn.cursor()
        try:
                cur.execute("""
                    SELECT b.id, b.ho_ten, b.dien_thoai, b.ngay_sinh, b.so_cccd,
                        (
                            SELECT ma_hoso FROM tiep_don td WHERE td.benh_nhan_id = b.id ORDER BY td.id DESC LIMIT 1
                        ) as ma_hoso
                    FROM benh_nhan b
                    ORDER BY b.ho_ten
                """)
                rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()

        self.hoten.clear()
        # Thêm placeholder
        self.hoten.addItem("-- Chọn bệnh nhân --", None)
        display_texts = []
        for r in rows:
            pid, name, phone, dob, cccd, ma_hoso = r
            parts = []
            if phone:
                parts.append(str(phone))
            if cccd:
                parts.append(str(cccd))
            if dob:
                try:
                    parts.append(str(dob).split('-')[0])
                except Exception:
                    pass
            if ma_hoso:
                disp = f"{name} — Mã:{ma_hoso}"
            else:
                disp = f"{name} — ID:{pid}"

            if parts:
                disp += ' — ' + ' / '.join(parts)

            # add item and store benh_nhan id in itemData (UserRole)
            self.hoten.addItem(disp)
            idx = self.hoten.count() - 1
            self.hoten.setItemData(idx, pid, Qt.UserRole)
            display_texts.append(disp)

        try:
            if self.completer:
                model = QStringListModel(display_texts)
                self.completer.setModel(model)
                # Connect completer to instance handler (created above)
                try:
                    # Disconnect existing to avoid duplicate connections
                    self.completer.activated.disconnect()
                except Exception:
                    pass
                try:
                    self.completer.activated.connect(self._on_completer_activated)
                except Exception:
                    pass
        except Exception:
            pass

        # Connect editingFinished handler on combobox line edit to our instance handler
        try:
            le = self.hoten.lineEdit()
            try:
                le.editingFinished.disconnect()
            except Exception:
                pass
            try:
                le.editingFinished.connect(self._on_hoten_editing_finished)
            except Exception:
                pass
        except Exception:
            pass
        # Đặt về placeholder làm lựa chọn mặc định sau khi load để tránh trạng thái cũ
        try:
            self.hoten.setCurrentIndex(0)
        except Exception:
            pass

    def load_icd10_list(self):
        """Load danh sách mã ICD10 từ database (dùng khi khởi tạo)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT code, description FROM danh_muc_icd10 ORDER BY code")
            self.all_icd10_data = cur.fetchall()
        except Exception:
            self.all_icd10_data = []
        finally:
            conn.close()

    def refresh_and_select_patient(self, benh_nhan_id=None):
        """Reload patient list and optionally select a patient by id.

        Use this when opening the form from other parts of the app to ensure
        the combobox is up-to-date and the selection handler runs.
        """
        self.load_benh_nhan_list()
        if benh_nhan_id:
            try:
                idx = self.hoten.findData(benh_nhan_id)
                if idx is None or idx < 0:
                    # Try linear search as fallback
                    for i in range(self.hoten.count()):
                        if self.hoten.itemData(i) == benh_nhan_id:
                            idx = i
                            break
                if idx is not None and idx >= 0:
                    self.hoten.setCurrentIndex(idx)
                    # explicitly call handler to load full data
                    try:
                        self.on_select_benh_nhan(idx)
                    except Exception:
                        pass
            except Exception:
                pass

    def update_icd10_display(self):
        """Cập nhật text hiển thị của ICD10 dựa trên selected_icd10_codes."""
        if self.selected_icd10_codes:
            # Tạo display text từ selected codes
            display_parts = []
            for code in self.selected_icd10_codes:
                # Tìm description tương ứng với code
                for icd_code, icd_desc in self.all_icd10_data:
                    if icd_code == code:
                        display_parts.append(f"{code} - {icd_desc}")
                        break
                else:
                    display_parts.append(code)
            self.icd10_display.setText("; ".join(display_parts))
        else:
            self.icd10_display.clear()

    def open_icd10_dialog(self):
        """Mở dialog để chọn multiple ICD10 codes."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Chọn mã ICD10")
        # Make dialog wider so buttons and text are not clipped
        dlg.setGeometry(100, 100, 760, 560)
        dlg.setMinimumWidth(760)
        
        layout = QVBoxLayout(dlg)
        
        # Top: List widget với checkboxes
        layout.addWidget(QLabel("Danh sách mã ICD10:"))
        list_widget = QListWidget()
        for code, desc in self.all_icd10_data:
            item_text = f"{code} - {desc}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, code)  # Store code as data
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Set checked state if already selected
            if code in self.selected_icd10_codes:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        
        # Middle: Input field để thêm ICD10 mới (ẩn lúc đầu)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)
        
        input_code = QLineEdit()
        input_code.setPlaceholderText("Mã ICD10")
        input_code.setMaximumWidth(120)
        input_layout.addWidget(input_code)
        
        input_desc = QLineEdit()
        input_desc.setPlaceholderText("Mô tả")
        # Let layout control width: give the description field stretch
        # so it expands up to the OK button without fixed min/max sizes.
        input_desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_layout.addWidget(input_desc, 1)
        
        # spacer so buttons are always aligned to the right (keeps small gap)
        input_layout.addSpacing(6)

        btn_input_ok = QPushButton("OK")
        btn_input_ok.setFixedWidth(90)
        btn_input_ok.setFixedHeight(30)
        input_layout.addWidget(btn_input_ok)
        
        btn_input_cancel = QPushButton("Hủy")
        btn_input_cancel.setFixedWidth(90)
        btn_input_cancel.setFixedHeight(30)
        input_layout.addWidget(btn_input_cancel)
        
        input_widget = QWidget()
        input_widget.setLayout(input_layout)
        input_widget.setVisible(False)
        layout.addWidget(input_widget)
        
        # Buttons: Thêm, Sửa, Xóa (định nghĩa trước nhưng sẽ hiển thị trên cùng hàng với OK/Hủy)
        btn_action_layout = QHBoxLayout()
        btn_action_layout.setSpacing(5)

        def add_single_icd10():
            """Mở hàng nhập để thêm mã ICD10"""
            input_widget.setVisible(True)
            input_code.clear()
            input_desc.clear()
            input_code.setFocus()
            list_widget.setEnabled(False)
        
        def confirm_add():
            """Xác nhận thêm mã ICD10 mới"""
            code = input_code.text().strip().upper()
            desc = input_desc.text().strip()
            
            if not code:
                QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng nhập mã ICD10!")
                return
            
            if not desc:
                QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng nhập mô tả!")
                return
            
            # Kiểm tra xem mã đã tồn tại chưa
            for i in range(list_widget.count()):
                if list_widget.item(i).data(Qt.UserRole) == code:
                    QMessageBox.warning(dlg, "Cảnh báo", "Mã ICD10 đã tồn tại!")
                    return
            
            # Thêm item mới vào list
            item_text = f"{code} - {desc}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            list_widget.addItem(item)
            
            # Cập nhật vào all_icd10_data
            self.all_icd10_data.append((code, desc))
            
            # Ẩn input
            input_widget.setVisible(False)
            list_widget.setEnabled(True)
            input_code.clear()
            input_desc.clear()
        
        def cancel_add():
            """Hủy thêm mã ICD10"""
            input_widget.setVisible(False)
            list_widget.setEnabled(True)
            input_code.clear()
            input_desc.clear()
        
        btn_input_ok.clicked.connect(confirm_add)
        btn_input_cancel.clicked.connect(cancel_add)
        
        def edit_single_icd10():
            """Sửa mã ICD10 được chọn trong list"""
            selected_items = [list_widget.item(i) for i in range(list_widget.count()) 
                            if list_widget.item(i).checkState() == Qt.Checked]
            
            if not selected_items:
                QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng chọn ít nhất một mã ICD10 để sửa!")
                return
            
            if len(selected_items) > 1:
                QMessageBox.warning(dlg, "Cảnh báo", "Chỉ có thể sửa một mã ICD10 tại một lần!")
                return
            
            selected_item = selected_items[0]
            old_code = selected_item.data(Qt.UserRole)
            
            # Tìm mô tả cũ
            old_desc = ""
            for code, desc in self.all_icd10_data:
                if code == old_code:
                    old_desc = desc
                    break
            
            # Mở field nhập để sửa
            input_widget.setVisible(True)
            input_code.setText(old_code)
            input_desc.setText(old_desc)
            input_code.setFocus()
            list_widget.setEnabled(False)
            
            # Thay đổi nút Xác nhận để sửa thay vì thêm
            btn_input_ok.setText("Cập nhật")
            
            def on_edit_confirm():
                new_code = input_code.text().strip().upper()
                new_desc = input_desc.text().strip()
                
                if not new_code:
                    QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng nhập mã ICD10!")
                    return
                
                if not new_desc:
                    QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng nhập mô tả!")
                    return
                
                # Kiểm tra xem mã mới đã tồn tại chưa (trừ mã cũ)
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.data(Qt.UserRole) == new_code and item.data(Qt.UserRole) != old_code:
                        QMessageBox.warning(dlg, "Cảnh báo", "Mã ICD10 đã tồn tại!")
                        return
                
                # Cập nhật item trong list
                item_text = f"{new_code} - {new_desc}"
                selected_item.setText(item_text)
                selected_item.setData(Qt.UserRole, new_code)
                
                # Cập nhật vào all_icd10_data
                for i, (code, desc) in enumerate(self.all_icd10_data):
                    if code == old_code:
                        self.all_icd10_data[i] = (new_code, new_desc)
                        break
                
                # Ẩn input
                input_widget.setVisible(False)
                list_widget.setEnabled(True)
                input_code.clear()
                input_desc.clear()
                btn_input_ok.setText("Xác nhận")
                btn_input_ok.clicked.disconnect()
                btn_input_ok.clicked.connect(confirm_add)
            
            # Disconnect nút OK từ confirm_add
            try:
                btn_input_ok.clicked.disconnect()
            except:
                pass
            
            btn_input_ok.clicked.connect(on_edit_confirm)
        
        def delete_single_icd10():
            """Xóa mã ICD10 được chọn trong list"""
            selected_items = [list_widget.item(i) for i in range(list_widget.count()) 
                            if list_widget.item(i).checkState() == Qt.Checked]
            
            if not selected_items:
                QMessageBox.warning(dlg, "Cảnh báo", "Vui lòng chọn ít nhất một mã ICD10 để xóa!")
                return
            
            reply = QMessageBox.question(dlg, "Xác nhận", 
                                        f"Xóa {len(selected_items)} mã ICD10 được chọn?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for item in selected_items:
                    list_widget.takeItem(list_widget.row(item))
        
        btn_add = QPushButton("Thêm")
        btn_add.setFixedWidth(70)
        btn_add.setFixedHeight(30)
        btn_add.clicked.connect(add_single_icd10)
        btn_action_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("Sửa")
        btn_edit.setFixedWidth(70)
        btn_edit.setFixedHeight(30)
        btn_edit.clicked.connect(edit_single_icd10)
        btn_action_layout.addWidget(btn_edit)
        
        btn_del = QPushButton("Xóa")
        btn_del.setFixedWidth(70)
        btn_del.setFixedHeight(30)
        btn_del.clicked.connect(delete_single_icd10)
        btn_action_layout.addWidget(btn_del)
        
        btn_action_layout.addStretch()
        btn_action_layout.setContentsMargins(0, 5, 0, 5)

        # Bottom: OK và Hủy buttons + action buttons cùng hàng
        btn_layout = QHBoxLayout()
        # đặt 3 nút hành động ở bên trái
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(90)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setFixedWidth(90)
        
        def on_ok():
            self.selected_icd10_codes = []
            diagnosis_parts = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    code = item.data(Qt.UserRole)
                    self.selected_icd10_codes.append(code)
                    # Lấy description và thêm vào diagnosis_parts
                    for icd_code, icd_desc in self.all_icd10_data:
                        if icd_code == code:
                            diagnosis_parts.append(icd_desc)
                            break
            self.update_icd10_display()
            # Tự động điền trường Chẩn đoán với các mô tả, ngăn cách bằng dấu phẩy
            self.chandoan.setPlainText(", ".join(diagnosis_parts))
            dlg.accept()
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dlg.reject)
        
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dlg.exec_()


    def on_reload(self):

        """Tải lại form (reinit UI) khi code thay đổi."""
        try:
            # Lưu lại các giá trị quan trọng
            current_bn_idx = self.hoten.currentIndex()  # Updated from combo_bn to hoten
            current_date = self.ngaylap.date()
            
            # Tải lại UI
            self.setParent(None)  # Xóa widget khỏi parent
            self.__init__(parent=self.parent())  # Reinit với parent cũ
            
            # Khôi phục lại các giá trị
            if current_bn_idx >= 0:
                self.hoten.setCurrentIndex(current_bn_idx)  # Updated from combo_bn to hoten
            self.ngaylap.setDate(current_date)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải lại form: {e}")

    def mo_form_chidinh(self):
        """Mở form chỉ định dịch vụ"""
        from .chi_dinh_dich_vu import ChiDinhDichVu
        
        # Kiểm tra xem đã chọn bệnh nhân chưa
        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn bệnh nhân trước khi chỉ định dịch vụ!")
            self.tab_chidinh.setChecked(False)
            return

        try:
            # Tạo instance mới của form ChiDinhDichVu (top-level window)
            form_chidinh = ChiDinhDichVu()
            # giữ reference để không bị GC khi ra ngoài scope
            self._chi_dinh_window = form_chidinh
            form_chidinh.setWindowTitle("Chỉ định dịch vụ")
            # Chọn bệnh nhân tương ứng trong form chỉ định
            try:
                idx = form_chidinh.hoten.findData(benh_nhan_id)
            except Exception:
                idx = -1
            if idx is not None and idx >= 0:
                form_chidinh.hoten.setCurrentIndex(idx)

            # Hiển thị form như một cửa sổ riêng (non-modal) và đưa lên trước
            try:
                form_chidinh.setWindowModality(Qt.NonModal)
            except Exception:
                pass
            form_chidinh.show()
            try:
                form_chidinh.raise_()
                form_chidinh.activateWindow()
            except Exception:
                pass
            
            # Khi form đóng, reset nút về trạng thái trắng (inactive)
            try:
                def _on_chidinh_destroyed():
                    try:
                        if getattr(self, 'tab_chidinh', None):
                            self.tab_chidinh.setChecked(False)
                    except Exception:
                        pass
                form_chidinh.destroyed.connect(_on_chidinh_destroyed)
            except Exception:
                pass
            
        except Exception as e:
            logger.exception("Error in mo_form_chidinh")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở form chỉ định dịch vụ: {e}")
            self.tab_chidinh.setChecked(False)

    def mo_form_don(self):
        """Mở form Đơn điều trị và truyền phieu_kham_id (nếu có).

        Nếu phiếu khám hiện tại chưa được lưu, cố gắng lưu trước (gọi self.on_save()).
        Sau đó mở `KeDonThuoc` và truyền `phieu_kham_id` để form đơn tự load thông tin khám / chẩn đoán.
        """
        from .don_thuoc import KeDonThuoc

        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn bệnh nhân trước khi mở Đơn điều trị!")
            self.tab_don.setChecked(False)
            return

        # Nếu chưa có phieu_kham được lưu, cố gắng lưu hiện trạng
        if not self.current_phieu_kham_id:
            try:
                self.on_save()
            except Exception:
                # on_save đã hiển thị QMessageBox nếu lỗi; bỏ qua
                pass

        phieu_id = self.current_phieu_kham_id
        benh_nhan_id = self.hoten.currentData()
        try:
            form = KeDonThuoc(phieu_kham_id=phieu_id, benh_nhan_id=benh_nhan_id)
            self._don_thuoc_window = form
            try:
                form.setWindowModality(Qt.NonModal)
            except Exception:
                pass
            form.show()
            try:
                form.raise_()
                form.activateWindow()
            except Exception:
                pass
            
            # Khi form đóng, reset nút về trạng thái trắng (inactive)
            try:
                def on_form_destroyed():
                    try:
                        if self.tab_don:  # Check if button still exists
                            self.tab_don.setChecked(False)
                    except:
                        pass
                form.destroyed.connect(on_form_destroyed)
            except Exception:
                pass
        except Exception as e:
            logger.exception("Error opening DonThuoc")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Đơn điều trị: {e}")
            self.tab_don.setChecked(False)

    def mo_form_donbosung(self):
        """Mở form Đơn bổ sung (mở KeDonThuoc như một đơn bổ sung)."""
        from .don_thuoc import KeDonThuoc

        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn bệnh nhân trước khi mở Đơn bổ sung!")
            self.tab_donbosung.setChecked(False)
            return

        # If there is no current phieu_kham, try to save current form first
        if not self.current_phieu_kham_id:
            try:
                self.on_save()
            except Exception:
                pass

        phieu_id = self.current_phieu_kham_id
        try:
            # Defer the creation/showing of the supplemental form to the next
            # event loop iteration to avoid potential layout parenting races
            # that can cause Qt warnings/errors when creating complex widgets.
            from .don_thuoc_bo_sung import DonThuocKhac
            def _create_and_show():
                try:
                    form = DonThuocKhac(phieu_kham_id=phieu_id, benh_nhan_id=benh_nhan_id)
                    self._don_bosung_window = form
                    try:
                        form.setWindowModality(Qt.NonModal)
                    except Exception:
                        pass
                    form.show()
                    try:
                        form.raise_()
                        form.activateWindow()
                    except Exception:
                        pass

                    # reset button when form closes
                    def reset_tab():
                        try:
                            if self.tab_donbosung and not self.tab_donbosung.isBeingDeleted():
                                self.tab_donbosung.setChecked(False)
                        except:
                            pass

                    try:
                        form.destroyed.connect(reset_tab)
                    except Exception:
                        pass
                except Exception as ex:
                    logger.exception("Error creating DonThuocKhac deferred")
                    QMessageBox.critical(self, "Lỗi", f"Không thể mở Đơn bổ sung: {ex}")
                    try:
                        self.tab_donbosung.setChecked(False)
                    except Exception:
                        pass

            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, _create_and_show)
        except Exception as e:
            logger.exception("Error scheduling DonBosung creation")
            QMessageBox.critical(self, "Lỗi", f"Không thể mở Đơn bổ sung: {e}")
            try:
                self.tab_donbosung.setChecked(False)
            except Exception:
                pass
            