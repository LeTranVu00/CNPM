from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QDialog, QFormLayout,
    QHeaderView, QSizePolicy, QTabWidget, QTextEdit, QCompleter, QDateEdit
)
from PyQt5.QtCore import Qt, QDateTime, QTimer, QDate, pyqtSignal
from app_signals import app_signals
from database import get_connection


class QuanLyThuoc(QWidget):
    """Form quản lý thuốc và quản lý thanh toán (thuốc/dịch vụ)."""
    # Signal để thông báo khi dữ liệu được ghi nhận
    data_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý thuốc và thanh toán")
        self.init_db()
        self.init_ui()
        self.load_drugs()
        self.load_import_drugs_history()
        self.load_summary()
        self.load_detail_services()
        
        # Timer tự động cập nhật mỗi 5 giây để cập nhật doanh thu ngay khi có dữ liệu mới
        self.auto_update_timer = QTimer()
        self.auto_update_timer.timeout.connect(self.auto_refresh_summary)
        self.auto_update_timer.start(5000)  # 5 giây = 5000ms

        # Kết nối global app signals để cập nhật khi có thay đổi từ các form khác
        try:
            app_signals.data_changed.connect(self.on_data_updated)
            print("✓ QuanLyThuoc kết nối data_changed signal")
        except Exception as e:
            print(f"✗ Lỗi kết nối data_changed: {e}")
        try:
            app_signals.medicine_exported.connect(self.on_data_updated)
            print("✓ QuanLyThuoc kết nối medicine_exported signal")
        except Exception as e:
            print(f"✗ Lỗi kết nối medicine_exported: {e}")

    def init_db(self):
        conn = get_connection()
        cur = conn.cursor()
        # Ensure payments table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS thanh_toan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ngay TEXT,
                loai TEXT,
                mo_ta TEXT,
                so_tien REAL
            )
        """)
        conn.commit()
        conn.close()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget để chuyển đổi giữa các view
        self.tabs = QTabWidget()
        
        # Tab 1: Danh mục thuốc
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        
        # Top: simple tabs-like layout using two panels stacked vertically
        # Panel 1: Danh mục thuốc
        lbl_danh_muc = QLabel("DANH MỤC THUỐC")
        lbl_danh_muc.setStyleSheet("color: #0078D7; font-weight: bold;")
        tab1_layout.addWidget(lbl_danh_muc)
        
        # Thanh tìm kiếm cho bảng danh mục
        search_drug_row = QHBoxLayout()
        self.search_drugs = QLineEdit()
        self.search_drugs.setPlaceholderText("Tìm kiếm danh mục (Mã/Tên thuốc)...")
        self.search_drugs.setMaximumWidth(300)
        self.search_drugs.textChanged.connect(self.filter_drugs_table)
        search_drug_row.addWidget(self.search_drugs)
        search_drug_row.addStretch()
        tab1_layout.addLayout(search_drug_row)
        
        self.table_drugs = QTableWidget(0, 5)
        self.table_drugs.setHorizontalHeaderLabels(["Mã thuốc", "Tên thuốc", "Đơn vị", "Giá", "Tồn kho"])
        self.table_drugs.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_drugs.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_drugs.setSelectionMode(QTableWidget.SingleSelection)
        # Make the drugs table larger and allow it to expand
        self.table_drugs.setMinimumHeight(300)
        self.table_drugs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Column sizing: make 'Tên thuốc' stretch to fill available width
        header = self.table_drugs.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_drugs.setColumnWidth(0, 120)
        self.table_drugs.setColumnWidth(2, 100)
        self.table_drugs.setColumnWidth(3, 100)
        self.table_drugs.setColumnWidth(4, 80)
        tab1_layout.addWidget(self.table_drugs)

        # Tổng giá trị tồn kho
        self.lbl_total_value = QLabel("Tổng giá trị tồn kho: 0")
        self.lbl_total_value.setStyleSheet("font-size: 12pt; font-weight: bold; color: #0078D7;")
        tab1_layout.addWidget(self.lbl_total_value)

        hbtn = QHBoxLayout()
        btn_add = QPushButton("Thêm")
        btn_edit = QPushButton("Sửa")
        btn_del = QPushButton("Xóa")
        btn_refresh = QPushButton("Làm mới")
        hbtn.addWidget(btn_add)
        hbtn.addWidget(btn_edit)
        hbtn.addWidget(btn_del)
        hbtn.addStretch()
        hbtn.addWidget(btn_refresh)
        tab1_layout.addLayout(hbtn)

        btn_add.clicked.connect(self.on_add_drug)
        btn_edit.clicked.connect(self.on_edit_drug)
        btn_del.clicked.connect(self.on_delete_drug)
        btn_refresh.clicked.connect(self.load_drugs)

        # Divider
        tab1_layout.addSpacing(8)
        # The "Nhập thuốc" input area was removed per user request; keep only import history below.

        # Bảng lịch sử nhập thuốc
        tab1_layout.addSpacing(8)
        lbl_lich_su = QLabel("LỊCH SỬ NHẬP THUỐC")
        lbl_lich_su.setStyleSheet("color: #0078D7; font-weight: bold;")
        tab1_layout.addWidget(lbl_lich_su)
        
        # Thanh tìm kiếm cho bảng lịch sử
        search_row = QHBoxLayout()
        self.search_import = QLineEdit()
        self.search_import.setPlaceholderText("Tìm kiếm (Mã/Tên thuốc)...")
        self.search_import.setMaximumWidth(300)
        self.search_import.textChanged.connect(self.filter_import_drugs_table)
        search_row.addWidget(self.search_import)
        search_row.addStretch()
        tab1_layout.addLayout(search_row)
        
        self.table_import_drugs = QTableWidget(0, 5)
        self.table_import_drugs.setHorizontalHeaderLabels(["Ngày", "Mã thuốc", "Tên thuốc", "Đơn vị", "Số lượng nhập"])
        self.table_import_drugs.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_import_drugs.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_import_drugs.setMinimumHeight(200)
        
        header_import = self.table_import_drugs.horizontalHeader()
        header_import.setSectionResizeMode(0, QHeaderView.Fixed)
        header_import.setSectionResizeMode(1, QHeaderView.Fixed)
        header_import.setSectionResizeMode(2, QHeaderView.Stretch)
        header_import.setSectionResizeMode(3, QHeaderView.Fixed)
        header_import.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_import_drugs.setColumnWidth(0, 150)
        self.table_import_drugs.setColumnWidth(1, 120)
        # Make 'Đơn vị' and 'Số lượng nhập' columns wider for readability
        self.table_import_drugs.setColumnWidth(3, 140)
        self.table_import_drugs.setColumnWidth(4, 140)
        tab1_layout.addWidget(self.table_import_drugs)

        # Nút thêm, sửa, xóa, làm mới cho bảng lịch sử nhập
        import_btn_layout = QHBoxLayout()
        btn_refresh_import = QPushButton("Làm mới")
        import_btn_layout.addStretch()
        import_btn_layout.addWidget(btn_refresh_import)
        tab1_layout.addLayout(import_btn_layout)

        # Keep only the refresh action for the import history
        btn_refresh_import.clicked.connect(self.load_import_drugs_history)
        
        # Tab 2: Tổng hợp doanh thu
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        # Nút làm mới tổng hợp
        summary_btn_layout = QHBoxLayout()
        btn_refresh_summary = QPushButton("Làm mới tổng hợp")
        btn_refresh_summary.clicked.connect(self.load_summary)
        # Thêm filter ngày, nút xem chi tiết theo ngày và xuất CSV
        self.summary_date_from = QDateEdit()
        self.summary_date_from.setCalendarPopup(True)
        self.summary_date_from.setDisplayFormat("yyyy-MM-dd")
        self.summary_date_from.setDate(QDate.currentDate().addMonths(-7))
        self.summary_date_from.setMaximumWidth(140)
        self.summary_date_to = QDateEdit()
        self.summary_date_to.setCalendarPopup(True)
        self.summary_date_to.setDisplayFormat("yyyy-MM-dd")
        self.summary_date_to.setDate(QDate.currentDate())
        self.summary_date_to.setMaximumWidth(140)

        btn_apply_summary = QPushButton("Áp dụng")
        btn_apply_summary.setMaximumWidth(90)
        btn_apply_summary.clicked.connect(self.filter_summary_apply)
        btn_clear_summary = QPushButton("Xóa")
        btn_clear_summary.setMaximumWidth(60)
        btn_clear_summary.clicked.connect(self.clear_summary_filters)

        btn_export_summary = QPushButton("Export CSV")
        btn_export_summary.setMaximumWidth(100)
        btn_export_summary.setToolTip("Xuất bảng tổng hợp ra file CSV trong thư mục output")
        btn_export_summary.clicked.connect(self.export_summary_csv)

        btn_view_day = QPushButton("Xem ngày")
        btn_view_day.setMaximumWidth(90)
        btn_view_day.setToolTip("Mở chi tiết cho ngày chọn trong filter")
        btn_view_day.clicked.connect(lambda: self.open_summary_day_detail(self.summary_date_from.date().toString('yyyy-MM-dd')))

        summary_btn_layout.addWidget(QLabel("Từ:"))
        summary_btn_layout.addWidget(self.summary_date_from)
        summary_btn_layout.addWidget(QLabel("Đến:"))
        summary_btn_layout.addWidget(self.summary_date_to)
        summary_btn_layout.addWidget(btn_apply_summary)
        summary_btn_layout.addWidget(btn_clear_summary)
        summary_btn_layout.addStretch()
        summary_btn_layout.addWidget(btn_view_day)
        summary_btn_layout.addWidget(btn_export_summary)
        summary_btn_layout.addWidget(btn_refresh_summary)
        tab2_layout.addLayout(summary_btn_layout)
        
        # Tổng tiền hiện tại
        self.lbl_total = QLabel("Tổng: 0")
        self.lbl_total.setStyleSheet("font-size: 16pt; font-weight: bold; color: #0078D7;")
        tab2_layout.addWidget(self.lbl_total)
        
        # Bảng tổng hợp theo ngày
        self.table_summary = QTableWidget(0, 3)
        self.table_summary.setHorizontalHeaderLabels(["Ngày", "Dịch vụ (Dịch vụ)", "Thuốc (Thuốc)"])
        self.table_summary.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_summary.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_summary.setMinimumHeight(400)
        self.table_summary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        sh = self.table_summary.horizontalHeader()
        sh.setSectionResizeMode(0, QHeaderView.Fixed)
        sh.setSectionResizeMode(1, QHeaderView.Stretch)
        sh.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_summary.setColumnWidth(0, 150)
        # Usability: alternating colors, sorting, double-click to open details for that day
        try:
            self.table_summary.setAlternatingRowColors(True)
        except Exception:
            pass
        try:
            self.table_summary.setSortingEnabled(True)
        except Exception:
            pass
        try:
            self.table_summary.cellDoubleClicked.connect(self._on_summary_row_double_click)
        except Exception:
            pass
        tab2_layout.addWidget(self.table_summary)
        
        # Tab 3: Chi tiết dịch vụ và thuốc theo ngày
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        
        # Nút làm mới
        detail_btn_layout = QHBoxLayout()
        btn_refresh_detail = QPushButton("Làm mới chi tiết")
        btn_refresh_detail.clicked.connect(self.load_detail_services)
        detail_btn_layout.addStretch()
        detail_btn_layout.addWidget(btn_refresh_detail)
        tab3_layout.addLayout(detail_btn_layout)
        
        # Bảng chi tiết dịch vụ và thuốc (gộp theo bệnh nhân / loại / nội dung)
        # Thêm các control lọc phía trên bảng
        filter_controls = QHBoxLayout()
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Tất cả", "Dịch vụ", "Thuốc"])
        self.filter_type.setMaximumWidth(120)
        self.filter_date_from = QDateEdit()
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.setDisplayFormat("yyyy-MM-dd")
        self.filter_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.filter_date_from.setMaximumWidth(140)
        self.filter_date_to = QDateEdit()
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.setDisplayFormat("yyyy-MM-dd")
        self.filter_date_to.setDate(QDate.currentDate())
        self.filter_date_to.setMaximumWidth(140)
        btn_apply_filter = QPushButton("TÌM KIẾM")
        btn_clear_filter = QPushButton("HỦY")
        filter_controls.addWidget(QLabel("Loại:"))
        filter_controls.addWidget(self.filter_type)
        filter_controls.addSpacing(8)
        filter_controls.addWidget(QLabel("Từ:"))
        filter_controls.addWidget(self.filter_date_from)
        filter_controls.addWidget(QLabel("Đến:"))
        filter_controls.addWidget(self.filter_date_to)
        filter_controls.addSpacing(8)
        # Thêm ô tìm kiếm chi tiết trước các nút Áp dụng / Xóa filter
        self.search_detail = QLineEdit()
        self.search_detail.setPlaceholderText("Tìm kiếm chi tiết (Bệnh nhân/Loại/Nội dung)...")
        self.search_detail.setMaximumWidth(350)
        # Có nút clear nhỏ bên trong QLineEdit
        try:
            self.search_detail.setClearButtonEnabled(True)
        except Exception:
            pass
        self.search_detail.setToolTip("Gõ để lọc theo Bệnh nhân / Loại / Nội dung. Nhấn Enter để áp dụng.")
        self.search_detail.textChanged.connect(self.filter_detail_apply)
        filter_controls.addWidget(QLabel("Tìm kiếm:"))
        filter_controls.addWidget(self.search_detail)
        filter_controls.addSpacing(8)
        # Thu gọn kích thước nút
        btn_apply_filter.setMaximumWidth(90)
        btn_clear_filter.setMaximumWidth(90)
        btn_apply_filter.setToolTip("Áp dụng bộ lọc")
        btn_clear_filter.setToolTip("Xóa tất cả bộ lọc và hiển thị tất cả")
        # Tooltips cho các control khác
        self.filter_type.setToolTip("Chọn loại bản ghi (Tất cả / Dịch vụ / Thuốc)")
        self.filter_date_from.setToolTip("Ngày bắt đầu (yyyy-mm-dd)")
        self.filter_date_to.setToolTip("Ngày kết thúc (yyyy-mm-dd)")
        # Enter trên ô tìm kiếm cũng sẽ áp dụng filter
        try:
            self.search_detail.returnPressed.connect(self.filter_detail_apply)
        except Exception:
            pass
        filter_controls.addWidget(btn_apply_filter)
        filter_controls.addWidget(btn_clear_filter)
        filter_controls.addStretch()

        tab3_layout.addLayout(filter_controls)
        self.table_detail = QTableWidget(0, 7)
        self.table_detail.setHorizontalHeaderLabels(["Ngày", "Bệnh nhân", "Loại", "Nội dung", "Số lượng", "Tổng tiền", "Xem chi tiết"])
        self.table_detail.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_detail.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_detail.setMinimumHeight(400)
        self.table_detail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        dh = self.table_detail.horizontalHeader()
        dh.setSectionResizeMode(0, QHeaderView.Fixed)
        dh.setSectionResizeMode(1, QHeaderView.Fixed)
        dh.setSectionResizeMode(2, QHeaderView.Fixed)
        dh.setSectionResizeMode(3, QHeaderView.Stretch)
        dh.setSectionResizeMode(4, QHeaderView.Fixed)
        dh.setSectionResizeMode(5, QHeaderView.Fixed)
        dh.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table_detail.setColumnWidth(0, 150)
        self.table_detail.setColumnWidth(1, 150)
        self.table_detail.setColumnWidth(2, 80)
        self.table_detail.setColumnWidth(4, 80)
        self.table_detail.setColumnWidth(5, 120)
        self.table_detail.setColumnWidth(6, 100)
        
        tab3_layout.addWidget(self.table_detail)
        
        # Kết nối các nút lọc
        btn_apply_filter.clicked.connect(self.filter_detail_apply)
        btn_clear_filter.clicked.connect(self.clear_detail_filters)
        self.filter_type.currentIndexChanged.connect(self.filter_detail_apply)
        
        # Lưu tham chiếu tới từng tab để có thể cấu hình hiển thị động
        self.tab_payment = tab1
        self.tab_summary = tab2
        self.tab_detail = tab3

        # Thêm các tab vào widget (mặc định hiển thị cả 3)
        self.tabs.addTab(self.tab_payment, "Ghi nhận thanh toán")
        self.tabs.addTab(self.tab_summary, "Tổng hợp doanh thu")
        self.tabs.addTab(self.tab_detail, "Chi tiết dịch vụ/thuốc")
        layout.addWidget(self.tabs)

    def set_mode(self, mode: str):
        """Cấu hình các tab hiện thị dựa trên chế độ:
        - 'quanly': chỉ hiển thị tab Ghi nhận thanh toán
        - 'thutien': chỉ hiển thị tab Chi tiết dịch vụ/thuốc
        - 'doanhthu': chỉ hiển thị tab Tổng hợp doanh thu
        """
        try:
            # Remove all existing tabs but keep the widget instances
            while self.tabs.count() > 0:
                self.tabs.removeTab(0)

            if mode == 'quanly':
                self.tabs.addTab(self.tab_payment, "Ghi nhận thanh toán")
            elif mode == 'thutien':
                self.tabs.addTab(self.tab_detail, "Chi tiết dịch vụ/thuốc")
            elif mode == 'doanhthu':
                self.tabs.addTab(self.tab_summary, "Tổng hợp doanh thu")
            else:
                # Nếu không rõ, hiển thị cả 3
                self.tabs.addTab(self.tab_payment, "Ghi nhận thanh toán")
                self.tabs.addTab(self.tab_summary, "Tổng hợp doanh thu")
                self.tabs.addTab(self.tab_detail, "Chi tiết dịch vụ/thuốc")

            # luôn chọn tab đầu tiên sau khi cấu hình
            if self.tabs.count() > 0:
                self.tabs.setCurrentIndex(0)
        except Exception:
            # Không làm vỡ giao diện nếu có lỗi
            pass

    # --- Drugs CRUD ---
    def load_drugs(self):
        """Tải danh mục thuốc từ cơ sở dữ liệu."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ma_thuoc, ten_thuoc, don_vi, gia_thuoc, ton_kho FROM danh_muc_thuoc ORDER BY ma_thuoc")
            rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()

        self.table_drugs.setRowCount(0)
        for r in rows:
            row = self.table_drugs.rowCount()
            self.table_drugs.insertRow(row)
            self.table_drugs.setItem(row, 0, QTableWidgetItem(r[0] or ""))
            self.table_drugs.setItem(row, 1, QTableWidgetItem(r[1] or ""))
            self.table_drugs.setItem(row, 2, QTableWidgetItem(r[2] or ""))
            # Hiển thị giá với định dạng tiền tệ
            gia = r[3] or 0
            gia_item = QTableWidgetItem(f"{gia:,.0f}" if gia else "0")
            gia_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_drugs.setItem(row, 3, gia_item)
            self.table_drugs.setItem(row, 4, QTableWidgetItem(str(r[4] or 0)))
        
        # Cập nhật autocomplete
        self.update_drug_autocomplete()
        # Cập nhật tổng giá trị
        self.calculate_total_inventory_value()

    def load_import_drugs_history(self):
        """Tải lịch sử nhập thuốc từ bảng nhap_thuoc."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ngay, ma_thuoc, ten_thuoc, don_vi, so_luong_nhap FROM nhap_thuoc ORDER BY ngay DESC LIMIT 500")
            rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            conn.close()

        self.table_import_drugs.setRowCount(0)
        for r in rows:
            row = self.table_import_drugs.rowCount()
            self.table_import_drugs.insertRow(row)
            self.table_import_drugs.setItem(row, 0, QTableWidgetItem(r[0] or ""))
            self.table_import_drugs.setItem(row, 1, QTableWidgetItem(r[1] or ""))
            self.table_import_drugs.setItem(row, 2, QTableWidgetItem(r[2] or ""))
            self.table_import_drugs.setItem(row, 3, QTableWidgetItem(r[3] or ""))
            self.table_import_drugs.setItem(row, 4, QTableWidgetItem(str(r[4] or 0)))

    def on_add_drug(self):
        dlg = DrugDialog(parent=self)

        if dlg.exec_():
            ma, ten, don_vi, gia, ton_kho = dlg.values()
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO danh_muc_thuoc (ma_thuoc, ten_thuoc, don_vi, gia_thuoc, ton_kho) VALUES (?, ?, ?, ?, ?)",
                            (ma, ten, don_vi, gia, ton_kho))
                conn.commit()
                QMessageBox.information(self, "Thành công", "Đã thêm thuốc vào danh mục.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm thuốc: {e}")
            finally:
                conn.close()
            self.load_drugs()

    def on_add_drug_input(self):
        """Ghi nhận lịch sử nhập thuốc: lưu vào bảng nhap_thuoc và cập nhật ton_kho."""
        # If input area was removed from UI, do nothing
        if not hasattr(self, 'input_drug_code'):
            QMessageBox.information(self, "Thông báo", "Chức năng nhập thuốc tạm thời bị vô hiệu hoá.")
            return

        ma = self.input_drug_code.text().strip()
        ten = self.input_drug_name.text().strip()
        don_vi = self.input_drug_unit.text().strip()
        
        if not ma or not ten or not don_vi:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin (Mã, Tên, Đơn vị).")
            return
        
        try:
            gia = float(self.input_drug_price.text().strip() or 0)
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Giá phải là số.")
            return
        
        try:
            so_luong = int(self.input_drug_quantity.text().strip() or 0)
        except Exception:
            QMessageBox.warning(self, "Lỗi", "Số lượng phải là số.")
            return
        
        if so_luong <= 0:
            QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0.")
            return
        
        ngay = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Kiểm tra xem mã thuốc đã tồn tại hay chưa
            cur.execute("SELECT ton_kho FROM danh_muc_thuoc WHERE ma_thuoc = ?", (ma,))
            result = cur.fetchone()
            
            if result:
                # Nếu tồn tại, lấy tồn kho hiện tại
                ton_kho_hien_tai = result[0] or 0
            else:
                # Nếu không tồn tại, thêm vào danh mục
                cur.execute("INSERT INTO danh_muc_thuoc (ma_thuoc, ten_thuoc, don_vi, gia_thuoc, ton_kho) VALUES (?, ?, ?, ?, ?)",
                            (ma, ten, don_vi, gia, so_luong))
                ton_kho_hien_tai = 0
            
            # Lưu lịch sử nhập vào bảng nhap_thuoc
            cur.execute("INSERT INTO nhap_thuoc (ngay, ma_thuoc, ten_thuoc, don_vi, so_luong_nhap) VALUES (?, ?, ?, ?, ?)",
                        (ngay, ma, ten, don_vi, so_luong))
            
            # Cập nhật tồn kho và giá trong danh_muc_thuoc
            if result:  # Chỉ cập nhật nếu đã tồn tại
                ton_kho_moi = ton_kho_hien_tai + so_luong
                cur.execute("UPDATE danh_muc_thuoc SET ton_kho = ?, gia_thuoc = ? WHERE ma_thuoc = ?", 
                            (ton_kho_moi, gia, ma))
            
            conn.commit()
            QMessageBox.information(self, "Thành công", f"Đã ghi nhận nhập {so_luong} {don_vi} thuốc '{ten}' giá {gia:,.0f}.")
            
            # Xóa các trường input
            self.input_drug_code.clear()
            self.input_drug_name.clear()
            self.input_drug_unit.clear()
            self.input_drug_price.clear()
            self.input_drug_quantity.clear()
            
            # Reload dữ liệu
            self.load_drugs()
            self.load_import_drugs_history()
            

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận nhập: {e}")
        finally:
            conn.close()

    def on_edit_drug(self):
        sel = self.table_drugs.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn 1 thuốc để sửa.")
            return
        # Update total after loading
        # Cập nhật các tổng hiển thị (nếu cần)
        try:
            self.update_total()
        except Exception:
            # Fallback: nếu chưa có update_total, gọi calculate_total_inventory_value
            try:
                self.calculate_total_inventory_value()
            except Exception:
                pass
        it = self.table_drugs.item(sel, 0)
        ma = it.text() if it else ""
        it = self.table_drugs.item(sel, 1)
        ten = it.text() if it else ""
        it = self.table_drugs.item(sel, 2)
        don_vi = it.text() if it else ""
        # Giá nằm ở cột 3 (index 3), có thể hiển thị dạng có dấu phẩy
        try:
            it = self.table_drugs.item(sel, 3)
            gia_text = it.text().replace(",", "") if it else "0"
            gia = float(gia_text or 0)
        except Exception:
            gia = 0.0
        # Cột tồn kho là cột 4 (index 4)
        try:
            it = self.table_drugs.item(sel, 4)
            ton_kho = int(it.text() or 0) if it else 0
        except Exception:
            ton_kho = 0

        dlg = DrugDialog(parent=self, ma=ma, ten=ten, don_vi=don_vi, ton_kho=ton_kho, gia=gia, editing=True)
        if dlg.exec_():
            new_ma, new_ten, new_don_vi, new_gia, new_ton = dlg.values()
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE danh_muc_thuoc SET ma_thuoc=?, ten_thuoc=?, don_vi=?, gia_thuoc=?, ton_kho=? WHERE ma_thuoc=?",
                            (new_ma, new_ten, new_don_vi, new_gia, new_ton, ma))
                conn.commit()
                QMessageBox.information(self, "Thành công", "Đã cập nhật thuốc.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật thuốc: {e}")
            finally:
                conn.close()
            self.load_drugs()

    def on_delete_drug(self):
        sel = self.table_drugs.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn 1 thuốc để xóa.")
            return
        it = self.table_drugs.item(sel, 0)
        ma = it.text() if it else ""
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa thuốc {ma}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM danh_muc_thuoc WHERE ma_thuoc = ?", (ma,))
                conn.commit()
                QMessageBox.information(self, "Thành công", "Đã xóa thuốc.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa thuốc: {e}")
            finally:
                conn.close()
            self.load_drugs()

    def on_edit_import(self):
        """Sửa lịch sử nhập thuốc."""
        sel = self.table_import_drugs.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn 1 dòng để sửa.")
            return
        
        # Lấy dữ liệu từ bảng
        it = self.table_import_drugs.item(sel, 0)
        ngay = it.text() if it else ""
        it = self.table_import_drugs.item(sel, 1)
        ma = it.text() if it else ""
        it = self.table_import_drugs.item(sel, 2)
        ten = it.text() if it else ""
        it = self.table_import_drugs.item(sel, 3)
        don_vi = it.text() if it else ""
        try:
            it = self.table_import_drugs.item(sel, 4)
            so_luong_cu = int(it.text() or 0) if it else 0
        except Exception:
            so_luong_cu = 0
        
        # Tạo dialog để sửa
        dialog = QDialog(self)
        dialog.setWindowTitle("Sửa lịch sử nhập")
        layout = QFormLayout(dialog)
        
        edit_ma = QLineEdit(ma)
        edit_ten = QLineEdit(ten)
        edit_don_vi = QLineEdit(don_vi)
        edit_so_luong = QLineEdit(str(so_luong_cu))
        
        layout.addRow("Mã thuốc:", edit_ma)
        layout.addRow("Tên thuốc:", edit_ten)
        layout.addRow("Đơn vị:", edit_don_vi)
        layout.addRow("Số lượng:", edit_so_luong)
        
        btn_ok = QPushButton("Lưu")
        btn_cancel = QPushButton("Hủy")
        layout.addRow(btn_ok, btn_cancel)
        
        def on_save():
            try:
                so_luong_moi = int(edit_so_luong.text().strip() or 0)
            except Exception:
                QMessageBox.warning(dialog, "Lỗi", "Số lượng phải là số.")
                return
            
            if so_luong_moi <= 0:
                QMessageBox.warning(dialog, "Lỗi", "Số lượng phải lớn hơn 0.")
                return
            
            conn = get_connection()
            cur = conn.cursor()
            try:
                # Cập nhật lịch sử nhập
                cur.execute("UPDATE nhap_thuoc SET ma_thuoc = ?, ten_thuoc = ?, don_vi = ?, so_luong_nhap = ? WHERE ngay = ? AND ma_thuoc = ?",
                            (edit_ma.text().strip(), edit_ten.text().strip(), edit_don_vi.text().strip(), so_luong_moi, ngay, ma))
                
                # Cập nhật lại tồn kho nếu số lượng thay đổi
                if so_luong_moi != so_luong_cu:
                    so_luong_khac = so_luong_moi - so_luong_cu
                    cur.execute("UPDATE danh_muc_thuoc SET ton_kho = ton_kho + ? WHERE ma_thuoc = ?",
                                (so_luong_khac, edit_ma.text().strip()))
                
                conn.commit()
                QMessageBox.information(dialog, "Thành công", "Đã cập nhật lịch sử nhập.")
                dialog.accept()
                self.load_import_drugs_history()
                self.load_drugs()
            except Exception as e:
                QMessageBox.critical(dialog, "Lỗi", f"Không thể cập nhật: {e}")
            finally:
                conn.close()
        
        btn_ok.clicked.connect(on_save)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()

    def on_delete_import(self):
        """Xóa lịch sử nhập thuốc."""
        sel = self.table_import_drugs.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn 1 dòng để xóa.")
            return
        
        it = self.table_import_drugs.item(sel, 0)
        ngay = it.text() if it else ""
        it = self.table_import_drugs.item(sel, 1)
        ma = it.text() if it else ""
        it = self.table_import_drugs.item(sel, 2)
        ten = it.text() if it else ""
        try:
            it = self.table_import_drugs.item(sel, 4)
            so_luong = int(it.text() or 0) if it else 0
        except Exception:
            so_luong = 0
        
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa lịch sử nhập '{ten}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Xóa lịch sử nhập
            cur.execute("DELETE FROM nhap_thuoc WHERE ngay = ? AND ma_thuoc = ?", (ngay, ma))
            
            # Cập nhật lại tồn kho (trừ đi số lượng đã nhập)
            cur.execute("UPDATE danh_muc_thuoc SET ton_kho = ton_kho - ? WHERE ma_thuoc = ?", 
                        (so_luong, ma))
            
            conn.commit()
            QMessageBox.information(self, "Thành công", "Đã xóa lịch sử nhập.")
            self.load_import_drugs_history()
            self.load_drugs()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")
        finally:
            conn.close()

    # --- Tổng hợp doanh thu ---
    def load_summary(self):
        """Tải và hiển thị tổng hợp doanh thu theo ngày."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Build query optionally with date filter
            base_sql = """
                SELECT 
                    DATE(ngay) as ngay,
                    SUM(CASE WHEN loai = 'Dịch vụ' THEN so_tien ELSE 0 END) as doanh_thu_dv,
                    SUM(CASE WHEN loai = 'Thuốc' THEN so_tien ELSE 0 END) as doanh_thu_thuoc,
                    SUM(so_tien) as tong_tien
                FROM thanh_toan
            """
            params = []
            # If summary_date_from/summary_date_to controls exist, use them
            try:
                date_from = self.summary_date_from.date().toString("yyyy-MM-dd")
                date_to = self.summary_date_to.date().toString("yyyy-MM-dd")
                if date_from and date_to:
                    base_sql += " WHERE DATE(ngay) BETWEEN ? AND ?"
                    params.extend([date_from, date_to])
            except Exception:
                pass

            base_sql += " GROUP BY DATE(ngay) ORDER BY ngay DESC"
            cur.execute(base_sql, params)
            rows = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải tổng hợp: {e}")
            rows = []
        finally:
            conn.close()

        # Cập nhật bảng tổng hợp
        self.table_summary.setRowCount(0)
        total_all = 0
        for r in rows:
            ngay = r[0] or ""
            doanh_thu_dv = r[1] or 0
            doanh_thu_thuoc = r[2] or 0
            tong_tien = r[3] or 0
            
            total_all += tong_tien
            
            row = self.table_summary.rowCount()
            self.table_summary.insertRow(row)
            self.table_summary.setItem(row, 0, QTableWidgetItem(ngay))
            self.table_summary.setItem(row, 1, QTableWidgetItem(f"{doanh_thu_dv:,.0f}"))
            item_thuoc = QTableWidgetItem(f"{doanh_thu_thuoc:,.0f}")
            item_thuoc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_summary.setItem(row, 2, item_thuoc)
        
        # Cập nhật tổng tiền
        total_str = f"Tổng doanh thu: {total_all:,.0f} VNĐ"
        self.lbl_total.setText(total_str)
    
    def auto_refresh_summary(self):
        """Hàm được gọi bởi timer để tự động cập nhật tổng hợp."""
        self.load_summary()
    
    def on_data_updated(self):
        """Cập nhật ngay khi dữ liệu thay đổi (từ signal)."""
        print("📊 on_data_updated được gọi - đang tải lại dữ liệu...")
        try:
            self.load_summary()
            self.load_detail_services()
            self.calculate_total_inventory_value()
            print("✓ Dữ liệu đã được cập nhật")
        except Exception as e:
            print(f"✗ Lỗi khi cập nhật dữ liệu: {e}")

    # --- Summary filters / helpers ---
    def filter_summary_apply(self):
        try:
            self.load_summary()
        except Exception:
            pass

    def clear_summary_filters(self):
        try:
            self.summary_date_from.setDate(QDate.currentDate().addMonths(-7))
            self.summary_date_to.setDate(QDate.currentDate())
        except Exception:
            pass
        try:
            self.load_summary()
        except Exception:
            pass

    def export_summary_csv(self):
        # Export current table_summary contents to output/summary_export.csv
        try:
            import os, csv
            out_dir = os.path.join(os.getcwd(), 'output')
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            out_path = os.path.join(out_dir, 'summary_export.csv')
            with open(out_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # headers
                headers = [self.table_summary.horizontalHeaderItem(i).text() for i in range(self.table_summary.columnCount())]
                writer.writerow(headers)
                for r in range(self.table_summary.rowCount()):
                    row_vals = []
                    for c in range(self.table_summary.columnCount()):
                        it = self.table_summary.item(r, c)
                        row_vals.append(it.text() if it else '')
                    writer.writerow(row_vals)
            QMessageBox.information(self, 'Export', f'Đã xuất file: {out_path}')
        except Exception as e:
            QMessageBox.warning(self, 'Lỗi', f'Không thể xuất CSV: {e}')

    def _on_summary_row_double_click(self, row, col):
        try:
            item = self.table_summary.item(row, 0)
            if item:
                ngay = item.text()
                self.open_summary_day_detail(ngay)
        except Exception:
            pass

    def open_summary_day_detail(self, ngay):
        """Hiển thị các bản ghi thanh_toan cho ngày được chọn."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ngay, loai, mo_ta, so_tien FROM thanh_toan WHERE DATE(ngay) = ? ORDER BY ngay DESC", (ngay,))
            rows = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(self, 'Lỗi', f'Không tải được chi tiết ngày: {e}')
            rows = []
        finally:
            conn.close()

        dialog = QDialog(self)
        dialog.setWindowTitle(f'Chi tiết ngày {ngay}')
        dialog.setGeometry(150, 150, 700, 400)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        if rows:
            lines = []
            for r in rows:
                ngay_r, loai, mo_ta, so_tien = r
                lines.append(f"[{ngay_r}] {loai} — {mo_ta} — {so_tien:,.0f} VNĐ")
            text.setPlainText('\n'.join(lines))
        else:
            text.setPlainText('Không có bản ghi cho ngày này.')
        text.setReadOnly(True)
        layout.addWidget(text)
        btn_close = QPushButton('Đóng')
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        dialog.exec_()
    
    # --- Chi tiết dịch vụ và thuốc ---
    def load_detail_services(self):
        """Tải chi tiết dịch vụ và thuốc từ các bệnh nhân."""
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Lấy và gộp dữ liệu dịch vụ: nhóm theo ngày, bệnh nhân, tên dịch vụ
            cur.execute("""
                SELECT
                    DATE(pk.ngay_lap) as ngay,
                    bn.ho_ten,
                    'Dịch vụ' as loai,
                    cd.ten_dich_vu as noi_dung,
                    SUM(cd.so_luong) as so_luong,
                    SUM(cd.thanh_tien) as thanh_tien,
                    GROUP_CONCAT(cd.id) as ids
                FROM chi_dinh cd
                JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                GROUP BY DATE(pk.ngay_lap), bn.ho_ten, cd.ten_dich_vu
                ORDER BY DATE(pk.ngay_lap) DESC
            """)
            dich_vu_rows = cur.fetchall()

            # Kiểm tra xem bảng don_thuoc có cột xuat_thuoc không
            cur.execute("PRAGMA table_info('don_thuoc')")
            cols_info = cur.fetchall()
            cols = [c[1] for c in cols_info]
            has_xuat_thuoc = 'xuat_thuoc' in cols
            
            # Lấy và gộp dữ liệu thuốc: nhóm theo ngày, bệnh nhân, tổng danh sách thuốc và tổng tiền (tính từ danh_muc_thuoc.gia_thuoc * so_luong)
            # Chỉ lấy thuốc đã xuất nếu cột xuat_thuoc tồn tại
            where_clause = "WHERE dt.xuat_thuoc = 1" if has_xuat_thuoc else ""
            
            cur.execute(f"""
                SELECT
                    DATE(dt.ngay_ke) as ngay,
                    bn.ho_ten,
                    'Thuốc' as loai,
                    GROUP_CONCAT(cdt.ten_thuoc, ', ') as noi_dung,
                    SUM(COALESCE(cdt.so_luong,0)) as so_luong,
                    SUM(COALESCE(dmh.gia_thuoc * cdt.so_luong, 0)) as thanh_tien,
                    GROUP_CONCAT(dt.id) as ids
                FROM don_thuoc dt
                JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
                JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id
                LEFT JOIN chi_tiet_don_thuoc cdt ON dt.id = cdt.don_thuoc_id
                LEFT JOIN danh_muc_thuoc dmh ON cdt.ma_thuoc = dmh.ma_thuoc
                {where_clause}
                GROUP BY DATE(dt.ngay_ke), bn.ho_ten
                ORDER BY DATE(dt.ngay_ke) DESC
            """)
            thuoc_rows = cur.fetchall()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải chi tiết: {e}")
            dich_vu_rows = []
            thuoc_rows = []
        finally:
            conn.close()
        # Gộp tất cả vào 1 danh sách để hiển thị (dich_vu_rows và thuoc_rows đã là các hàng gộp)
        all_rows = []
        for r in dich_vu_rows:
            # r: (ngay, ho_ten, loai, noi_dung, so_luong, thanh_tien, ids)
            all_rows.append(r)
        for r in thuoc_rows:
            all_rows.append(r)

        # Sắp xếp theo ngày giảm dần
        all_rows.sort(key=lambda x: x[0] if x[0] else "", reverse=True)

        # Cập nhật bảng
        self.table_detail.setRowCount(0)
        for row in all_rows:
            ngay = row[0] or ""
            benh_nhan = row[1] or ""
            loai = row[2] or ""
            noi_dung = row[3] or ""
            so_luong = row[4] or 0
            thanh_tien = row[5] or 0
            ids = row[6] or ""

            row_pos = self.table_detail.rowCount()
            self.table_detail.insertRow(row_pos)

            self.table_detail.setItem(row_pos, 0, QTableWidgetItem(ngay))
            self.table_detail.setItem(row_pos, 1, QTableWidgetItem(benh_nhan))
            self.table_detail.setItem(row_pos, 2, QTableWidgetItem(loai))
            self.table_detail.setItem(row_pos, 3, QTableWidgetItem(noi_dung))
            qty_item = QTableWidgetItem(str(so_luong))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.table_detail.setItem(row_pos, 4, qty_item)
            total_item = QTableWidgetItem(f"{thanh_tien:,.0f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_detail.setItem(row_pos, 5, total_item)

            # Nút xem chi tiết — truyền ids (có thể là nhiều id, phân tách bởi dấu phẩy) và tổng tiền
            btn_detail = QPushButton("Xem chi tiết")
            btn_detail.setMaximumWidth(100)
            # Safely capture the handler now to avoid AttributeError during connect/runtime
            _show_fn = getattr(self, "show_detail_info", None)
            if not callable(_show_fn):
                def _show_fn(ids_str, lt, tt):
                    QMessageBox.warning(self, "Lỗi", "Hàm xem chi tiết chưa khả dụng.")
            btn_detail.clicked.connect(lambda checked, ids_str=ids, lt=loai, tt=thanh_tien, fn=_show_fn: fn(ids_str, lt, tt))
            self.table_detail.setCellWidget(row_pos, 6, btn_detail)
    
    def show_detail_info(self, ids_str, loai, total_amount=0):
        """Hiển thị chi tiết của dịch vụ hoặc thuốc trong dialog.
        ids_str: chuỗi id phân tách bởi dấu phẩy (GROUP_CONCAT từ SQL)
        loai: 'Dịch vụ' hoặc 'Thuốc'
        total_amount: tổng tiền đã được tính sẵn từ truy vấn gộp
        """
        conn = get_connection()
        cur = conn.cursor()

        try:
            ids = [i for i in (ids_str or "").split(',') if i.strip()]
            detail_lines = []

            if loai == "Dịch vụ":
                # Lấy các chi_dinh theo id
                if ids:
                    q = f"SELECT cd.so_chi_dinh, cd.ten_dich_vu, cd.so_luong, cd.don_gia, cd.thanh_tien, pk.so_phieu, bn.ho_ten, pk.ngay_lap, COALESCE(ctpk.chan_doan, '') FROM chi_dinh cd JOIN phieu_kham pk ON cd.phieu_kham_id = pk.id JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id LEFT JOIN chi_tiet_phieu_kham ctpk ON pk.id = ctpk.phieu_kham_id WHERE cd.id IN ({','.join(['?']*len(ids))}) ORDER BY pk.ngay_lap DESC"
                    cur.execute(q, ids)
                    rows = cur.fetchall()
                    for r in rows:
                        so_chi_dinh, ten_dv, so_luong, don_gia, thanh_tien, so_phieu, ho_ten, ngay, chan_doan = r
                        detail_lines.append(f"[SCD:{so_chi_dinh}] {ten_dv} — SL: {so_luong} — ĐG: {don_gia:,.0f} — TT: {thanh_tien:,.0f} (Phiếu: {so_phieu})")
            else:
                # Thuốc: lấy chi tiết trong chi_tiet_don_thuoc của các đơn thuốc có id trong ids
                if ids:
                    q = f"SELECT dt.id, dt.ngay_ke, bn.ho_ten, pk.so_phieu, cdt.ten_thuoc, cdt.so_luong, COALESCE(cdt.don_vi,'') FROM don_thuoc dt JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id JOIN benh_nhan bn ON pk.benh_nhan_id = bn.id LEFT JOIN chi_tiet_don_thuoc cdt ON dt.id = cdt.don_thuoc_id WHERE dt.id IN ({','.join(['?']*len(ids))}) ORDER BY dt.ngay_ke DESC"
                    cur.execute(q, ids)
                    rows = cur.fetchall()
                    # Nhóm theo đơn thuốc
                    grouped = {}
                    for r in rows:
                        don_id, ngay, ho_ten, so_phieu, ten_thuoc, so_luong, don_vi = r
                        grouped.setdefault(don_id, {'meta': (ngay, ho_ten, so_phieu), 'lines': []})
                        grouped[don_id]['lines'].append((ten_thuoc, so_luong, don_vi))

                    for did, info in grouped.items():
                        ngay, ho_ten, so_phieu = info['meta']
                        detail_lines.append(f"ĐƠN ID:{did} — Phiếu:{so_phieu} — Ngày:{ngay}")
                        for ln in info['lines']:
                            detail_lines.append(f"  - {ln[0]} — SL: {ln[1]} {ln[2]}")

            # Chuẩn bị nội dung hiển thị
            header = f"Chi tiết {loai}\nTổng tiền (gộp): {total_amount:,.0f} VNĐ\n\n"
            body = "\n".join(detail_lines) if detail_lines else "Không có chi tiết." 
            detail_text = header + body

            # Hiển thị trong dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Chi tiết {loai}")
            dialog.setGeometry(100, 100, 700, 500)

            layout = QVBoxLayout()

            text_edit = QTextEdit()
            text_edit.setPlainText(detail_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            btn_close = QPushButton("Đóng")
            btn_close.clicked.connect(dialog.close)
            layout.addWidget(btn_close)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải chi tiết: {e}")
        finally:
            conn.close()
    

    def update_drug_autocomplete(self):
        """Cập nhật danh sách autocomplete cho mã thuốc."""
        # If the input area was removed, skip setting completer
        if not hasattr(self, 'input_drug_code'):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ma_thuoc FROM danh_muc_thuoc ORDER BY ma_thuoc")
            drug_codes = [row[0] for row in cur.fetchall()]
        except Exception:
            drug_codes = []
        finally:
            conn.close()
        
        # Tạo completer cho input_drug_code
        if drug_codes:
            completer = QCompleter(drug_codes)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.input_drug_code.setCompleter(completer)

    def on_drug_code_selected(self, text):
        """Khi chọn/gõ mã thuốc, tự động điền thông tin từ danh mục."""
        # If the input area was removed, ignore
        if not hasattr(self, 'input_drug_code'):
            return

        if not text.strip():
            return
        
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ten_thuoc, don_vi, gia_thuoc FROM danh_muc_thuoc WHERE ma_thuoc = ?", (text.strip(),))
            result = cur.fetchone()
            if result:
                self.input_drug_name.setText(result[0] or "")
                self.input_drug_unit.setText(result[1] or "")
                self.input_drug_price.setText(str(result[2] or 0))
        except Exception:
            pass
        finally:
            conn.close()

    def filter_drugs_table(self, text):
        """Lọc bảng danh mục thuốc theo text tìm kiếm."""
        for row in range(self.table_drugs.rowCount()):
            it = self.table_drugs.item(row, 0)
            ma = it.text().lower() if it and it.text() else ""
            it = self.table_drugs.item(row, 1)
            ten = it.text().lower() if it and it.text() else ""
            search_text = text.lower()
            should_show = (search_text in ma) or (search_text in ten)
            self.table_drugs.setRowHidden(row, not should_show)

    def filter_import_drugs_table(self, text):
        """Lọc bảng lịch sử nhập theo text tìm kiếm."""
        for row in range(self.table_import_drugs.rowCount()):
            it = self.table_import_drugs.item(row, 1)
            ma = it.text().lower() if it and it.text() else ""
            it = self.table_import_drugs.item(row, 2)
            ten = it.text().lower() if it and it.text() else ""
            search_text = text.lower()
            should_show = (search_text in ma) or (search_text in ten)
            self.table_import_drugs.setRowHidden(row, not should_show)

    def filter_detail_table(self, text):
        """Lọc bảng chi tiết (tab Chi tiết dịch vụ/thuốc)."""
        search_text = text.lower()
        for row in range(self.table_detail.rowCount()):
            benh_nhan = self.table_detail.item(row, 1).text().lower() if self.table_detail.item(row, 1) else ""
            loai = self.table_detail.item(row, 2).text().lower() if self.table_detail.item(row, 2) else ""
            noi_dung = self.table_detail.item(row, 3).text().lower() if self.table_detail.item(row, 3) else ""
            total = self.table_detail.item(row, 5).text().lower() if self.table_detail.item(row, 5) else ""
            should_show = (search_text in benh_nhan) or (search_text in loai) or (search_text in noi_dung) or (search_text in total)
            self.table_detail.setRowHidden(row, not should_show)

    def filter_detail_apply(self, _=None):
        """Áp dụng bộ lọc tổng hợp: search text + loại + khoảng ngày."""
        search_text = (self.search_detail.text() or "").lower()
        sel_type = self.filter_type.currentText() if hasattr(self, 'filter_type') else "Tất cả"
        # parse dates
        try:
            date_from = self.filter_date_from.date().toString("yyyy-MM-dd")
            date_to = self.filter_date_to.date().toString("yyyy-MM-dd")
        except Exception:
            date_from = date_to = None

        for row in range(self.table_detail.rowCount()):
            # date in column 0
            date_text = self.table_detail.item(row, 0).text() if self.table_detail.item(row, 0) else ""
            try:
                in_range = True
                if date_from:
                    in_range = in_range and (date_text >= date_from)
                if date_to:
                    in_range = in_range and (date_text <= date_to)
            except Exception:
                in_range = True

            benh_nhan = self.table_detail.item(row, 1).text().lower() if self.table_detail.item(row, 1) else ""
            loai = self.table_detail.item(row, 2).text() if self.table_detail.item(row, 2) else ""
            noi_dung = self.table_detail.item(row, 3).text().lower() if self.table_detail.item(row, 3) else ""
            total = self.table_detail.item(row, 5).text().lower() if self.table_detail.item(row, 5) else ""

            # type filter
            type_match = (sel_type == "Tất cả") or (loai == sel_type)

            # search text
            search_match = (search_text in benh_nhan) or (search_text in loai.lower()) or (search_text in noi_dung) or (search_text in total)

            should_show = in_range and type_match and (search_match if search_text else True)
            self.table_detail.setRowHidden(row, not should_show)

    def clear_detail_filters(self):
        try:
            self.search_detail.clear()
        except Exception:
            pass
        try:
            self.filter_type.setCurrentIndex(0)
            self.filter_date_from.setDate(QDate.currentDate().addMonths(-1))
            self.filter_date_to.setDate(QDate.currentDate())
        except Exception:
            pass
        # show all rows
        for row in range(self.table_detail.rowCount()):
            self.table_detail.setRowHidden(row, False)

    def calculate_total_inventory_value(self):
        """Tính tổng giá trị tồn kho: SUM(giá × tồn kho)."""
        total_value = 0
        try:
            for row in range(self.table_drugs.rowCount()):
                # Lấy giá (cột 3) và tồn kho (cột 4)
                gia_item = self.table_drugs.item(row, 3)
                ton_item = self.table_drugs.item(row, 4)
                if gia_item and ton_item:
                    gia_text = gia_item.text().replace(",", "")
                    try:
                        gia = float(gia_text or 0)
                        ton = int(ton_item.text() or 0)
                        total_value += gia * ton
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Cập nhật label
        self.lbl_total_value.setText(f"Tổng giá trị tồn kho: {total_value:,.0f}")

    def update_total(self):
        """Compatibility shim: cập nhật các tổng hiển thị trên form.

        Trước đây code gọi `update_total()` — để tránh AttributeError, cung cấp method này
        và chuyển tiếp tới `calculate_total_inventory_value()`.
        """
        try:
            self.calculate_total_inventory_value()
        except Exception:
            pass


class DrugDialog(QDialog):
    def __init__(self, parent=None, ma="", ten="", don_vi="", ton_kho=0, gia=0.0, editing=False):
        super().__init__(parent)
        self.setWindowTitle("Sửa thuốc" if editing else "Thêm thuốc")
        self._editing = editing
        self._ma = ma
        self.init_ui(ma, ten, don_vi, ton_kho, gia)

    def init_ui(self, ma, ten, don_vi, ton_kho, gia):
        layout = QFormLayout(self)
        self.input_ma = QLineEdit(ma)
        self.input_ten = QLineEdit(ten)
        self.input_don_vi = QLineEdit(don_vi)
        self.input_gia = QLineEdit(str(gia))
        self.input_ton = QLineEdit(str(ton_kho))
        layout.addRow("Mã thuốc:", self.input_ma)
        layout.addRow("Tên thuốc:", self.input_ten)
        layout.addRow("Đơn vị:", self.input_don_vi)
        layout.addRow("Giá:", self.input_gia)
        layout.addRow("Tồn kho:", self.input_ton)

        btns = QHBoxLayout()
        ok = QPushButton("OK")
        cancel = QPushButton("Hủy")
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addRow(btns)

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
    
    def values(self):
        """Trả về tuple (ma, ten, don_vi, ton_kho) từ dialog.

        Gọi từ `on_add_drug` hoặc `on_edit_drug` để nhận giá trị người dùng nhập.
        """
        ma = self.input_ma.text().strip()
        ten = self.input_ten.text().strip()
        don_vi = self.input_don_vi.text().strip()
        try:
            gia = float(self.input_gia.text().strip().replace(',', '') or 0)
        except Exception:
            gia = 0.0
        try:
            ton = int(self.input_ton.text().strip() or 0)
        except Exception:
            ton = 0
        return ma, ten, don_vi, gia, ton

