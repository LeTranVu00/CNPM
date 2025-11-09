# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QAbstractItemView

class ThongKeThuChi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Form")
        self.resize(1207, 600)

        # === Layout chính ===
        main_layout = QtWidgets.QVBoxLayout(self)

        # --- Top layout: GroupBox 1 + GroupBox 2 ---
        top_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_layout)

        # === GroupBox 1: Điều kiện thống kê ===
        self.groupBox = QtWidgets.QGroupBox("ĐIỀU KIỆN THỐNG KÊ")
        self.groupBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_layout.addWidget(self.groupBox)

        grid_cond = QtWidgets.QGridLayout(self.groupBox)

        # Các label + input
        self.label = QtWidgets.QLabel("Số Phiếu")
        self.Sophieu = QtWidgets.QLineEdit()
        grid_cond.addWidget(self.label, 0, 0)
        grid_cond.addWidget(self.Sophieu, 0, 1)

        self.label_2 = QtWidgets.QLabel("Người Lập")
        self.nguoiLap = QtWidgets.QComboBox()
        self.nguoiLap.setEditable(True)
        self.nguoiLap.addItems(["Bác sĩ", "Quản trị", "Tiếp đón"])
        grid_cond.addWidget(self.label_2, 1, 0)
        grid_cond.addWidget(self.nguoiLap, 1, 1)

        self.label_3 = QtWidgets.QLabel("Khoản TC")
        self.khoanTC = QtWidgets.QComboBox()
        self.khoanTC.setEditable(True)
        grid_cond.addWidget(self.label_3, 2, 0)
        grid_cond.addWidget(self.khoanTC, 2, 1)

        self.label_4 = QtWidgets.QLabel("Loại Quỹ")
        self.loaiQuy = QtWidgets.QComboBox()
        self.loaiQuy.setEditable(True)
        grid_cond.addWidget(self.label_4, 3, 0)
        grid_cond.addWidget(self.loaiQuy, 3, 1)

        self.label_5 = QtWidgets.QLabel("Bệnh nhân")
        self.BenhNhan = QtWidgets.QComboBox()
        self.BenhNhan.setEditable(True)
        grid_cond.addWidget(self.label_5, 4, 0)
        grid_cond.addWidget(self.BenhNhan, 4, 1)

        self.label_6 = QtWidgets.QLabel("Từ ngày")
        self.dateFrom = QtWidgets.QDateEdit()
        self.dateFrom.setCalendarPopup(True)
        grid_cond.addWidget(self.label_6, 0, 2)
        grid_cond.addWidget(self.dateFrom, 0, 3)

        self.label_7 = QtWidgets.QLabel("Đến ngày")
        self.dateTo = QtWidgets.QDateEdit()
        self.dateTo.setCalendarPopup(True)
        grid_cond.addWidget(self.label_7, 0, 4)
        grid_cond.addWidget(self.dateTo, 0, 5)

        # Hình thức thanh toán
        self.frame_thanh_toan = QtWidgets.QFrame()
        layout_tt = QtWidgets.QHBoxLayout(self.frame_thanh_toan)
        self.rdNganhang = QtWidgets.QRadioButton("Ngân hàng")
        self.rdTienmat = QtWidgets.QRadioButton("Tiền mặt")
        self.rdTT_TatCa = QtWidgets.QRadioButton("Tất cả")
        layout_tt.addWidget(self.rdNganhang)
        layout_tt.addWidget(self.rdTienmat)
        layout_tt.addWidget(self.rdTT_TatCa)
        grid_cond.addWidget(self.frame_thanh_toan, 1, 2, 1, 4)

        # Loại thu chi
        self.frame_loai_thu_chi = QtWidgets.QFrame()
        layout_ltc = QtWidgets.QHBoxLayout(self.frame_loai_thu_chi)
        self.rdoLoai_Thu = QtWidgets.QRadioButton("Thu")
        self.rdLoai_Chi = QtWidgets.QRadioButton("Chi")
        self.rdLoai_Tatca = QtWidgets.QRadioButton("Tất cả")
        layout_ltc.addWidget(self.rdoLoai_Thu)
        layout_ltc.addWidget(self.rdLoai_Chi)
        layout_ltc.addWidget(self.rdLoai_Tatca)
        grid_cond.addWidget(self.frame_loai_thu_chi, 2, 2, 1, 4)

        # Trạng thái thanh toán
        self.frame_trang_thai_thanhtoan = QtWidgets.QFrame()
        layout_tt2 = QtWidgets.QHBoxLayout(self.frame_trang_thai_thanhtoan)
        self.rdTrangThai_Huy = QtWidgets.QRadioButton("Hủy")
        self.rdTrangThai_koHuy = QtWidgets.QRadioButton("Không hủy")
        self.rdTrangThai_TatCa = QtWidgets.QRadioButton("Tất cả")
        layout_tt2.addWidget(self.rdTrangThai_Huy)
        layout_tt2.addWidget(self.rdTrangThai_koHuy)
        layout_tt2.addWidget(self.rdTrangThai_TatCa)
        grid_cond.addWidget(self.frame_trang_thai_thanhtoan, 3, 2, 1, 4)

        # === GroupBox 2: Thông tin tổng hợp ===
        self.groupBox_2 = QtWidgets.QGroupBox("THÔNG TIN TỔNG HỢP")
        self.groupBox_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_layout.addWidget(self.groupBox_2)

        grid_info = QtWidgets.QGridLayout(self.groupBox_2)
        self.label_8 = QtWidgets.QLabel("Tổng số phiếu")
        self.TongSophieu = QtWidgets.QLineEdit()
        grid_info.addWidget(self.label_8, 0, 0)
        grid_info.addWidget(self.TongSophieu, 0, 1)

        self.label_9 = QtWidgets.QLabel("Thu")
        self.TongTienThu = QtWidgets.QLineEdit("0")
        self.TongTienThu.setReadOnly(True)
        grid_info.addWidget(self.label_9, 1, 0)
        grid_info.addWidget(self.TongTienThu, 1, 1)

        self.label_10 = QtWidgets.QLabel("Chi")
        self.TongTienChi = QtWidgets.QLineEdit("0")
        self.TongTienChi.setReadOnly(True)
        grid_info.addWidget(self.label_10, 2, 0)
        grid_info.addWidget(self.TongTienChi, 2, 1)

        self.label_11 = QtWidgets.QLabel("Tổng")
        self.TongTienTC = QtWidgets.QLineEdit("0")
        self.TongTienTC.setReadOnly(True)
        grid_info.addWidget(self.label_11, 3, 0)
        grid_info.addWidget(self.TongTienTC, 3, 1)

        # Nút thao tác
        self.btnXem = QtWidgets.QPushButton("Xem")
        self.pushButton = QtWidgets.QPushButton("In TK")
        self.pushButton_2 = QtWidgets.QPushButton("Thoát")
        grid_info.addWidget(self.btnXem, 4, 0)
        grid_info.addWidget(self.pushButton, 4, 1)
        grid_info.addWidget(self.pushButton_2, 4, 2)

        # === TableWidget ===
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(12)
        self.tableWidget.setRowCount(0)
        main_layout.addWidget(self.tableWidget)

        headers = ["Ngày", "Số Phiếu", "Khoản", "Quỹ", "Đơn vị - Bệnh nhân",
                   "Tổng Tiền", "Tiền giảm", "Thành Tiền", "Thực thu", "Thực chi",
                   "Người lập", "Hủy"]
        self.tableWidget.setHorizontalHeaderLabels(headers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
