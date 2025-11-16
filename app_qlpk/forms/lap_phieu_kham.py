#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QDateEdit,
    QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QToolButton, QSpinBox, QSizePolicy, QFrame, QStyle,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QDialogButtonBox, QCompleter, QMessageBox,
    QScrollArea, QShortcut  # ## NÂNG CẤP: Thêm QScrollArea
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QStringListModel
from PyQt5.QtGui import QFont, QKeySequence
import sys
import locale

# ----------------------------------------------------------------------
## I. CÀI ĐẶT CHUNG & STYLESHEET
# ----------------------------------------------------------------------

# Thiết lập locale
try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
except locale.Error:
    print("Locale 'vi_VN.UTF-8' không được hỗ trợ, dùng locale mặc định.")

# ----------------------------------------------------------------------
## DỮ LIỆU ICD-10 (ĐÃ MỞ RỘNG)
# ----------------------------------------------------------------------
ICD10_DATA = [
    # Bệnh nhiễm trùng và ký sinh trùng (A00-B99)
    ("A09", "Tiêu chảy và viêm dạ dày-ruột do nhiễm trùng"),
    ("A15", "Bệnh lao đường hô hấp"),
    ("A30", "Bệnh phong (bệnh Hansen)"),
    ("B18.1", "Viêm gan virus B mạn, không có đồng nhiễm virus D"),
    ("B18.2", "Viêm gan virus C mạn tính"),
    ("B20", "Bệnh do nhiễm virus gây suy giảm miễn dịch (HIV) dẫn đến bệnh nhiễm trùng"),
    ("B34.2", "Nhiễm Coronavirus, vị trí không xác định (Bao gồm COVID-19)"),

    # U (C00-D48)
    ("C18", "U ác của đại tràng"),
    ("C34", "U ác của phế quản và phổi"),
    ("C50", "U ác của vú"),
    ("D12", "U lành của đại tràng, trực tràng, hậu môn và ống hậu môn"),
    ("D25", "U cơ trơn lành tính của tử cung (U xơ tử cung)"),

    # Rối loạn nội tiết, dinh dưỡng (E00-E90)
    ("E05", "Nhiễm độc giáp (Cường giáp)"),
    ("E10", "Đái tháo đường type 1"),
    ("E11", "Đái tháo đường type 2"),
    ("E66", "Béo phì"),
    ("E78", "Rối loạn chuyển hóa lipoprotein (Mỡ máu cao)"),

    # Rối loạn tâm thần (F00-F99)
    ("F10", "Rối loạn tâm thần và hành vi do sử dụng rượu"),
    ("F20", "Tâm thần phân liệt"),
    ("F32", "Giai đoạn trầm cảm"),
    ("F41", "Rối loạn lo âu khác"),

    # Rối loạn thần kinh (G00-G99)
    ("G40", "Động kinh"),
    ("G43", "Migraine (Đau nửa đầu)"),
    ("G47.0", "Rối loạn bắt đầu và duy trì giấc ngủ (Mất ngủ)"),
    ("G62.9", "Viêm đa dây thần kinh, không xác định"),

    # Rối loạn mắt (H00-H59)
    ("H25", "Đục thủy tinh thể do tuổi già (Cườm khô)"),
    ("H40", "Glôcôm (Cườm nước)"),
    ("H52.1", "Cận thị"),

    # Rối loạn hệ tuần hoàn (I00-I99)
    ("I10", "Tăng huyết áp vô căn (nguyên phát)"),
    ("I20", "Đau thắt ngực"),
    ("I21", "Nhồi máu cơ tim cấp"),
    ("I25", "Bệnh tim thiếu máu cục bộ mạn"),
    ("I50", "Suy tim"),
    ("I63", "Nhồi máu não"),

    # Rối loạn hệ hô hấp (J00-J99)
    ("J00", "Viêm mũi họng cấp (Cảm lạnh thông thường)"),
    ("J03", "Viêm amidan cấp"),
    ("J10", "Cúm do virus cúm được xác định"),
    ("J18", "Viêm phổi, không xác định rõ sinh vật"),
    ("J44", "Bệnh phổi tắc nghẽn mạn tính khác"),
    ("J45", "Hen phế quản"),

    # Rối loạn hệ tiêu hóa (K00-K93)
    ("K21", "Bệnh trào ngược dạ dày - thực quản (GERD)"),
    ("K25", "Loét dạ dày"),
    ("K29.7", "Viêm dạ dày, không xác định (Đau dạ dày)"),
    ("K59.0", "Táo bón"),
    ("K80", "Sỏi túi mật"),

    # Rối loạn da (L00-L99)
    ("L20", "Viêm da cơ địa (Chàm)"),
    ("L40", "Vẩy nến"),
    ("L70", "Mụn trứng cá"),

    # Rối loạn cơ xương khớp (M00-M99)
    ("M10", "Bệnh Gút (Gout)"),
    ("M16", "Thoái hóa khớp háng"),
    ("M17", "Thoái hóa khớp gối"),
    ("M54.5", "Đau thắt lưng"),
    ("M79.7", "Đau cơ xơ hóa (Fibromyalgia)"),
    ("M81", "Loãng xương không có gãy xương bệnh lý"),

    # Rối loạn hệ sinh dục, tiết niệu (N00-N99)
    ("N18", "Suy thận mạn"),
    ("N20", "Sỏi thận và niệu quản"),
    ("N40", "Tăng sản lành tính tuyến tiền liệt"),

    # Mang thai, sinh đẻ (O00-O99)
    ("O80", "Sinh đẻ một con, ngôi chỏm, không có tai biến"),

    # Triệu chứng, dấu hiệu (R00-R99)
    ("R05", "Ho"),
    ("R06.0", "Khó thở"),
    ("R07.4", "Đau ngực, không xác định"),
    ("R10", "Đau bụng và đau vùng chậu"),
    ("R42", "Chóng mặt và hoa mắt"),
    ("R50.9", "Sốt, không rõ nguyên nhân"),
    ("R51", "Đau đầu"),

    # Chấn thương, ngộ độc (S00-T98)
    ("S52", "Gãy xương cẳng tay"),
    ("S72", "Gãy xương đùi"),

    # Yếu tố liên quan sức khỏe (Z00-Z99)
    ("Z00", "Khám sức khỏe tổng quát"),
    ("Z03", "Theo dõi và đánh giá y tế các trường hợp nghi ngờ bệnh"),
    ("Z34", "Giám sát thai nghén bình thường"),
    ("Z38", "Trẻ sơ sinh (sinh thường)"),
    ("Z49.1", "Lọc máu ngoài cơ thể (thận nhân tạo)"),
    ("Z51.1", "Hóa trị liệu cho khối u"),
    ("Z71", "Tiếp xúc dịch vụ y tế vì mục đích tư vấn khác"),
]

# STYLESHEET (Làm đẹp)
APP_STYLESHEET = """
QWidget {
    font-family: "Tahoma", Arial, sans-serif;
    font-size: 10pt;
}
/* Toolbar trên cùng */
#TopToolbar {
    background-color: #f0f3f7;
    border-bottom: 1px solid #c8d0d8;
    padding: 2px;
}
#TopToolbar QToolButton {
    border: none;
    padding: 6px 10px;
    margin-right: 4px;
    border-radius: 4px;
    font-weight: bold;
}
#TopToolbar QToolButton:hover { background: rgba(0,0,0,0.04); }
#TopToolbar QToolButton:pressed { background: rgba(0,0,0,0.08); }

/* Các GroupBox */
QGroupBox { 
    font-weight: bold; 
    color: #1e88e5; /* Màu tiêu đề chính */
    margin-top: 10px;
    border: 1px solid #c8d0d8;
    border-radius: 5px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px 0 5px;
    left: 10px;
    background-color: #f0f4f8;
    border: 1px solid #c8d0d8;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
#KetQuaKhamGroup { color: #d32f2f; }
#ThongTinKhacGroup { color: #00695c; }

/* Các ô nhập liệu */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QTextEdit {
    padding: 4px 6px;
    border: 1px solid #c8d0d8;
    border-radius: 4px;
    background-color: white;
}
/* BỎ ReadOnly */
/*
QLineEdit:read-only, QTextEdit:read-only, QComboBox:disabled {
    background-color: #f0f0f0;
}
*/
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #1e88e5;
}
/* Nút chọn ICD10 */
#BtnChonICD {
    color: #1e88e5; 
    text-decoration: underline; 
    border: none; 
    padding: 0; 
    text-align: left;
    font-weight: bold;
}
/* Vùng cuộn */
QScrollArea {
    border: none;
}
#scrollAreaContent {
    background-color: white; /* Đặt nền trắng cho nội dung cuộn */
}
"""


# ----------------------------------------------------------------------
## II. CLASS HỖ TRỢ 1 (Dialog Tìm kiếm ICD-10)
# ----------------------------------------------------------------------
class ICD10SearchDialog(QDialog):
    """Dialog cho phép tìm kiếm và chọn mã ICD-10."""

    icd10_selected = pyqtSignal(str)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm ICD-10 (Đã mở rộng)")
        self.resize(700, 500)
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
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

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
## III. LỚP CHÍNH (LapPhieuKham)
# ----------------------------------------------------------------------
class LapPhieuKham(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lập phiếu khám")
        self.resize(1100, 780)
        self.setFont(QFont("Tahoma", 10))

        self.icd10_dialog = None
        self.benh_nhan_data_store = {}

        # Khởi tạo UI
        self.init_ui()

        # Tải dữ liệu giả lập
        self.load_benh_nhan_list()

        # Kết nối sự kiện
        self._connect_events()
        self.update_followup_date()

        # Bắt đầu ở chế độ "Thêm mới" (luôn cho phép nhập)
        self._handle_them_moi()

    # ----------------------------------
    # KHỞI TẠO GIAO DIỆN
    # ----------------------------------

    def init_ui(self):
        # ## NÂNG CẤP: Thêm QScrollArea
        # Layout chính của cửa sổ
        window_layout = QVBoxLayout(self)
        window_layout.setSpacing(0)
        window_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Thanh Công Cụ (Toolbar) - Cố định
        window_layout.addWidget(self._create_toolbar())

        # 2. Vùng Cuộn
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        window_layout.addWidget(scroll_area)  # Vùng cuộn chiếm phần còn lại

        # 3. Widget Nội dung (Nằm BÊN TRONG vùng cuộn)
        content_widget = QWidget()
        content_widget.setObjectName("scrollAreaContent")  # ID cho CSS
        scroll_area.setWidget(content_widget)

        # 4. Layout cho Nội dung
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # 5. Thêm các GroupBox vào layout NỘI DUNG
        main_layout.addWidget(self._create_hanh_chinh_group())
        main_layout.addWidget(self._create_ket_qua_kham_group())
        main_layout.addWidget(self._create_thong_tin_khac_group())
        main_layout.addStretch()  # Đẩy mọi thứ lên trên

        # Đặt style tổng
        self.setStyleSheet(APP_STYLESHEET)

    def _create_toolbar(self):
        """Tạo thanh công cụ trên cùng."""
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("TopToolbar")

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(6, 4, 6, 4)
        toolbar_layout.setSpacing(6)
        style = QApplication.style()

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

        self.btn_them = make_tb(QStyle.SP_FileIcon, "Thêm mới", "Tạo phiếu khám mới (F1)")
        self.btn_boqua = make_tb(QStyle.SP_DialogCancelButton, "Bỏ qua", "Hủy thay đổi (Esc)")
        self.btn_xoa = make_tb(QStyle.SP_TrashIcon, "Xóa", "Xóa phiếu khám (Ctrl+D)")
        self.btn_khamxong = make_tb(QStyle.SP_DialogApplyButton, "Khám xong", "Lưu phiếu (F2)")
        self.btn_ls = make_tb(QStyle.SP_FileDialogContentsView, "Lịch sử khám")
        self.btn_in = make_tb(QStyle.SP_FileDialogDetailedView, "In phiếu")

        for w in (self.btn_them, self.btn_boqua, self.btn_xoa, self.btn_khamxong, self.btn_ls, self.btn_in):
            toolbar_layout.addWidget(w)

        toolbar_layout.addStretch()

        self.combo_phieukham = QComboBox()
        self.combo_phieukham.setEditable(True)
        self.combo_phieukham.setMinimumWidth(240)
        self.combo_phieukham.addItems(
            ["Phiếu khám", "Phiếu tái khám", "Phiếu xét nghiệm", "Bệnh án ngoại trú - tờ 1", "Bệnh án ngoại trú - tờ 2",
             "Tờ điều trị"])
        self.combo_phieukham.setCurrentIndex(0)
        toolbar_layout.addWidget(self.combo_phieukham)

        return toolbar_frame

    def _create_hanh_chinh_group(self):
        """Tạo GroupBox Thông tin hành chính."""
        group = QGroupBox("THÔNG TIN HÀNH CHÍNH")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(6)

        self.date_ngaykham = QDateEdit(QDate.currentDate())
        self.edit_sohoso = QLineEdit("0")
        self.date_ngaysinh = QDateEdit()
        self.combo_loaikham = QComboBox()
        self.combo_benhnhan = QComboBox()
        self.completer_bn = QCompleter()
        self.combo_gioitinh = QComboBox()
        self.spin_tienkham = QSpinBox()
        self.edit_diachi = QLineEdit()
        self.edit_dienthoai = QLineEdit()
        self.combo_phong = QComboBox()
        self.edit_nghenghiep = QLineEdit()
        self.combo_dantoc = QComboBox()
        self.combo_tinhtrang = QComboBox()
        self.combo_bacsi = QComboBox()
        self.text_lydo = QTextEdit()

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
        self.spin_tienkham.setSuffix(" VND")
        self.spin_tienkham.setGroupSeparatorShown(True)
        self.spin_tienkham.setStepType(QSpinBox.AdaptiveDecimalStepType)
        self.spin_tienkham.setSingleStep(10000)
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
        self.combo_bacsi.addItems(["--Chọn Bác sĩ--", "BS. Nguyễn Văn An", "BS. Trần Thị Bình"])
        self.combo_bacsi.setFixedWidth(150)
        self.text_lydo.setFixedHeight(50)

        def req_label(text): return QLabel(f"<b>{text}</b>")

        def label(text): return QLabel(text)

        layout.addWidget(label("Ngày khám:"), 0, 0)
        layout.addWidget(self.date_ngaykham, 0, 1)
        layout.addWidget(label("Số hồ sơ:"), 0, 2)
        layout.addWidget(self.edit_sohoso, 0, 3)
        layout.addWidget(label("Ngày sinh:"), 0, 4)
        layout.addWidget(self.date_ngaysinh, 0, 5)
        layout.addWidget(label("Loại khám:"), 0, 6)
        layout.addWidget(self.combo_loaikham, 0, 7)

        layout.addWidget(req_label("Bệnh nhân:"), 1, 0)
        layout.addWidget(self.combo_benhnhan, 1, 1, 1, 3)
        layout.addWidget(label("Giới tính:"), 1, 4)
        layout.addWidget(self.combo_gioitinh, 1, 5)
        layout.addWidget(label("Tiền khám:"), 1, 6)
        layout.addWidget(self.spin_tienkham, 1, 7)

        layout.addWidget(label("Địa chỉ:"), 2, 0)
        layout.addWidget(self.edit_diachi, 2, 1, 1, 3)
        layout.addWidget(label("Điện thoại:"), 2, 4)
        layout.addWidget(self.edit_dienthoai, 2, 5)
        layout.addWidget(label("Phòng khám:"), 2, 6)
        layout.addWidget(self.combo_phong, 2, 7)

        layout.addWidget(label("Nghề nghiệp:"), 3, 0)
        layout.addWidget(self.edit_nghenghiep, 3, 1)
        layout.addWidget(label("Dân tộc:"), 3, 2)
        layout.addWidget(self.combo_dantoc, 3, 3)
        layout.addWidget(label("Tình trạng BN:"), 3, 4)
        layout.addWidget(self.combo_tinhtrang, 3, 5)
        layout.addWidget(req_label("Bác sĩ Khám:"), 3, 6)
        layout.addWidget(self.combo_bacsi, 3, 7)

        layout.addWidget(label("Ghi chú / lý do khám:"), 4, 0)
        layout.addWidget(self.text_lydo, 4, 1, 1, 7)

        return group

    def _create_ket_qua_kham_group(self):
        """Tạo GroupBox Kết quả khám (2 cột)."""
        group = QGroupBox("KẾT QUẢ KHÁM")
        group.setObjectName("KetQuaKhamGroup")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)

        layout.addWidget(self._create_kham_lam_sang_col(), 1)
        layout.addWidget(self._create_tien_su_col(), 1)

        return group

    def _create_kham_lam_sang_col(self):
        """Tạo cột bên trái (Khám lâm sàng, Chẩn đoán...)."""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_khamlam = QTextEdit()
        self.text_benkem = QTextEdit()
        self.combo_icd10 = QComboBox()
        self.btn_icd10 = QPushButton("Chọn ICD10")
        self.text_chandoan = QTextEdit()
        self.text_ketluan = QTextEdit()

        self.text_khamlam.setFixedHeight(80)
        self.text_benkem.setFixedHeight(50)
        self.combo_icd10.setEditable(True)
        self.combo_icd10.addItem("--Chọn ICD10--")
        self.btn_icd10.setObjectName("BtnChonICD")
        self.text_chandoan.setFixedHeight(50)
        self.text_ketluan.setFixedHeight(80)

        layout.addWidget(QLabel("<b>Khám lâm sàng:</b>"), 0, 0, 1, 2)
        layout.addWidget(self.text_khamlam, 1, 0, 1, 2)
        layout.addWidget(QLabel("Bệnh kèm theo:"), 2, 0, 1, 2)
        layout.addWidget(self.text_benkem, 3, 0, 1, 2)
        layout.addWidget(QLabel("Bệnh theo ICD10:"), 4, 0)
        layout.addWidget(self.combo_icd10, 5, 0)
        layout.addWidget(self.btn_icd10, 5, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QLabel("<b>Chẩn đoán bệnh:</b>"), 6, 0, 1, 2)
        layout.addWidget(self.text_chandoan, 7, 0, 1, 2)
        layout.addWidget(QLabel("Kết luận & hướng điều trị:"), 8, 0, 1, 2)
        layout.addWidget(self.text_ketluan, 9, 0, 1, 2)

        layout.setColumnStretch(0, 1)

        return widget

    def _create_tien_su_col(self):
        """Tạo cột bên phải (Dấu hiệu sinh tồn, Tiền sử...)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._create_vitals_group())

        self.text_cls = QTextEdit()
        self.text_diungthuoc = QTextEdit()
        self.text_tiensubn = QTextEdit()
        self.text_tiensugd = QTextEdit()

        self.text_cls.setFixedHeight(50)
        self.text_diungthuoc.setFixedHeight(50)
        self.text_tiensubn.setFixedHeight(50)
        self.text_tiensugd.setFixedHeight(50)

        layout.addWidget(QLabel("Kết quả CLS:"))
        layout.addWidget(self.text_cls)
        layout.addWidget(QLabel("Dị ứng thuốc:"))
        layout.addWidget(self.text_diungthuoc)
        layout.addWidget(QLabel("Tiền sử bản thân:"))
        layout.addWidget(self.text_tiensubn)
        layout.addWidget(QLabel("Tiền sử gia đình:"))
        layout.addWidget(self.text_tiensugd)
        layout.addStretch()

        return widget

    def _create_vitals_group(self):
        """Tạo GroupBox Dấu hiệu sinh tồn."""
        self.edit_nhiptim = QLineEdit()
        self.edit_huyetap = QLineEdit()
        self.edit_nhietdo = QLineEdit()
        self.edit_nhiptho = QLineEdit()
        self.edit_chieucao = QLineEdit()
        self.edit_cannang = QLineEdit()

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

        return vitals_group

    def _create_vitals_input(self, label_text, line_edit, unit_text):
        """Hàm trợ giúp tạo một nhóm nhập liệu (Label - Input - Unit)."""
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

    def _create_thong_tin_khac_group(self):
        """Tạo GroupBox Hẹn khám, Tuổi thai..."""
        group = QGroupBox("THÔNG TIN KHÁC")
        group.setObjectName("ThongTinKhacGroup")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        self.date_kinhcuoi = QDateEdit()
        self.date_dukien = QDateEdit()
        self.edit_tuoitthai = QLineEdit()
        self.edit_hen = QLineEdit()
        self.spin_sau = QSpinBox()
        self.date_hen = QDateEdit()

        self.date_kinhcuoi.setDisplayFormat("dd/MM/yyyy")
        self.date_dukien.setDisplayFormat("dd/MM/yyyy")
        layout.addWidget(QLabel("Ngày kinh cuối:"), 0, 0)
        layout.addWidget(self.date_kinhcuoi, 0, 1)
        layout.addWidget(QLabel("Dự kiến sinh:"), 0, 2)
        layout.addWidget(self.date_dukien, 0, 3)
        layout.addWidget(QLabel("Tuổi thai:"), 0, 4)
        self.edit_tuoitthai.setFixedWidth(100)
        layout.addWidget(self.edit_tuoitthai, 0, 5)
        layout.setColumnStretch(6, 1)

        self.spin_sau.setRange(0, 365)
        self.spin_sau.setFixedWidth(50)
        self.date_hen.setDisplayFormat("dd/MM/yyyy")
        self.date_hen.setCalendarPopup(True)
        self.date_hen.setFixedWidth(120)

        layout.addWidget(QLabel("Hẹn tái khám:"), 1, 0)
        layout.addWidget(self.edit_hen, 1, 1)
        layout.addWidget(QLabel("Sau (ngày):"), 1, 2)
        layout.addWidget(self.spin_sau, 1, 3)
        layout.addWidget(QLabel("Ngày hẹn tái khám:"), 1, 4)
        layout.addWidget(self.date_hen, 1, 5)

        frame_attach = QFrame()
        frame_attach.setFrameShape(QFrame.StyledPanel)
        frame_attach.setMinimumHeight(40)
        attach_layout = QHBoxLayout(frame_attach)
        attach_layout.addWidget(QLabel("[ CHỌN DOCUMENT ]"))
        attach_layout.addStretch()
        layout.addWidget(QLabel("Tài liệu đính kèm:"), 2, 0)
        layout.addWidget(frame_attach, 2, 1, 1, 5)

        return group

    def _connect_events(self):
        """Nơi tập trung kết nối các sự kiện."""
        # Toolbar
        self.btn_them.clicked.connect(self._handle_them_moi)
        self.btn_khamxong.clicked.connect(self._handle_luu_kham_xong)
        self.btn_boqua.clicked.connect(self._handle_bo_qua)
        self.btn_xoa.clicked.connect(self._handle_xoa)
        self.btn_in.clicked.connect(self._handle_in_phieu)

        # Phím tắt
        QShortcut(QKeySequence("F1"), self, self._handle_them_moi)
        QShortcut(QKeySequence("F2"), self, self._handle_luu_kham_xong)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._handle_bo_qua)
        QShortcut(QKeySequence(Qt.ControlModifier + Qt.Key_D), self, self._handle_xoa)

        # Logic
        self.combo_benhnhan.currentIndexChanged.connect(self._on_benh_nhan_selected)
        self.btn_icd10.clicked.connect(self.show_icd10_dialog)
        self.spin_sau.valueChanged.connect(self.update_followup_date)
        self.date_ngaykham.dateChanged.connect(self.update_followup_date)

    # ----------------------------------
    # CÁC HÀM LOGIC VÀ XỬ LÝ SỰ KIỆN
    # ----------------------------------

    def load_benh_nhan_list(self):
        """Giả lập load danh sách BN và dữ liệu chi tiết."""
        # ## TODO: Thay thế bằng logic load database
        self.benh_nhan_data_store = {
            101: {
                "ten": "NGUYỄN THỊ THUÝ HIỀN",
                "ngaysinh": QDate(1990, 5, 10),
                "gioitinh": "Nữ",
                "diachi": "123 Đường ABC, Quận 1, TP.HCM",
                "dienthoai": "0901234567",
                "nghenghiep": "Kế toán",
                "dantoc": "Kinh"
            },
            102: {
                "ten": "NGUYỄN VĂN A",
                "ngaysinh": QDate(1985, 10, 20),
                "gioitinh": "Nam",
                "diachi": "456 Đường XYZ, Gò Vấp, TP.HCM",
                "dienthoai": "0987654321",
                "nghenghiep": "Lập trình viên",
                "dantoc": "Kinh"
            },
            103: {
                "ten": "TRẦN VĂN B",
                "ngaysinh": QDate(2000, 1, 15),
                "gioitinh": "Nam",
                "diachi": "789 Đường LMN, TP. Thủ Đức",
                "dienthoai": "0123456789",
                "nghenghiep": "Sinh viên",
                "dantoc": "Tày"
            }
        }

        names = [info["ten"] for bid, info in self.benh_nhan_data_store.items()]

        self.combo_benhnhan.blockSignals(True)
        self.combo_benhnhan.clear()

        self.combo_benhnhan.addItem("--Chọn hoặc gõ tên bệnh nhân--", -1)
        for bid, info in self.benh_nhan_data_store.items():
            self.combo_benhnhan.addItem(info["ten"], bid)

        model = QStringListModel(names)
        self.completer_bn.setModel(model)
        self.combo_benhnhan.setCompleter(self.completer_bn)
        self.combo_benhnhan.setEditable(True)
        self.combo_benhnhan.setCurrentIndex(0)

        self.combo_benhnhan.blockSignals(False)

    def _on_benh_nhan_selected(self, index):
        """Khi chọn BN, tự động điền các trường thông tin."""
        if index == -1:
            self._clear_patient_info()
            return

        patient_id = self.combo_benhnhan.itemData(index)

        if patient_id in self.benh_nhan_data_store:
            info = self.benh_nhan_data_store[patient_id]
            self.date_ngaysinh.setDate(info["ngaysinh"])
            self.combo_gioitinh.setCurrentText(info["gioitinh"])
            self.edit_diachi.setText(info["diachi"])
            self.edit_dienthoai.setText(info["dienthoai"])
            self.edit_nghenghiep.setText(info["nghenghiep"])
            self.combo_dantoc.setCurrentText(info["dantoc"])

            # ## XÓA LOGIC SET_MODE
            # self._set_mode(self.MODE_NEW)
            self.text_lydo.setFocus()
        else:
            self._clear_patient_info()

    def show_icd10_dialog(self):
        """Hiển thị cửa sổ chọn ICD-10."""
        if self.icd10_dialog is None:
            self.icd10_dialog = ICD10SearchDialog(ICD10_DATA, self)
            self.icd10_dialog.icd10_selected.connect(self.update_icd10_combo)
        self.icd10_dialog.exec_()

    def update_icd10_combo(self, icd10_full_text):
        """Cập nhật QComboBox ICD-10 với mã/tên đã chọn."""
        self.combo_icd10.setEditText(icd10_full_text)

    def update_followup_date(self):
        """Tính ngày hẹn = ngày khám + số ngày (spin_sau) và cập nhật date_hen."""
        try:
            days = int(self.spin_sau.value())
        except Exception:
            days = 0
        base_date = self.date_ngaykham.date()
        follow_date = base_date.addDays(days)
        self.date_hen.setDate(follow_date)

    # ----------------------------------
    # CÁC HÀM XỬ LÝ (Handlers)
    # ----------------------------------

    # ## XÓA BỎ HÀM _set_mode

    def _clear_form(self, clear_patient=False):
        """Xóa trắng form, trừ thông tin bệnh nhân (trừ khi clear_patient=True)."""
        if clear_patient:
            self.combo_benhnhan.setCurrentIndex(0)
            # Các trường BN khác sẽ tự xóa

        self.date_ngaykham.setDate(QDate.currentDate())
        self.edit_sohoso.setText("0")
        self.combo_loaikham.setCurrentIndex(0)
        self.spin_tienkham.setValue(0)
        self.combo_phong.setCurrentIndex(0)
        self.combo_tinhtrang.setCurrentIndex(0)
        self.combo_bacsi.setCurrentIndex(0)
        self.text_lydo.clear()

        self.text_khamlam.clear()
        self.text_benkem.clear()
        self.combo_icd10.setEditText("")
        self.text_chandoan.clear()
        self.text_ketluan.clear()

        for w in (self.edit_nhiptim, self.edit_huyetap, self.edit_nhietdo,
                  self.edit_nhiptho, self.edit_chieucao, self.edit_cannang,
                  self.text_cls, self.text_diungthuoc, self.text_tiensubn,
                  self.text_tiensugd):
            w.clear()

        self.date_kinhcuoi.setDate(QDate())
        self.date_dukien.setDate(QDate())
        self.edit_tuoitthai.clear()
        self.edit_hen.clear()
        self.spin_sau.setValue(0)
        self.update_followup_date()

    def _clear_patient_info(self):
        """Chỉ xóa các trường thông tin bệnh nhân."""
        self.date_ngaysinh.setDate(QDate())
        self.combo_gioitinh.setCurrentIndex(0)
        self.edit_diachi.clear()
        self.edit_dienthoai.clear()
        self.edit_nghenghiep.clear()
        self.combo_dantoc.setCurrentIndex(0)

    def _handle_them_moi(self):
        print("Đang Thêm mới...")
        self._clear_form(clear_patient=True)
        # self._set_mode(self.MODE_NEW) # Xóa
        self.combo_benhnhan.setFocus()

    def _handle_luu_kham_xong(self):
        print("Đang Lưu (Khám xong)...")
        if self.combo_benhnhan.currentIndex() <= 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một bệnh nhân.")
            self.combo_benhnhan.setFocus()
            return
        if self.combo_bacsi.currentIndex() <= 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn Bác sĩ khám.")
            self.combo_bacsi.setFocus()
            return
        if not self.text_chandoan.toPlainText().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Chẩn đoán bệnh.")
            self.text_chandoan.setFocus()
            return

        # ## TODO: Thêm logic lưu database

        QMessageBox.information(self, "Thành công", "Đã lưu phiếu khám thành công.")
        # self._set_mode(self.MODE_VIEW) # Xóa
        self._clear_form(clear_patient=True)  # Xóa form sau khi lưu

    def _handle_bo_qua(self):
        print("Đang Bỏ qua...")
        reply = QMessageBox.question(self, "Xác nhận",
                                     "Bạn có chắc muốn hủy bỏ các thay đổi hiện tại?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # ## TODO: Tải lại dữ liệu cũ từ DB (nếu là chế độ sửa)
            print("Đang tải lại dữ liệu... (Giả lập)")

            self._clear_form(clear_patient=True)
            # self._set_mode(self.MODE_VIEW) # Xóa

    def _handle_xoa(self):
        print("Đang Xóa...")
        if self.combo_benhnhan.currentIndex() <= 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một bệnh nhân để xóa phiếu.")
            return

        reply = QMessageBox.question(self, "Xác nhận Xóa",
                                     f"Bạn có chắc muốn XÓA phiếu khám của bệnh nhân:\n{self.combo_benhnhan.currentText()}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # ## TODO: Thêm logic xóa database
            print("Đã xóa phiếu (Giả lập).")
            self._clear_form(clear_patient=True)
            # self._set_mode(self.MODE_VIEW) # Xóa

    def _handle_in_phieu(self):
        print("Đang In phiếu...")
        QMessageBox.information(self, "Thông báo", "Chức năng 'In Phiếu' đang được phát triển.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Tahoma", 10))
    w = LapPhieuKham()
    w.show()
    sys.exit(app.exec_())