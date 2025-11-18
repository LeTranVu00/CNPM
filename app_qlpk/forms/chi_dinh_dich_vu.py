import sys
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDateEdit, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QStringListModel
from PyQt5.QtGui import QFont

# --- CẤU HÌNH ĐƯỜNG DẪN IMPORT ---
# Thêm thư mục cha vào hệ thống để tìm thấy database.py và app_signals.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

#
# Import các module từ thư mục cha
try:
    from app_signals import app_signals
    from database import get_connection, initialize_database
except ImportError as e:
    print(f"Lỗi Import: {e}")
    # Fallback để không crash IDE khi xem code
    app_signals = None
    get_connection = None
    initialize_database = lambda: None

# Khởi tạo DB nếu cần
if initialize_database:
    initialize_database()

# Cấu hình ReportLab và Font
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_path = os.path.join(current_dir, "..", "fonts", "arial.ttf")
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

import logging

# Configure logging
LOG_PATH = os.path.join(parent_dir, 'app.log')
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

        self.setStyleSheet("""
            QDialog { background-color: white; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; min-width: 80px; }
            QPushButton:hover { background-color: #005a9e; }
            QTextEdit { border: 1px solid #ccc; border-radius: 3px; padding: 4px; }
            QTextEdit:focus { border-color: #0078D7; }
        """)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setFont(QFont("Arial", 10))
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
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
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()

    def mouseReleaseEvent(self, ev):
        self.clicked.emit()
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(ev)


class ChiDinhDichVu(QWidget):
    data_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_phieu_kham_id = None

        self.base_stylesheet = """
            QGroupBox { font-weight: bold; border: 1px solid #cccccc; border-radius: 3px; margin-top: 6px; padding-top: 6px; }
            QGroupBox::title { color: #0078D7; subcontrol-origin: margin; left: 7px; padding: 0 5px; }
            QLabel#required { font-weight: bold; color: #0078D7; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #005a9e; }
            QLineEdit, QDateEdit, QComboBox { padding: 3px; border: 1px solid #ccc; border-radius: 3px; }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus { border-color: #0078D7; }
            QTableWidget { gridline-color: #ddd; selection-background-color: #e6f2ff; selection-color: black; }
            QHeaderView::section { background-color: #0078D7; padding: 4px; border: 1px solid #ddd; font-weight: bold; color: white; }
        """
        self.setStyleSheet(self.base_stylesheet)

        self.initUI()

        # Load data
        self.load_dich_vu_list()
        self.load_benh_nhan_list()

        # Signals
        self.hoten.currentIndexChanged.connect(self.on_select_benh_nhan)

        # Lắng nghe signal từ form Tiếp đón (nếu form đó bắn signal patient_selected)
        if app_signals:
            try:
                app_signals.patient_selected.connect(self.on_external_patient_selected)
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
        grid_bn = QGridLayout()

        self.hoten = QComboBox()
        self.gioitinh = QLineEdit();
        self.gioitinh.setReadOnly(True)
        self.dienthoai = QLineEdit();
        self.dienthoai.setReadOnly(True)
        self.ngaysinh = QDateEdit();
        self.ngaysinh.setReadOnly(True);
        self.ngaysinh.setDisplayFormat("dd/MM/yyyy")

        self.diachi = QLineEdit();
        self.diachi.setReadOnly(True)
        self.sophieukham = QLineEdit();
        self.sophieukham.setReadOnly(True)
        self.sochidinh = QLineEdit();
        self.sochidinh.setReadOnly(True)
        self.ngaylap = QLineEdit(QDate.currentDate().toString("dd/MM/yyyy"));
        self.ngaylap.setReadOnly(True)
        self.tinhtrang = QLineEdit();
        self.tinhtrang.setReadOnly(True)

        self.doituong = QLineEdit();
        self.doituong.setReadOnly(True)
        self.nghenghiep = QLineEdit();
        self.nghenghiep.setReadOnly(True)
        self.socccd = QLineEdit();
        self.socccd.setReadOnly(True)
        self.tuoi = QLineEdit();
        self.tuoi.setReadOnly(True)
        self.phongkham = QLineEdit();
        self.phongkham.setReadOnly(True)
        self.tongtien = QLineEdit("0");
        self.tongtien.setReadOnly(True)

        self.nguoilap = QComboBox();
        self.nguoilap.addItems(["Bác sĩ", "Y tá"])
        self.bacsithuchien = QComboBox();
        self.bacsithuchien.addItems(["BS. Nguyễn Văn A", "BS. Trần Thị B"])

        # Hidden fields for actual data storage
        self.khamlamsang = QLineEdit();
        self.khamlamsang.hide()
        self.chandoanbandau = QLineEdit();
        self.chandoanbandau.hide()

        # Clickable labels
        self.lbl_khamlamsang = ClickableLabel("Nhấn để nhập")
        self.lbl_khamlamsang.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: white;")
        self.lbl_khamlamsang.doubleClicked.connect(lambda: self.show_text_dialog("Khám lâm sàng", self.khamlamsang))

        self.lbl_chandoanbandau = ClickableLabel("Nhấn để nhập")
        self.lbl_chandoanbandau.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: white;")
        self.lbl_chandoanbandau.doubleClicked.connect(lambda: self.show_text_dialog("Chẩn đoán", self.chandoanbandau))

        # Layout Grid
        grid_bn.addWidget(required_label("Họ và tên *"), 0, 0)
        grid_bn.addWidget(self.hoten, 0, 1)
        grid_bn.addWidget(QLabel("Số CCCD"), 0, 2);
        grid_bn.addWidget(self.socccd, 0, 3)
        grid_bn.addWidget(QLabel("Giới tính"), 0, 4);
        grid_bn.addWidget(self.gioitinh, 0, 5)

        grid_bn.addWidget(QLabel("Ngày sinh"), 1, 0);
        grid_bn.addWidget(self.ngaysinh, 1, 1)
        grid_bn.addWidget(QLabel("Điện thoại"), 1, 2);
        grid_bn.addWidget(self.dienthoai, 1, 3)
        grid_bn.addWidget(QLabel("Tuổi"), 1, 4);
        grid_bn.addWidget(self.tuoi, 1, 5)

        grid_bn.addWidget(QLabel("Địa chỉ"), 2, 0);
        grid_bn.addWidget(self.diachi, 2, 1)
        grid_bn.addWidget(QLabel("Đối tượng"), 2, 2);
        grid_bn.addWidget(self.doituong, 2, 3)
        grid_bn.addWidget(QLabel("Nghề nghiệp"), 2, 4);
        grid_bn.addWidget(self.nghenghiep, 2, 5)

        grid_bn.addWidget(QLabel("Số phiếu"), 3, 0);
        grid_bn.addWidget(self.sophieukham, 3, 1)
        grid_bn.addWidget(QLabel("Số chỉ định"), 3, 2);
        grid_bn.addWidget(self.sochidinh, 3, 3)
        grid_bn.addWidget(QLabel("Phòng khám"), 3, 4);
        grid_bn.addWidget(self.phongkham, 3, 5)

        grid_bn.addWidget(QLabel("Ngày lập"), 4, 0);
        grid_bn.addWidget(self.ngaylap, 4, 1)
        grid_bn.addWidget(QLabel("Người lập"), 4, 2);
        grid_bn.addWidget(self.nguoilap, 4, 3)
        grid_bn.addWidget(QLabel("Tình trạng"), 4, 4);
        grid_bn.addWidget(self.tinhtrang, 4, 5)

        grid_bn.addWidget(QLabel("Khám lâm sàng"), 5, 0)
        grid_bn.addWidget(self.lbl_khamlamsang, 5, 1, 1, 3)
        grid_bn.addWidget(QLabel("BS thực hiện"), 5, 4);
        grid_bn.addWidget(self.bacsithuchien, 5, 5)

        grid_bn.addWidget(QLabel("Chẩn đoán"), 6, 0)
        grid_bn.addWidget(self.lbl_chandoanbandau, 6, 1, 1, 3)
        grid_bn.addWidget(QLabel("Tổng tiền"), 6, 4);
        grid_bn.addWidget(self.tongtien, 6, 5)

        group_bn.setLayout(grid_bn)
        main_layout.addWidget(group_bn)

        # === 2. CHỈ ĐỊNH DỊCH VỤ ===
        group_cd = QGroupBox("CHỈ ĐỊNH DỊCH VỤ")
        grid_cd = QGridLayout()

        self.combo_dichvu = QComboBox()
        self.input_soluong = QLineEdit("1")
        self.input_dongia = QLineEdit("0")
        self.input_thanhtien = QLineEdit("0");
        self.input_thanhtien.setReadOnly(True)

        grid_cd.addWidget(QLabel("Tên dịch vụ"), 0, 0);
        grid_cd.addWidget(self.combo_dichvu, 0, 1)
        grid_cd.addWidget(QLabel("Số lượng"), 0, 2);
        grid_cd.addWidget(self.input_soluong, 0, 3)
        grid_cd.addWidget(QLabel("Đơn giá"), 1, 0);
        grid_cd.addWidget(self.input_dongia, 1, 1)
        grid_cd.addWidget(QLabel("Thành tiền"), 1, 2);
        grid_cd.addWidget(self.input_thanhtien, 1, 3)

        group_cd.setLayout(grid_cd)
        main_layout.addWidget(group_cd)

        self.combo_dichvu.currentIndexChanged.connect(self.on_select_dichvu)
        self.input_soluong.textChanged.connect(self.update_thanhtien)
        self.input_dongia.textChanged.connect(self.update_thanhtien)

        # === 3. DANH SÁCH ===
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["STT", "Tên dịch vụ", "Số lượng", "Đơn giá", "Thành tiền"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        group_ds = QGroupBox("DANH SÁCH DỊCH VỤ")
        vbox_ds = QVBoxLayout()
        vbox_ds.addWidget(self.table)
        group_ds.setLayout(vbox_ds)
        main_layout.addWidget(group_ds)

        # === 4. BUTTONS ===
        btn_layout = QHBoxLayout()
        self.btn_them = QPushButton("Thêm")
        self.btn_luu = QPushButton("Lưu")
        self.btn_sua = QPushButton("Sửa")
        self.btn_xoa = QPushButton("Xóa")
        self.btn_in = QPushButton("In phiếu")
        self.btn_thoat = QPushButton("Thoát")

        for b in [self.btn_them, self.btn_luu, self.btn_sua, self.btn_xoa, self.btn_in, self.btn_thoat]:
            b.setMinimumWidth(100)
            btn_layout.addWidget(b)

        main_layout.addLayout(btn_layout)

        self.btn_them.clicked.connect(self.on_them_dichvu)
        self.btn_luu.clicked.connect(self.on_luu)
        self.btn_xoa.clicked.connect(self.on_xoa_dichvu)
        self.btn_sua.clicked.connect(self.enable_edit)
        self.btn_in.clicked.connect(self.on_in)
        self.btn_thoat.clicked.connect(self.close)

    # --- LOGIC FUNCTIONS ---
    def load_benh_nhan_list(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, ho_ten FROM benh_nhan ORDER BY id DESC")
            rows = cur.fetchall()
            conn.close()

            self.hoten.blockSignals(True)
            self.hoten.clear()
            self.hoten.addItem("-- Chọn bệnh nhân --", None)
            for r in rows:
                self.hoten.addItem(r[1], r[0])
            self.hoten.blockSignals(False)
        except Exception as e:
            print(f"Lỗi load bệnh nhân: {e}")

    def load_dich_vu_list(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, ten_dich_vu, don_gia FROM dich_vu")
            rows = cur.fetchall()
            conn.close()

            self.combo_dichvu.clear()
            for r in rows:
                self.combo_dichvu.addItem(r[1], (r[0], r[2]))
        except Exception:
            pass

    def on_select_dichvu(self):
        data = self.combo_dichvu.currentData()
        if data:
            price = data[1]
            self.input_dongia.setText(f"{price:,.0f}".replace(",", "."))
            self.update_thanhtien()

    def update_thanhtien(self):
        try:
            sl = int(self.input_soluong.text() or 0)
            dg = float(self.input_dongia.text().replace(".", "") or 0)
            tt = sl * dg
            self.input_thanhtien.setText(f"{tt:,.0f}".replace(",", "."))
        except:
            pass

    def on_them_dichvu(self):
        ten = self.combo_dichvu.currentText()
        try:
            sl = int(self.input_soluong.text())
            dg = float(self.input_dongia.text().replace(".", ""))
            tt = sl * dg
        except:
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(ten))
        self.table.setItem(row, 2, QTableWidgetItem(str(sl)))
        self.table.setItem(row, 3, QTableWidgetItem(f"{dg:,.0f}".replace(",", ".")))

        item_tt = QTableWidgetItem(f"{tt:,.0f}".replace(",", "."))
        item_tt.setData(Qt.UserRole, tt)  # Lưu giá trị số để tính tổng
        self.table.setItem(row, 4, item_tt)

        self.recalculate_total()

    def recalculate_total(self):
        total = 0
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 4)
            if item:
                total += item.data(Qt.UserRole)
        self.tongtien.setText(f"{total:,.0f}".replace(",", "."))

    def on_xoa_dichvu(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.recalculate_total()

    def enable_edit(self):
        # Logic bật tắt sửa
        pass

    def on_select_benh_nhan(self):
        bn_id = self.hoten.currentData()
        if not bn_id: return

        # Load info from DB
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM benh_nhan WHERE id=?", (bn_id,))
        bn = cur.fetchone()
        if bn:
            # Cột: id, ho_ten, gioi_tinh, ngay_sinh, tuoi, dia_chi, dien_thoai...
            # Lưu ý index phụ thuộc vào cấu trúc bảng trong database.py
            self.gioitinh.setText(bn[2] or "")
            self.diachi.setText(bn[5] or "")
            self.dienthoai.setText(bn[6] or "")
        conn.close()

        # Sinh số phiếu tự động (Demo)
        self.sophieukham.setText(f"PK{bn_id}{datetime.now().strftime('%d%m')}")

    def on_external_patient_selected(self, bn_id):
        """Xử lý khi nhận signal từ form khác"""
        index = self.hoten.findData(bn_id)
        if index >= 0:
            self.hoten.setCurrentIndex(index)

    def on_luu(self):
        QMessageBox.information(self, "Thông báo", "Lưu thành công (Demo)")
        if app_signals:
            app_signals.data_changed.emit()
        self.data_saved.emit()

    def on_in(self):
        QMessageBox.information(self, "Thông báo", "Chức năng in đang phát triển")

    def show_text_dialog(self, title, linked_input):
        dlg = TextEditDialog(title, linked_input.text(), self)
        if dlg.exec_():
            txt = dlg.get_text()
            linked_input.setText(txt)
            # Update label preview
            lbl = self.lbl_khamlamsang if linked_input == self.khamlamsang else self.lbl_chandoanbandau
            lbl.setText(txt if txt else "Nhấn để nhập")
