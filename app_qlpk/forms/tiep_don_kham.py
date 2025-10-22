from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox, QDateEdit,
    QTableWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QSplitter, QHeaderView, QCompleter,
    QTableWidgetItem, QMessageBox, QAbstractItemView
)
# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os

# Đăng ký font tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont
from database import get_connection, initialize_database
initialize_database()

class TiepDonKham(QWidget):
    def __init__(self):
        self.is_resetting = False # Tránh gọi đệ quy khi reset form
        super().__init__()
        self.initUI() # Khởi tạo giao diện
        self.is_edit_mode = False  # Biến trạng thái chỉnh sửa
        self.selected_ma_hoso = None  # Mã hồ sơ đang chọn để sửa
        self.load_benh_nhan_list() # Load danh sách bệnh nhân vào combobox
        self.reset_form() # Khởi đầu reset form
        self.connect_combobox_event() # Kết nối sự kiện chọn combobox
        self.load_danh_sach_tiep_don() # Load danh sách tiếp đón
        self.load_thongke_luot_tiepdon() # Load thống kê lượt tiếp đón

        # Khi khởi tạo, load danh sách bệnh nhân vào combobox
    def load_benh_nhan_list(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ho_ten FROM benh_nhan ORDER BY ho_ten")
        names = [row[0] for row in cur.fetchall()]
        conn.close()
    
        # Gắn danh sách vào combobox và completer
        self.combo_hoten.clear()
        self.combo_hoten.addItems(names)
    
        model = QStringListModel(names)
        self.completer.setModel(model)
    
    def update_age(self):
        today = QDate.currentDate()
        birth = self.ngaysinh.date()
        age = birth.daysTo(today) // 365
        self.tuoi.setText(str(age))



    def initUI(self):
        # Font mặc định
        self.setFont(QFont("Arial", 10))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # ========== NHÓM 1: THÔNG TIN BỆNH NHÂN + THỐNG KÊ LƯỢT ==========
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setHandleWidth(4)

        # --- Bên trái: Thông tin bệnh nhân ---
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        group_bn.setStyleSheet("QGroupBox { font-weight: bold; color: #d32f2f; }")
        form_bn = QGridLayout()
        form_bn.setHorizontalSpacing(10)
        form_bn.setVerticalSpacing(6)

        # Họ tên (ComboBox có thể gõ)
        form_bn.addWidget(QLabel("Họ và tên "), 0, 0)
        self.combo_hoten = QComboBox()
        self.combo_hoten.setEditable(True)

        # Completer gợi ý
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(False)
        self.combo_hoten.setCompleter(self.completer)
        form_bn.addWidget(self.combo_hoten, 0, 1)

        # Giới tính
        form_bn.addWidget(QLabel("Giới tính "), 0, 2)
        self.gioitinh = QComboBox()
        self.gioitinh.addItem("Chọn giới tính")
        self.gioitinh.model().item(0).setFlags(Qt.NoItemFlags)
        self.gioitinh.addItems(["Nam", "Nữ", "Khác"])
        form_bn.addWidget(self.gioitinh, 0, 3)

        # Ngày sinh
        form_bn.addWidget(QLabel("Ngày sinh "), 1, 0)
        self.ngaysinh = QDateEdit()
        self.ngaysinh.setDate(QDate.currentDate())
        self.ngaysinh.setDisplayFormat("dd/MM/yyyy")
        form_bn.addWidget(self.ngaysinh, 1, 1)

        # Tuổi (readonly)
        form_bn.addWidget(QLabel("Tuổi"), 1, 2)
        self.tuoi = QLineEdit()
        self.tuoi.setReadOnly(True)
        form_bn.addWidget(self.tuoi, 1, 3)

        self.ngaysinh.dateChanged.connect(self.update_age)

        # Địa chỉ
        form_bn.addWidget(QLabel("Địa chỉ"), 2, 0)
        self.input_diachi = QLineEdit()
        form_bn.addWidget(self.input_diachi, 2, 1, 1, 3)

        # Điện thoại
        form_bn.addWidget(QLabel("Điện thoại"), 3, 0)
        self.input_dienthoai = QLineEdit()
        form_bn.addWidget(self.input_dienthoai, 3, 1)

        # Đối tượng
        form_bn.addWidget(QLabel("Đối tượng"), 3, 2)
        self.doituong = QComboBox()
        self.doituong.addItem("-Chọn đối tượng-")
        self.doituong.model().item(0).setFlags(Qt.NoItemFlags)
        self.doituong.addItems(["BHYT", "Dân sự", "Khác"])
        form_bn.addWidget(self.doituong, 3, 3)

        # Nghề nghiệp
        form_bn.addWidget(QLabel("Nghề nghiệp"), 4, 0)
        self.input_nghenghiep = QLineEdit()
        form_bn.addWidget(self.input_nghenghiep, 4, 1)

        # Người giới thiệu
        form_bn.addWidget(QLabel("Người giới thiệu"), 4, 2)
        self.nguoigt = QComboBox()
        self.nguoigt.addItem("-Chọn người giới thiệu-")
        self.nguoigt.model().item(0).setFlags(Qt.NoItemFlags)
        self.nguoigt.addItems(["Bác sĩ", "Tiếp tân", "Khác"])
        form_bn.addWidget(self.nguoigt, 4, 3)

        # Loại khám
        form_bn.addWidget(QLabel("Loại khám "), 5, 0)
        self.loaikham = QComboBox()
        self.loaikham.addItem("-Nhấn để chọn-")
        self.loaikham.model().item(0).setFlags(Qt.NoItemFlags)
        self.loaikham.addItems(["Khám và tư vấn", "Kê đơn", "Khác"])
        form_bn.addWidget(self.loaikham, 5, 1)

        # Số cccd
        form_bn.addWidget(QLabel("Số CCCD"), 5, 2)
        self.input_cccd = QLineEdit()
        form_bn.addWidget(self.input_cccd, 5, 3)

        group_bn.setLayout(form_bn)


        # --- Bên phải: Thống kê lượt tiếp đón ---
        group_thongke = QGroupBox("THỐNG KÊ LƯỢT TIẾP ĐÓN")
        group_thongke.setStyleSheet("QGroupBox { font-weight: bold; color: #d32f2f; }")
        thongke_layout = QVBoxLayout()
        self.table_thongke = QTableWidget(0, 3)
        self.table_thongke.setHorizontalHeaderLabels(["Phòng khám", "Tiếp đón", "Đã khám"])
        # 🚫 Không cho chỉnh sửa ô
        self.table_thongke.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # ✅ Khi chọn, chỉ được chọn nguyên hàng
        self.table_thongke.setSelectionBehavior(QAbstractItemView.SelectRows)

        # ✅ Không cho chọn nhiều hàng cùng lúc
        self.table_thongke.setSelectionMode(QAbstractItemView.SingleSelection)

        # ✅ Ẩn cột số thứ tự bên trái
        self.table_thongke.verticalHeader().setVisible(False)

        # ✅ Căn đều cột và hàng cho đẹp
        self.table_thongke.horizontalHeader().setStretchLastSection(True)
        self.table_thongke.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ✅ Màu xen kẽ (nhìn dễ hơn)
        self.table_thongke.setAlternatingRowColors(True)
        self.table_thongke.setStyleSheet("alternate-background-color: #f9f9f9;")
        self.table_thongke.horizontalHeader().setStretchLastSection(True)
        self.table_thongke.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table_thongke.horizontalHeader().setStretchLastSection(True)
        self.table_thongke.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        thongke_layout.addWidget(self.table_thongke)
        group_thongke.setLayout(thongke_layout)

        top_splitter.addWidget(group_bn)
        top_splitter.addWidget(group_thongke)
        top_splitter.setStretchFactor(0, 3)
        top_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(top_splitter)

        # ========== NHÓM 2: THÔNG TIN TIẾP ĐÓN BAN ĐẦU ==========
        group_tiepdon = QGroupBox("THÔNG TIN TIẾP ĐÓN BAN ĐẦU")
        group_tiepdon.setStyleSheet("QGroupBox { font-weight: bold; color: #d32f2f; }")
        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(10)
        grid2.setVerticalSpacing(6)

        grid2.addWidget(QLabel("Số hồ sơ"), 0, 0)
        self.sohoso = QLineEdit()
        # Tự động sinh, không cho sửa
        self.sohoso.setReadOnly(True)
        grid2.addWidget(self.sohoso, 0, 1)

        grid2.addWidget(QLabel("Tình trạng BN"), 0, 2)
        self.combo_tinhtrang = QComboBox()
        self.combo_tinhtrang.addItem("-Nhấn để chọn-")
        self.combo_tinhtrang.model().item(0).setFlags(Qt.NoItemFlags)
        self.combo_tinhtrang.addItems(["Ổn định", "Nặng", "Nguy kịch", "Đang điều trị", "Khỏi bệnh"])
        grid2.addWidget(self.combo_tinhtrang, 0, 3)

        grid2.addWidget(QLabel("Tiền khám"), 0, 4)
        self.input_tienkham = QLineEdit("0")
        grid2.addWidget(self.input_tienkham, 0, 5)

        grid2.addWidget(QLabel("Phòng khám"), 1, 0)
        self.combo_phongkham = QComboBox()
        self.combo_phongkham.addItem("-Nhấn để chọn-")
        self.combo_phongkham.model().item(0).setFlags(Qt.NoItemFlags)
        self.combo_phongkham.addItems([
            "Phòng Khám Nội tổng quát", "Phòng Khám Ngoại", "Phòng Tai - Mũi - Họng",
            "Phòng Mắt", "Phòng Răng - Hàm - Mặt", "Phòng Da liễu",
            "Phòng Sản - Phụ khoa", "Phòng Nhi", "Phòng Khám Đông y"
        ])
        grid2.addWidget(self.combo_phongkham, 1, 1)

        grid2.addWidget(QLabel("Ngày lập"), 1, 2)
        self.date_ngaylap = QDateEdit(QDate.currentDate())
        self.date_ngaylap.setDisplayFormat("dd/MM/yyyy")
        grid2.addWidget(self.date_ngaylap, 1, 3)

        grid2.addWidget(QLabel("NV tiếp đón"), 1, 4)
        self.combo_nvtiepdon = QComboBox()
        self.combo_nvtiepdon.addItem("-Nhấn để chọn-")
        self.combo_nvtiepdon.model().item(0).setFlags(Qt.NoItemFlags)  # Không cho chọn mục đầu tiên
        self.combo_nvtiepdon.addItems(["Nguyễn Thị Lan", "Trần Văn Hùng", "Phạm Thu Trang", "Lê Minh Đức"])
        grid2.addWidget(self.combo_nvtiepdon, 1, 5)

        grid2.addWidget(QLabel("Bác sỹ khám"), 2, 0)
        self.combo_bacsi = QComboBox()
        self.combo_bacsi.addItem("-Nhấn để chọn-")
        self.combo_bacsi.model().item(0).setFlags(Qt.NoItemFlags)
        self.combo_bacsi.addItems(["BS. Nguyễn Văn A", "BS. Trần Thị B", "BS. Lê Văn C"])
        grid2.addWidget(self.combo_bacsi, 2, 1)

        grid2.addWidget(QLabel("Huyết áp (mmHg)"), 2, 2)
        self.input_huyetap = QLineEdit()
        grid2.addWidget(self.input_huyetap, 2, 3)

        grid2.addWidget(QLabel("Nhiệt độ (°C)"), 2, 4)
        self.input_nhietdo = QLineEdit()
        grid2.addWidget(self.input_nhietdo, 2, 5)

        grid2.addWidget(QLabel("Chiều cao (cm)"), 3, 0)
        self.input_chieucao = QLineEdit()
        grid2.addWidget(self.input_chieucao, 3, 1)

        grid2.addWidget(QLabel("Cân nặng (kg)"), 3, 2)
        self.input_cannang = QLineEdit()
        grid2.addWidget(self.input_cannang, 3, 3)

        group_tiepdon.setLayout(grid2)
        main_layout.addWidget(group_tiepdon)


        # ========== NHÓM 3: DANH SÁCH PHIẾU TIẾP ĐÓN KCB ==========
        group_ds = QGroupBox("DANH SÁCH PHIẾU TIẾP ĐÓN KCB")
        group_ds.setStyleSheet("QGroupBox { font-weight: bold; color: #d32f2f; }")
        vbox = QVBoxLayout()
        self.tableTiepDon = QTableWidget(0, 6)
        self.tableTiepDon.setHorizontalHeaderLabels(["Số hồ sơ", "Ngày lập", "Phòng khám", "Họ tên BN", "Bác sĩ khám", "Tình trạng"])
        # Thêm signal khi chọn 1 hàng
        self.tableTiepDon.cellClicked.connect(self.on_row_selected)
        self.selected_ma_hoso = None
        self.tableTiepDon.horizontalHeader().setStretchLastSection(True)
        self.tableTiepDon.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 🚫 Không cho phép chỉnh sửa
        self.tableTiepDon.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # ✅ Khi chọn, chỉ được chọn nguyên hàng
        self.tableTiepDon.setSelectionBehavior(QAbstractItemView.SelectRows)

        # ✅ Không cho chọn nhiều hàng
        self.tableTiepDon.setSelectionMode(QAbstractItemView.SingleSelection)

        # ✅ Ẩn cột số thứ tự bên trái
        self.tableTiepDon.verticalHeader().setVisible(False)

        # ✅ Làm đẹp bảng (màu xen kẽ)
        self.tableTiepDon.setAlternatingRowColors(True)
        self.tableTiepDon.setStyleSheet("alternate-background-color: #f9f9f9;")

        # ✅ (Tùy chọn) Căn giữa chữ trong toàn bảng
        self.tableTiepDon.setStyleSheet("""
            QTableWidget::item {
                text-align: center;
            }
        """)


        self.tableTiepDon.horizontalHeader().setStretchLastSection(True)
        self.tableTiepDon.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vbox.addWidget(self.tableTiepDon)
        group_ds.setLayout(vbox)
        main_layout.addWidget(group_ds, 1)  # hệ số giãn = 1 để tự kéo full không gian còn lại

        # ========== NHÓM 4: CÁC NÚT CHỨC NĂNG ==========
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        # Tạo từng nút riêng để gán chức năng
        self.btn_nhapmoi = QPushButton("Nhập mới (F1)")
        self.btn_sua = QPushButton("Sửa")
        self.btn_xoa = QPushButton("Xóa")
        self.btn_inphieu = QPushButton("In phiếu")
        self.btn_instt = QPushButton("In STT")

        # Set kích thước
        for btn in [self.btn_nhapmoi, self.btn_sua, self.btn_xoa, self.btn_inphieu, self.btn_instt]:
            btn.setMinimumWidth(100)
            buttons.addWidget(btn)

        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # Gán sự kiện nút "Nhập mới" để lưu dữ liệu
        self.btn_nhapmoi.clicked.disconnect() if self.btn_nhapmoi.receivers(self.btn_nhapmoi.clicked) else None
        self.btn_nhapmoi.clicked.connect(self.save_and_reset)

        # Gán sự kiện nút "Sửa"
        self.btn_sua.clicked.connect(self.sua_du_lieu)

        # Gán sự kiện nút "Xóa"
        self.btn_xoa.clicked.connect(self.xoa_du_lieu)

        # Gán sự kiện nút "In phiếu"
        self.btn_inphieu.clicked.connect(self.in_phieu_tiep_don)

        # Gán sự kiện nút "In STT"
        self.btn_instt.clicked.connect(self.in_so_thu_tu)


    # ---------------------------
    # Helper: kiểm tra cột có tồn tại
    # ---------------------------
    def table_has_column(self, conn, table, column):
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        return column in cols


    # ---------------------------
    # Helper: thêm cột nếu thiếu
    # ---------------------------
    def add_column_if_missing(self, conn, table, column, col_type="TEXT"):
        if not self.table_has_column(conn, table, column):
            cur = conn.cursor()
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()

    # ---------------------------
    # Tìm bệnh nhân đã tồn tại
    # Kiểm tra theo: tên, số điện thoại (nếu cột dien_thoai tồn tại), cccd (nếu có)
    # ---------------------------
    def find_existing_patient(self, conn, ho_ten, dien_thoai=None, so_cccd=None):
        cur = conn.cursor()

        conditions = []
        params = []

        if ho_ten:
            conditions.append("ho_ten = ?")
            params.append(ho_ten)
        # kiểm tra cột dien_thoai có tồn tại không trước khi dùng
        if dien_thoai and self.table_has_column(conn, "benh_nhan", "dien_thoai"):
            conditions.append("dien_thoai = ?")
            params.append(dien_thoai)
        if so_cccd and self.table_has_column(conn, "benh_nhan", "so_cccd"):
            conditions.append("so_cccd = ?")
            params.append(so_cccd)

        if not conditions:
            return None

        sql = "SELECT id FROM benh_nhan WHERE " + " OR ".join(conditions) + " LIMIT 1"
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None



    # ---------------------------
    # Sinh số hồ sơ (TD + yyyymmdd + seq)
    # ---------------------------
    def generate_sohoso(self, conn):
        cur = conn.cursor()
        cur.execute("SELECT ma_hoso FROM tiep_don ORDER BY id DESC LIMIT 1")
        result = cur.fetchone()

        if result and result[0] and isinstance(result[0], str) and result[0].startswith("HS"):
            last_num = int(result[0][2:])  # bỏ "HS"
        else:
            last_num = 0

        new_num = last_num + 1
        return f"HS{new_num:03d}"  # HS001, HS002, ...



    # ---------------------------
    # Lưu bệnh nhân (nếu đã tồn tại -> trả về id, nếu chưa -> insert)
    # Trả về id bệnh nhân
    # ---------------------------
    def save_benh_nhan(self, conn, data):
        cur = conn.cursor()

        # kiểm tra bệnh nhân đã tồn tại chưa
        existing_id = self.find_existing_patient(
            conn,
            ho_ten=data.get("ho_ten"),
            dien_thoai=data.get("dien_thoai"),
            so_cccd=data.get("so_cccd")
        )
        if existing_id:
            return existing_id  # trả về id đã tồn tại

        # nếu chưa tồn tại, insert mới
        insert_cols = []
        insert_vals = []

        allowed = ["ho_ten", "gioi_tinh", "ngay_sinh", "tuoi", "dia_chi",
                   "dien_thoai", "so_cccd", "doi_tuong", "nghe_nghiep",
                   "nguoi_gioi_thieu"]
        # mapping: cung cấp dữ liệu từ data
        payload = {
            "ho_ten": data.get("ho_ten"),
            "gioi_tinh": data.get("gioi_tinh"),
            "ngay_sinh": data.get("ngay_sinh"),
            "tuoi": data.get("tuoi"),
            "dia_chi": data.get("dia_chi"),
            "dien_thoai": data.get("dien_thoai"),
            "so_cccd": data.get("so_cccd"),
            "doi_tuong": data.get("doi_tuong"),
            "nghe_nghiep": data.get("nghe_nghiep"),
            "nguoi_gioi_thieu": data.get("nguoi_gioi_thieu")
        }

        # dùng pragma để biết cột tồn tại (defensive)
        cur.execute("PRAGMA table_info(benh_nhan)")
        exist_cols = [r[1] for r in cur.fetchall()]

        for col in allowed:
            if col in exist_cols:
                insert_cols.append(col)
                insert_vals.append(payload.get(col))

        placeholders = ",".join(["?"] * len(insert_vals))
        sql = f"INSERT INTO benh_nhan ({', '.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, insert_vals)
        benh_nhan_id = cur.lastrowid
        conn.commit()


        return benh_nhan_id
    # ---------------------------
    # Lưu 1 record tiep_don, trả về id tiep_don
    # ---------------------------
    def save_tiep_don(self, conn, benh_nhan_id, data):
        # đảm bảo bảng tiep_don tồn tại
        cur = conn.cursor()

        # tạo so_hoso tự động dựa theo ngày (yyyy-mm-dd)
        ngay = data.get("ngay_tiep_don") or QDate.currentDate().toString("yyyy-MM-dd")
        sohoso = self.generate_sohoso(conn)

        insert_cols = []
        insert_vals = []

        allowed = ["ma_hoso", "benh_nhan_id", "ngay_tiep_don", "phong_kham", "bac_si_kham",
                   "tinh_trang", "loai_kham", "tien_kham", "nv_tiepdon", "so_cccd",
                   "huyet_ap", "nhiet_do", "chieu_cao", "can_nang"]
        # mapping: cung cấp dữ liệu từ data + benh_nhan_id + sohoso
        payload = {
            "ma_hoso": sohoso,
            "benh_nhan_id": benh_nhan_id,
            "ngay_tiep_don": ngay,
            "phong_kham": data.get("phong_kham"),
            "bac_si_kham": data.get("bac_si_kham"),
            "tinh_trang": data.get("tinh_trang"),
            "loai_kham": data.get("loai_kham"),
            "tien_kham": data.get("tien_kham"),
            "nv_tiepdon": data.get("nv_tiepdon"),
            "huyet_ap": data.get("huyet_ap"),
            "nhiet_do": data.get("nhiet_do"),
            "chieu_cao": data.get("chieu_cao"),
            "can_nang": data.get("can_nang")
        }

        # dùng pragma để biết cột tồn tại (defensive)
        cur.execute("PRAGMA table_info(tiep_don)")
        exist_cols = [r[1] for r in cur.fetchall()]

        for col in allowed:
            if col in exist_cols:
                insert_cols.append(col)
                insert_vals.append(payload.get(col))

        # nếu bảng vừa mới tạo (không có cột), ta fallback insert tất cả cột theo bảng tiêu chuẩn:
        if not insert_cols:
            # fallback: tạo theo cấu trúc chuẩn (ensure_tiep_don_table đã thực hiện) => sẽ có cột
            insert_cols = ["ma_hoso","benh_nhan_id","ngay_tiep_don","phong_kham","bac_si_kham","tinh_trang","loai_kham","tien_kham","nv_tiepdon","huyet_ap","nhiet_do","chieu_cao","can_nang"]
            insert_vals = [payload.get(c) for c in insert_cols]

        placeholders = ",".join(["?"] * len(insert_vals))
        sql = f"INSERT INTO tiep_don ({', '.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, insert_vals)
        tiep_don_id = cur.lastrowid
        conn.commit()
        return tiep_don_id

    # ---------------------------
    # Gom dữ liệu từ form vào dict
    # ---------------------------
    def collect_form_data(self):
        data_bn = {
            "ho_ten": self.combo_hoten.currentText().strip(),
            "gioi_tinh": self.gioitinh.currentText() if hasattr(self, "gioitinh") else None,
            "ngay_sinh": self.ngaysinh.date().toString("yyyy-MM-dd") if hasattr(self, "ngaysinh") else None,
            "tuoi": int(self.tuoi.text()) if self.tuoi.text().isdigit() else None,
            "dia_chi": self.input_diachi.text().strip() if hasattr(self, "input_diachi") else None,
            "dien_thoai": self.input_dienthoai.text().strip() if hasattr(self, "input_dienthoai") else None,
            "so_cccd": self.input_cccd.text().strip() if hasattr(self, "input_cccd") else None,
            "doi_tuong": self.doituong.currentText() if hasattr(self, "doituong") else None,
            "nghe_nghiep": self.input_nghenghiep.text().strip() if hasattr(self, "input_nghenghiep") else None,
            "nguoi_gioi_thieu": self.nguoigt.currentText() if hasattr(self, "nguoigt") else None,
            "loai_kham": self.loaikham.currentText() if hasattr(self, "loaikham") else None
        }

        data_td = {
            "ngay_tiep_don": self.date_ngaylap.date().toString("yyyy-MM-dd") if hasattr(self, "date_ngaylap") else QDate.currentDate().toString("yyyy-MM-dd"),
            "phong_kham": self.combo_phongkham.currentText() if hasattr(self, "combo_phongkham") else None,
            "bac_si_kham": self.combo_bacsi.currentText() if hasattr(self, "combo_bacsi") else None,
            "tinh_trang": self.combo_tinhtrang.currentText() if hasattr(self, "combo_tinhtrang") else None,
            "loai_kham": self.loaikham.currentText() if hasattr(self, "loaikham") else None,
            "tien_kham": float(self.input_tienkham.text()) if hasattr(self, "input_tienkham") and self.input_tienkham.text().replace('.','',1).isdigit() else 0.0,
            "nv_tiepdon": self.combo_nvtiepdon.currentText() if hasattr(self, "combo_nvtiepdon") else None,
            "huyet_ap": self.input_huyetap.text().strip() if hasattr(self, "input_huyetap") else None,
            "nhiet_do": float(self.input_nhietdo.text()) if hasattr(self, "input_nhietdo") and self.input_nhietdo.text().replace('.','',1).isdigit() else None,
            "chieu_cao": float(self.input_chieucao.text()) if hasattr(self, "input_chieucao") and self.input_chieucao.text().replace('.','',1).isdigit() else None,
            "can_nang": float(self.input_cannang.text()) if hasattr(self, "input_cannang") and self.input_cannang.text().replace('.','',1).isdigit() else None,
            "ma_hoso": self.sohoso.text().strip() if hasattr(self, "sohoso") else None
        }

        return data_bn, data_td

    # ---------------------------
    # Hàm chính: lưu cả bệnh nhân + tiếp đón
    # ---------------------------
    def save_data(self):
        """Lưu hoặc cập nhật thông tin bệnh nhân và phiếu tiếp đón vào CSDL"""
        try:
            conn = get_connection()
            data_bn, data_td = self.collect_form_data()
            print("🩺 Dữ liệu bệnh nhân:", data_bn)
            print("📋 Dữ liệu tiếp đón:", data_td)

            # 🟢 Nếu đang ở chế độ sửa → cập nhật bản ghi hiện tại
            if getattr(self, "is_edit_mode", False) and getattr(self, "selected_ma_hoso", None):
                self.cap_nhat_khi_nhan_sua(conn, self.selected_ma_hoso, data_bn, data_td)
                QMessageBox.information(self, "Thành công", f"Đã cập nhật hồ sơ {self.selected_ma_hoso} thành công!")
                self.is_edit_mode = False  # reset trạng thái sửa
            else:
                # ➕ Nếu KHÔNG ở chế độ sửa → thêm mới như cũ
                benh_nhan_id = self.save_benh_nhan(conn, data_bn)
                if not benh_nhan_id:
                    QMessageBox.warning(self, "Cảnh báo", "Không thể lưu bệnh nhân — dữ liệu trống hoặc lỗi.")
                    return None, None

                tiep_don_id = self.save_tiep_don(conn, benh_nhan_id, data_td)
                if not tiep_don_id:
                    QMessageBox.warning(self, "Cảnh báo", "Không thể lưu phiếu tiếp đón.")
                    return benh_nhan_id, None

                QMessageBox.information(self, "Thành công", "Đã lưu thông tin bệnh nhân và phiếu tiếp đón!")

            # 🔁 Load lại danh sách và bảng thống kê
            self.load_danh_sach_tiep_don()
            self.load_thongke_luot_tiepdon()

            # 🧹 Reset form sau khi lưu xong
            self.reset_form()

            conn.close()
            return True

        except Exception as e:
            print("❌ Lỗi khi lưu dữ liệu:", e)
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu dữ liệu:\n{e}")
            return None



    # ---------------------------
    # Lưu và reset (gán cho nút 'Nhập mới')
    # ---------------------------
    def save_and_reset(self):
        """Gọi lưu dữ liệu rồi reset form sau khi lưu thành công"""
        result = self.save_data()

        # ✅ Nếu lưu thành công → reset form
        if result:
            self.reset_form()


    # ---------------------------
    # Reset form (dọn sạch để nhập tiếp)
    # ---------------------------
    def reset_form(self):
        """Reset toàn bộ form sau khi nhập bệnh nhân mới"""
        try:
            # 🚫 Ngắt signal để không tự load dữ liệu cũ
            try:
                self.combo_hoten.blockSignals(True)
            except:
                pass

            # --- phần reset như cũ của bạn ---
            self.ngaysinh.dateChanged.disconnect(self.update_age)
            self.ngaysinh.setDate(QDate.currentDate())
            self.tuoi.clear()
            self.ngaysinh.dateChanged.connect(self.update_age)

            self.combo_hoten.setEditText("")
            self.gioitinh.setCurrentIndex(0)
            self.doituong.setCurrentIndex(0)
            self.nguoigt.setCurrentIndex(0)
            self.loaikham.setCurrentIndex(0)

            self.input_diachi.clear()
            self.input_dienthoai.clear()
            self.input_cccd.clear()
            self.input_nghenghiep.clear()

            self.combo_phongkham.setCurrentIndex(0)
            self.combo_bacsi.setCurrentIndex(0)
            self.combo_tinhtrang.setCurrentIndex(0)
            self.combo_nvtiepdon.setCurrentIndex(0)

            self.input_chieucao.clear()
            self.input_cannang.clear()
            self.input_huyetap.clear()
            self.input_nhietdo.clear()
            self.input_tienkham.setText("0")
            self.date_ngaylap.setDate(QDate.currentDate())

            # Sinh số hồ sơ mới
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM tiep_don")
                count = cur.fetchone()[0] or 0
                self.sohoso.setText(f"HS{count + 1:03d}")
                conn.close()
            except Exception as e:
                print("⚠️ Không thể sinh số hồ sơ mới:", e)
                self.sohoso.setText("HS001")

            # Làm mới danh sách
            self.load_benh_nhan_list()

            # Focus về họ tên
            self.combo_hoten.setFocus()
            self.combo_hoten.setEditText("")

            print("🧹 Form đã được reset hoàn toàn!")

        except Exception as e:
            print("❌ Lỗi khi reset form:", e)

        finally:
            # ✅ Bật lại signal sau khi reset xong
            try:
                self.combo_hoten.blockSignals(False)
            except:
                pass


    def sua_du_lieu(self):
        if not self.selected_ma_hoso:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một hồ sơ để sửa.")
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                t.ma_hoso, t.ngay_tiep_don, t.phong_kham, t.bac_si_kham, 
                t.tinh_trang, t.tien_kham, t.nv_tiepdon, t.huyet_ap, 
                t.nhiet_do, t.chieu_cao, t.can_nang,
                b.ho_ten, b.gioi_tinh, b.ngay_sinh, b.tuoi, b.dia_chi,
                b.dien_thoai, b.so_cccd, b.doi_tuong, b.nghe_nghiep,
                b.nguoi_gioi_thieu, b.loai_kham
            FROM tiep_don t
            JOIN benh_nhan b ON t.benh_nhan_id = b.id
            WHERE t.ma_hoso = ?
        """, (self.selected_ma_hoso,))
        record = cur.fetchone()
        conn.close()

        if not record:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy hồ sơ trong cơ sở dữ liệu.")
            return

        # --- Tách dữ liệu ---
        data_td = {
            "ma_hoso": record[0],
            "ngay_tiep_don": record[1],
            "phong_kham": record[2],
            "bac_si_kham": record[3],
            "tinh_trang": record[4],
            "tien_kham": record[5],
            "nv_tiepdon": record[6],
            "huyet_ap": record[7],
            "nhiet_do": record[8],
            "chieu_cao": record[9],
            "can_nang": record[10],
        }

        data_bn = {
            "ho_ten": record[11],
            "gioi_tinh": record[12],
            "ngay_sinh": record[13],
            "tuoi": record[14],
            "dia_chi": record[15],
            "dien_thoai": record[16],
            "so_cccd": record[17],
            "doi_tuong": record[18],
            "nghe_nghiep": record[19],
            "nguoi_gioi_thieu": record[20],
            "loai_kham": record[21],
        }

        # --- Đổ dữ liệu lên form bệnh nhân ---
        self.combo_hoten.setCurrentText(data_bn["ho_ten"])
        self.gioitinh.setCurrentText(data_bn["gioi_tinh"])
        if data_bn["ngay_sinh"]:
            self.ngaysinh.setDate(QDate.fromString(data_bn["ngay_sinh"], "yyyy-MM-dd"))
        self.update_age()
        self.input_diachi.setText(data_bn["dia_chi"] or "")
        self.input_dienthoai.setText(data_bn["dien_thoai"] or "")
        self.input_cccd.setText(data_bn["so_cccd"] or "")
        self.doituong.setCurrentText(data_bn["doi_tuong"] or "")
        self.input_nghenghiep.setText(data_bn["nghe_nghiep"] or "")
        self.nguoigt.setCurrentText(data_bn["nguoi_gioi_thieu"] or "")
        self.loaikham.setCurrentText(data_bn["loai_kham"] or "")

        # --- Đổ dữ liệu lên form tiếp đón ---
        self.sohoso.setText(data_td["ma_hoso"])
        self.combo_phongkham.setCurrentText(data_td["phong_kham"])
        self.combo_bacsi.setCurrentText(data_td["bac_si_kham"])
        if data_td["ngay_tiep_don"]:
            self.date_ngaylap.setDate(QDate.fromString(data_td["ngay_tiep_don"], "yyyy-MM-dd"))
        self.combo_tinhtrang.setCurrentText(data_td["tinh_trang"])
        self.input_tienkham.setText(str(data_td["tien_kham"] or "0"))
        self.combo_nvtiepdon.setCurrentText(data_td["nv_tiepdon"])
        self.input_huyetap.setText(str(data_td["huyet_ap"] or ""))
        self.input_nhietdo.setText(str(data_td["nhiet_do"] or ""))
        self.input_chieucao.setText(str(data_td["chieu_cao"] or ""))
        self.input_cannang.setText(str(data_td["can_nang"] or ""))

        self.is_edit_mode = True # Đánh dấu đang ở chế độ sửa
        QMessageBox.information(self, "Sẵn sàng", f"Đã tải thông tin hồ sơ {self.selected_ma_hoso} để chỉnh sửa.")

    # ---------------------------
    # Xóa hồ sơ tiếp đón và bệnh nhân liên quan
    # ---------------------------
    def xoa_du_lieu(self):
        """Xóa hồ sơ tiếp đón và thông tin bệnh nhân liên quan + cập nhật bảng thống kê"""
        if not self.selected_ma_hoso:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một hồ sơ để xóa.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa hồ sơ {self.selected_ma_hoso} và toàn bộ thông tin liên quan không?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            # 🔹 Lấy ID bệnh nhân tương ứng
            cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ?", (self.selected_ma_hoso,))
            result = cur.fetchone()
            benh_nhan_id = result[0] if result else None

            # 🔹 Xóa trong bảng tiep_don
            cur.execute("DELETE FROM tiep_don WHERE ma_hoso = ?", (self.selected_ma_hoso,))

            # 🔹 Xóa bệnh nhân (nếu cần)
            if benh_nhan_id:
                cur.execute("DELETE FROM benh_nhan WHERE id = ?", (benh_nhan_id,))

            conn.commit()
            conn.close()

            # 🔹 Xóa khỏi bảng thống kê lượt tiếp đón (nếu có)
            for row in range(self.table_thongke.rowCount()):
                ma_hoso_cell = self.table_thongke.item(row, 1)
                if ma_hoso_cell and ma_hoso_cell.text() == self.selected_ma_hoso:
                    self.table_thongke.removeRow(row)
                    break  # dừng luôn sau khi xóa

            QMessageBox.information(self, "Thành công", f"Đã xóa hồ sơ {self.selected_ma_hoso} thành công!")

            # 🔹 Làm mới danh sách và form
            self.load_danh_sach_tiep_don()
            self.reset_form()
            self.selected_ma_hoso = None

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa dữ liệu:\n{e}")

    # ---------------------------
    # In phiếu tiếp đón ra file PDF
    # ---------------------------
    def in_phieu_tiep_don(self):
        try:
            # Giả sử đoạn code của bạn phía trên đã tạo file PDF sẵn (ví dụ HS001.pdf)
            file_path = self.tao_file_pdf_tiepdon()  # Hàm này bạn đang dùng để sinh PDF

            # Mở cửa sổ xem PDF ngay trong app
            from forms.pdf_viewer import PDFViewer
            self.pdf_window = PDFViewer(file_path)
            self.pdf_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở file PDF:\n{e}")

    def tao_file_pdf_tiepdon(self):
        """
        Sinh file PDF cho hồ sơ tiếp đón.
        Dùng font Arial Unicode để hỗ trợ tiếng Việt.
        """
        try:
            # Tạo thư mục output nếu chưa có
            output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
            os.makedirs(output_dir, exist_ok=True)

            file_path = os.path.join(output_dir, f"{self.selected_ma_hoso}.pdf")

            # === Đăng ký font Unicode ===
            font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Không tìm thấy file font: {font_path}")

            pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

            # === Tạo file PDF ===
            c = canvas.Canvas(file_path, pagesize=A4)
            c.setFont("ArialUnicode", 16)
            c.drawCentredString(300, 800, "PHIẾU TIẾP ĐÓN KHÁM BỆNH")

            c.setFont("ArialUnicode", 12)
            y = 760
            line_height = 25

            def write_line(text):
                nonlocal y
                c.drawString(80, y, text)
                y -= line_height

            # Ghi nội dung phiếu
            write_line(f"Số hồ sơ: {self.selected_ma_hoso}")
            write_line(f"Họ và tên: {self.combo_hoten.currentText()}")
            write_line(f"Giới tính: {self.gioitinh.currentText()}")
            write_line(f"Phòng khám: {self.combo_phongkham.currentText()}")
            write_line(f"Bác sĩ khám: {self.combo_bacsi.currentText()}")

            c.save()
            return file_path

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo file PDF:\n{e}")
            print("❌ Lỗi tạo PDF:", e)
            return None

    def in_so_thu_tu(self):
        try:
            file_path = self.tao_file_stt_pdf()
            from forms.pdf_viewer import PDFViewer
            self.pdf_window = PDFViewer(file_path)
            self.pdf_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể in STT:\n{e}")


    def tao_file_stt_pdf(self):
        from reportlab.lib.pagesizes import A6, portrait
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from datetime import datetime
        import os, json

        # 🟢 Đăng ký font Unicode tiếng Việt
        font_path = os.path.join(os.getcwd(), "forms", "fonts", "arial.ttf")
        pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))

        # 🟢 Chuẩn bị dữ liệu
        hoten = self.combo_hoten.currentText().strip()
        phongkham = self.combo_phongkham.currentText().strip()
        bacsi = self.combo_bacsi.currentText().strip()
        gioitinh = self.gioitinh.currentText().strip()
        namsinh = self.tuoi.text().strip()
        ngay = datetime.now().strftime("%d tháng %m năm %Y")

        # 🟢 Tạo thư mục output và file lưu số thứ tự
        os.makedirs("output", exist_ok=True)
        counter_file = os.path.join("output", "stt_counter.json")

        today = datetime.now().strftime("%Y-%m-%d")
        stt = 1

        # 🟢 Đọc số thứ tự cũ (nếu có)
        if os.path.exists(counter_file):
            with open(counter_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == today:
                    stt = data.get("stt", 0) + 1

        # 🟢 Ghi lại STT mới và ngày hiện tại
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump({"date": today, "stt": stt}, f, ensure_ascii=False, indent=2)

        # 🟢 Tạo file PDF
        file_path = os.path.join("output", f"STT_{self.selected_ma_hoso}.pdf")
        c = canvas.Canvas(file_path, pagesize=portrait(A6))

        # ---- Giao diện in ----
        c.setFont("ArialUnicode", 14)
        c.drawCentredString(150, 400, "SỐ THỨ TỰ KHÁM")
        c.setFont("ArialUnicode", 10)
        c.drawCentredString(150, 385, f"Ngày {ngay}")

        c.setFont("ArialUnicode", 11)
        c.drawString(20, 360, f"Phòng: {phongkham}")
        c.drawString(20, 345, f"BS khám: {bacsi}")

        # --- Kẻ đường ---
        c.line(20, 340, 280, 340)

        # --- STT to và nổi bật ---
        c.setFont("ArialUnicode", 20)
        c.drawCentredString(150, 310, f"STT: {str(stt).zfill(2)}")

        # --- Họ tên ---
        c.setFont("ArialUnicode", 13)
        c.drawCentredString(150, 285, hoten)

        # --- Giới tính / Năm sinh ---
        c.setFont("ArialUnicode", 10)
        c.drawString(30, 260, f"Giới: {gioitinh}")
        c.drawRightString(270, 260, f"Năm sinh: {namsinh}")

        # --- Ghi chú ---
        c.setFont("ArialUnicode", 9)
        c.drawCentredString(150, 230, "Vui lòng chờ đến lượt theo số thứ tự được gọi")
        c.drawCentredString(150, 218, "(Phiếu chỉ có giá trị trong ngày)")

        c.save()
        return file_path



    # ---------------------------
    # Cập nhật bản ghi hiện có
    # ---------------------------
    def cap_nhat_khi_nhan_sua(self, conn, ma_hoso, data_bn, data_td):
        cur = conn.cursor()

        # Lấy ID bệnh nhân từ mã hồ sơ
        cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ?", (ma_hoso,))
        result = cur.fetchone()
        if not result:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy hồ sơ {ma_hoso}.")
            return
        benh_nhan_id = result[0]

        # --- Cập nhật bảng benh_nhan ---
        set_bn = ", ".join([f"{col} = ?" for col in data_bn.keys()])
        cur.execute(f"UPDATE benh_nhan SET {set_bn} WHERE id = ?", (*data_bn.values(), benh_nhan_id))

        # --- Cập nhật bảng tiep_don ---
        set_td = ", ".join([f"{col} = ?" for col in data_td.keys()])
        cur.execute(f"UPDATE tiep_don SET {set_td} WHERE ma_hoso = ?", (*data_td.values(), ma_hoso))

        conn.commit()

    # ---------------------------
    # Xử lý khi chọn 1 dòng trong bảng danh sách
    # ---------------------------
    def on_row_selected(self, *args):
        """Xử lý khi chọn 1 dòng trong bảng tiếp đón"""
        if self.tableTiepDon.currentRow() < 0:
            return  # không có dòng nào được chọn

        row = self.tableTiepDon.currentRow()
        item = self.tableTiepDon.item(row, 0)
        if item:
            self.selected_ma_hoso = item.text()
            print(f"👉 Đã chọn hồ sơ: {self.selected_ma_hoso}")

    
    # ---------------------------
    # Load dữ liệu bệnh nhân vào form (khi chọn từ combobox)
    # ---------------------------
    def load_patient_into_form(self, ho_ten):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM benh_nhan WHERE ho_ten = ? LIMIT 1", (ho_ten,))
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            conn.close()

            if not row:
                return

            data = dict(zip(columns, row))

            # Điền dữ liệu vào form
            self.combo_hoten.setCurrentText(data.get("ho_ten", ""))
            self.gioitinh.setCurrentText(data.get("gioi_tinh", "Nam"))
            if data.get("ngay_sinh"):
                self.ngaysinh.setDate(QDate.fromString(data.get("ngay_sinh"), "yyyy-MM-dd"))
            self.update_age()
            self.input_diachi.setText(data.get("dia_chi", ""))
            self.input_dienthoai.setText(data.get("dien_thoai", ""))
            self.input_cccd.setText(data.get("so_cccd", ""))
            self.doituong.setCurrentText(data.get("doi_tuong", "BHYT"))
            self.input_nghenghiep.setText(data.get("nghe_nghiep", ""))
            self.nguoigt.setCurrentText(data.get("nguoi_gioi_thieu", "Bác sĩ"))
            self.loaikham.setCurrentText(data.get("loai_kham", "Khám và tư vấn"))
            self.combo_hoten.setFocus()
            self.combo_hoten.setEditText(ho_ten)

            # --- Load thêm thông tin tiếp đón ---
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM tiep_don 
                WHERE benh_nhan_id = (
                    SELECT id FROM benh_nhan WHERE ho_ten = ? LIMIT 1
                )
                ORDER BY ngay_tiep_don DESC LIMIT 1
            """, (ho_ten,))
            tiepdon = cur.fetchone()
            columns = [desc[0] for desc in cur.description] if tiepdon else []
            conn.close()

            try:
                if tiepdon:
                    td_data = dict(zip(columns, tiepdon))

                    # Hàm nhỏ để ép mọi giá trị sang chuỗi, kể cả None hay float
                    def safe_str(value):
                        if value is None:
                            return ""
                        if isinstance(value, float):
                            # Nếu là số thực nhưng tròn (vd: 70.0) → hiển thị "70"
                            if value.is_integer():
                                return str(int(value))
                            else:
                                return f"{value:.2f}".rstrip('0').rstrip('.')  # Giữ tối đa 2 chữ số sau dấu phẩy
                        return str(value)

                    self.sohoso.setText(safe_str(td_data.get("ma_hoso")))
                    self.combo_phongkham.setCurrentText(safe_str(td_data.get("phong_kham")))
                    self.combo_bacsi.setCurrentText(safe_str(td_data.get("bac_si_kham")))
                    self.date_ngaylap.setDate(QDate.fromString(safe_str(td_data.get("ngay_tiep_don")), "yyyy-MM-dd"))
                    self.combo_tinhtrang.setCurrentText(safe_str(td_data.get("tinh_trang")))
                    self.input_tienkham.setText(safe_str(td_data.get("tien_kham")))
                    self.combo_nvtiepdon.setCurrentText(safe_str(td_data.get("nv_tiepdon")))
                    self.input_huyetap.setText(safe_str(td_data.get("huyet_ap")))
                    self.input_nhietdo.setText(safe_str(td_data.get("nhiet_do")))
                    self.input_chieucao.setText(safe_str(td_data.get("chieu_cao")))
                    self.input_cannang.setText(safe_str(td_data.get("can_nang")))
            except Exception as e:
                print("❌ Lỗi khi load tiếp đón:", e)



        except Exception as e:
            import traceback
            print("❌ Lỗi khi load bệnh nhân:", e)
            traceback.print_exc()

        
        
    
    # ---------------------------
    # Kết nối sự kiện khi chọn tên từ combobox
    # ---------------------------
    def connect_combobox_event(self):
        self.combo_hoten.currentTextChanged.connect(self.load_patient_into_form)
        self.combo_hoten.lineEdit().editingFinished.connect(lambda: self.load_patient_into_form(self.combo_hoten.currentText()))



    # ---------------------------
    # Load danh sách tiếp đón khám chữa bệnh
    # ---------------------------
    def load_danh_sach_tiep_don(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT td.ma_hoso, td.ngay_tiep_don, td.phong_kham, bn.ho_ten, td.bac_si_kham, td.tinh_trang
            FROM tiep_don td
            JOIN benh_nhan bn ON td.benh_nhan_id = bn.id
            ORDER BY td.ngay_tiep_don ASC
        """)
        records = cur.fetchall()
        conn.close()

        # Gán đúng bảng
        table = self.tableTiepDon  # hoặc self.findChild(QTableWidget, "tableTiepDon")
        table.setRowCount(0)

        for row_data in records:
            row = table.rowCount()
            table.insertRow(row)
            for col, value in enumerate(row_data):
                table.setItem(row, col, QTableWidgetItem(str(value)))

    # ---------------------------
    # Load danh sách thống kê lượt tiếp đón
    # ---------------------------
    def add_thongke_row(self, phong_kham, ma_hoso, da_kham=False):
        """Thêm một dòng vào bảng thống kê lượt tiếp đón"""
        row = self.table_thongke.rowCount()
        self.table_thongke.insertRow(row)

        # Cột 1: Phòng khám
        item_phongkham = QTableWidgetItem(phong_kham)
        item_phongkham.setTextAlignment(Qt.AlignCenter)
        self.table_thongke.setItem(row, 0, item_phongkham)

        # Cột 2: Tiếp đón (số hồ sơ)
        item_mahoso = QTableWidgetItem(ma_hoso)
        item_mahoso.setTextAlignment(Qt.AlignCenter)
        self.table_thongke.setItem(row, 1, item_mahoso)

        # Cột 3: Checkbox "Đã khám"
        checkbox = QCheckBox()
        checkbox.setChecked(da_kham)
        checkbox.setStyleSheet("margin-left:50%; margin-right:50%;")  # căn giữa
        self.table_thongke.setCellWidget(row, 2, checkbox)

    def load_thongke_luot_tiepdon(self):
        """Load toàn bộ dữ liệu thống kê lượt tiếp đón từ DB"""
        from database import get_connection
        conn = get_connection()
        cur = conn.cursor()

        # Lấy dữ liệu từ bảng tiep_don (và nối với benh_nhan nếu cần)
        cur.execute("""
            SELECT 
                t.phong_kham, 
                t.ma_hoso, 
                CASE 
                    WHEN t.tinh_trang LIKE '%đã khám%' OR t.tinh_trang LIKE '%hoàn thành%' 
                    THEN 1 ELSE 0 
                END AS da_kham
            FROM tiep_don t
            ORDER BY t.id ASC
        """)
        rows = cur.fetchall()
        conn.close()

        # Xóa toàn bộ hàng cũ
        self.table_thongke.setRowCount(0)

        # Đổ dữ liệu vào bảng
        for row in rows:
            phong_kham, ma_hoso, da_kham = row
            self.add_thongke_row(phong_kham or "", ma_hoso or "", bool(da_kham))


