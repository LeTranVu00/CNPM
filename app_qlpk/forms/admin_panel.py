import csv
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QTabWidget, QHeaderView, QMessageBox,
    QSplitter, QComboBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- Xử lý import database ---
# Đoạn này giúp tìm thấy database.py dù file này nằm ở root hay trong thư mục con
try:
    from database import get_connection, get_sessions_by_role
except ImportError:
    # Nếu không tìm thấy, thử thêm thư mục cha vào sys.path (trường hợp file này nằm trong folder forms/)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from database import get_connection, get_sessions_by_role
    except ImportError:
        print("❌ Lỗi: Không tìm thấy file database.py. Vui lòng đảm bảo file này tồn tại.")
        raise


class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Base font and style
        self.setFont(QFont("Arial", 10))
        self.setWindowTitle("Admin Panel")
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Admin Panel — Quản lý bệnh nhân & phiên làm việc")
        title.setStyleSheet("font-weight: bold; font-size: 15pt; color: #0b63a7;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 8px 16px; }")
        layout.addWidget(tabs)

        # ======================================================
        # TAB 1: BỆNH NHÂN
        # ======================================================
        self.patients_tab = QWidget()
        p_layout = QVBoxLayout(self.patients_tab)
        p_layout.setSpacing(6)

        # Search / actions row
        search_actions = QHBoxLayout()
        self.patient_search = QLineEdit()
        self.patient_search.setPlaceholderText("Tìm theo tên hoặc số điện thoại...")
        self.patient_search.setMinimumWidth(300)
        # Tìm khi nhấn Enter
        self.patient_search.returnPressed.connect(self.load_patients)

        self.btn_patient_search = QPushButton("Tìm")
        self.btn_patient_search.clicked.connect(self.load_patients)

        self.btn_patient_clear = QPushButton("Xóa")
        self.btn_patient_clear.clicked.connect(self.clear_patient_search)

        self.btn_export_patients = QPushButton("Xuất CSV")
        self.btn_export_patients.clicked.connect(self.export_patients_csv)

        self.lbl_patient_count = QLabel("")
        self.lbl_patient_count.setStyleSheet("color:#555; font-weight: bold;")

        search_actions.addWidget(self.patient_search)
        search_actions.addWidget(self.btn_patient_search)
        search_actions.addWidget(self.btn_patient_clear)
        search_actions.addStretch()
        search_actions.addWidget(self.lbl_patient_count)
        search_actions.addWidget(self.btn_export_patients)
        p_layout.addLayout(search_actions)

        # Splitter: left list, right details
        splitter = QSplitter(Qt.Horizontal)

        # Left: patient list
        self.table_patients = QTableWidget(0, 5)
        self.table_patients.setHorizontalHeaderLabels(["ID", "Họ tên", "Ngày sinh", "Điện thoại", "Địa chỉ"])
        self.table_patients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_patients.verticalHeader().setVisible(False)
        self.table_patients.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_patients.setEditTriggers(QTableWidget.NoEditTriggers)  # Không cho sửa trực tiếp trên bảng
        self.table_patients.setAlternatingRowColors(True)
        self.table_patients.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #e0e0e0;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #0b63a7;
                color: white;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }
        """)

        self.table_patients.cellClicked.connect(self.on_patient_selected)
        splitter.addWidget(self.table_patients)

        # Right: patient detail + visits
        right = QWidget()
        r_layout = QVBoxLayout(right)
        r_layout.setSpacing(6)
        r_layout.setContentsMargins(5, 0, 0, 0)

        self.detail_title = QLabel("Chi tiết hồ sơ bệnh án")
        self.detail_title.setStyleSheet("font-weight: bold; color: #0b63a7; font-size: 11pt;")
        r_layout.addWidget(self.detail_title)

        # Formatted detail label
        self.lbl_patient_detail = QLabel("<i>Chọn một bệnh nhân để xem chi tiết</i>")
        self.lbl_patient_detail.setWordWrap(True)
        self.lbl_patient_detail.setStyleSheet(
            "background: #f7f9fb; padding: 10px; border: 1px solid #e6eef8; border-radius: 4px;")
        r_layout.addWidget(self.lbl_patient_detail)

        # Visits table header
        visits_header_layout = QHBoxLayout()
        visits_header_layout.addWidget(QLabel("<b>Lịch sử khám:</b>"))
        visits_header_layout.addStretch()
        self.btn_export_visits = QPushButton("Xuất lượt khám")
        self.btn_export_visits.clicked.connect(self.export_visits_csv)
        self.btn_export_visits.setEnabled(False)  # Chỉ enable khi có dữ liệu
        visits_header_layout.addWidget(self.btn_export_visits)
        r_layout.addLayout(visits_header_layout)

        self.table_visits = QTableWidget(0, 4)
        self.table_visits.setHorizontalHeaderLabels(["Mã HS", "Ngày", "Phòng khám", "Bác sĩ"])
        self.table_visits.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_visits.verticalHeader().setVisible(False)
        self.table_visits.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_visits.setAlternatingRowColors(True)
        r_layout.addWidget(self.table_visits)

        splitter.addWidget(right)
        splitter.setSizes([600, 400])  # Tỉ lệ chia khung hình
        p_layout.addWidget(splitter)

        tabs.addTab(self.patients_tab, "Quản lý Bệnh nhân")

        # ======================================================
        # TAB 2: PHIÊN LÀM VIỆC (SESSIONS)
        # ======================================================
        self.sessions_tab = QWidget()
        s_layout = QVBoxLayout(self.sessions_tab)
        s_layout.setSpacing(8)

        role_layout = QHBoxLayout()
        self.role_combo = QComboBox()
        self.role_combo.setEditable(False)
        self.role_combo.addItem("-- Tất cả Role --")  # Sửa lại logic load một chút cho tiện

        # populate roles from users table
        self.populate_roles()

        self.btn_load_sessions = QPushButton("Tải dữ liệu")
        self.btn_load_sessions.clicked.connect(self.load_sessions_by_role)
        self.btn_load_sessions.setStyleSheet("background-color: #0b63a7; color: white; font-weight: bold;")

        self.btn_refresh_roles = QPushButton("🔄")
        self.btn_refresh_roles.setToolTip("Tải lại danh sách Role")
        self.btn_refresh_roles.clicked.connect(self.populate_roles)

        self.btn_export_sessions = QPushButton("Xuất Excel/CSV")
        self.btn_export_sessions.clicked.connect(self.export_sessions_csv)

        role_layout.addWidget(QLabel("Lọc theo Role:"))
        role_layout.addWidget(self.role_combo)
        role_layout.addWidget(self.btn_refresh_roles)
        role_layout.addWidget(self.btn_load_sessions)
        role_layout.addStretch()
        role_layout.addWidget(self.btn_export_sessions)
        s_layout.addLayout(role_layout)

        self.table_sessions = QTableWidget(0, 3)
        self.table_sessions.setHorizontalHeaderLabels(
            ["Tài khoản (Username)", "Thời gian đăng nhập", "Thời gian đăng xuất"])
        self.table_sessions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sessions.verticalHeader().setVisible(False)
        self.table_sessions.setAlternatingRowColors(True)
        self.table_sessions.setEditTriggers(QTableWidget.NoEditTriggers)
        s_layout.addWidget(self.table_sessions)

        tabs.addTab(self.sessions_tab, "Lịch sử Đăng nhập")

        # Load initial patient list
        self.load_patients()

    # ==========================================================
    # LOGIC XỬ LÝ - BỆNH NHÂN
    # ==========================================================
    def clear_patient_search(self):
        self.patient_search.clear()
        self.load_patients()

    def load_patients(self):
        query = self.patient_search.text().strip()
        conn = get_connection()
        cur = conn.cursor()
        try:
            if query:
                q = f"%{query}%"
                # Tìm theo tên, sđt hoặc mã hồ sơ (nếu có join) - ở đây tìm bảng benh_nhan
                cur.execute("""
                    SELECT id, ho_ten, ngay_sinh, dien_thoai, dia_chi 
                    FROM benh_nhan 
                    WHERE ho_ten LIKE ? OR dien_thoai LIKE ? 
                    ORDER BY id DESC
                """, (q, q))
            else:
                cur.execute(
                    "SELECT id, ho_ten, ngay_sinh, dien_thoai, dia_chi FROM benh_nhan ORDER BY id DESC LIMIT 100")
            rows = cur.fetchall()
        finally:
            conn.close()

        self.table_patients.setRowCount(0)
        for r in rows:
            row = self.table_patients.rowCount()
            self.table_patients.insertRow(row)
            for c, v in enumerate(r):
                item = QTableWidgetItem(str(v) if v is not None else "")
                self.table_patients.setItem(row, c, item)

        self.lbl_patient_count.setText(f"Hiển thị: {len(rows)} kết quả")

    def on_patient_selected(self, row, col):
        try:
            item = self.table_patients.item(row, 0)
            if not item:
                return
            pid = int(item.text())
            conn = get_connection()
            cur = conn.cursor()
            try:
                # Load chi tiết
                cur.execute(
                    "SELECT ho_ten, ngay_sinh, dien_thoai, dia_chi, gioi_tinh, doi_tuong FROM benh_nhan WHERE id = ?",
                    (pid,))
                r = cur.fetchone()
                if r:
                    ho_ten, ns, dt, dc, gt, doituong = r
                    detail = (
                        f"<h3 style='color:#0b63a7; margin-bottom:5px;'>{ho_ten}</h3>"
                        f"<b>Mã ID:</b> {pid} &nbsp;|&nbsp; <b>Giới tính:</b> {gt}<br>"
                        f"<b>Ngày sinh:</b> {ns}<br>"
                        f"<b>Điện thoại:</b> {dt}<br>"
                        f"<b>Địa chỉ:</b> {dc}<br>"
                        f"<b>Đối tượng:</b> {doituong}"
                    )
                    self.lbl_patient_detail.setText(detail)
                else:
                    self.lbl_patient_detail.setText("Không tìm thấy thông tin bệnh nhân")

                # Load lịch sử khám (Visits)
                cur.execute("""
                    SELECT ma_hoso, ngay_tiep_don, phong_kham, bac_si_kham 
                    FROM tiep_don 
                    WHERE benh_nhan_id = ? 
                    ORDER BY ngay_tiep_don DESC
                """, (pid,))
                visits = cur.fetchall()
            finally:
                conn.close()

            self.table_visits.setRowCount(0)
            for vr in visits:
                r2 = self.table_visits.rowCount()
                self.table_visits.insertRow(r2)
                for c2, v2 in enumerate(vr):
                    val = str(v2) if v2 is not None else ""
                    # Format ngày tháng cho đẹp nếu cần
                    if c2 == 1 and val:
                        try:
                            val = val.split(" ")[0]
                        except:
                            pass
                    self.table_visits.setItem(r2, c2, QTableWidgetItem(val))

            # Enable nút xuất lịch sử khám nếu có dữ liệu
            self.btn_export_visits.setEnabled(self.table_visits.rowCount() > 0)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin bệnh nhân:\n{e}")

    def export_csv_general(self, table, default_name):
        """Hàm dùng chung để xuất CSV từ QTableWidget"""
        try:
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)

            path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file CSV",
                os.path.join(output_dir, default_name),
                "CSV Files (*.csv)"
            )
            if not path:
                return

            rows_data = []
            headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]

            for r in range(table.rowCount()):
                row_data = []
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    row_data.append(item.text() if item else "")
                rows_data.append(row_data)

            with open(path, "w", newline='', encoding='utf-8-sig') as f:  # utf-8-sig để Excel mở không bị lỗi font
                w = csv.writer(f)
                w.writerow(headers)
                w.writerows(rows_data)

            QMessageBox.information(self, "Hoàn tất", f"Đã xuất file thành công:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file:\n{e}")

    def export_patients_csv(self):
        self.export_csv_general(self.table_patients, "danh_sach_benh_nhan.csv")

    def export_visits_csv(self):
        self.export_csv_general(self.table_visits, "lich_su_kham.csv")

    # ==========================================================
    # LOGIC XỬ LÝ - SESSIONS
    # ==========================================================
    def populate_roles(self):
        """Lấy danh sách Role từ DB"""
        try:
            current_text = self.role_combo.currentText()
            self.role_combo.clear()

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT role FROM users")
            roles = [r[0] for r in cur.fetchall() if r[0]]
            conn.close()

            if roles:
                self.role_combo.addItems(roles)
            else:
                self.role_combo.addItem("admin")  # Fallback nếu chưa có user

            # Giữ lại lựa chọn cũ nếu có
            index = self.role_combo.findText(current_text)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)

        except Exception as e:
            print("Lỗi load roles:", e)

    def load_sessions_by_role(self):
        role = self.role_combo.currentText()

        try:
            rows = get_sessions_by_role(role)

            if not rows:
                QMessageBox.information(self, "Thông báo", f"Không có dữ liệu phiên làm việc cho role: {role}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải phiên:\n{e}")
            return

        self.table_sessions.setRowCount(0)
        for r in rows:
            row = self.table_sessions.rowCount()
            self.table_sessions.insertRow(row)
            for c, v in enumerate(r):
                self.table_sessions.setItem(row, c, QTableWidgetItem(str(v) if v is not None else ""))

    def export_sessions_csv(self):
        self.export_csv_general(self.table_sessions, "lich_su_dang_nhap.csv")


# --- Block này giúp bạn chạy thử file này độc lập để kiểm tra ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Đảm bảo database đã được khởi tạo
    if os.path.exists("database.py"):
        try:
            from database import initialize_database

            initialize_database()
        except Exception as e:
            print("Cảnh báo khởi tạo DB:", e)

    window = AdminPanel()
    window.show()
    sys.exit(app.exec_())