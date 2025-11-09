# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtPrintSupport import QPrintPreviewWidget

class ThuTienDichVu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()
        
    def setupUi(self):
        self.setObjectName("ThuTienDichVuWidget")
        self.resize(1120, 876)
        
        # === Layout chính ===
        main_layout = QtWidgets.QHBoxLayout(self)
        
        # ===== GroupBox 1: Danh sách chờ thanh toán =====
        self.groupBox = QtWidgets.QGroupBox("DANH SÁCH CHỜ THANH TOÁN")
        self.groupBox.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        groupBox_layout = QtWidgets.QVBoxLayout(self.groupBox)
        
        # Frame nút và radio
        self.frmCacButton = QtWidgets.QFrame()
        frmCacButton_layout = QtWidgets.QHBoxLayout(self.frmCacButton)
        self.rdDaThanhToan = QtWidgets.QRadioButton("Đã thanh toán")
        self.napLai = QtWidgets.QPushButton("Nạp lại")
        self.btnDuyetThu = QtWidgets.QPushButton("Duyệt thu")
        frmCacButton_layout.addWidget(self.rdDaThanhToan)
        frmCacButton_layout.addWidget(self.napLai)
        frmCacButton_layout.addWidget(self.btnDuyetThu)
        groupBox_layout.addWidget(self.frmCacButton)
        
        # Frame danh sách bệnh nhân
        self.framHienTenBN = QtWidgets.QFrame()
        framHienTenBN_layout = QtWidgets.QVBoxLayout(self.framHienTenBN)
        
        # Dòng thông tin CK, Giảm tiền, BHYT
        info_layout = QtWidgets.QHBoxLayout()
        self.btnBenhNhan = QtWidgets.QPushButton("Bệnh nhân")
        self.labelCK = QtWidgets.QLabel("CK(%)")
        self.chietKhau = QtWidgets.QLineEdit("0")
        self.labelGiamTien = QtWidgets.QLabel("Giảm tiền")
        self.GiamTien = QtWidgets.QLineEdit()
        self.checkBoxBHYT = QtWidgets.QCheckBox("BHYT")
        info_layout.addWidget(self.btnBenhNhan)
        info_layout.addWidget(self.labelCK)
        info_layout.addWidget(self.chietKhau)
        info_layout.addWidget(self.labelGiamTien)
        info_layout.addWidget(self.GiamTien)
        info_layout.addWidget(self.checkBoxBHYT)
        framHienTenBN_layout.addLayout(info_layout)
        
        # Table danh sách chờ
        self.tableWidgetDSChoThanhToan = QtWidgets.QTableWidget()
        self.tableWidgetDSChoThanhToan.setColumnCount(8)
        self.tableWidgetDSChoThanhToan.setHorizontalHeaderLabels([
            "Dịch vụ", "SL", "T.Tiền", "CK(%)","T.Giảm", "TT.Tiền", "Y", "N"
        ])
        self.tableWidgetDSChoThanhToan.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tableWidgetDSChoThanhToan.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        framHienTenBN_layout.addWidget(self.tableWidgetDSChoThanhToan)
        
        groupBox_layout.addWidget(self.framHienTenBN)
        main_layout.addWidget(self.groupBox, 2)  # tỉ lệ 2:3
        
        # ===== GroupBox 2: Chi tiết thanh toán =====
        self.groupBox_2 = QtWidgets.QGroupBox("CHI TIẾT THANH TOÁN")
        self.groupBox_2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        groupBox2_layout = QtWidgets.QVBoxLayout(self.groupBox_2)
        
        # Thông tin bệnh nhân
        self.thongTinBN = QtWidgets.QFrame()
        thongTinBN_layout = QtWidgets.QGridLayout(self.thongTinBN)
        self.SoHoSo = QtWidgets.QLineEdit()
        self.NgayTT = QtWidgets.QDateEdit()
        self.NgayTT.setCalendarPopup(True)
        self.TenBN = QtWidgets.QLineEdit()
        self.DiaChi = QtWidgets.QLineEdit()
        self.GioiTinh = QtWidgets.QLineEdit()
        self.namSinh = QtWidgets.QDateEdit()
        self.namSinh.setCalendarPopup(True)
        self.dienThoai = QtWidgets.QLineEdit()
        self.Chuandoan = QtWidgets.QLineEdit()
        
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Số hồ sơ"), 0, 0)
        thongTinBN_layout.addWidget(self.SoHoSo, 0, 1)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Ngày"), 0, 2)
        thongTinBN_layout.addWidget(self.NgayTT, 0, 3)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Tên BN"), 1, 0)
        thongTinBN_layout.addWidget(self.TenBN, 1, 1, 1, 3)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Địa chỉ"), 2, 0)
        thongTinBN_layout.addWidget(self.DiaChi, 2, 1, 1, 3)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Giới tính"), 0, 4)
        thongTinBN_layout.addWidget(self.GioiTinh, 0, 5)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Năm sinh"), 0, 6)
        thongTinBN_layout.addWidget(self.namSinh, 0, 7)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Điện thoại"), 1, 4)
        thongTinBN_layout.addWidget(self.dienThoai, 1, 5, 1, 3)
        thongTinBN_layout.addWidget(QtWidgets.QLabel("Chuẩn đoán"), 2, 4)
        thongTinBN_layout.addWidget(self.Chuandoan, 2, 5, 1, 3)
        
        groupBox2_layout.addWidget(self.thongTinBN)
        
        # Thông tin tiền
        self.frmThongTinTien = QtWidgets.QFrame()
        frmThongTinTien_layout = QtWidgets.QGridLayout(self.frmThongTinTien)
        self.TongTien = QtWidgets.QLineEdit("0")
        self.TienGiam = QtWidgets.QLineEdit("0")
        self.comboBox = QtWidgets.QComboBox()
        self.PhaiThu = QtWidgets.QLineEdit("0")
        self.ThucThu = QtWidgets.QLineEdit("0")
        self.btnThuTien = QtWidgets.QPushButton("Thu Tiền")
        self.btnXemLai = QtWidgets.QPushButton("Xem Lại")
        
        frmThongTinTien_layout.addWidget(QtWidgets.QLabel("Tổng tiền:"), 0, 0)
        frmThongTinTien_layout.addWidget(self.TongTien, 0, 1)
        frmThongTinTien_layout.addWidget(QtWidgets.QLabel("Tiền giảm"), 0, 2)
        frmThongTinTien_layout.addWidget(self.TienGiam, 0, 3)
        frmThongTinTien_layout.addWidget(QtWidgets.QLabel("HTTT:"), 1, 0)
        frmThongTinTien_layout.addWidget(self.comboBox, 1, 1, 1, 3)
        frmThongTinTien_layout.addWidget(QtWidgets.QLabel("Phải thu:"), 0, 4)
        frmThongTinTien_layout.addWidget(self.PhaiThu, 0, 5)
        frmThongTinTien_layout.addWidget(QtWidgets.QLabel("Thực thu:"), 1, 4)
        frmThongTinTien_layout.addWidget(self.ThucThu, 1, 5)
        frmThongTinTien_layout.addWidget(self.btnThuTien, 0, 6, 2, 1)
        frmThongTinTien_layout.addWidget(self.btnXemLai, 0, 7, 2, 1)
        
        groupBox2_layout.addWidget(self.frmThongTinTien)
        
        # Print Preview
        self.frmPrintPreView = QPrintPreviewWidget()
        self.frmPrintPreView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        groupBox2_layout.addWidget(self.frmPrintPreView)
        
        main_layout.addWidget(self.groupBox_2, 3)
        
        # Kết thúc setupUi
        self.setLayout(main_layout)
