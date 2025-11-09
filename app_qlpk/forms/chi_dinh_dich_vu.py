from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from database import get_connection

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Đăng ký font Unicode tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

class ChiDinhDichVu(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Arial", 10))
        self.setStyleSheet("QGroupBox { font-weight: bold; color: #1565c0; }")
        self.initUI()
        self.load_benh_nhan()
        self.load_dich_vu_mau()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # === 1. THÔNG TIN BỆNH NHÂN ===
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        grid_bn = QGridLayout()

        self.combo_hoten = QComboBox()
        self.input_gioitinh = QLineEdit()
        self.input_ngaysinh = QLineEdit()
        self.input_dienthoai = QLineEdit()
        self.input_diachi = QLineEdit()

        grid_bn.addWidget(QLabel("Họ và tên"), 0, 0)
        grid_bn.addWidget(self.combo_hoten, 0, 1)
        grid_bn.addWidget(QLabel("Giới tính"), 0, 2)
        grid_bn.addWidget(self.input_gioitinh, 0, 3)
        grid_bn.addWidget(QLabel("Ngày sinh"), 1, 0)
        grid_bn.addWidget(self.input_ngaysinh, 1, 1)
        grid_bn.addWidget(QLabel("Điện thoại"), 1, 2)
        grid_bn.addWidget(self.input_dienthoai, 1, 3)
        grid_bn.addWidget(QLabel("Địa chỉ"), 2, 0)
        grid_bn.addWidget(self.input_diachi, 2, 1, 1, 3)
        group_bn.setLayout(grid_bn)
        main_layout.addWidget(group_bn)

        # === 2. CHỈ ĐỊNH DỊCH VỤ ===
        group_cd = QGroupBox("CHỈ ĐỊNH DỊCH VỤ")
        grid_cd = QGridLayout()

        self.combo_dichvu = QComboBox()
        self.input_soluong = QLineEdit("1")
        self.input_dongia = QLineEdit()
        self.input_thanhtien = QLineEdit()
        self.input_thanhtien.setReadOnly(True)
        self.btn_them = QPushButton("➕ Thêm")

        grid_cd.addWidget(QLabel("Tên dịch vụ"), 0, 0)
        grid_cd.addWidget(self.combo_dichvu, 0, 1)
        grid_cd.addWidget(QLabel("Số lượng"), 0, 2)
        grid_cd.addWidget(self.input_soluong, 0, 3)
        grid_cd.addWidget(QLabel("Đơn giá"), 1, 0)
        grid_cd.addWidget(self.input_dongia, 1, 1)
        grid_cd.addWidget(QLabel("Thành tiền"), 1, 2)
        grid_cd.addWidget(self.input_thanhtien, 1, 3)
        grid_cd.addWidget(self.btn_them, 0, 4, 2, 1)
        group_cd.setLayout(grid_cd)
        main_layout.addWidget(group_cd)

        # === 3. DANH SÁCH DỊCH VỤ ===
        group_ds = QGroupBox("DANH SÁCH DỊCH VỤ ĐÃ CHỈ ĐỊNH")
        vbox_ds = QVBoxLayout()

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["STT", "Tên dịch vụ", "Số lượng", "Đơn giá", "Thành tiền"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        vbox_ds.addWidget(self.table)
        group_ds.setLayout(vbox_ds)
        main_layout.addWidget(group_ds)

        # === 4. NÚT CHỨC NĂNG ===
        btn_layout = QHBoxLayout()
        self.btn_luu = QPushButton("💾 Lưu (F2)")
        self.btn_xoa = QPushButton("🗑️ Xóa")
        self.btn_in = QPushButton("🖨️ In phiếu CD")
        self.btn_thoat = QPushButton("❌ Thoát")
        for b in [self.btn_luu, self.btn_xoa, self.btn_in, self.btn_thoat]:
            b.setMinimumWidth(120)
        btn_layout.addWidget(self.btn_luu)
        btn_layout.addWidget(self.btn_xoa)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_in)
        btn_layout.addWidget(self.btn_thoat)
        main_layout.addLayout(btn_layout)

        # === EVENT ===
        self.combo_dichvu.currentTextChanged.connect(self.cap_nhat_gia)
        self.btn_them.clicked.connect(self.them_dich_vu)
        self.btn_xoa.clicked.connect(self.xoa_dong)
        self.btn_luu.clicked.connect(self.luu_du_lieu)
        self.btn_in.clicked.connect(self.in_phieu) 

    # ========================== FUNCTION ==========================
    def load_benh_nhan(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ho_ten FROM benh_nhan")
        rows = cur.fetchall()
        conn.close()
        self.combo_hoten.clear()
        self.combo_hoten.addItems([r[0] for r in rows])

    def load_dich_vu_mau(self):
        self.dichvu_dict = {
            "Khám và tư vấn": 80000,
            "Siêu âm tổng quát": 120000,
            "Xét nghiệm máu": 150000,
            "Chụp X-quang": 180000,
            "Điện tim ECG": 90000
        }
        self.combo_dichvu.addItems(self.dichvu_dict.keys())
        self.cap_nhat_gia()

    def cap_nhat_gia(self):
        dv = self.combo_dichvu.currentText()
        if dv in self.dichvu_dict:
            gia = self.dichvu_dict[dv]
            self.input_dongia.setText(str(gia))
            sl = int(self.input_soluong.text() or 1)
            self.input_thanhtien.setText(str(sl * gia))

    def them_dich_vu(self):
        dv = self.combo_dichvu.currentText()
        sl = int(self.input_soluong.text())
        dg = float(self.input_dongia.text())
        tt = sl * dg
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(dv))
        self.table.setItem(row, 2, QTableWidgetItem(str(sl)))
        self.table.setItem(row, 3, QTableWidgetItem(str(dg)))
        self.table.setItem(row, 4, QTableWidgetItem(str(tt)))

    def xoa_dong(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def luu_du_lieu(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có dịch vụ nào được thêm.")
            return
        QMessageBox.information(self, "Thành công", "Đã lưu phiếu chỉ định dịch vụ!")

    def in_phieu(self):
        ho_ten = self.combo_hoten.currentText()
        file_name = f"phieu_chidinh_{ho_ten.replace(' ', '_')}.pdf"
        file_path = os.path.join(os.getcwd(), file_name)
        c = canvas.Canvas(file_path, pagesize=A4)
        c.setFont("ArialUnicode", 14)
        c.drawCentredString(300, 800, "PHIẾU CHỈ ĐỊNH DỊCH VỤ")
        c.setFont("ArialUnicode", 11)
        c.drawString(50, 770, f"Họ tên: {ho_ten}")
        c.drawString(50, 750, f"Ngày lập: {QDate.currentDate().toString('dd/MM/yyyy')}")
        y = 720
        c.setFont("ArialUnicode", 10)
        c.drawString(50, y, "Tên dịch vụ")
        c.drawString(250, y, "Số lượng")
        c.drawString(350, y, "Đơn giá")
        c.drawString(450, y, "Thành tiền")
        y -= 20
        for i in range(self.table.rowCount()):
            c.drawString(50, y, self.table.item(i, 1).text())
            c.drawString(250, y, self.table.item(i, 2).text())
            c.drawString(350, y, self.table.item(i, 3).text())
            c.drawString(450, y, self.table.item(i, 4).text())
            y -= 20
        c.save()
        QMessageBox.information(self, "In phiếu", f"Đã tạo file PDF: {file_path}")
