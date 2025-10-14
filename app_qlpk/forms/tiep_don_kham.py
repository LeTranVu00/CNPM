from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox, QDateEdit,
    QTableWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QSplitter, QHeaderView, QCompleter
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont
from database import get_connection, initialize_database
initialize_database()

class TiepDonKham(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_benh_nhan_list()

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
        self.gioitinh.addItems(["Nam", "Nữ", "Khác"])
        form_bn.addWidget(self.gioitinh, 0, 3)

        # Ngày sinh
        form_bn.addWidget(QLabel("Ngày sinh *"), 1, 0)
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
        self.diachi = QLineEdit()
        form_bn.addWidget(self.diachi, 2, 1, 1, 3)

        # Điện thoại
        form_bn.addWidget(QLabel("Điện thoại"), 3, 0)
        self.dienthoai = QLineEdit()
        form_bn.addWidget(self.dienthoai, 3, 1)

        # Đối tượng
        form_bn.addWidget(QLabel("Đối tượng"), 3, 2)
        self.doituong = QComboBox()
        self.doituong.addItems(["BHYT", "Dân sự", "Khác"])
        form_bn.addWidget(self.doituong, 3, 3)

        # Nghề nghiệp
        form_bn.addWidget(QLabel("Nghề nghiệp"), 4, 0)
        self.nghenghiep = QLineEdit()
        form_bn.addWidget(self.nghenghiep, 4, 1)

        # Người giới thiệu
        form_bn.addWidget(QLabel("Người giới thiệu"), 4, 2)
        self.nguoigt = QComboBox()
        self.nguoigt.addItems(["Bác sĩ", "Tiếp tân", "Khác"])
        form_bn.addWidget(self.nguoigt, 4, 3)

        # Loại khám
        form_bn.addWidget(QLabel("Loại khám "), 5, 0)
        self.loaikham = QComboBox()
        self.loaikham.addItems(["Khám và tư vấn", "Kê đơn", "Khác"])
        form_bn.addWidget(self.loaikham, 5, 1)

        # Cấp cứu
        self.capcuu = QCheckBox("Cấp cứu")
        form_bn.addWidget(self.capcuu, 5, 3)

        group_bn.setLayout(form_bn)


        # --- Bên phải: Thống kê lượt tiếp đón ---
        group_thongke = QGroupBox("THỐNG KÊ LƯỢT TIẾP ĐÓN")
        group_thongke.setStyleSheet("QGroupBox { font-weight: bold; color: #d32f2f; }")
        thongke_layout = QVBoxLayout()
        table_tk = QTableWidget(0, 3)
        table_tk.setHorizontalHeaderLabels(["Phòng khám", "Tiếp đón", "Đã khám"])
        table_tk.horizontalHeader().setStretchLastSection(True)
        table_tk.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table_tk.horizontalHeader().setStretchLastSection(True)
        table_tk.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        thongke_layout.addWidget(table_tk)
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
        self.input_sohoso = QLineEdit()
        grid2.addWidget(self.input_sohoso, 0, 1)

        grid2.addWidget(QLabel("Tình trạng BN"), 0, 2)
        self.combo_tinhtrang = QComboBox()
        self.combo_tinhtrang.addItems(["Ổn định", "Nặng", "Nguy kịch", "Đang điều trị", "Khỏi bệnh"])
        grid2.addWidget(self.combo_tinhtrang, 0, 3)

        grid2.addWidget(QLabel("Tiền khám"), 0, 4)
        self.input_tienkham = QLineEdit("0")
        grid2.addWidget(self.input_tienkham, 0, 5)

        grid2.addWidget(QLabel("Phòng khám"), 1, 0)
        self.combo_phongkham = QComboBox()
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
        self.combo_nvtiepdon.addItems(["Nguyễn Thị Lan", "Trần Văn Hùng", "Phạm Thu Trang", "Lê Minh Đức"])
        grid2.addWidget(self.combo_nvtiepdon, 1, 5)

        grid2.addWidget(QLabel("Bác sỹ khám"), 2, 0)
        self.combo_bacsi = QComboBox()
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
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["Số hồ sơ", "Ngày lập", "Phòng khám", "Họ tên BN", "Bác sĩ khám", "Tình trạng"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vbox.addWidget(table)
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

        # Set kích thước
        for btn in [self.btn_nhapmoi, self.btn_sua, self.btn_xoa, self.btn_inphieu]:
            btn.setMinimumWidth(100)
            buttons.addWidget(btn)

        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # Gán sự kiện nút "Nhập mới" để lưu dữ liệu
        self.btn_nhapmoi.clicked.disconnect() if self.btn_nhapmoi.receivers(self.btn_nhapmoi.clicked) else None
        self.btn_nhapmoi.clicked.connect(self.save_and_reset)


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
    # Sinh mã bệnh nhân tự động (BN00001)
    # Sau khi insert, dùng id để tạo mã và cập nhật trường ma_benhnhan
    # ---------------------------
    def generate_and_store_patient_code(self, conn, benh_nhan_id):
        # đảm bảo cột ma_benhnhan tồn tại
        self.add_column_if_missing(conn, "benh_nhan", "ma_benhnhan", "TEXT")
        code = f"BN{benh_nhan_id:05d}"
        cur = conn.cursor()
        cur.execute("UPDATE benh_nhan SET ma_benhnhan = ? WHERE id = ?", (code, benh_nhan_id))
        conn.commit()
        return code

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

        # kiểm tra có bệnh nhân tồn tại không (ưu tiên dựa theo tên/điện thoại/cccd nếu có)
        existing_id = self.find_existing_patient(conn, data.get("ho_ten"), data.get("dien_thoai"), data.get("so_cccd"))
        if existing_id:
            return existing_id

        # Lấy danh sách cột hiện có của bảng benh_nhan để chỉ insert những cột tồn tại
        cur.execute("PRAGMA table_info(benh_nhan)")
        exist_cols = [r[1] for r in cur.fetchall()]

        # Nếu muốn lưu ma_benhnhan, đảm bảo cột tồn tại (sẽ cập nhật sau khi biết id)
        if "ma_benhnhan" not in exist_cols:
            self.add_column_if_missing(conn, "benh_nhan", "ma_benhnhan", "TEXT")
            exist_cols.append("ma_benhnhan")

        # Chuẩn bị cột & giá trị để insert (chỉ những cột tồn tại)
        insert_cols = []
        insert_vals = []
        allowed = ["ho_ten", "gioi_tinh", "ngay_sinh", "tuoi", "dia_chi", "dien_thoai", "so_cccd", "doi_tuong", "nghe_nghiep", "nguoi_gioi_thieu", "loai_kham"]
        for col in allowed:
            if col in exist_cols and data.get(col) is not None:
                insert_cols.append(col)
                insert_vals.append(data.get(col))

        if not insert_cols:
            # không có cột hợp lệ để chèn
            return None

        placeholders = ",".join(["?"] * len(insert_vals))
        sql = f"INSERT INTO benh_nhan ({', '.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, insert_vals)
        benh_nhan_id = cur.lastrowid
        conn.commit()

        # tạo mã BN và lưu
        self.generate_and_store_patient_code(conn, benh_nhan_id)

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
                   "tinh_trang", "loai_kham", "tien_kham", "nv_tiepdon", "cap_cuu",
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
            "cap_cuu": 1 if data.get("cap_cuu") else 0,
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
            insert_cols = ["so_hoso","benh_nhan_id","ngay_tiep_don","phong_kham","bac_si_kham","tinh_trang","loai_kham","tien_kham","nv_tiepdon","cap_cuu","huyet_ap","nhiet_do","chieu_cao","can_nang"]
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
            "dia_chi": self.diachi.text().strip() if hasattr(self, "diachi") else None,
            "dien_thoai": self.dienthoai.text().strip() if hasattr(self, "dienthoai") else None,
            "so_cccd": None,  # nếu bạn có ô cccd, map ở đây
            "doi_tuong": self.doituong.currentText() if hasattr(self, "doituong") else None,
            "nghe_nghiep": self.nghenghiep.text().strip() if hasattr(self, "nghenghiep") else None,
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
            "cap_cuu": self.capcuu.isChecked() if hasattr(self, "capcuu") else False,
            "huyet_ap": self.input_huyetap.text().strip() if hasattr(self, "input_huyetap") else None,
            "nhiet_do": float(self.input_nhietdo.text()) if hasattr(self, "input_nhietdo") and self.input_nhietdo.text().replace('.','',1).isdigit() else None,
            "chieu_cao": float(self.input_chieucao.text()) if hasattr(self, "input_chieucao") and self.input_chieucao.text().replace('.','',1).isdigit() else None,
            "can_nang": float(self.input_cannang.text()) if hasattr(self, "input_cannang") and self.input_cannang.text().replace('.','',1).isdigit() else None,
            "so_hoso": None
        }

        return data_bn, data_td

    # ---------------------------
    # Hàm chính: lưu cả bệnh nhân + tiếp đón
    # ---------------------------
    def save_data(self):
        conn = get_connection()
        try:
            # đảm bảo bảng/tập cột cần thiết
            # (tốt nhất bạn đã gọi initialize_database() khi app khởi động)
            self.add_column_if_missing(conn, "benh_nhan", "ma_benhnhan", "TEXT")

            # thu thập data
            data_bn, data_td = self.collect_form_data()

            # lưu bệnh nhân (nếu chưa có)
            benh_nhan_id = self.save_benh_nhan(conn, data_bn)
            if not benh_nhan_id:
                raise Exception("Không lưu được thông tin bệnh nhân")

            # lưu phiếu tiếp đón
            data_td["benh_nhan_id"] = benh_nhan_id
            tiep_don_id = self.save_tiep_don(conn, benh_nhan_id, data_td)

            # reload danh sách bệnh nhân (combo)
            self.load_benh_nhan_list()

            print(f"✅ Đã lưu bệnh nhân id={benh_nhan_id}, tiếp đón id={tiep_don_id}")

            return benh_nhan_id, tiep_don_id
        finally:
            conn.close()

    # ---------------------------
    # Lưu và reset (gán cho nút 'Nhập mới')
    # ---------------------------
    def save_and_reset(self):
        try:
            self.save_data()
        except Exception as e:
            print("Lỗi khi lưu:", e)
            return

        # reset form
        self.reset_form()

    # ---------------------------
    # Reset form (dọn sạch để nhập tiếp)
    # ---------------------------
    def reset_form(self):
        # clear all QLineEdit
        for w in self.findChildren(QLineEdit):
            w.clear()

        # reset comboboxes to first
        for cb in self.findChildren(QComboBox):
            try:
                cb.setCurrentIndex(0)
            except:
                pass

        # reset date edits to today
        for d in self.findChildren(QDateEdit):
            d.setDate(QDate.currentDate())

        # uncheck checkboxes
        from PyQt5.QtWidgets import QCheckBox
        for ch in self.findChildren(QCheckBox):
            ch.setChecked(False)

        # reload patient list
        self.load_benh_nhan_list()
        # focus vào họ tên
        try:
            self.combo_hoten.setFocus()
            self.combo_hoten.setEditText("")
        except:
            pass


