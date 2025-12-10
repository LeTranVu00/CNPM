from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QSizePolicy, QSpacerItem,
    QMessageBox, QDateEdit, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from app_signals import app_signals
from PyQt5.QtGui import QFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# Đăng ký font tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont
from database import get_connection, initialize_database
initialize_database()
import logging

# Configure simple file logger for the form (one logger shared across module)
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.log'))
logger = logging.getLogger('app_qlpk')
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH, encoding='utf-8')
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)
logger.setLevel(logging.INFO)

class TextEditDialog(QDialog):
    def __init__(self, title, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 400)
        
        # Set stylesheet to match main window (buttons use green theme)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; min-width: 80px; }
            QPushButton:hover { background-color: #005a9e; }
            QTextEdit { border: 1px solid #ccc; border-radius: 3px; padding: 4px; }
            QTextEdit:focus { border-color: #0078D7; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setFont(QFont("Arial", 10))
        layout.addWidget(self.text_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_text(self):
        return self.text_edit.toPlainText()


class ClickableLabel(QLabel):
    """A QLabel that emits clicked and doubleClicked signals."""
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()

    def mouseReleaseEvent(self, ev):
        try:
            self.clicked.emit()
        except Exception:
            pass
        return super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        try:
            self.doubleClicked.emit()
        except Exception:
            pass
        return super().mouseDoubleClickEvent(ev)


class ChiDinhDichVu(QWidget):
    # Signal để thông báo khi dữ liệu được lưu
    data_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_phieu_kham_id = None
        
        # Set stylesheet (use green button style like reception form)
        self.base_stylesheet = """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 3px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                color: #0078D7;
                subcontrol-origin: margin;
                left: 7px;
                padding: 0px 5px 0px 5px;
            }
            QLabel#required {
                font-weight: bold;
                color: #0078D7;
            }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #005a9e; }
            QLineEdit, QDateEdit, QComboBox {
                padding: 3px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border-color: #0078D7;
            }
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #e6f2ff;
            }
            QHeaderView::section {
                background-color: #0078D7;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """
        self.setStyleSheet(self.base_stylesheet)
        
        # UI setup
        self.initUI()
        
        # Load initial data
        try:
            self.load_dich_vu_list()
        except Exception:
            pass
        try:
            self.load_benh_nhan_list()
        except Exception:
            pass
            
        # Connect signals
        self.hoten.currentIndexChanged.connect(self.on_select_benh_nhan)
        # completer and editing finished: only load on explicit selections
        try:
            if self.completer:
                self.completer.activated.connect(self._on_completer_activated)
            try:
                # lineEdit exists because we setEditable(True)
                self.hoten.lineEdit().editingFinished.connect(self._on_hoten_editing_finished)
            except Exception:
                pass
        except Exception:
            pass

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        def required_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("required")
            return lbl

        # === 1. THÔNG TIN BỆNH NHÂN ===
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        # Sử dụng QGridLayout với 4 cột chính: Cột 0=Label | Cột 1=Input | Cột 2=Label | Cột 3=Input
        grid_bn = QGridLayout()
        grid_bn.setHorizontalSpacing(6)
        grid_bn.setVerticalSpacing(4)

        # ---------------------------------------------
        # KHỞI TẠO VÀ CẤU HÌNH CÁC TRƯỜNG DỮ LIỆU
        # ---------------------------------------------

        # 1. Hàng đầu tiên (Họ tên - Giới tính - Điện thoại - Ngày sinh)
        self.hoten = QComboBox()
        self.hoten.setEditable(True)
        try:
            from PyQt5.QtWidgets import QCompleter
            self.completer = QCompleter()
            self.completer.setCaseSensitivity(False)
            self.hoten.setCompleter(self.completer)
        except Exception:
            self.completer = None
        self.gioitinh = QLineEdit()
        self.gioitinh.setReadOnly(True)
        self.dienthoai = QLineEdit()
        self.dienthoai.setReadOnly(True)
        self.ngaysinh = QDateEdit()
        self.ngaysinh.setDate(QDate.currentDate())
        self.ngaysinh.setDisplayFormat("dd/MM/yyyy")
        self.ngaysinh.setReadOnly(True)

        # 2. Hàng tiếp theo (Địa chỉ - Số phiếu khám - Số chỉ định - Ngày lập)
        self.diachi = QLineEdit()
        self.diachi.setReadOnly(True)
        self.sophieukham = QLineEdit()
        self.sophieukham.setReadOnly(True)
        self.sochidinh = QLineEdit()
        self.sochidinh.setReadOnly(True)
        self.ngaylap = QLineEdit(QDate.currentDate().toString("dd/MM/yyyy"))
        self.ngaylap.setReadOnly(True)
        self.tinhtrang = QLineEdit()
        self.tinhtrang.setReadOnly(True)
        # 3. Các trường mới bổ sung
        self.doituong = QLineEdit()
        self.doituong.setReadOnly(True)
        self.nghenghiep = QLineEdit()
        self.nghenghiep.setReadOnly(True)
        self.socccd = QLineEdit()
        self.socccd.setReadOnly(True)
        self.tuoi = QLineEdit("26 tuổi")
        self.tuoi.setReadOnly(True)
        self.tuoi.setAlignment(Qt.AlignLeft)
        self.phongkham = QLineEdit()
        self.phongkham.setReadOnly(True)
        self.nguoilap = QComboBox()
        self.khamlamsang = QLineEdit()
        self.bacsithuchien = QComboBox()
        self.chandoanbandau = QLineEdit()
        self.tongtien = QLineEdit("0")
        self.tongtien.setReadOnly(True)

        # Cấu hình ComboBox
        self.nguoilap.addItems(["Bác sĩ", "Y tá"])
        self.bacsithuchien.addItems(["a", "b"])
        # ---------------------------------------------
        # SẮP XẾP VÀO GRID LAYOUT
        # ---------------------------------------------

        # Hàng 0: Họ tên | Giới tính
        grid_bn.addWidget(required_label("Họ và tên *"), 0, 0)
        grid_bn.addWidget(self.hoten, 0, 1)
        grid_bn.addWidget(QLabel("Số CCCD"), 0, 2)
        grid_bn.addWidget(self.socccd, 0, 3)
        grid_bn.addWidget(QLabel("Giới tính"), 0, 4)
        grid_bn.addWidget(self.gioitinh, 0, 5) # Cột 3 (Input)

        # Hàng 1: Ngày sinh | Tuổi
        grid_bn.addWidget(QLabel("Ngày sinh"), 1, 0)
        grid_bn.addWidget(self.ngaysinh, 1, 1)
        grid_bn.addWidget(QLabel("Điện thoại"), 1, 2)
        grid_bn.addWidget(self.dienthoai, 1, 3)
        grid_bn.addWidget(QLabel("Tuổi"), 1, 4)
        grid_bn.addWidget(self.tuoi, 1, 5)

        # Hàng 2: Địa chỉ | Điện thoại
        grid_bn.addWidget(QLabel("Địa chỉ"), 2, 0)
        grid_bn.addWidget(self.diachi, 2, 1)
        grid_bn.addWidget(QLabel("Đối tượng"), 2, 2)
        grid_bn.addWidget(self.doituong, 2, 3)
        grid_bn.addWidget(QLabel("Nghề nghiệp"), 2, 4)
        grid_bn.addWidget(self.nghenghiep, 2, 5)

        # Hàng 5: Số phiếu khám | Số chỉ định | Phòng khám
        grid_bn.addWidget(QLabel("Số phiếu khám"), 3, 0)
        h_layout_phieu = QHBoxLayout()
        h_layout_phieu.setContentsMargins(0, 0, 0, 0)
        h_layout_phieu.addWidget(self.sophieukham)
        grid_bn.addLayout(h_layout_phieu, 3, 1)
        grid_bn.addWidget(QLabel("Số chỉ định"), 3, 2)
        grid_bn.addWidget(self.sochidinh, 3, 3)
        grid_bn.addWidget(QLabel("Phòng khám"), 3, 4)
        grid_bn.addWidget(self.phongkham, 3, 5)

        # Hàng 6: Ngày lập | Người lập (Bác sĩ)
        grid_bn.addWidget(QLabel("Ngày lập"), 4, 0)
        grid_bn.addWidget(self.ngaylap, 4, 1)
        grid_bn.addWidget(QLabel("Người lập"), 4, 2)
        grid_bn.addWidget(self.nguoilap, 4, 3)
        grid_bn.addWidget(QLabel("Tình trạng"), 4, 4)
        grid_bn.addWidget(self.tinhtrang, 4, 5)

        # Widget tùy chỉnh cho Khám lâm sàng (hiển thị dạng label, double-click để sửa)
        self.lbl_khamlamsang = ClickableLabel("Nhấn để nhập")
        self.lbl_khamlamsang.setStyleSheet("""
            QLabel { text-align: left; padding: 6px 12px; background-color: white; color: #333333; border: 1px solid #ccc; border-radius: 4px; }
        """)
        self.lbl_khamlamsang.setWordWrap(True)
        self.lbl_khamlamsang.doubleClicked.connect(lambda: self.show_text_dialog("Khám lâm sàng", self.khamlamsang))

        # Widget tùy chỉnh cho Chẩn đoán (label preview)
        self.lbl_chandoanbandau = ClickableLabel("Nhấn để nhập")
        self.lbl_chandoanbandau.setStyleSheet("""
            QLabel { text-align: left; padding: 6px 12px; background-color: white; color: #333333; border: 1px solid #ccc; border-radius: 4px; }
        """)
        self.lbl_chandoanbandau.setWordWrap(True)
        self.lbl_chandoanbandau.doubleClicked.connect(lambda: self.show_text_dialog("Chẩn đoán", self.chandoanbandau))

        # Hàng 7: Khám lâm sàng
        grid_bn.addWidget(QLabel("Khám lâm sàng"), 7, 0)
        grid_bn.addWidget(self.lbl_khamlamsang, 7, 1)

        # Thêm BS thực hiện riêng
        grid_bn.addWidget(QLabel("BS thực hiện"), 7, 2)
        grid_bn.addWidget(self.bacsithuchien, 7, 3)
        grid_bn.addWidget(QLabel("Tổng tiền"), 7, 4)
        grid_bn.addWidget(self.tongtien, 7, 5)

        # Hàng 9: Chẩn đoán
        grid_bn.addWidget(QLabel("Chẩn đoán ban đầu"), 8, 0)
        grid_bn.addWidget(self.lbl_chandoanbandau, 8, 1, 1, 3) # Chiếm 3 cột

        # Ẩn các input gốc (vẫn giữ để lưu giá trị)
        self.khamlamsang.hide()
        self.chandoanbandau.hide()

        # Căn chỉnh cột Input
        grid_bn.setColumnStretch(1, 1) # Cột Input 1 co giãn
        grid_bn.setColumnStretch(3, 1) # Cột Input 2 co giãn

        group_bn.setLayout(grid_bn)
        main_layout.addWidget(group_bn)

        # === 2. CHỈ ĐỊNH DỊCH VỤ === (Giữ nguyên)
        group_cd = QGroupBox("CHỈ ĐỊNH DỊCH VỤ")
        grid_cd = QGridLayout()
        grid_cd.setHorizontalSpacing(6)
        grid_cd.setVerticalSpacing(4)

        self.combo_dichvu = QComboBox()
        self.input_soluong = QLineEdit("1")
        self.input_dongia = QLineEdit("80000")
        self.input_thanhtien = QLineEdit("80000")
        self.input_thanhtien.setReadOnly(True)

        grid_cd.addWidget(QLabel("Tên dịch vụ"), 0, 0)
        grid_cd.addWidget(self.combo_dichvu, 0, 1)
        grid_cd.addWidget(QLabel("Số lượng"), 0, 2)
        grid_cd.addWidget(self.input_soluong, 0, 3)
        grid_cd.addWidget(QLabel("Đơn giá"), 1, 0)
        grid_cd.addWidget(self.input_dongia, 1, 1)
        grid_cd.addWidget(QLabel("Thành tiền"), 1, 2)
        grid_cd.addWidget(self.input_thanhtien, 1, 3)

        # ✅ Căn giãn cân bằng
        grid_cd.setColumnStretch(0, 0)
        grid_cd.setColumnStretch(1, 4)
        grid_cd.setColumnStretch(2, 0)
        grid_cd.setColumnStretch(3, 1)

        group_cd.setLayout(grid_cd)
        main_layout.addWidget(group_cd)

        # Kết nối sự kiện cho phần CHỈ ĐỊNH DỊCH VỤ
        self.combo_dichvu.currentIndexChanged.connect(self.on_select_dichvu)
        self.input_soluong.textChanged.connect(self.update_thanhtien_from_inputs)
        self.input_dongia.textChanged.connect(self.update_thanhtien_from_inputs)

        # === 3. DANH SÁCH DỊCH VỤ === 
        group_ds = QGroupBox("DANH SÁCH DỊCH VỤ ĐÃ CHỈ ĐỊNH")
        vbox_ds = QVBoxLayout()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["STT", "Tên dịch vụ", "Số lượng", "Đơn giá", "Thành tiền"])
        
        # Cấu hình độ rộng cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # STT cột cố định
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Tên dịch vụ co giãn
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Số lượng cột cố định
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Đơn giá cột cố định
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Thành tiền cột cố định
        
        # Đặt độ rộng cụ thể cho các cột
        self.table.setColumnWidth(0, 50)  # STT
        self.table.setColumnWidth(2, 80)  # Số lượng
        self.table.setColumnWidth(3, 100)  # Đơn giá
        self.table.setColumnWidth(4, 100)  # Thành tiền
        
        self.table.setAlternatingRowColors(True)
        # Không cho chỉnh sửa trực tiếp ô
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Khi chọn, chỉ chọn nguyên hàng và chỉ 1 hàng
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        vbox_ds.addWidget(self.table)
        group_ds.setLayout(vbox_ds)
        main_layout.addWidget(group_ds)

        # === 4. NÚT CHỨC NĂNG === (Giữ nguyên)
        btn_layout = QHBoxLayout()
        self.btn_them = QPushButton("Thêm")
        self.btn_luu = QPushButton("Lưu")
        self.btn_sua = QPushButton("Sửa")
        self.btn_xoa = QPushButton("Xóa")
        self.btn_in = QPushButton("In phiếu CD")
        self.btn_thoat = QPushButton("Thoát")
        for b in [self.btn_them, self.btn_luu, self.btn_sua, self.btn_xoa, self.btn_in, self.btn_thoat]:
            b.setMinimumWidth(120)
        btn_layout.addWidget(self.btn_them)
        btn_layout.addWidget(self.btn_luu)
        btn_layout.addWidget(self.btn_sua)
        btn_layout.addWidget(self.btn_xoa)
        btn_layout.addStretch() # Tạo khoảng trống lớn
        btn_layout.addWidget(self.btn_in)
        btn_layout.addWidget(self.btn_thoat)
        main_layout.addLayout(btn_layout)

        # Kết nối nút
        self.btn_them.clicked.connect(self.on_them_dichvu)
        self.btn_luu.clicked.connect(self.on_luu)
        self.btn_xoa.clicked.connect(self.on_xoa_dichvu)
        self.btn_sua.clicked.connect(self.enable_form_edit)
        self.btn_in.clicked.connect(self.on_in)
        self.btn_thoat.clicked.connect(self.close)
        
        # Initialize form state
        self.set_form_editable(True)  # Start with editable form


    # ========================== FUNCTION ==========================
    def load_benh_nhan_list(self):
        """Tải danh sách bệnh nhân vào hoten"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT b.id, b.ho_ten, b.dien_thoai, b.ngay_sinh, b.so_cccd,
                (
                    SELECT ma_hoso FROM tiep_don td WHERE td.benh_nhan_id = b.id ORDER BY td.id DESC LIMIT 1
                ) as ma_hoso
            FROM benh_nhan b
            ORDER BY b.ho_ten
        """)
        ds = cur.fetchall()
        conn.close()

        # Đặt placeholder để combobox bắt đầu ở trạng thái trống.
        # Khi người dùng nhấn mũi tên mới hiện danh sách và khi chọn tên sẽ gọi on_select_benh_nhan
        self.hoten.clear()
        self.hoten.addItem("-- Chọn bệnh nhân --", None)
        display_texts = []
        for row in ds:
            pid, name, phone, dob, cccd, ma_hoso = row
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

            self.hoten.addItem(disp, pid)
            display_texts.append(disp)

        # update completer model
        try:
            if self.completer:
                from PyQt5.QtCore import QStringListModel
                model = QStringListModel(display_texts)
                self.completer.setModel(model)
        except Exception:
            pass
        # Giữ placeholder được chọn ban đầu
        self.hoten.setCurrentIndex(0)

    # ========== Quản lý danh sách dịch vụ ===========
    def load_dich_vu_list(self):
        """Tải danh sách dịch vụ từ DB vào combo_dichvu. Nếu không có bảng, dùng danh sách tạm."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, ten_dich_vu, don_gia FROM dich_vu ORDER BY ten_dich_vu")
            rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()

        # Nếu không có dữ liệu, tạo danh sách mẫu
        if not rows:
            sample = [(-1, 'Khám tổng quát', 50000), (-2, 'Xét nghiệm máu', 120000), (-3, 'Siêu âm', 200000)]
            rows = sample

        self.combo_dichvu.clear()
        for r in rows:
            vid, name, price = r
            # lưu (id, don_gia) trong itemData
            self.combo_dichvu.addItem(f"{name}", (vid, price))

    def on_select_dichvu(self, idx):
        data = self.combo_dichvu.itemData(idx)
        if data:
            _, don_gia = data
            # Hiển thị đơn giá theo định dạng tiền tệ
            try:
                self.input_dongia.setText(self.format_currency(don_gia))
            except Exception:
                self.input_dongia.setText(str(don_gia))
        self.update_thanhtien_from_inputs()

    def format_currency(self, value):
        """Định dạng số tiền với dấu chấm phân cách hàng nghìn"""
        try:
            return "{:,.0f}".format(float(value)).replace(",", ".")
        except:
            return "0"
            
    def parse_currency(self, text):
        """Chuyển chuỗi số tiền có định dạng về số"""
        try:
            # Loại bỏ dấu chấm phân cách hàng nghìn
            text = text.replace(".", "")
            return float(text)
        except:
            return 0.0
            
    def update_thanhtien_from_inputs(self):
        try:
            sl = int(self.input_soluong.text() or 0)
        except:
            sl = 0
            
        try:
            # Chuyển đổi đơn giá từ định dạng tiền tệ về số
            dg = self.parse_currency(self.input_dongia.text())
        except:
            dg = 0.0
            
        tt = sl * dg
        
        # Cập nhật đơn giá với định dạng tiền tệ
        self.input_dongia.setText(self.format_currency(dg))
        # Cập nhật thành tiền với định dạng tiền tệ
        self.input_thanhtien.setText(self.format_currency(tt))

    # ========== Thêm / Sửa / Xóa hàng trên bảng ===========
    def on_them_dichvu(self):
        ten = self.combo_dichvu.currentText()
        data = self.combo_dichvu.currentData()
        dv_id = data[0] if data else None
        try:
            sl = int(self.input_soluong.text())
            # đọc đơn giá từ input bằng parser chung để chấp nhận "120.000" hoặc "120000"
            dg = self.parse_currency(self.input_dongia.text())
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Số lượng hoặc đơn giá không hợp lệ")
            return
        tt = int(sl * dg)

        # Thêm vào bảng UI
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # STT
        stt_item = QTableWidgetItem(str(row + 1))
        stt_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, stt_item)
        
        # Tên dịch vụ
        item_name = QTableWidgetItem(ten)
        item_name.setData(Qt.UserRole, dv_id)
        item_name.setData(Qt.UserRole + 2, dg)  # Lưu giá trị gốc của đơn giá
        item_name.setData(Qt.UserRole + 3, tt)  # Lưu giá trị gốc của thành tiền
        self.table.setItem(row, 1, item_name)
        
        # Số lượng, đơn giá, thành tiền
        sl_item = QTableWidgetItem(str(sl))
        sl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 2, sl_item)
        
        # Định dạng đơn giá với dấu phân cách hàng nghìn
        formatted_dg = "{:,.0f}".format(dg).replace(",", ".")
        dg_item = QTableWidgetItem(formatted_dg)
        dg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dg_item.setData(Qt.UserRole, dg)  # Lưu giá trị gốc
        self.table.setItem(row, 3, dg_item)
        
        # Định dạng thành tiền với dấu phân cách hàng nghìn
        formatted_tt = "{:,.0f}".format(tt).replace(",", ".")
        tt_item = QTableWidgetItem(formatted_tt)
        tt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tt_item.setData(Qt.UserRole, tt)  # Lưu giá trị gốc
        self.table.setItem(row, 4, tt_item)

        # Nếu chưa có phieu_kham trong DB cho form này, kiểm tra phiếu khám trong ngày và tạo mới nếu cần
        if not self.current_phieu_kham_id:
            if not self.hoten.currentData():
                QMessageBox.warning(self, "Lỗi", "Chưa chọn bệnh nhân. Vui lòng chọn bệnh nhân trước khi thêm dịch vụ.")
                # revert table insert
                self.table.removeRow(row)
                return
            
            # Kiểm tra xem đã có phiếu khám mới nhất của bệnh nhân chưa (không giới hạn ngày)
            conn = get_connection() 
            cur = conn.cursor()
            cur.execute("""
                SELECT id, so_phieu FROM phieu_kham 
                WHERE benh_nhan_id = ?
                ORDER BY ngay_lap DESC, id DESC LIMIT 1
            """, (self.hoten.currentData(),))
            existing_pk = cur.fetchone()
            conn.close()

            if existing_pk:
                # Nếu đã có phiếu khám trong ngày thì dùng lại
                self.current_phieu_kham_id = existing_pk[0]
                self.sophieukham.setText(existing_pk[1])
            else:
                # Nếu chưa có thì tạo mới
                try:
                    phieu_id, so_phieu = self.create_phieu_kham_in_db(
                        self.hoten.currentData(), self.ngaylap.text(), self.nguoilap.currentText(), self.phongkham.text()
                    )
                    self.current_phieu_kham_id = phieu_id
                    self.sophieukham.setText(so_phieu)
                    # Tự động sinh số chỉ định khi tạo phiếu khám
                    try:
                        so_chi_dinh = self.tao_so_chi_dinh_moi()
                        self.sochidinh.setText(so_chi_dinh)
                    except Exception:
                        pass
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Tạo phiếu khám thất bại: {e}")
                    self.table.removeRow(row)
                    return

        # Lưu chi_dinh cho hàng vừa thêm (dùng helper)
        try:
            chi_id, so_chi_dinh = self.insert_chi_dinh_in_db(self.current_phieu_kham_id, ten, sl, dg, tt)
            # lưu chi_id vào item để tiện sửa/xóa
            self.table.item(row, 1).setData(Qt.UserRole + 1, chi_id)
            # cập nhật tổng tiền
            self.recalculate_tongtien()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lưu chỉ định thất bại: {e}")
            # rollback UI
            self.table.removeRow(row)
            return

    def enable_form_edit(self):
        """Enable editing when Sửa button is clicked"""
        self.set_form_editable(True)

    def on_xoa_dichvu(self):
        sel = self.table.currentRow()
        if sel < 0:
            return
        # nếu đã lưu DB, xóa bản ghi chi_dinh
        chi_item = self.table.item(sel, 1)
        chi_id = chi_item.data(Qt.UserRole + 1) if chi_item else None
        if chi_id:
            logger.info(f"User requested delete: chi_id={chi_id}, row={sel}")
            try:
                self.delete_chi_dinh_in_db(chi_id)
                logger.info(f"Delete succeeded in DB: chi_id={chi_id}")
            except Exception as e:
                logger.exception(f"Delete failed in DB for chi_id={chi_id}: {e}")
                QMessageBox.critical(self, "Lỗi", f"Xóa thất bại: {e}")
                return
        self.table.removeRow(sel)
        for r in range(self.table.rowCount()):
            self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
        self.recalculate_tongtien()
        self.set_form_editable(False)  # Lock form after delete
        # Phát tín hiệu để cập nhật form quản lý
        self.data_saved.emit()
        try:
            app_signals.data_changed.emit()
        except Exception:
            pass

    def on_sua_dichvu(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.information(self, "Sửa", "Chọn hàng cần sửa")
            return
        # Lấy dữ liệu từ inputs và update cả UI lẫn DB nếu cần
        try:
            sl = int(self.input_soluong.text())
            # đọc đơn giá từ input theo định dạng tiền tệ
            dg = self.parse_currency(self.input_dongia.text())
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Số lượng/đơn giá không hợp lệ")
            return
        tt = int(sl * dg)
        ten = self.combo_dichvu.currentText()

        # Preserve existing chi_id (if row was loaded from DB or previously saved)
        existing_chi_id = None
        existing_item = self.table.item(sel, 1)
        if existing_item is not None:
            try:
                existing_chi_id = existing_item.data(Qt.UserRole + 1)
            except Exception:
                existing_chi_id = None

        ten_item = QTableWidgetItem(ten)
        if existing_chi_id is not None:
            ten_item.setData(Qt.UserRole + 1, existing_chi_id)
        ten_item.setData(Qt.UserRole + 2, dg)
        ten_item.setData(Qt.UserRole + 3, tt)

        sl_item = QTableWidgetItem(str(sl))
        sl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Hiển thị giá theo format_currency để luôn thấy dấu chấm hàng nghìn
        dg_item = QTableWidgetItem(self.format_currency(dg))
        dg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dg_item.setData(Qt.UserRole, dg)

        tt_item = QTableWidgetItem(self.format_currency(tt))
        tt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tt_item.setData(Qt.UserRole, tt)

        # cập nhật UI
        self.table.setItem(sel, 1, ten_item)
        self.table.setItem(sel, 2, sl_item)
        self.table.setItem(sel, 3, dg_item)
        self.table.setItem(sel, 4, tt_item)
        # cập nhật DB nếu có chi_id
        chi_item = self.table.item(sel, 1)
        chi_id = chi_item.data(Qt.UserRole + 1) if chi_item else None
        if chi_id:
            try:
                self.update_chi_dinh_in_db(chi_id, ten, sl, dg, tt)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Cập nhật thất bại: {e}")
        self.recalculate_tongtien()
        # Phát tín hiệu để cập nhật form quản lý
        self.data_saved.emit()
        try:
            app_signals.data_changed.emit()
        except Exception:
            pass

    def recalculate_tongtien(self):
        total = 0
        for r in range(self.table.rowCount()):
            try:
                # Lấy giá trị gốc của thành tiền đã được lưu
                item = self.table.item(r, 4)
                thanh_tien = item.data(Qt.UserRole)
                if thanh_tien is not None:
                    total += float(thanh_tien)
            except Exception:
                pass
        # Định dạng tổng tiền với dấu phân cách hàng nghìn
        formatted_total = "{:,.0f}".format(total).replace(",", ".")
        self.tongtien.setText(formatted_total)
        # Nếu đã có phieu_kham trong DB, cập nhật tong_tien
        if self.current_phieu_kham_id:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE phieu_kham SET tong_tien = ? WHERE id = ?", (total, self.current_phieu_kham_id))
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                conn.close()

    # ========== In phiếu sang PDF (đơn giản) ===========
    def on_in(self):
        """In phiếu chỉ định dịch vụ"""
        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn bệnh nhân trước khi in.")
            return

        if not self.current_phieu_kham_id:
            conn = get_connection()
            cur = conn.cursor()
            # Tìm phiếu khám gần nhất của bệnh nhân
            try:
                cur.execute("""
                    SELECT id FROM phieu_kham 
                    WHERE benh_nhan_id = ? 
                    ORDER BY ngay_lap DESC LIMIT 1
                """, (benh_nhan_id,))
                row = cur.fetchone()
                if row:
                    self.current_phieu_kham_id = row[0]
                else:
                    QMessageBox.information(self, "Thông báo", "Bệnh nhân chưa có phiếu khám nào.")
                    return
            finally:
                conn.close()

        try:
            from .print_chi_dinh import print_chi_dinh
            # Thu thập dữ liệu cho phiếu in
            dich_vu = []
            for r in range(self.table.rowCount()):
                try:
                    # Kiểm tra xem các item có tồn tại không
                    items = [self.table.item(r, col) for col in range(1, 5)]
                    if any(item is None for item in items):
                        QMessageBox.warning(self, "Cảnh báo",
                            f"Dòng {r+1} có ô trống.\nVui lòng kiểm tra lại dữ liệu.")
                        return
                    
                    ten_dv = items[0].text().strip()
                    so_luong = items[1].text().strip()
                    # Parse currency strings robustly (handles "1.440.000", "1.234,56", "120000")
                    don_gia = self.parse_currency(items[2].text().strip())
                    thanh_tien = self.parse_currency(items[3].text().strip())
                    
                    # Kiểm tra dữ liệu trống
                    if not all([ten_dv, so_luong, don_gia, thanh_tien]):
                        QMessageBox.warning(self, "Cảnh báo",
                            f"Dòng {r+1} có dữ liệu trống.\nVui lòng kiểm tra lại.")
                        return
                    
                    dich_vu.append({
                        'ten_dich_vu': ten_dv,
                        'so_luong': int(float(so_luong)),
                        'don_gia': don_gia,
                        'thanh_tien': thanh_tien
                    })
                except (ValueError, AttributeError) as e:
                    QMessageBox.warning(self, "Cảnh báo", 
                        f"Có lỗi ở dòng {r+1}: {e}\nVui lòng kiểm tra lại số liệu.")
                    return

            phieu_data = {
                'so_chi_dinh': self.sochidinh.text(),
                'so_phieu_kham': self.sophieukham.text(),
                'ngay_lap': self.ngaylap.text(),
                'ho_ten': self.hoten.currentText(),
                'gioi_tinh': self.gioitinh.text(),
                'ngay_sinh': self.ngaysinh.text(),
                'tuoi': self.tuoi.text(),
                'dia_chi': self.diachi.text(),
                'dien_thoai': self.dienthoai.text(),
                'doi_tuong': self.doituong.text(),
                'nghe_nghiep': self.nghenghiep.text(),
                'kham_lam_sang': self.khamlamsang.text(),
                'chan_doan': self.chandoanbandau.text(),
                'dich_vu': dich_vu,
                'tong_tien': self.parse_currency(self.tongtien.text()),
                'nguoi_lap': self.nguoilap.currentText(),
                'bac_si_chi_dinh': self.bacsithuchien.currentText()
            }
            
            # Gọi hàm in phiếu
            output_path = print_chi_dinh(phieu_data)
            
            # Mở cửa sổ xem trước PDF
            from .pdf_viewer import PDFViewer
            viewer = PDFViewer(output_path, parent=self)
            viewer.setWindowTitle(f"Xem trước phiếu chỉ định - {self.sochidinh.text()}")
            viewer.resize(800, 900)
            viewer.show()
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"In thất bại: {e}")


    def set_form_editable(self, editable=True):
        """Lock/unlock form controls"""
        self.combo_dichvu.setEnabled(editable)
        self.input_soluong.setEnabled(editable)
        self.input_dongia.setEnabled(editable)
        self.btn_them.setEnabled(editable)
        
        self.btn_sua.setEnabled(not editable)  # Enabled when form is locked
        self.btn_luu.setEnabled(editable)  # Enabled when form is editable
        self.btn_xoa.setEnabled(not editable)  # Enabled when form is locked

    def on_luu(self):
        """Lưu các thay đổi vào cơ sở dữ liệu"""
        if not self.current_phieu_kham_id:
            if not self.hoten.currentData():
                QMessageBox.warning(self, "Lỗi", "Chưa chọn bệnh nhân. Vui lòng chọn bệnh nhân trước khi lưu.")
                return
            try:
                phieu_id, so_phieu = self.create_phieu_kham_in_db(
                    self.hoten.currentData(), 
                    self.ngaylap.text(), 
                    self.nguoilap.currentText(), 
                    self.phongkham.text()
                )
                self.current_phieu_kham_id = phieu_id
                self.sophieukham.setText(so_phieu)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Tạo phiếu khám thất bại: {e}")
                return

        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            
            # Cập nhật thông tin phiếu khám
            # Update phieu_kham: do NOT store chẩn đoán here anymore (we keep it in chi_dinh)
            cur.execute("""
                UPDATE phieu_kham 
                SET 
                    ngay_lap = ?,
                    bac_si = ?,
                    phong_kham = ?,
                    tong_tien = ?
                WHERE id = ?
            """, (
                self.ngaylap.text(),
                self.nguoilap.currentText(),
                self.phongkham.text(),
                # Use parse_currency to accept formatted strings like '1.440.000'
                self.parse_currency(self.tongtien.text() or "0"),
                self.current_phieu_kham_id
            ))

            # Xóa tất cả chỉ định cũ
            cur.execute("DELETE FROM chi_dinh WHERE phieu_kham_id = ?", (self.current_phieu_kham_id,))

            # Thêm lại tất cả chỉ định từ bảng
            for row in range(self.table.rowCount()):
                ten = self.table.item(row, 1).text()
                so_luong = int(self.table.item(row, 2).text())
                # Lấy giá trị gốc đã lưu trong UserRole
                don_gia = self.table.item(row, 3).data(Qt.UserRole)
                thanh_tien = self.table.item(row, 4).data(Qt.UserRole)

                # Lấy kham_lam_sang và chan_doan_ban_dau từ form
                kham_lam_sang = self.khamlamsang.text().strip()
                chan_doan_ban_dau = self.chandoanbandau.text().strip()
                # Debug: log values being saved
                try:
                    print(f"[DEBUG] on_luu: phieu_kham_id={self.current_phieu_kham_id}, kham_lam_sang='''{kham_lam_sang}''', chan_doan_ban_dau='''{chan_doan_ban_dau}'''")
                except Exception:
                    pass

                chi_id = cur.execute(
                    """INSERT INTO chi_dinh(
                        phieu_kham_id, ten_dich_vu, so_luong, don_gia, thanh_tien, kham_lam_sang, chan_doan_ban_dau
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (self.current_phieu_kham_id, ten, so_luong, don_gia, thanh_tien, kham_lam_sang, chan_doan_ban_dau)
                ).lastrowid

                so_chi_dinh = f"CD{chi_id:04d}"
                cur.execute("UPDATE chi_dinh SET so_chi_dinh = ? WHERE id = ?", 
                          (so_chi_dinh, chi_id))

                # Lưu chi_id vào item trong bảng để tiện cập nhật sau này
                self.table.item(row, 1).setData(Qt.UserRole + 1, chi_id)
                
                # Cũng insert vào bảng thanh_toan để doanh thu được cập nhật
                cur.execute("""
                    INSERT OR REPLACE INTO thanh_toan (ngay, loai, mo_ta, so_tien)
                    VALUES (?, 'Dịch vụ', ?, ?)
                """, (self.ngaylap.text(), ten, thanh_tien))

            conn.commit()
            try:
                print(f"[DEBUG] on_luu: commit successful for phieu_kham_id={self.current_phieu_kham_id}")
            except Exception:
                pass
            self.set_form_editable(False)  # Lock form after saving
            QMessageBox.information(self, "Thông báo", "Đã lưu thành công!")
            # Phát tín hiệu để cập nhật form quản lý
            self.data_saved.emit()
            try:
                # Phát signal múlần để chắc chắn QuanLyThuoc nhận được
                app_signals.data_changed.emit()
                # Cũng phát medicine_exported để chắc chắn
                app_signals.medicine_exported.emit()
            except Exception as e:
                print(f"Lỗi khi phát signal: {e}")

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Lỗi", f"Lưu thất bại: {e}")
        finally:
            conn.close()

    def on_select_benh_nhan(self):
        """Khi chọn bệnh nhân -> hiển thị đầy đủ thông tin"""
        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            return

        conn = get_connection()
        cur = conn.cursor()

        # 🧍 Thông tin bệnh nhân
        cur.execute("""
            SELECT ho_ten, gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai,
                so_cccd, doi_tuong, nghe_nghiep
            FROM benh_nhan WHERE id = ?
        """, (benh_nhan_id,))
        bn = cur.fetchone()

        if not bn:
            conn.close()
            return

        # Gán dữ liệu lên form
        self.gioitinh.setText(bn[1] or "")
        self.ngaysinh.setDate(QDate.fromString(bn[2], "yyyy-MM-dd") if bn[2] else QDate.currentDate())
        self.tuoi.setText(str(bn[3]) + " tuổi" if bn[3] else "")
        self.diachi.setText(bn[4] or "")
        self.dienthoai.setText(bn[5] or "")
        self.socccd.setText(bn[6] or "")
        self.doituong.setText(bn[7] or "")
        self.nghenghiep.setText(bn[8] or "")

        # 🧾 Lấy phiếu khám mới nhất của bệnh nhân (không giới hạn ngày)
        cur.execute("""
            SELECT id, so_phieu, ngay_lap, bac_si, phong_kham, tong_tien
            FROM phieu_kham
            WHERE benh_nhan_id = ?
            ORDER BY ngay_lap DESC, id DESC LIMIT 1
        """, (benh_nhan_id,))
        pk = cur.fetchone()

        if pk:
            # Nếu đã có phiếu khám trong ngày, sử dụng lại phiếu khám đó
            self.current_phieu_kham_id = pk[0]
            self.sophieukham.setText(pk[1] or "")
            self.ngaylap.setText(pk[2] or "")
            self.nguoilap.setCurrentText(pk[3] or "")
            self.phongkham.setText(pk[4] or "")
            # Load chẩn đoán từ chi_dinh (we do not store diagnosis in phieu_kham)
            try:
                cur.execute("SELECT chan_doan_ban_dau FROM chi_dinh WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (pk[0],))
                cd_row = cur.fetchone()
                if cd_row and cd_row[0]:
                    self.chandoanbandau.setText(cd_row[0])
                    # Update preview label as well
                    preview = cd_row[0][:50] + "..." if len(cd_row[0]) > 50 else cd_row[0]
                    try:
                        self.lbl_chandoanbandau.setText(preview)
                    except Exception:
                        pass
                else:
                    self.chandoanbandau.clear()
                    try:
                        self.lbl_chandoanbandau.setText("Nhấn để nhập")
                    except Exception:
                        pass
            except Exception:
                self.chandoanbandau.clear()
            self.tongtien.setText(self.format_currency(pk[5] or 0))
            self.set_form_editable(False)  # Lock form when loading existing record
        else:
            # Nếu không có phiếu khám trong ngày, tạo số phiếu mới
            self.current_phieu_kham_id = None
            self.sophieukham.clear()
            self.ngaylap.setText(QDate.currentDate().toString("dd/MM/yyyy")) 
            self.chandoanbandau.clear()
            self.tongtien.setText(self.format_currency(0))        # 🏥 Lấy thông tin tiếp đón (phòng khám & tình trạng)
        cur.execute("""
            SELECT phong_kham, bac_si_kham, tinh_trang
            FROM tiep_don
            WHERE benh_nhan_id = ?
            ORDER BY id DESC LIMIT 1
        """, (benh_nhan_id,))
        td = cur.fetchone()
        if td:
            self.phongkham.setText(td[0] or "")
            self.nguoilap.setCurrentText(td[1] or "")
            self.tinhtrang.setText(td[2] or "")
        else:
            self.tinhtrang.clear()

        # 🧪 Lấy danh sách dịch vụ đã chỉ định
        cur.execute("""
            SELECT cd.id, cd.ten_dich_vu, cd.so_luong, cd.don_gia, cd.thanh_tien
            FROM chi_dinh cd
            JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
            WHERE pk.benh_nhan_id = ?
        """, (benh_nhan_id,))
        dich_vu_list = cur.fetchall()

        # Đổ dữ liệu vào bảng dịch vụ
        self.table.setRowCount(0)
        for idx, row_data in enumerate(dich_vu_list, start=1):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Thêm STT
            stt_item = QTableWidgetItem(str(idx))
            stt_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, stt_item)

            chi_id, ten_dv, so_luong, don_gia, thanh_tien = row_data

            # Tên dịch vụ (lưu chi_id để có thể xóa trực tiếp)
            ten_item = QTableWidgetItem(str(ten_dv))
            ten_item.setData(Qt.UserRole + 1, chi_id)
            self.table.setItem(row, 1, ten_item)

            # Số lượng
            sl_item = QTableWidgetItem(str(so_luong))
            sl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, sl_item)

            # Đơn giá
            dg_item = QTableWidgetItem(self.format_currency(don_gia))
            dg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            dg_item.setData(Qt.UserRole, float(don_gia))
            self.table.setItem(row, 3, dg_item)

            # Thành tiền
            tt_item = QTableWidgetItem(self.format_currency(thanh_tien))
            tt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tt_item.setData(Qt.UserRole, float(thanh_tien))
            self.table.setItem(row, 4, tt_item)

        conn.close()

    def _on_completer_activated(self, text):
        try:
            if not text or not text.strip():
                return
            # If display contains Mã:HS... parse and find corresponding benh_nhan id
            if "Mã:" in text:
                try:
                    ma = text.split("Mã:")[1].split()[0].strip()
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (ma,))
                    r = cur.fetchone()
                    conn.close()
                    if r and r[0]:
                        # find index with itemData equal to this id
                        target_id = r[0]
                        for i in range(self.hoten.count()):
                            if self.hoten.itemData(i) == target_id:
                                self.hoten.setCurrentIndex(i)
                                self.on_select_benh_nhan()
                                return
                except Exception:
                    pass

            # fallback: find exact display text entry and select it
            idx = self.hoten.findText(text.strip(), Qt.MatchExactly)
            if idx >= 0:
                self.hoten.setCurrentIndex(idx)
                self.on_select_benh_nhan()
        except Exception as e:
            logger.exception("_on_completer_activated error: %s", e)

    def _on_hoten_editing_finished(self):
        try:
            text = self.hoten.currentText().strip()
            if not text:
                return
            # If the user typed a full display (including 'Mã:'), try to lookup and select
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
                            if self.hoten.itemData(i) == target_id:
                                self.hoten.setCurrentIndex(i)
                                self.on_select_benh_nhan()
                                return
                except Exception:
                    pass

            # If the text exactly matches a full display item, select it; otherwise do nothing
            idx = self.hoten.findText(text, Qt.MatchExactly)
            if idx >= 0:
                self.hoten.setCurrentIndex(idx)
                self.on_select_benh_nhan()
        except Exception as e:
            logger.exception("_on_hoten_editing_finished error: %s", e)

        # (moved) --- the code to load related chi_dinh entries is executed below inside this function

    def tao_so_chi_dinh_moi(self):
        """Tạo số chỉ định mới dựa trên mã bệnh nhân và số thứ tự chỉ định"""
        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            raise Exception("Chưa chọn bệnh nhân")

        conn = get_connection()
        cur = conn.cursor()
        try:
            # Lấy số chỉ định lớn nhất của bệnh nhân này
            cur.execute("""
                SELECT MAX(CAST(SUBSTR(so_chi_dinh, -4) AS INTEGER))
                FROM chi_dinh cd
                JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
                WHERE pk.benh_nhan_id = ? AND so_chi_dinh LIKE ?
            """, (benh_nhan_id, f'CD{benh_nhan_id}%'))
            max_num = cur.fetchone()[0]
            
            if max_num is None:
                next_num = 1
            else:
                next_num = int(max_num) + 1
                
            # Format: CD[mã BN][số thứ tự 4 chữ số]
            return f"CD{benh_nhan_id:03d}{next_num:04d}"
        finally:
            conn.close()
    
    def tao_so_phieu_kham_moi(self):
        """Tạo số phiếu khám mới dựa trên mã bệnh nhân và số thứ tự khám"""
        benh_nhan_id = self.hoten.currentData()
        if not benh_nhan_id:
            raise Exception("Chưa chọn bệnh nhân")

        conn = get_connection()
        cur = conn.cursor()
        try:
            # Lấy số phiếu khám lớn nhất của bệnh nhân này
            cur.execute("""
                SELECT MAX(CAST(SUBSTR(so_phieu, -4) AS INTEGER))
                FROM phieu_kham 
                WHERE benh_nhan_id = ? AND so_phieu LIKE ?
            """, (benh_nhan_id, f'PK{benh_nhan_id}%'))
            max_num = cur.fetchone()[0]
            
            if max_num is None:
                next_num = 1
            else:
                next_num = int(max_num) + 1

            # Format: PK[mã BN][số thứ tự 4 chữ số] 
            return f"PK{benh_nhan_id:03d}{next_num:04d}"
        finally:
            conn.close()

    # ======= DB helper methods (tách riêng để dễ bảo trì) =======
    def create_phieu_kham_in_db(self, benh_nhan_id, ngay_lap, bac_si, phong_kham):
        """Tạo một bản ghi phieu_kham và trả về (phieu_id, so_phieu).
        Note: phieu_kham no longer stores 'chan_doan'; diagnosis is stored in chi_dinh."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            cur.execute(
                "INSERT INTO phieu_kham(benh_nhan_id, ngay_lap, bac_si, phong_kham, tong_tien) VALUES(?,?,?,?,?)",
                (benh_nhan_id, ngay_lap, bac_si, phong_kham, 0)
            )
            phieu_id = cur.lastrowid
            so_phieu = f"PK{phieu_id:04d}"
            cur.execute("UPDATE phieu_kham SET so_phieu = ? WHERE id = ?", (so_phieu, phieu_id))
            conn.commit()
            return phieu_id, so_phieu
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_chi_dinh_in_db(self, phieu_kham_id, ten, so_luong, don_gia, thanh_tien):
        """Insert chi_dinh, trả về (chi_id, so_chi_dinh)."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            # Lưu thêm kham_lam_sang và chan_doan nếu cột tồn tại
            cur.execute("PRAGMA table_info(chi_dinh)")
            cols = [r[1] for r in cur.fetchall()]
            # Determine which column name for chẩn đoán exists in the schema
            chan_col = None
            if 'chan_doan_ban_dau' in cols:
                chan_col = 'chan_doan_ban_dau'
            elif 'chan_doan' in cols:
                chan_col = 'chan_doan'

            if 'kham_lam_sang' in cols and chan_col:
                # Use parameterized SQL with the correct column name for chan_doan
                sql = f"INSERT INTO chi_dinh(phieu_kham_id, ten_dich_vu, so_luong, don_gia, thanh_tien, kham_lam_sang, {chan_col}) VALUES(?,?,?,?,?,?,?)"
                kh_text = getattr(self, 'khamlamsang', None).text() if hasattr(self, 'khamlamsang') else None
                chan_text = getattr(self, 'chandoanbandau', None).text() if hasattr(self, 'chandoanbandau') else None
                cur.execute(sql, (phieu_kham_id, ten, so_luong, don_gia, thanh_tien, kh_text, chan_text))
            else:
                cur.execute(
                    "INSERT INTO chi_dinh(phieu_kham_id, ten_dich_vu, so_luong, don_gia, thanh_tien) VALUES(?,?,?,?,?)",
                    (phieu_kham_id, ten, so_luong, don_gia, thanh_tien)
                )
            chi_id = cur.lastrowid
            so_chi_dinh = f"CD{chi_id:04d}"
            cur.execute("UPDATE chi_dinh SET so_chi_dinh = ? WHERE id = ?", (so_chi_dinh, chi_id))
            conn.commit()
            return chi_id, so_chi_dinh
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_chi_dinh_in_db(self, chi_id):
        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            cur.execute("DELETE FROM chi_dinh WHERE id = ?", (chi_id,))
            conn.commit()
            logger.info(f"delete_chi_dinh_in_db: deleted chi_dinh id={chi_id}")
        except Exception:
            conn.rollback()
            logger.exception(f"delete_chi_dinh_in_db: failed to delete chi_dinh id={chi_id}")
            raise
        finally:
            conn.close()

    def update_chi_dinh_in_db(self, chi_id, ten, so_luong, don_gia, thanh_tien):
        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.execute("BEGIN")
            cur.execute("UPDATE chi_dinh SET ten_dich_vu = ?, so_luong = ?, don_gia = ?, thanh_tien = ? WHERE id = ?",
                        (ten, so_luong, don_gia, thanh_tien, chi_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def show_text_dialog(self, title, linked_input):
        """Hiển thị dialog cho phép nhập text và cập nhật vào input field tương ứng"""
        dialog = TextEditDialog(title, linked_input.text(), self)
        if dialog.exec_() == QDialog.Accepted:
            new_text = dialog.get_text()
            linked_input.setText(new_text)
            # Cập nhật text trên button
            if linked_input == self.khamlamsang:
                preview = new_text[:50] + "..." if len(new_text) > 50 else new_text
                if not preview.strip():
                    preview = "Nhấn để nhập"
                try:
                    self.lbl_khamlamsang.setText(preview)
                except Exception:
                    pass
            elif linked_input == self.chandoanbandau:
                preview = new_text[:50] + "..." if len(new_text) > 50 else new_text
                if not preview.strip():
                    preview = "Nhấn để nhập"
                try:
                    self.lbl_chandoanbandau.setText(preview)
                except Exception:
                    pass

    