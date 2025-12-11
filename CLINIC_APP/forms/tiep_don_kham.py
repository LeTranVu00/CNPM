from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QCheckBox, QDateEdit,
    QTableWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QSplitter, QHeaderView, QCompleter,
    QTableWidgetItem, QMessageBox, QAbstractItemView
)
# Sinh file PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os

# Đăng ký font tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
try:
    # Đăng ký nếu file font tồn tại — tránh crash khi import module nếu thiếu font
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))
    else:
        print(f"⚠️ Font không tìm thấy, sẽ bỏ qua đăng ký font: {font_path}")
except Exception as _e:
    # Nếu có lỗi khi đăng ký font thì log và tiếp tục — không nên làm crash toàn app
    print(f"⚠️ Lỗi khi đăng ký font ArialUnicode: {_e}")

from PyQt5.QtCore import Qt, QDate, QStringListModel
from PyQt5.QtGui import QFont
from database import get_connection, initialize_database
import logging
from signals import app_signals

# Thiết lập logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '../error_log.txt'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
initialize_database()

class TiepDonKham(QWidget):
    def __init__(self, role=None):
        self.is_resetting = False # Tránh gọi đệ quy khi reset form
        self.role = role
        super().__init__()
        self.initUI() # Khởi tạo giao diện
        self.is_edit_mode = False  # Biến trạng thái chỉnh sửa
        self.selected_ma_hoso = None  # Mã hồ sơ đang chọn để sửa

        # Khởi tạo danh sách các widget cần khóa/mở (phải nằm sau initUI())
        self.editable_widgets = [
            self.hoten, self.gioitinh, self.ngaysinh,
            self.diachi, self.dienthoai, self.doituong,
            self.nghenghiep, self.nguoigioithieu, self.loaikham,
            self.socccd, self.phongkham, self.bacsi, self.tinhtrang,
            self.nhiptho, self.nhiptim, self.nhanvientiepdon, self.huyetap,
            self.nhietdo, self.chieucao, self.cannang
        ]

        # Log đường dẫn file database khi khởi tạo form
        try:
            from database import DB_NAME
            logging.info(f"[TiepDonKham] Using database file: {DB_NAME}")
        except Exception as e:
            logging.error(f"[TiepDonKham] Error getting DB_NAME: {e}")
        # Tải dữ liệu và chuẩn bị giao diện
        self.load_benh_nhan_list() # Load danh sách bệnh nhân vào combobox
        self.reset_form() # Khởi đầu reset form
        self.connect_combobox_event() # Kết nối sự kiện chọn combobox
        self.load_danh_sach_tiep_don() # Load danh sách tiếp đón
        self.load_thongke_luot_tiepdon() # Load thống kê lượt tiếp đón

        # Khi khởi tạo, load danh sách bệnh nhân vào combobox
    def load_benh_nhan_list(self):
        conn = get_connection()
        cur = conn.cursor()
        # Lấy thêm id và một số trường để phân biệt các bản ghi có cùng tên
        # Lấy kèm mã hồ sơ gần nhất cho mỗi bệnh nhân (nếu có)
        cur.execute("""
            SELECT b.id, b.ho_ten, b.dien_thoai, b.ngay_sinh, b.so_cccd,
                (
                    SELECT ma_hoso FROM tiep_don td WHERE td.benh_nhan_id = b.id ORDER BY td.id DESC LIMIT 1
                ) as ma_hoso
            FROM benh_nhan b
            ORDER BY b.ho_ten
        """)
        rows = cur.fetchall()
        # Tạo display text chứa thông tin phân biệt (tên — ID — SDT/CCCD/NGS)
        names = []
        items = []  # list of tuples (display, id)
        for r in rows:
            pid, name, phone, dob, cccd, ma_hoso = r
            extra = []
            if phone:
                extra.append(str(phone))
            if cccd:
                extra.append(str(cccd))
            # Nếu có ngày sinh, show năm sinh ngắn để dễ đọc
            if dob:
                try:
                    yyyy = str(dob).split("-")[0]
                    extra.append(yyyy)
                except Exception:
                    pass
            display = name
            # ưu tiên hiển thị mã hồ sơ để dễ phân biệt (mã HSxxx). Nếu chưa có ma_hoso, hiển thị id nội bộ
            if ma_hoso:
                # ma_hoso có thể là None — sử dụng khi có giá trị
                display += f" — Mã:{ma_hoso}"
            else:
                display += f" — ID:{pid}"
            if extra:
                display += f" — {' / '.join(extra)}"
            items.append((display, pid))
        conn.close()
    
        # Gắn danh sách vào combobox và completer
        self.hoten.clear()
        display_texts = []
        for display, pid in items:
            # lưu id trong itemData để khi người dùng chọn có thể lấy pid
            self.hoten.addItem(display)
            idx = self.hoten.count() - 1
            self.hoten.setItemData(idx, pid, Qt.UserRole)
            display_texts.append(display)

        model = QStringListModel(display_texts)
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
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ========== NHÓM 1: THÔNG TIN BỆNH NHÂN + THỐNG KÊ LƯỢT ==========
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setHandleWidth(4)

        # --- Bên trái: Thông tin bệnh nhân ---
        group_bn = QGroupBox("THÔNG TIN BỆNH NHÂN")
        group_bn.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
        form_bn = QGridLayout()
        form_bn.setHorizontalSpacing(6)
        form_bn.setVerticalSpacing(4)

        # Họ tên (ComboBox có thể gõ)
        form_bn.addWidget(QLabel("Họ và tên "), 0, 0)
        self.hoten = QComboBox()
        self.hoten.setEditable(True)

        # Completer gợi ý
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(False)
        self.hoten.setCompleter(self.completer)
        form_bn.addWidget(self.hoten, 0, 1)

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
        self.diachi = QLineEdit()
        form_bn.addWidget(self.diachi, 2, 1, 1, 3)

        # Điện thoại
        form_bn.addWidget(QLabel("Điện thoại"), 3, 0)
        self.dienthoai = QLineEdit()
        form_bn.addWidget(self.dienthoai, 3, 1)

        # Đối tượng
        form_bn.addWidget(QLabel("Đối tượng"), 3, 2)
        self.doituong = QComboBox()
        self.doituong.addItem("-Chọn đối tượng-")
        self.doituong.model().item(0).setFlags(Qt.NoItemFlags)
        self.doituong.addItems(["BHYT", "Dân sự", "Khác"])
        form_bn.addWidget(self.doituong, 3, 3)

        # Nghề nghiệp
        form_bn.addWidget(QLabel("Nghề nghiệp"), 4, 0)
        self.nghenghiep = QLineEdit()
        form_bn.addWidget(self.nghenghiep, 4, 1)

        # Người giới thiệu
        form_bn.addWidget(QLabel("Người giới thiệu"), 4, 2)
        self.nguoigioithieu = QComboBox()
        self.nguoigioithieu.addItem("-Chọn người giới thiệu-")
        self.nguoigioithieu.model().item(0).setFlags(Qt.NoItemFlags)
        self.nguoigioithieu.addItems(["Bác sĩ", "Tiếp tân", "Khác"])
        form_bn.addWidget(self.nguoigioithieu, 4, 3)

        # Loại khám
        form_bn.addWidget(QLabel("Loại khám "), 5, 0)
        self.loaikham = QComboBox()
        self.loaikham.addItem("-Nhấn để chọn-")
        self.loaikham.model().item(0).setFlags(Qt.NoItemFlags)
        self.loaikham.addItems(["Khám và tư vấn", "Kê đơn", "Khác"])
        form_bn.addWidget(self.loaikham, 5, 1)

        # Số cccd
        form_bn.addWidget(QLabel("Số CCCD"), 5, 2)
        self.socccd = QLineEdit()
        form_bn.addWidget(self.socccd, 5, 3)

        group_bn.setLayout(form_bn)


        # --- Bên phải: Thống kê lượt tiếp đón ---
        group_thongke = QGroupBox("THỐNG KÊ LƯỢT TIẾP ĐÓN")
        group_thongke.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
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
        group_tiepdon.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(6)
        grid2.setVerticalSpacing(4)

        grid2.addWidget(QLabel("Số hồ sơ"), 0, 0)
        self.mahoso = QLineEdit()
        # Tự động sinh, không cho sửa
        self.mahoso.setReadOnly(True)
        grid2.addWidget(self.mahoso, 0, 1)

        grid2.addWidget(QLabel("Tình trạng BN"), 0, 2)
        self.tinhtrang = QComboBox()
        self.tinhtrang.addItem("-Nhấn để chọn-")
        self.tinhtrang.model().item(0).setFlags(Qt.NoItemFlags)
        self.tinhtrang.addItems(["Ổn định", "Nặng", "Nguy kịch", "Đang điều trị", "Khỏi bệnh"])
        grid2.addWidget(self.tinhtrang, 0, 3)

        # Bác sỹ khám (moved here from row 2)
        grid2.addWidget(QLabel("Bác sỹ khám"), 0, 4)
        self.bacsi = QComboBox()
        self.bacsi.addItem("-Nhấn để chọn-")
        self.bacsi.model().item(0).setFlags(Qt.NoItemFlags)
        self.bacsi.addItems(["BS. Nguyễn Văn A", "BS. Trần Thị B", "BS. Lê Văn C"])
        grid2.addWidget(self.bacsi, 0, 5)

        grid2.addWidget(QLabel("Phòng khám"), 1, 0)
        self.phongkham = QComboBox()
        self.phongkham.addItem("-Nhấn để chọn-")
        self.phongkham.model().item(0).setFlags(Qt.NoItemFlags)
        self.phongkham.addItems([
            "Phòng 1", "Phòng 2", "Phòng 3", "Phòng 4"
        ])
        grid2.addWidget(self.phongkham, 1, 1)

        grid2.addWidget(QLabel("Ngày lập"), 1, 2)
        self.ngaylap = QDateEdit(QDate.currentDate())
        self.ngaylap.setDisplayFormat("dd/MM/yyyy")
        grid2.addWidget(self.ngaylap, 1, 3)

        grid2.addWidget(QLabel("NV tiếp đón"), 1, 4)
        self.nhanvientiepdon = QComboBox()
        self.nhanvientiepdon.addItem("-Nhấn để chọn-")
        self.nhanvientiepdon.model().item(0).setFlags(Qt.NoItemFlags)  # Không cho chọn mục đầu tiên
        self.nhanvientiepdon.addItems(["Nguyễn Thị Lan", "Trần Văn Hùng", "Phạm Thu Trang", "Lê Minh Đức"])
        grid2.addWidget(self.nhanvientiepdon, 1, 5)


        # Nhịp thở (moved here from row 0)
        grid2.addWidget(QLabel("Nhịp thở (lần/phút)"), 2, 0)
        self.nhiptho = QLineEdit()
        grid2.addWidget(self.nhiptho, 2, 1)

        grid2.addWidget(QLabel("Nhịp tim (bpm)"), 2, 2)
        self.nhiptim = QLineEdit()
        grid2.addWidget(self.nhiptim, 2, 3)

        grid2.addWidget(QLabel("Huyết áp (mmHg)"), 2, 4)
        self.huyetap = QLineEdit()
        grid2.addWidget(self.huyetap, 2, 5)

        grid2.addWidget(QLabel("Nhiệt độ (°C)"), 3, 0)
        self.nhietdo = QLineEdit()
        grid2.addWidget(self.nhietdo, 3, 1)

        grid2.addWidget(QLabel("Chiều cao (cm)"), 3, 2)
        self.chieucao = QLineEdit()
        grid2.addWidget(self.chieucao, 3, 3)

        grid2.addWidget(QLabel("Cân nặng (kg)"), 3, 4)
        self.cannang = QLineEdit()
        grid2.addWidget(self.cannang, 3, 5)

        group_tiepdon.setLayout(grid2)
        main_layout.addWidget(group_tiepdon)


        # ========== NHÓM 3: DANH SÁCH PHIẾU TIẾP ĐÓN KCB ==========
        group_ds = QGroupBox("DANH SÁCH PHIẾU TIẾP ĐÓN KCB")
        group_ds.setStyleSheet("QGroupBox { font-weight: bold; color: #0078D7; }")
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

        # Áp dụng stylesheet: inputs trung tính, viền xanh khi focus
        # Lưu stylesheet gốc vào self.base_stylesheet để các hàm khác chỉ bổ sung
        self.base_stylesheet = """
            QGroupBox { font-weight: bold; color: #0078D7; }
            /* Default (neutral) appearance for input widgets */
            QLineEdit, QComboBox, QDateEdit, QTextEdit {
                border: 1px solid #cfcfcf;
                background: white;
                padding: 4px;
                border-radius: 4px;
            }
            /* Focused: show a clear green outer border */
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 2px solid #0078D7; /* green focus */
                outline: none;
            }
            /* Make selection solid blue with white text (matches global theme) */
            QTableWidget::item:selected, QTableWidget::item:selected:!active { background-color: #0078D7; color: white; }
            QHeaderView::section { background-color: #0078D7; color: white; padding: 4px; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #005a9e; }
        """
        self.setStyleSheet(self.base_stylesheet)

        # ========== NHÓM 4: CÁC NÚT CHỨC NĂNG ==========
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        # Tạo từng nút riêng để gán chức năng
        self.btn_nhapmoi = QPushButton("Nhập mới")
        self.btn_luu = QPushButton("Lưu")
        self.btn_sua = QPushButton("Sửa")
        self.btn_xoa = QPushButton("Xóa")
        self.btn_inphieu = QPushButton("In phiếu")
        self.btn_instt = QPushButton("In STT")
        self.btn_reload = QPushButton("Tải lại")

        # Set kích thước cơ bản
        self.btn_luu.setEnabled(True)
        for btn in [self.btn_nhapmoi, self.btn_luu, self.btn_sua, self.btn_xoa]:
            btn.setMinimumWidth(100)
            buttons.addWidget(btn)

        # Giữa hai nhóm: dùng stretch để đẩy nhóm sau sang phải
        buttons.addStretch(1)

        # Các nút phải (right-aligned)
        for btn in [self.btn_inphieu, self.btn_instt]:
            btn.setMinimumWidth(100)
            buttons.addWidget(btn)

        # Thêm nút reload (Tải lại) chỉ cho bác sĩ hoặc admin, đặt bên phải
        if self.role in ['bac_si', 'admin']:
            self.btn_reload.setMinimumWidth(100)
            buttons.addWidget(self.btn_reload)
            self.btn_reload.clicked.connect(self.on_reload_clicked)

        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # Gán sự kiện nút "Nhập mới" để chỉ reset form (không lưu)
        try:
            # Nếu trước đó có kết nối cũ thì ngắt, nếu không thì bỏ qua
            self.btn_nhapmoi.clicked.disconnect()
        except Exception:
            pass
        # Khi nhấn Nhập mới -> chỉ reset về form trắng để nhập bệnh nhân mới
        self.btn_nhapmoi.clicked.connect(self.reset_form)

        # Gán sự kiện nút "Lưu" — lưu khi đang ở chế độ sửa
        self.btn_luu.clicked.connect(self.luu_du_lieu)

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


        # Chỉ coi là 'đã tồn tại' khi trùng theo cccd hoặc số điện thoại.
        # Trùng theo tên hoàn toàn (ho_ten) sẽ không coi là duplicate —
        # vì nhiều người có thể trùng tên.
        if so_cccd and self.table_has_column(conn, "benh_nhan", "so_cccd"):
            conditions.append("so_cccd = ?")
            params.append(so_cccd)
        elif dien_thoai and self.table_has_column(conn, "benh_nhan", "dien_thoai"):
            # chỉ kiểm tra số điện thoại nếu cccd không được cung cấp
            conditions.append("dien_thoai = ?")
            params.append(dien_thoai)

        if not conditions:
            return None

        sql = "SELECT id FROM benh_nhan WHERE " + " OR ".join(conditions) + " LIMIT 1"
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None



    # ---------------------------
    # Sinh số hồ sơ (TD + yyyymmdd + seq)
    # ---------------------------
    def generate_mahoso(self, conn):
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
                   "nguoi_gioi_thieu", "loai_kham"]
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
            "nguoi_gioi_thieu": data.get("nguoi_gioi_thieu"),
            "loai_kham": data.get("loai_kham")
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
        mahoso = self.generate_mahoso(conn)

        insert_cols = []
        insert_vals = []

        allowed = ["ma_hoso", "benh_nhan_id", "ngay_tiep_don", "phong_kham", "bac_si_kham",
                   "tinh_trang", "nv_tiepdon", "so_cccd",
                   "huyet_ap", "nhiet_do", "chieu_cao", "can_nang", "nhip_tho", "nhip_tim"]
        # mapping: cung cấp dữ liệu từ data + benh_nhan_id + mahoso
        payload = {
            "ma_hoso": mahoso,
            "benh_nhan_id": benh_nhan_id,
            "ngay_tiep_don": ngay,
            "phong_kham": data.get("phong_kham"),
            "bac_si_kham": data.get("bac_si_kham"),
            "tinh_trang": data.get("tinh_trang"),
            "nv_tiepdon": data.get("nv_tiepdon"),
            "huyet_ap": data.get("huyet_ap"),
            "nhiet_do": data.get("nhiet_do"),
            "chieu_cao": data.get("chieu_cao"),
            "can_nang": data.get("can_nang"),
            "nhip_tho": data.get("nhip_tho"),
            "nhip_tim": data.get("nhip_tim")
        }

        # dùng pragma để biết cột tồn tại (defensive)
        try:
            cur.execute("PRAGMA table_info(tiep_don)")
            exist_cols = [r[1] for r in cur.fetchall()]

            for col in allowed:
                if col in exist_cols:
                    insert_cols.append(col)
                    insert_vals.append(payload.get(col))

            # nếu bảng vừa mới tạo (không có cột), ta fallback insert tất cả cột theo bảng tiêu chuẩn:
            if not insert_cols:
                insert_cols = ["ma_hoso","benh_nhan_id","ngay_tiep_don","phong_kham","bac_si_kham","tinh_trang","nv_tiepdon","huyet_ap","nhiet_do","chieu_cao","can_nang","nhip_tho","nhip_tim"]
                insert_vals = [payload.get(c) for c in insert_cols]

            placeholders = ",".join(["?"] * len(insert_vals))
            sql = f"INSERT INTO tiep_don ({', '.join(insert_cols)}) VALUES ({placeholders})"
            logging.info(f"[save_tiep_don] SQL: {sql} | VALUES: {insert_vals}")
            cur.execute(sql, insert_vals)
            tiep_don_id = cur.lastrowid
            conn.commit()
            return tiep_don_id
        except Exception as e:
            logging.error(f"[save_tiep_don] Error: {e}")
            raise

    # ---------------------------
    # Gom dữ liệu từ form vào dict
    # ---------------------------
    def collect_form_data(self):
        # Helper function để chuyển đổi số thành string mà không có .0
        def format_number(text):
            try:
                num = float(text)
                return str(int(num)) if num.is_integer() else f"{num:.1f}".rstrip('0').rstrip('.')
            except:
                return text

        data_bn = {
            "ho_ten": self.hoten.currentText().strip(),
            "gioi_tinh": self.gioitinh.currentText() if hasattr(self, "gioitinh") else None,
            "ngay_sinh": self.ngaysinh.date().toString("yyyy-MM-dd") if hasattr(self, "ngaysinh") else None,
            "tuoi": int(self.tuoi.text()) if self.tuoi.text().isdigit() else None,
            "dia_chi": self.diachi.text().strip() if hasattr(self, "diachi") else None,
            "dien_thoai": self.dienthoai.text().strip() if hasattr(self, "dienthoai") else None,
            "so_cccd": self.socccd.text().strip() if hasattr(self, "socccd") else None,
            "doi_tuong": self.doituong.currentText() if hasattr(self, "doituong") else None,
            "nghe_nghiep": self.nghenghiep.text().strip() if hasattr(self, "nghenghiep") else None,
            "nguoi_gioi_thieu": self.nguoigioithieu.currentText() if hasattr(self, "nguoigioithieu") else None,
            "loai_kham": self.loaikham.currentText() if hasattr(self, "loaikham") else None,
        }

        # Xử lý số tiền và các số liệu y tế
        nhip_tho_text = self.nhip_tho.text().strip() if hasattr(self, "nhip_tho") else ""
        nhip_tim_text = self.nhip_tim.text().strip() if hasattr(self, "nhip_tim") else ""
        try:
            nhip_tho = int(nhip_tho_text) if nhip_tho_text else None
        except:
            nhip_tho = None
        try:
            nhip_tim = int(nhip_tim_text) if nhip_tim_text else None
        except:
            nhip_tim = None

        data_td = {
            "ngay_tiep_don": self.ngaylap.date().toString("yyyy-MM-dd") if hasattr(self, "ngaylap") else QDate.currentDate().toString("yyyy-MM-dd"),
            "phong_kham": self.phongkham.currentText() if hasattr(self, "phongkham") else None,
            "bac_si_kham": self.bacsi.currentText() if hasattr(self, "bacsi") else None,
            "tinh_trang": self.tinhtrang.currentText() if hasattr(self, "tinhtrang") else None,
            "nv_tiepdon": self.nhanvientiepdon.currentText() if hasattr(self, "nhanvientiepdon") else None,
            "huyet_ap": self.huyetap.text().strip() if hasattr(self, "huyetap") else None,
            "nhiet_do": self.nhietdo.text().strip() if hasattr(self, "nhietdo") else None,
            "chieu_cao": self.chieucao.text().strip() if hasattr(self, "chieucao") else None,
            "can_nang": self.cannang.text().strip() if hasattr(self, "cannang") else None,
            "nhip_tho": self.nhiptho.text().strip() if hasattr(self, "nhiptho") else None,
            "nhip_tim": self.nhiptim.text().strip() if hasattr(self, "nhiptim") else None,
            "ma_hoso": self.mahoso.text().strip() if hasattr(self, "mahoso") else None
        }

        return data_bn, data_td

    # ---------------------------
    # Kiểm tra tính hợp lệ của các trường số
    # ---------------------------
    def validate_numeric_fields(self):
        """Kiểm tra xem các trường nhập chữ số có hợp lệ không.
        
        Trả về: (is_valid, error_message)
        - is_valid: True nếu tất cả hợp lệ, False nếu có lỗi
        - error_message: Thông báo lỗi (nếu có)
        """
        errors = []
        
        # Các trường cần kiểm tra (không bắt buộc nhập nhưng nếu nhập phải là số)
        fields_to_check = {
            "nhịp thở (nhip_tho)": self.nhiptho,
            "nhịp tim (nhip_tim)": self.nhiptim,
            "nhiệt độ (nhiet_do)": self.nhietdo,
            "chiều cao (chieu_cao)": self.chieucao,
            "cân nặng (can_nang)": self.cannang,
            "huyết áp (huyet_ap)": self.huyetap,
        }
        
        for field_name, widget in fields_to_check.items():
            text = widget.text().strip() if hasattr(widget, "text") else ""
            if text:  # Nếu trường có dữ liệu thì kiểm tra
                try:
                    float(text)  # Cố gắng chuyển thành số
                except ValueError:
                    errors.append(f"  • {field_name}: '{text}' không phải là số hợp lệ")
        
        if errors:
            error_msg = "❌ Các trường sau không hợp lệ (phải nhập chữ số):\n" + "\n".join(errors)
            return False, error_msg
        
        return True, ""

    # ---------------------------
    # Hàm chính: lưu cả bệnh nhân + tiếp đón
    # ---------------------------
    def save_data(self):
        """Lưu hoặc cập nhật thông tin bệnh nhân và phiếu tiếp đón vào CSDL"""
        # Kiểm tra tính hợp lệ của các trường số trước khi lưu
        is_valid, error_msg = self.validate_numeric_fields()
        if not is_valid:
            QMessageBox.warning(self, "Lỗi dữ liệu", error_msg)
            return None
        
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
                self.set_form_editable(False)  # Khóa form sau khi sửa xong
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
                self.set_form_editable(False)  # Khóa form sau khi lưu mới

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
    # Khóa hoặc mở khóa các trường thông tin trong form
    # ---------------------------
    def set_form_editable(self, editable=True):
        """Khóa hoặc mở khóa các trường thông tin trong form"""
        for widget in self.editable_widgets:
            if isinstance(widget, QLineEdit):
                widget.setReadOnly(not editable)
            elif isinstance(widget, (QComboBox, QDateEdit)):
                widget.setEnabled(editable)
        
        # Không thay đổi trạng thái enabled của các nút ở đây — giữ luôn có thể bấm được
        # (Vẫn có thể bật/tắt nút ở các chỗ cụ thể nếu cần, nhưng mặc định ta sẽ giữ enable.)
        try:
            for btn in [self.btn_nhapmoi, self.btn_luu, self.btn_sua, self.btn_xoa, self.btn_inphieu, self.btn_instt]:
                btn.setEnabled(True)
        except Exception:
            pass
        
        # Đặt stylesheet cho các widget dựa trên trạng thái
        style_readonly = """
            QLineEdit:read-only {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
            }
            QComboBox:disabled, QDateEdit:disabled {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
            }
        """
        # Gộp với base stylesheet để không vô hiệu hóa style của nút
        try:
            combined = getattr(self, 'base_stylesheet', '') + style_readonly
            self.setStyleSheet(combined)
        except Exception:
            # Fallback: nếu không có base_stylesheet thì chỉ áp dụng style_readonly
            self.setStyleSheet(style_readonly)



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
    # Reload dữ liệu khi bác sĩ nhấn Tải lại
    # ---------------------------
    def on_reload_clicked(self):
        """Tải lại danh sách tiếp đón và thống kê"""
        try:
            self.load_danh_sach_tiep_don()
            self.load_thongke_luot_tiepdon()
        except Exception as e:
            print(f"Lỗi khi tải lại dữ liệu: {e}")

    # ---------------------------
    # Reset form (dọn sạch để nhập tiếp)
    # ---------------------------
    def reset_form(self):
        """Reset toàn bộ form sau khi nhập bệnh nhân mới"""
        try:
            # Reset edit mode và selected record
            self.is_edit_mode = False
            self.selected_ma_hoso = None
            
            # Mở khóa form để nhập mới
            self.set_form_editable(True)
            
            # 🚫 Ngắt signal để không tự load dữ liệu cũ
            try:
                self.hoten.blockSignals(True)
            except:
                pass

            # --- phần reset như cũ của bạn ---
            self.ngaysinh.dateChanged.disconnect(self.update_age)
            self.ngaysinh.setDate(QDate.currentDate())
            self.tuoi.clear()
            self.ngaysinh.dateChanged.connect(self.update_age)

            self.hoten.setEditText("")
            self.gioitinh.setCurrentIndex(0)
            self.doituong.setCurrentIndex(0)
            self.nguoigioithieu.setCurrentIndex(0)
            self.loaikham.setCurrentIndex(0)

            self.diachi.clear()
            self.dienthoai.clear()
            self.socccd.clear()
            self.nghenghiep.clear()

            self.phongkham.setCurrentIndex(0)
            self.bacsi.setCurrentIndex(0)
            self.tinhtrang.setCurrentIndex(0)
            self.nhanvientiepdon.setCurrentIndex(0)

            self.chieucao.clear()
            self.cannang.clear()
            self.huyetap.clear()
            self.nhietdo.clear()
            self.nhiptho.clear()
            self.nhiptim.clear()
            self.ngaylap.setDate(QDate.currentDate())

            # Sinh số hồ sơ mới
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM tiep_don")
                count = cur.fetchone()[0] or 0
                self.mahoso.setText(f"HS{count + 1:03d}")
                conn.close()
            except Exception as e:
                print("⚠️ Không thể sinh số hồ sơ mới:", e)
                self.mahoso.setText("HS001")

            # Làm mới danh sách
            self.load_benh_nhan_list()

            # Focus về họ tên
            self.hoten.setFocus()
            self.hoten.setEditText("")

            print("🧹 Form đã được reset hoàn toàn!")

        except Exception as e:
            print("❌ Lỗi khi reset form:", e)

        finally:
            # ✅ Bật lại signal sau khi reset xong
            try:
                self.hoten.blockSignals(False)
            except:
                pass


    def sua_du_lieu(self):
        if not self.selected_ma_hoso:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một hồ sơ để sửa.")
            return

        # Khi người dùng chọn sửa, delegate sang hàm chung để load dữ liệu
        # và bật chế độ sửa.
        self.load_hoso_to_form(self.selected_ma_hoso)
        self.is_edit_mode = True
        self.set_form_editable(True)  # Mở khóa form để sửa
        QMessageBox.information(self, "Sẵn sàng", f"Đã tải thông tin hồ sơ {self.selected_ma_hoso} để chỉnh sửa.")

    def load_hoso_to_form(self, ma_hoso):
        """Load dữ liệu hồ sơ (ma_hoso) vào form mà không bật chế độ sửa hay thông báo.

        Dùng cả bảng tiep_don và benh_nhan để điền các trường có sẵn.
        """
        if not ma_hoso:
            return
            
        # Khóa form trước khi load dữ liệu
        self.set_form_editable(False)
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    t.ma_hoso, t.ngay_tiep_don, t.phong_kham, t.bac_si_kham, 
                    t.tinh_trang, t.tien_kham, t.nv_tiepdon, t.huyet_ap, 
                    t.nhiet_do, t.chieu_cao, t.can_nang, t.nhip_tho, t.nhip_tim,
                    b.ho_ten, b.gioi_tinh, b.ngay_sinh, b.tuoi, b.dia_chi,
                    b.dien_thoai, b.so_cccd, b.doi_tuong, b.nghe_nghiep,
                    b.nguoi_gioi_thieu, b.loai_kham
                FROM tiep_don t
                JOIN benh_nhan b ON t.benh_nhan_id = b.id
                WHERE t.ma_hoso = ?
            """, (ma_hoso,))
            record = cur.fetchone()
        finally:
            conn.close()

        if not record:
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
            "nhip_tho": record[11],
            "nhip_tim": record[12],
        }

        data_bn = {
            "ho_ten": record[13],
            "gioi_tinh": record[14],
            "ngay_sinh": record[15],
            "tuoi": record[16],
            "dia_chi": record[17],
            "dien_thoai": record[18],
            "so_cccd": record[19],
            "doi_tuong": record[20],
            "nghe_nghiep": record[21],
            "nguoi_gioi_thieu": record[22],
            "loai_kham": record[23],
        }


        # --- Đổ dữ liệu lên form bệnh nhân ---
        try:
            self.hoten.setCurrentText(data_bn["ho_ten"])
        except Exception:
            pass
        try:
            self.gioitinh.setCurrentText(data_bn["gioi_tinh"])
        except Exception:
            pass
        try:
            if data_bn["ngay_sinh"]:
                self.ngaysinh.setDate(QDate.fromString(data_bn["ngay_sinh"], "yyyy-MM-dd"))
        except Exception:
            pass
        try:
            self.update_age()
        except Exception:
            pass
        try:
            self.diachi.setText(data_bn["dia_chi"] or "")
        except Exception:
            pass
        try:
            self.dienthoai.setText(data_bn["dien_thoai"] or "")
        except Exception:
            pass
        try:
            self.socccd.setText(data_bn["so_cccd"] or "")
        except Exception:
            pass
        try:
            self.doituong.setCurrentText(data_bn["doi_tuong"] or "")
        except Exception:
            pass
        try:
            self.nghenghiep.setText(data_bn["nghe_nghiep"] or "")
        except Exception:
            pass
        try:
            self.nguoigioithieu.setCurrentText(data_bn["nguoi_gioi_thieu"] or "")
        except Exception:
            pass
        try:
            self.loaikham.setCurrentText(data_bn["loai_kham"] or "")
        except Exception:
            pass

        # --- Đổ dữ liệu lên form tiếp đón ---
        try:
            self.mahoso.setText(data_td["ma_hoso"])
        except Exception:
            pass
        try:
            self.phongkham.setCurrentText(data_td["phong_kham"])
        except Exception:
            pass
        try:
            self.bacsi.setCurrentText(data_td["bac_si_kham"])
        except Exception:
            pass
        try:
            if data_td["ngay_tiep_don"]:
                self.ngaylap.setDate(QDate.fromString(data_td["ngay_tiep_don"], "yyyy-MM-dd"))
        except Exception:
            pass
        try:
            self.tinhtrang.setCurrentText(data_td["tinh_trang"])
        except Exception:
            pass
        try:
            # Helpers để định dạng số khi load hồ sơ
            def _format_number(v):
                if v is None or v == "":
                    return ""
                try:
                    num = float(v)
                except Exception:
                    return str(v)
                return str(int(num)) if float(num).is_integer() else f"{num:.1f}".rstrip('0').rstrip('.')

            def _format_money(v):
                if v is None or v == "":
                    return "0"
                try:
                    num = float(v)
                    return "{:,.0f}".format(num).replace(",", ".")
                except Exception:
                    return str(v)

            # Tiền khám hiển thị với dấu chấm phân cách hàng nghìn
            self.nhiptho.setText(_format_number(data_td.get("nhip_tho")))
            self.nhiptim.setText(_format_number(data_td.get("nhip_tim")))

            # Những trường text/chuỗi
            self.nhanvientiepdon.setCurrentText(str(data_td.get("nv_tiepdon") or ""))
            self.huyetap.setText(_format_number(data_td.get("huyet_ap")))

            # Số liệu y tế (không hiển thị .0 nếu là số nguyên)
            self.huyetap.setText(str(data_td.get("huyet_ap") or ""))
            self.nhietdo.setText(_format_number(data_td.get("nhiet_do")))
            self.chieucao.setText(_format_number(data_td.get("chieu_cao")))
            self.cannang.setText(_format_number(data_td.get("can_nang")))
        except Exception:
            pass

        # Emit patient_selected signal with benh_nhan id when known
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Lấy benh_nhan_id từ bảng tiep_don theo ma_hoso để đảm bảo đúng bản ghi
            try:
                mid = data_td.get("ma_hoso")
            except Exception:
                mid = None

            if mid:
                cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (mid,))
                rid = cur.fetchone()
            else:
                rid = None

            conn.close()
            if rid and rid[0]:
                try:
                    import signals as sig_module
                    sig_module.current_patient_id = int(rid[0])
                    app_signals.patient_selected.emit(int(rid[0]))
                except Exception:
                    pass
        except Exception:
            pass

    def luu_du_lieu(self):
        """Lưu các thay đổi khi đang ở chế độ sửa (được gọi bởi nút 'Lưu')."""
        # Nếu đang ở chế độ sửa và có hồ sơ đang chọn -> cập nhật
        if getattr(self, "is_edit_mode", False) and getattr(self, "selected_ma_hoso", None):
            try:
                conn = get_connection()
                data_bn, data_td = self.collect_form_data()
                # Cập nhật vào DB
                self.cap_nhat_khi_nhan_sua(conn, self.selected_ma_hoso, data_bn, data_td)
                conn.close()

                QMessageBox.information(self, "Thành công", f"Đã lưu thay đổi cho hồ sơ {self.selected_ma_hoso}!")

                # Reset trạng thái
                self.is_edit_mode = False
                try:
                    self.btn_luu.setEnabled(False)
                except Exception:
                    pass

                # Làm mới giao diện
                self.load_danh_sach_tiep_don()
                self.load_thongke_luot_tiepdon()
                self.reset_form()
                self.selected_ma_hoso = None

            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu thay đổi:\n{e}")
        else:
            # Nếu không ở chế độ sửa -> hành vi nút Lưu là lưu bản ghi mới (tạo mới)
            result = self.save_data()
            if result:
                # Sau khi lưu mới, disable nút lưu và khóa form
                try:
                    self.btn_luu.setEnabled(False)
                except Exception:
                    pass
            # Nếu save_data xử lý reset_form bên trong, không cần làm thêm

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

            # 🔹 Load lại bảng thống kê và danh sách từ database để đảm bảo đồng bộ
            try:
                self.load_thongke_luot_tiepdon()
                self.load_danh_sach_tiep_don()
                self.reset_form()
                self.selected_ma_hoso = None
            except Exception as _:
                # Nếu có lỗi khi load lại, bỏ qua nhưng vẫn tiếp tục (đã xóa trong DB)
                pass

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
        """
        try:
            output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
            os.makedirs(output_dir, exist_ok=True)

            file_path = os.path.join(output_dir, f"{self.selected_ma_hoso}.pdf")

            # === Đăng ký font Unicode (nếu cần) ===
            font_path = os.path.join(os.path.dirname(__file__), "fonts", "arial.ttf")
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))
                except Exception:
                    # Nếu đăng ký thất bại thì vẫn tiếp tục với font mặc định
                    pass

            # === Tạo file PDF ===
            c = canvas.Canvas(file_path, pagesize=A4)
            try:
                c.setFont("ArialUnicode", 16)
            except Exception:
                c.setFont("Helvetica", 16)
            c.drawCentredString(300, 800, "PHIẾU TIẾP ĐÓN KHÁM BỆNH")

            try:
                c.setFont("ArialUnicode", 12)
            except Exception:
                c.setFont("Helvetica", 12)
            y = 760
            line_height = 25

            def write_line(text):
                nonlocal y
                c.drawString(80, y, text)
                y -= line_height

            # Ghi nội dung phiếu
            write_line(f"Số hồ sơ: {self.selected_ma_hoso}")
            # Thông tin chính của bệnh nhân (hiển thị đầy đủ theo yêu cầu)
            def safe_widget_text(widget, method="currentText"):
                try:
                    if not widget:
                        return ""
                    if method == "currentText" and hasattr(widget, "currentText"):
                        return widget.currentText()
                    if method == "text" and hasattr(widget, "text"):
                        return widget.text()
                    return str(widget)
                except Exception:
                    return ""

            hoten = safe_widget_text(getattr(self, "hoten", None), "currentText")
            gioitinh = safe_widget_text(getattr(self, "gioitinh", None), "currentText")
            ngaysinh = ""
            try:
                if hasattr(self, "ngaysinh") and self.ngaysinh.date():
                    ngaysinh = self.ngaysinh.date().toString("dd/MM/yyyy")
            except Exception:
                ngaysinh = ""
            tuoi = safe_widget_text(getattr(self, "tuoi", None), "text")
            diachi = safe_widget_text(getattr(self, "diachi", None), "text")
            dienthoai = safe_widget_text(getattr(self, "dienthoai", None), "text")
            nghenghiep = safe_widget_text(getattr(self, "nghenghiep", None), "text")
            loaikham = safe_widget_text(getattr(self, "loaikham", None), "currentText")

            write_line(f"Họ và tên: {hoten}")
            write_line(f"Giới tính: {gioitinh}")
            write_line(f"Ngày sinh: {ngaysinh}")
            write_line(f"Tuổi: {tuoi}")
            write_line(f"Địa chỉ: {diachi}")
            write_line(f"Điện thoại: {dienthoai}")
            write_line(f"Nghề nghiệp: {nghenghiep}")
            write_line(f"Loại khám: {loaikham}")

            # Thông tin tiếp đón (phòng, bác sĩ)
            write_line(f"Phòng khám: {self.phongkham.currentText()}")
            write_line(f"Bác sĩ khám: {self.bacsi.currentText()}")

            c.save()
            return file_path

        except Exception as e:
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
        hoten = self.hoten.currentText().strip()
        phongkham = self.phongkham.currentText().strip()
        bacsi = self.bacsi.currentText().strip()
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

        # === Cấu trúc phiếu STT ===
        PAGE_WIDTH = 300
        PAGE_CENTER = PAGE_WIDTH // 2
        
        # --- Tiêu đề ---
        c.setFont("ArialUnicode", 16)
        c.drawCentredString(PAGE_CENTER, 400, "PHIẾU SỐ THỨ TỰ")
        
        # --- Thông tin ngày ---
        c.setFont("ArialUnicode", 11)
        c.drawCentredString(PAGE_CENTER, 380, f"Ngày {ngay}")

        # --- STT to và nổi bật ---
        c.setFont("ArialUnicode", 24)  # Size lớn hơn để STT nổi bật
        c.drawCentredString(PAGE_CENTER, 340, f"STT: {str(stt).zfill(2)}")

        # --- Thông tin bệnh nhân ---
        c.setFont("ArialUnicode", 12)
        # Tên bệnh nhân - in đậm bằng cách vẽ 2 lần với offset nhỏ
        c.drawCentredString(PAGE_CENTER+0.5, 300, hoten)
        c.drawCentredString(PAGE_CENTER, 300, hoten)

        c.setFont("ArialUnicode", 11)
        # Thông tin cá nhân
        y = 270
        c.drawString(30, y, f"Giới tính: {gioitinh}")
        c.drawString(160, y, f"Tuổi: {namsinh}")

        # Kẻ đường ngang phân cách
        y -= 15
        c.line(30, y, PAGE_WIDTH-30, y)
        
        # Thông tin phòng và bác sĩ
        y -= 20
        c.setFont("ArialUnicode", 11)
        c.drawString(30, y, f"Phòng khám:")
        c.setFont("ArialUnicode", 11)
        c.drawString(50, y-15, phongkham)

        y -= 40
        c.setFont("ArialUnicode", 11)
        c.drawString(30, y, f"Bác sĩ khám:")
        c.setFont("ArialUnicode", 11)
        c.drawString(50, y-15, bacsi)

        # Ghi chú ở cuối
        y -= 40
        c.setFont("ArialUnicode", 10)
        c.drawCentredString(PAGE_CENTER, y, "Vui lòng chờ đến lượt theo số thứ tự được gọi")
        c.drawCentredString(PAGE_CENTER, y-15, "(Phiếu chỉ có giá trị trong ngày)")
        
        c.save()
        return file_path



    # ---------------------------
    # Cập nhật bản ghi hiện có
    # ---------------------------
    def cap_nhat_khi_nhan_sua(self, conn, ma_hoso, data_bn, data_td):
        import logging
        cur = conn.cursor()

        # Lấy ID bệnh nhân từ mã hồ sơ
        cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ?", (ma_hoso,))
        result = cur.fetchone()
        if not result:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy hồ sơ {ma_hoso}.")
            return
        benh_nhan_id = result[0]

        try:
            # --- Cập nhật bảng benh_nhan ---
            set_bn = ", ".join([f"{col} = ?" for col in data_bn.keys()])
            cur.execute(f"UPDATE benh_nhan SET {set_bn} WHERE id = ?", (*data_bn.values(), benh_nhan_id))

            # --- Cập nhật bảng tiep_don ---
            set_td = ", ".join([f"{col} = ?" for col in data_td.keys()])
            sql = f"UPDATE tiep_don SET {set_td} WHERE ma_hoso = ?"
            values = (*data_td.values(), ma_hoso)
            logging.info(f"[cap_nhat_khi_nhan_sua] SQL: {sql} | VALUES: {values}")
            cur.execute(sql, values)

            conn.commit()
        except Exception as e:
            logging.error(f"[cap_nhat_khi_nhan_sua] Error: {e}")
            raise
        # Sau khi cập nhật thành công, khóa lại form
        self.set_form_editable(False)

    # ---------------------------
    # Xử lý khi chọn 1 dòng trong bảng danh sách
    # ---------------------------
    def on_row_selected(self, row, column):
        """Xử lý khi chọn 1 dòng trong bảng tiếp đón
        Handler signature uses the (row, column) args provided by cellClicked
        so we always act on the exact clicked row.
        """
        if row < 0:
            return  # không có dòng nào được chọn
        item = self.tableTiepDon.item(row, 0)
        if item:
            # ensure only this row is visually selected
            try:
                self.tableTiepDon.clearSelection()
            except Exception:
                pass
            try:
                self.tableTiepDon.selectRow(row)
            except Exception:
                # Dự phòng: dùng setCurrentCell nếu selectRow không khả dụng
                try:
                    self.tableTiepDon.setCurrentCell(row, 0)
                except Exception:
                    pass

            self.selected_ma_hoso = item.text()
            print(f"👉 Đã chọn hồ sơ: {self.selected_ma_hoso}")
            # Load form data and disable editing
            self.load_hoso_to_form(self.selected_ma_hoso)
            self.set_form_editable(False)  # Lock form after loading
            self.btn_sua.setEnabled(True)  # Enable edit button
            self.btn_xoa.setEnabled(True)  # Enable delete button

    
    # ---------------------------
    # Load dữ liệu bệnh nhân vào form (khi chọn từ combobox)
    # ---------------------------
    def load_patient_into_form(self, ho_ten):
        try:
            # Nếu người dùng truyền chuỗi chứa Mã hồ sơ (ví dụ 'Họ Tên — Mã:HS005'),
            # tìm benh_nhan_id từ bảng tiep_don theo ma_hoso và load theo id đó.
            if isinstance(ho_ten, str) and "Mã:" in ho_ten:
                try:
                    ma = ho_ten.split("Mã:")[1].split()[0].strip().strip('—').strip()
                    if ma:
                        cur = get_connection().cursor()
                        cur.execute("SELECT benh_nhan_id FROM tiep_don WHERE ma_hoso = ? LIMIT 1", (ma,))
                        r = cur.fetchone()
                        try:
                            cur.connection.close()
                        except Exception:
                            pass
                        if r and r[0]:
                            return self.load_patient_by_id(r[0])
                except Exception:
                    # nếu parse hoặc lookup thất bại, fallback sang tìm theo tên
                    pass
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
            self.hoten.setCurrentText(data.get("ho_ten", ""))
            self.gioitinh.setCurrentText(data.get("gioi_tinh", "Nam"))
            if data.get("ngay_sinh"):
                self.ngaysinh.setDate(QDate.fromString(data.get("ngay_sinh"), "yyyy-MM-dd"))
            self.update_age()
            self.diachi.setText(data.get("dia_chi", ""))
            self.dienthoai.setText(data.get("dien_thoai", ""))
            self.socccd.setText(data.get("so_cccd", ""))
            self.doituong.setCurrentText(data.get("doi_tuong", "BHYT"))
            self.nghenghiep.setText(data.get("nghe_nghiep", ""))
            self.nguoigioithieu.setCurrentText(data.get("nguoi_gioi_thieu", "Bác sĩ"))
            self.loaikham.setCurrentText(data.get("loai_kham", "Khám và tư vấn"))
            self.hoten.setFocus()
            self.hoten.setEditText(ho_ten)

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

                    # Hàm nhỏ để định dạng số
                    def format_number(value):
                        if value is None:
                            return ""
                        if isinstance(value, (int, float)):
                            if float(value).is_integer():
                                return str(int(value))
                            return f"{value:.1f}".rstrip('0').rstrip('.')
                        return str(value)

                    # Hàm định dạng tiền
                    def format_money(value):
                        if value is None:
                            return "0"
                        try:
                            num = float(value)
                            return "{:,.0f}".format(num).replace(",", ".")
                        except:
                            return str(value)

                    self.mahoso.setText(str(td_data.get("ma_hoso") or ""))
                    self.phongkham.setCurrentText(str(td_data.get("phong_kham") or ""))
                    self.bacsi.setCurrentText(str(td_data.get("bac_si_kham") or ""))
                    self.ngaylap.setDate(QDate.fromString(str(td_data.get("ngay_tiep_don") or ""), "yyyy-MM-dd"))
                    self.tinhtrang.setCurrentText(str(td_data.get("tinh_trang") or ""))
                    self.nhiptho.setText(str(td_data.get("nhip_tho") or ""))
                    self.nhiptim.setText(str(td_data.get("nhip_tim") or ""))
                    self.nhanvientiepdon.setCurrentText(str(td_data.get("nv_tiepdon") or ""))
                    self.huyetap.setText(str(td_data.get("huyet_ap") or ""))
                    self.nhietdo.setText(format_number(td_data.get("nhiet_do")))
                    self.chieucao.setText(format_number(td_data.get("chieu_cao")))
                    self.cannang.setText(format_number(td_data.get("can_nang")))
            except Exception as e:
                print("❌ Lỗi khi load tiếp đón:", e)

            # Phát tín hiệu patient_selected để các form khác phản ứng
            try:
                pid = data.get('id') or data.get('ID') or None
                if pid:
                    import signals as sig_module
                    sig_module.current_patient_id = int(pid)
                    app_signals.patient_selected.emit(int(pid))
            except Exception:
                pass



        except Exception as e:
            import traceback
            print("❌ Lỗi khi load bệnh nhân:", e)
            traceback.print_exc()

    # ---------------------------
    # Load bệnh nhân theo id (an toàn khi có nhiều người cùng tên)
    # ---------------------------
    def load_patient_by_id(self, pid):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM benh_nhan WHERE id = ? LIMIT 1", (pid,))
            columns = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            conn.close()

            if not row:
                return

            data = dict(zip(columns, row))

            # Điền dữ liệu vào form giống như load_patient_into_form
            self.hoten.setCurrentText(data.get("ho_ten", ""))
            self.gioitinh.setCurrentText(data.get("gioi_tinh", "Nam"))
            if data.get("ngay_sinh"):
                self.ngaysinh.setDate(QDate.fromString(data.get("ngay_sinh"), "yyyy-MM-dd"))
            self.update_age()
            self.diachi.setText(data.get("dia_chi", ""))
            self.dienthoai.setText(data.get("dien_thoai", ""))
            self.socccd.setText(data.get("so_cccd", ""))
            self.doituong.setCurrentText(data.get("doi_tuong", "BHYT"))
            self.nghenghiep.setText(data.get("nghe_nghiep", ""))
            self.nguoigioithieu.setCurrentText(data.get("nguoi_gioi_thieu", "Bác sĩ"))
            self.loaikham.setCurrentText(data.get("loai_kham", "Khám và tư vấn"))
            self.hoten.setFocus()

            # Tải bản ghi `tiep_don` mới nhất cho bệnh nhân này
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM tiep_don WHERE benh_nhan_id = ? ORDER BY ngay_tiep_don DESC LIMIT 1", (pid,))
            tiepdon = cur.fetchone()
            td_columns = [desc[0] for desc in cur.description] if tiepdon else []
            conn.close()

            if tiepdon:
                td_data = dict(zip(td_columns, tiepdon))
                # copy existing formatting logic
                def format_number(value):
                    if value is None:
                        return ""
                    if isinstance(value, (int, float)):
                        if float(value).is_integer():
                            return str(int(value))
                        return f"{value:.1f}".rstrip('0').rstrip('.')
                    return str(value)

                self.mahoso.setText(str(td_data.get("ma_hoso") or ""))
                self.phongkham.setCurrentText(str(td_data.get("phong_kham") or ""))
                self.bacsi.setCurrentText(str(td_data.get("bac_si_kham") or ""))
                if td_data.get("ngay_tiep_don"):
                    self.ngaylap.setDate(QDate.fromString(str(td_data.get("ngay_tiep_don") or ""), "yyyy-MM-dd"))
                self.tinhtrang.setCurrentText(str(td_data.get("tinh_trang") or ""))
                self.nhiptho.setText(str(td_data.get("nhip_tho") or ""))
                self.nhiptim.setText(str(td_data.get("nhip_tim") or ""))
                self.nhanvientiepdon.setCurrentText(str(td_data.get("nv_tiepdon") or ""))
                self.huyetap.setText(str(td_data.get("huyet_ap") or ""))
                self.nhietdo.setText(format_number(td_data.get("nhiet_do")))
                self.chieucao.setText(format_number(td_data.get("chieu_cao")))
                self.cannang.setText(format_number(td_data.get("can_nang")))

            try:
                if pid:
                    import signals as sig_module
                    sig_module.current_patient_id = int(pid)
                    app_signals.patient_selected.emit(int(pid))
            except Exception:
                pass

        except Exception as e:
            import traceback
            print("❌ Lỗi khi load bệnh nhân theo id:", e)
            traceback.print_exc()

        
        
    
    # ---------------------------
    # Các hàm xử lý việc tải có kiểm soát từ combobox/completer
    # ---------------------------
    def on_completer_activated(self, text):
        """Called when user selects a name from the completer list (explicit selection)."""
        try:
            if not text or not text.strip():
                return

            # Khi completer trả về display text (vì chúng ta tạo display bao gồm ID),
            # tìm index trong combobox và lấy id từ itemData (Qt.UserRole)
            idx = self.hoten.findText(text.strip(), Qt.MatchExactly)
            if idx >= 0:
                pid = self.hoten.itemData(idx, Qt.UserRole)
                if pid:
                    return self.load_patient_by_id(pid)

            # Fallback: nếu không có id (ví dụ combobox cũ), thử load theo tên
            self.load_patient_into_form(text.strip())
        except Exception as e:
            print("❌ Lỗi on_completer_activated:", e)

    def on_editing_finished(self):
        """Called when editing finished in the combobox line edit.

        Only auto-load when the entered text exactly matches a full existing name
        (case-insensitive). This avoids loading on partial typing like "ro".
        """
        try:
            text = self.hoten.currentText().strip()
            if not text:
                return

            model = self.completer.model()
            # Ưu tiên dùng QStringListModel.stringList() khi có
            try:
                names = model.stringList()
            except Exception:
                # Dự phòng: lấy dữ liệu qua model index
                names = [model.data(model.index(i, 0)) for i in range(model.rowCount())]

            # Chỉ tự động tải khi văn bản nhập khớp chính xác một mục hiển thị đầy đủ
            # (ví dụ: mục bao gồm ID và ta có thể lấy itemData).
            # Điều này tránh vô tình tải bệnh nhân đã có khi người dùng
            # đang gõ một bệnh nhân mới có cùng tên.
            exact_idx = self.hoten.findText(text.strip(), Qt.MatchExactly)
            if exact_idx >= 0:
                pid = self.hoten.itemData(exact_idx, Qt.UserRole)
                if pid:
                    return self.load_patient_by_id(pid)

            # Nếu không thì KHÔNG tự động tải — người dùng có thể đang nhập bệnh nhân mới
            return
        except Exception as e:
            print("❌ Lỗi on_editing_finished:", e)

    # ---------------------------
    # Kết nối sự kiện khi chọn tên từ combobox
    # ---------------------------
    def connect_combobox_event(self):
        # Ngắt mọi kết nối hiện có để tránh gọi trùng lặp
        try:
            self.hoten.currentTextChanged.disconnect()
        except Exception:
            pass
        try:
            self.hoten.lineEdit().editingFinished.disconnect()
        except Exception:
            pass

        # Chỉ tải khi người dùng chọn rõ ràng từ completer
        try:
            self.completer.activated.connect(self.on_completer_activated)
        except Exception as e:
            print("⚠️ Không thể kết nối completer.activated:", e)

        # Khi hoàn tất chỉnh sửa, chỉ tải nếu khớp chính xác
        try:
            self.hoten.lineEdit().editingFinished.connect(self.on_editing_finished)
        except Exception as e:
            print("⚠️ Không thể kết nối editingFinished:", e)



    # ---------------------------
    # Load danh sách tiếp đón khám chữa bệnh
    # ---------------------------
    def load_danh_sach_tiep_don(self, limit=50):
        """Load danh sách tiếp đón với giới hạn số lượng bản ghi"""
        conn = get_connection()
        cur = conn.cursor()
        
        # Lấy tổng số bản ghi để tính số trang
        cur.execute("SELECT COUNT(*) FROM tiep_don")
        total_records = cur.fetchone()[0]
        
        # Chỉ lấy số lượng bản ghi theo limit, sắp xếp theo ngày mới nhất
        cur.execute("""
            SELECT td.ma_hoso, td.ngay_tiep_don, td.phong_kham, bn.ho_ten, td.bac_si_kham, td.tinh_trang
            FROM tiep_don td
            JOIN benh_nhan bn ON td.benh_nhan_id = bn.id
            ORDER BY td.ngay_tiep_don DESC
            LIMIT ?
        """, (limit,))
        records = cur.fetchall()
        conn.close()

        # Xóa dữ liệu cũ
        self.tableTiepDon.setRowCount(0)

        # Thêm dữ liệu mới theo từng dòng
        for row_data in records:
            row = self.tableTiepDon.rowCount()
            self.tableTiepDon.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)  # Căn giữa dữ liệu
                self.tableTiepDon.setItem(row, col, item)

        # Tối ưu hiển thị
        self.tableTiepDon.setAlternatingRowColors(True)  # Màu xen kẽ
        # Giữ cho các cột giãn đều để bảng luôn lấp đầy vùng hiển thị khi load lại
        try:
            header = self.tableTiepDon.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            self.tableTiepDon.setAlternatingRowColors(True)
        except Exception:
            # Nếu không thành công, fallback về resizeColumnsToContents
            self.tableTiepDon.resizeColumnsToContents()
        
        # Sau khi load xong, clear selection để không highlight hàng đầu mặc định
        try:
                # bỏ chọn mọi ô (xóa selection và current cell nếu có)
            self.tableTiepDon.clearSelection()
                # setCurrentCell(-1,-1) có thể gây lỗi trên một số phiên bản PyQt, bỏ qua nếu lỗi
            try:
                self.tableTiepDon.setCurrentCell(-1, -1)
            except Exception:
                pass
        except Exception:
            pass

        # Thông báo số lượng bản ghi đang hiển thị
        if total_records > limit:
            QMessageBox.information(self, "Thông báo", 
                f"Đang hiển thị {limit} bản ghi mới nhất trong tổng số {total_records} bản ghi.\n"
                "Sử dụng chức năng tìm kiếm để xem thêm bản ghi cũ hơn.")

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
        """Load thống kê lượt tiếp đón từ DB, chỉ lấy thống kê của ngày hiện tại"""
        from database import get_connection
        import datetime
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = get_connection()
        cur = conn.cursor()

        # Chỉ lấy thống kê của ngày hiện tại
        cur.execute("""
            SELECT 
                t.phong_kham, 
                COUNT(t.ma_hoso) as total_tiepdon,
                SUM(CASE WHEN t.tinh_trang LIKE '%đã khám%' OR t.tinh_trang LIKE '%hoàn thành%' 
                    THEN 1 ELSE 0 END) as total_dakham
            FROM tiep_don t
            WHERE date(t.ngay_tiep_don) = ?
            GROUP BY t.phong_kham
        """, (today,))
        rows = cur.fetchall()
        conn.close()

        # Xóa toàn bộ hàng cũ
        self.table_thongke.setRowCount(0)

        # Đổ dữ liệu vào bảng
        for row in rows:
            phong_kham, total_tiepdon, total_dakham = row
            row = self.table_thongke.rowCount()
            self.table_thongke.insertRow(row)
            
            # Cột phòng khám
            item_phong = QTableWidgetItem(phong_kham or "")
            item_phong.setTextAlignment(Qt.AlignCenter)
            self.table_thongke.setItem(row, 0, item_phong)
            
            # Cột số lượng tiếp đón
            item_tiepdon = QTableWidgetItem(str(total_tiepdon))
            item_tiepdon.setTextAlignment(Qt.AlignCenter)
            self.table_thongke.setItem(row, 1, item_tiepdon)
            
            # Cột số lượng đã khám
            item_dakham = QTableWidgetItem(str(total_dakham))
            item_dakham.setTextAlignment(Qt.AlignCenter)
            self.table_thongke.setItem(row, 2, item_dakham)