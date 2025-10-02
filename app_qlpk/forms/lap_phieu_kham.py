#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDateEdit,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QToolButton, QSpinBox, QSizePolicy, QFrame, QStyle,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QDialogButtonBox, QCompleter
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QStringListModel
from PyQt5.QtGui import QFont
import sys

# ----------------------------------------------------------------------
## DỮ LIỆU ICD-10 (Trích xuất từ tài liệu kèm theo)
# ----------------------------------------------------------------------
ICD10_DATA = [
    ("A15-A19", "Bệnh lao (trừ A15)"),
    ("A30", "Bệnh phong (bệnh Hansen)"),
    ("B18.0", "Viêm gan virus B mạn, có đồng nhiễm virus D"),
    ("B18.1", "Viêm gan virus B mạn, không có đồng nhiễm virus D"),
    ("B18.2", "Viêm gan virus C mạn tính"),
    ("J00", "Viêm mũi họng cấp (Cảm lạnh thông thường)"),
    ("J10", "Cúm do virus cúm được xác định"),
    ("R82", "Các phát hiện bất thường khác về nước tiêu"),
    ("Z49.1", "Lọc máu ngoài cơ thể (thận nhân tạo)"),
]

# ----------------------------------------------------------------------
## I. CLASS HỖ TRỢ 1 (Dialog Tìm kiếm ICD-10)
# ----------------------------------------------------------------------
class ICD10SearchDialog(QDialog):
    """Dialog cho phép tìm kiếm và chọn mã ICD-10."""
    
    icd10_selected = pyqtSignal(str)
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm ICD-10")
        self.resize(600, 500)
        self.data = data
        
        self.init_ui()
        self.load_data(self.data)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. Ô tìm kiếm
        search_layout = QHBoxLayout()
        search_label = QLabel("Tìm kiếm:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập mã hoặc tên bệnh...")
        self.search_input.textChanged.connect(self.filter_data)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        
        # 2. Bảng hiển thị kết quả
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Mã ICD-10", "Tên bệnh/Nhóm bệnh"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("Tahoma", 9))
        
        self.table.doubleClicked.connect(self.accept_selection)
        main_layout.addWidget(self.table)
        
        # 3. Nút bấm
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_selection)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_data(self, data_list):
        """Đổ dữ liệu ICD-10 vào bảng."""
        self.table.setRowCount(len(data_list))
        for row, (code, name) in enumerate(data_list):
            self.table.setItem(row, 0, QTableWidgetItem(code))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.item(row, 0).setTextAlignment(Qt.AlignCenter)
            
    def filter_data(self, text):
        """Lọc dữ liệu dựa trên từ khóa tìm kiếm."""
        search_term = text.strip().lower()
        filtered_data = []
        if search_term:
            for code, name in self.data:
                if search_term in code.lower() or search_term in name.lower():
                    filtered_data.append((code, name))
        else:
            filtered_data = self.data
            
        self.load_data(filtered_data)
        
    def accept_selection(self):
        """Xử lý chọn hàng và phát tín hiệu."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            code = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            full_text = f"{code} - {name}"
            
            self.icd10_selected.emit(full_text)
            self.accept()
        else:
            self.reject()


# ----------------------------------------------------------------------
## II. LỚP CHÍNH (LapPhieuKham)
# ----------------------------------------------------------------------
class LapPhieuKham(QWidget):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lập phiếu khám")
        self.resize(1100, 780) 
        self.setFont(QFont("Tahoma", 10))
        
        # Vitals
        self.edit_nhiptim = QLineEdit()
        self.edit_huyetap = QLineEdit()
        self.edit_nhietdo = QLineEdit()
        self.edit_nhiptho = QLineEdit()
        self.edit_chieucao = QLineEdit()
        self.edit_cannang = QLineEdit()
        
        # Khám lâm sàng
        self.text_khamlam = QTextEdit()
        self.text_benkem = QTextEdit()
        self.combo_icd10 = QComboBox()
        self.text_chandoan = QTextEdit()
        self.text_ketluan = QTextEdit()
        
        # Tiền sử, Dị ứng
        self.text_cls = QTextEdit()
        self.text_diungthuoc = QTextEdit()
        self.text_tiensubn = QTextEdit()
        self.text_tiensugd = QTextEdit()
        
        # Hẹn khám
        self.date_kinhcuoi = QDateEdit()
        self.date_dukien = QDateEdit()
        self.edit_tuoitthai = QLineEdit()
        self.edit_hen = QLineEdit()
        self.spin_sau = QSpinBox()
        self.date_hen = QDateEdit()
        
        # Thông tin hành chính
        self.date_ngaykham = QDateEdit(QDate.currentDate())
        self.edit_sohoso = QLineEdit("0")
        self.date_ngaysinh = QDateEdit()
        self.combo_loaikham = QComboBox()
        self.combo_benhnhan = QComboBox() # Sẽ dùng Completer
        self.combo_gioitinh = QComboBox()
        self.spin_tienkham = QSpinBox()
        self.edit_diachi = QLineEdit()
        self.edit_dienthoai = QLineEdit()
        self.combo_phong = QComboBox()
        self.edit_nghenghiep = QLineEdit()
        self.combo_dantoc = QComboBox()
        self.combo_tinhtrang = QComboBox()
        self.spin_bacsi = QSpinBox()
        self.text_lydo = QTextEdit()

        self.icd10_dialog = None
        self.completer_bn = QCompleter() # Thêm completer cho Bệnh nhân
        
        self.init_ui()
        self.load_benh_nhan_list() # Giả lập load danh sách BN

    # Giả lập hàm load bệnh nhân tương tự tiep_don_kham.py
    def load_benh_nhan_list(self):
        # Giả lập dữ liệu bệnh nhân (ID, Tên)
        data = [
            (101, "NGUYỄN THỊ THUÝ HIỀN"),
            (102, "NGUYỄN VĂN A"),
            (103, "TRẦN VĂN B"),
            (104, "LÊ THỊ C"),
        ]
        
        names = [name for id, name in data]
        
        self.combo_benhnhan.blockSignals(True)
        self.combo_benhnhan.clear()
        
        # Thêm các item với UserData là ID
        for bid, name in data:
            self.combo_benhnhan.addItem(name, bid)
        
        # Thiết lập Completer
        model = QStringListModel(names)
        self.completer_bn.setModel(model)
        self.combo_benhnhan.setCompleter(self.completer_bn)
        self.combo_benhnhan.setEditable(True)
        self.combo_benhnhan.setCurrentIndex(-1)
        self.combo_benhnhan.setPlaceholderText("--Chọn hoặc gõ tên bệnh nhân--")
        
        self.combo_benhnhan.blockSignals(False)

    def show_icd10_dialog(self):
        """Hiển thị cửa sổ chọn ICD-10."""
        if self.icd10_dialog is None:
            self.icd10_dialog = ICD10SearchDialog(ICD10_DATA, self)
            self.icd10_dialog.icd10_selected.connect(self.update_icd10_combo)
        self.icd10_dialog.exec_()

    def update_icd10_combo(self, icd10_full_text):
        """Cập nhật QComboBox ICD-10 với mã/tên đã chọn."""
        self.combo_icd10.setEditText(icd10_full_text)

    def _create_vitals_input(self, label_text, line_edit, unit_text):
        """Hàm trợ giúp tạo một nhóm nhập liệu (Label - Input - Unit) cho Dấu hiệu sinh tồn."""
        hbox = QHBoxLayout()
        hbox.setSpacing(4)
        hbox.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setFixedWidth(60)
        
        hbox.addWidget(label)
        line_edit.setFixedWidth(50) 
        line_edit.setAlignment(Qt.AlignCenter)
        hbox.addWidget(line_edit)
        hbox.addWidget(QLabel(unit_text))
        hbox.addStretch()
        return hbox
    
    def update_followup_date(self):
        """Tính ngày hẹn = ngày khám + số ngày (spin_sau) và cập nhật date_hen."""
        try:
            days = int(self.spin_sau.value())
        except Exception:
            days = 0
        base_date = self.date_ngaykham.date() if hasattr(self, "date_ngaykham") else QDate.currentDate()
        follow_date = base_date.addDays(days)
        if hasattr(self, "date_hen"):
            self.date_hen.setDate(follow_date)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(6,6,6,6)

        style = QApplication.style()

        # 1. Thanh Công Cụ (Toolbar)
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbar_frame")
        toolbar_frame.setStyleSheet("""
            QFrame#toolbar_frame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #f0f3f7, stop:1 #dde3ea);
                border: 1px solid #c8d0d8;
                padding: 4px;
            }
            QToolButton {
                border: none;
                padding: 6px 10px;
                margin-right: 4px;
                border-radius: 4px;
            }
            QToolButton:hover { background: rgba(0,0,0,0.04); }
            QToolButton:pressed { background: rgba(0,0,0,0.08); }
            QComboBox {
                min-width: 220px;
                max-width: 420px;
                padding: 4px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(6, 4, 6, 4)
        toolbar_layout.setSpacing(6)

        def make_tb(std_icon, text, tooltip=None):
            tb = QToolButton()
            icon = style.standardIcon(std_icon)
            tb.setIcon(icon)
            tb.setText(text)
            tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tb.setAutoRaise(True)
            if tooltip:
                tb.setToolTip(tooltip)
            tb.setMinimumHeight(30)
            tb.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            return tb

        btn_them = make_tb(QStyle.SP_DialogApplyButton, "Thêm mới")
        btn_boqua = make_tb(QStyle.SP_DialogCancelButton, "Bỏ qua")
        btn_xoa = make_tb(QStyle.SP_TrashIcon if hasattr(QStyle, "SP_TrashIcon") else QStyle.SP_DialogCloseButton,
                              "Xóa")
        btn_khamxong = make_tb(QStyle.SP_DialogApplyButton, "Khám xong")
        btn_ls = make_tb(QStyle.SP_FileDialogContentsView, "Lịch sử khám")
        btn_in = make_tb(QStyle.SP_FileDialogDetailedView, "In phiếu")

        for w in (btn_them, btn_boqua, btn_xoa, btn_khamxong, btn_ls, btn_in):
            toolbar_layout.addWidget(w)

        toolbar_layout.addStretch()

        combo_phieukham = QComboBox()
        combo_phieukham.setEditable(True)
        combo_phieukham.setMinimumWidth(240)
        combo_phieukham.addItems(["Phiếu khám", "Phiếu tái khám", "Phiếu xét nghiệm", "Bệnh án ngoại trú - tờ 1", "Bệnh án ngoại trú - tờ 2", "Tờ điều trị"])
        combo_phieukham.setCurrentIndex(0)
        toolbar_layout.addWidget(combo_phieukham)

        main_layout.addWidget(toolbar_frame)
        
        # 2. THÔNG TIN HÀNH CHÍNH (Simplified GroupBox)
        thong_tin_hanh_chinh_group = QGroupBox("THÔNG TIN HÀNH CHÍNH")
        thong_tin_hanh_chinh_group.setStyleSheet("QGroupBox{font-weight:bold; color: #1e88e5;}")
        group_v_layout = QVBoxLayout(thong_tin_hanh_chinh_group)
        group_v_layout.setContentsMargins(10, 20, 10, 10)
        
        form_layout_bn = QGridLayout() 
        form_layout_bn.setHorizontalSpacing(10)
        form_layout_bn.setVerticalSpacing(6)

        def req_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: black;")
            return lbl
            
        # Cấu hình các control
        self.date_ngaykham.setDisplayFormat("dd/MM/yyyy")
        self.date_ngaykham.setCalendarPopup(True)
        self.date_ngaykham.setFixedWidth(140)
        self.edit_sohoso.setFixedWidth(100)
        self.date_ngaysinh.setDisplayFormat("dd/MM/yyyy")
        self.date_ngaysinh.setCalendarPopup(True)
        self.date_ngaysinh.setFixedWidth(100)
        self.combo_loaikham.addItems(["--Chọn loại khám--", "Khám thông thường", "Khám chuyên khoa"])
        self.combo_loaikham.setMinimumWidth(150)
        self.combo_benhnhan.setMinimumWidth(250)
        self.combo_gioitinh.addItems(["--Chọn giới tính--", "Nam", "Nữ", "Khác"])
        self.combo_gioitinh.setFixedWidth(120)
        self.spin_tienkham.setRange(0, 100000000)
        self.spin_tienkham.setPrefix("0") 
        self.spin_tienkham.setFixedWidth(150)
        self.edit_dienthoai.setFixedWidth(120)
        self.combo_phong.addItems(["P1", "P2", "P3"])
        self.combo_phong.setCurrentText("P1")
        self.combo_phong.setFixedWidth(150)
        self.combo_dantoc.addItems(["Kinh", "Tày", "Thái", "Mường"])
        self.combo_dantoc.setFixedWidth(120)
        self.combo_tinhtrang.addItems(["BT", "NG", "Nặng"])
        self.combo_tinhtrang.setCurrentText("BT")
        self.combo_tinhtrang.setFixedWidth(120)
        self.spin_bacsi.setRange(1, 99)
        self.spin_bacsi.setValue(17)
        self.spin_bacsi.setFixedWidth(150)
        self.text_lydo.setFixedHeight(50) # Giảm chiều cao

        # Sắp xếp Layout Grid HÀNH CHÍNH
        
        # Hàng 0
        form_layout_bn.addWidget(req_label("Ngày khám:"), 0, 0)
        form_layout_bn.addWidget(self.date_ngaykham, 0, 1)
        form_layout_bn.addWidget(req_label("Số hồ sơ:"), 0, 2)
        form_layout_bn.addWidget(self.edit_sohoso, 0, 3)
        form_layout_bn.addWidget(req_label("Ngày sinh:"), 0, 4)
        form_layout_bn.addWidget(self.date_ngaysinh, 0, 5)
        form_layout_bn.addWidget(req_label("Loại khám:"), 0, 6)
        form_layout_bn.addWidget(self.combo_loaikham, 0, 7) # Bỏ dấu * phức tạp

        # Hàng 1 (THÔNG TIN BỆNH NHÂN)
        form_layout_bn.addWidget(req_label("Bệnh nhân:"), 1, 0)
        form_layout_bn.addWidget(self.combo_benhnhan, 1, 1, 1, 3) 

        form_layout_bn.addWidget(req_label("Giới tính:"), 1, 4)
        form_layout_bn.addWidget(self.combo_gioitinh, 1, 5)
        form_layout_bn.addWidget(req_label("Tiền khám:"), 1, 6)
        form_layout_bn.addWidget(self.spin_tienkham, 1, 7)

        # Hàng 2 (Địa chỉ, Điện thoại, Phòng khám)
        form_layout_bn.addWidget(req_label("Địa chỉ:"), 2, 0)
        form_layout_bn.addWidget(self.edit_diachi, 2, 1, 1, 3) 

        form_layout_bn.addWidget(req_label("Điện thoại:"), 2, 4)
        form_layout_bn.addWidget(self.edit_dienthoai, 2, 5)
        form_layout_bn.addWidget(req_label("Phòng khám:"), 2, 6)
        form_layout_bn.addWidget(self.combo_phong, 2, 7)

        # Hàng 3 (Nghề nghiệp, Dân tộc, Tình trạng BN, Bác sĩ Khám)
        form_layout_bn.addWidget(req_label("Nghề nghiệp:"), 3, 0)
        form_layout_bn.addWidget(self.edit_nghenghiep, 3, 1)

        form_layout_bn.addWidget(req_label("Dân tộc:"), 3, 2)
        form_layout_bn.addWidget(self.combo_dantoc, 3, 3)

        form_layout_bn.addWidget(req_label("Tình trạng BN:"), 3, 4)
        form_layout_bn.addWidget(self.combo_tinhtrang, 3, 5)

        form_layout_bn.addWidget(req_label("Bác sĩ Khám:"), 3, 6)
        form_layout_bn.addWidget(self.spin_bacsi, 3, 7)

        # Hàng 4 (Ghi chú / Lý do khám)
        form_layout_bn.addWidget(req_label("Ghi chú / lý do khám:"), 4, 0)
        form_layout_bn.addWidget(self.text_lydo, 4, 1, 1, 7) 
            
        group_v_layout.addLayout(form_layout_bn)
        main_layout.addWidget(thong_tin_hanh_chinh_group)
        
        # 3. KẾT QUẢ KHÁM (Splitter layout)
        mid_group = QGroupBox("KẾT QUẢ KHÁM")
        mid_group.setStyleSheet("QGroupBox{font-weight:bold; color: #d32f2f;}")
        mid_layout = QHBoxLayout(mid_group)
        mid_layout.setContentsMargins(10, 20, 10, 10)

        # --- Cột trái: Khám lâm sàng, Bệnh, Chẩn đoán, Kết luận ---
        left_col_widget = QWidget()
        left_col_layout = QGridLayout(left_col_widget)
        left_col_layout.setSpacing(6)
        left_col_layout.setContentsMargins(0,0,0,0)
        
        self.text_khamlam.setFixedHeight(80)
        left_col_layout.addWidget(QLabel("Khám lâm sàng:"), 0, 0, 1, 2)
        left_col_layout.addWidget(self.text_khamlam, 1, 0, 1, 2)

        self.text_benkem.setFixedHeight(50)
        left_col_layout.addWidget(QLabel("Bệnh kèm theo:"), 2, 0, 1, 2)
        left_col_layout.addWidget(self.text_benkem, 3, 0, 1, 2)
        
        # Bệnh theo ICD10 (Combo + Button)
        self.combo_icd10.setEditable(True)
        self.combo_icd10.addItem("--Chọn ICD10--")
        
        self.btn_icd10 = QPushButton("Chọn ICD10")
        self.btn_icd10.setStyleSheet("QPushButton{color:#1e88e5; text-decoration:underline; border: none; padding: 0; text-align: left;}")
        self.btn_icd10.clicked.connect(self.show_icd10_dialog)
        
        left_col_layout.addWidget(QLabel("Bệnh theo ICD10:"), 4, 0)
        left_col_layout.addWidget(self.combo_icd10, 5, 0)
        left_col_layout.addWidget(self.btn_icd10, 5, 1, alignment=Qt.AlignLeft)

        self.text_chandoan.setFixedHeight(50)
        left_col_layout.addWidget(QLabel("Chẩn đoán bệnh:"), 6, 0, 1, 2)
        left_col_layout.addWidget(self.text_chandoan, 7, 0, 1, 2)

        self.text_ketluan.setFixedHeight(80)
        left_col_layout.addWidget(QLabel("Kết luận & hướng điều trị:"), 8, 0, 1, 2)
        left_col_layout.addWidget(self.text_ketluan, 9, 0, 1, 2)
        
        # --- Cột phải: Dấu hiệu sinh tồn, CLS, Tiền sử, Dị ứng ---
        right_col_widget = QWidget()
        right_col_layout = QGridLayout(right_col_widget)
        right_col_layout.setSpacing(6)
        right_col_layout.setContentsMargins(0,0,0,0)
        
        # A. Vitals (Dấu hiệu sinh tồn)
        vitals_group = QGroupBox("Dấu hiệu sinh tồn")
        vitals_grid = QGridLayout(vitals_group)
        vitals_grid.setHorizontalSpacing(10)
        vitals_grid.setVerticalSpacing(4)
        vitals_grid.addLayout(self._create_vitals_input("Nhịp tim:", self.edit_nhiptim, "nhịp/phút"), 0, 0)
        vitals_grid.addLayout(self._create_vitals_input("Huyết áp:", self.edit_huyetap, "mmHg"), 0, 1)
        vitals_grid.addLayout(self._create_vitals_input("Nhiệt độ:", self.edit_nhietdo, "độ C"), 1, 0)
        vitals_grid.addLayout(self._create_vitals_input("Nhịp thở:", self.edit_nhiptho, "nhịp/phút"), 1, 1)
        vitals_grid.addLayout(self._create_vitals_input("Chiều cao:", self.edit_chieucao, "cm"), 2, 0)
        vitals_grid.addLayout(self._create_vitals_input("Cân nặng:", self.edit_cannang, "kg"), 2, 1)
        right_col_layout.addWidget(vitals_group, 0, 0, 1, 2)

        # B. Kết quả CLS 
        self.text_cls.setFixedHeight(50)
        right_col_layout.addWidget(QLabel("Kết quả CLS:"), 1, 0, 1, 2)
        right_col_layout.addWidget(self.text_cls, 2, 0, 1, 2)

        # C. Dị ứng thuốc
        self.text_diungthuoc.setFixedHeight(50)
        right_col_layout.addWidget(QLabel("Dị ứng thuốc:"), 3, 0, 1, 2)
        right_col_layout.addWidget(self.text_diungthuoc, 4, 0, 1, 2)

        # D. Tiền sử bản thân
        self.text_tiensubn.setFixedHeight(50)
        right_col_layout.addWidget(QLabel("Tiền sử bản thân:"), 5, 0, 1, 2)
        right_col_layout.addWidget(self.text_tiensubn, 6, 0, 1, 2)

        # E. Tiền sử gia đình
        self.text_tiensugd.setFixedHeight(50)
        right_col_layout.addWidget(QLabel("Tiền sử gia đình:"), 7, 0, 1, 2)
        right_col_layout.addWidget(self.text_tiensugd, 8, 0, 1, 2)
        
        mid_layout.addWidget(left_col_widget, 1)
        mid_layout.addWidget(right_col_widget, 1)
        main_layout.addWidget(mid_group)

        # 4. Phần Dưới (Tuổi thai, Hẹn khám lại, Tài liệu đính kèm)
        lower_group = QGroupBox("THÔNG TIN KHÁC")
        lower_layout = QGridLayout()
        lower_layout.setHorizontalSpacing(8)
        lower_layout.setVerticalSpacing(8)
        lower_group.setLayout(lower_layout)

        # Ngày kinh cuối, Dự kiến sinh, Tuổi thai
        self.date_kinhcuoi.setDisplayFormat("dd/MM/yyyy")
        self.date_dukien.setDisplayFormat("dd/MM/yyyy")
        lower_layout.addWidget(QLabel("Ngày kinh cuối:"), 0, 0)
        lower_layout.addWidget(self.date_kinhcuoi, 0, 1)
        lower_layout.addWidget(QLabel("Dự kiến sinh:"), 0, 2)
        lower_layout.addWidget(self.date_dukien, 0, 3)
        lower_layout.addWidget(QLabel("Tuổi thai:"), 0, 4)
        self.edit_tuoitthai.setFixedWidth(100)
        lower_layout.addWidget(self.edit_tuoitthai, 0, 5)
        lower_layout.setColumnStretch(6, 1) # Cho cột cuối giãn ra

        # Hẹn khám lại
        self.spin_sau.setRange(0,365)
        self.spin_sau.setFixedWidth(50)
        self.date_hen.setDisplayFormat("dd/MM/yyyy")
        self.date_hen.setCalendarPopup(True)
        self.date_hen.setFixedWidth(120)
        
        lower_layout.addWidget(QLabel("Hẹn tái khám:"), 1, 0)
        lower_layout.addWidget(self.edit_hen, 1, 1)
        lower_layout.addWidget(QLabel("Sau (ngày):"), 1, 2)
        lower_layout.addWidget(self.spin_sau, 1, 3)
        lower_layout.addWidget(QLabel("Ngày hẹn tái khám:"), 1, 4)
        lower_layout.addWidget(self.date_hen, 1, 5)

        # Tài liệu đính kèm (Placeholder)
        frame_attach = QFrame()
        frame_attach.setFrameShape(QFrame.StyledPanel)
        frame_attach.setMinimumHeight(40) # Giảm chiều cao
        attach_layout = QHBoxLayout(frame_attach)
        attach_layout.addWidget(QLabel("[ CHỌN DOCUMENT ]"))
        attach_layout.addStretch()
        lower_layout.addWidget(QLabel("Tài liệu đính kèm:"), 2, 0)
        lower_layout.addWidget(frame_attach, 2, 1, 1, 5)

        main_layout.addWidget(lower_group)
        main_layout.addStretch() # Đẩy mọi thứ lên trên

        # Kết nối sự kiện hẹn khám
        self.spin_sau.valueChanged.connect(self.update_followup_date)
        self.date_ngaykham.dateChanged.connect(self.update_followup_date)
        self.update_followup_date()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Tahoma", 10)) 
    w = LapPhieuKham()
    w.show()
    sys.exit(app.exec_())