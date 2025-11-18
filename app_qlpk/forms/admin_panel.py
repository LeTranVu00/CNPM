from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QTabWidget, QHeaderView, QMessageBox, QSplitter, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import get_connection, get_sessions_by_role
import csv, os


class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Base font and style
        self.setFont(QFont("Arial", 10))
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Admin Panel — Quản lý bệnh nhân & phiên làm việc")
        title.setStyleSheet("font-weight: bold; font-size: 15pt; color: #0b63a7;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 8px 16px; }")
        layout.addWidget(tabs)

        # ---------------- Patients tab ----------------
        self.patients_tab = QWidget()
        p_layout = QVBoxLayout(self.patients_tab)
        p_layout.setSpacing(6)

        # Search / actions row
        search_actions = QHBoxLayout()
        self.patient_search = QLineEdit()
        self.patient_search.setPlaceholderText("Tìm theo tên hoặc số điện thoại...")
        self.patient_search.setMinimumWidth(300)
        self.btn_patient_search = QPushButton("Tìm")
        self.btn_patient_search.clicked.connect(self.load_patients)
        self.btn_patient_clear = QPushButton("Xóa")
        self.btn_patient_clear.clicked.connect(self.clear_patient_search)
        self.btn_export_patients = QPushButton("Xuất CSV")
        self.btn_export_patients.clicked.connect(self.export_patients_csv)
        self.lbl_patient_count = QLabel("")
        self.lbl_patient_count.setStyleSheet("color:#555")

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
        self.table_patients.setAlternatingRowColors(True)
        self.table_patients.setStyleSheet(
            "QTableWidget { border: 1px solid #ddd; }"
            "QHeaderView::section { background: #0b63a7; color: white; padding: 6px; }"
            "QTableWidget::item:selected { background: #cfe8ff; }"
        )
        self.table_patients.cellClicked.connect(self.on_patient_selected)
        splitter.addWidget(self.table_patients)

        # Right: patient detail + visits
        right = QWidget()
        r_layout = QVBoxLayout(right)
        r_layout.setSpacing(6)

        self.detail_title = QLabel("Chi tiết bệnh nhân")
        self.detail_title.setStyleSheet("font-weight: bold; color: #0b63a7;")
        r_layout.addWidget(self.detail_title)

        # Formatted detail label
        self.lbl_patient_detail = QLabel("Chọn một bệnh nhân để xem chi tiết")
        self.lbl_patient_detail.setWordWrap(True)
        self.lbl_patient_detail.setStyleSheet("background: #f7f9fb; padding: 8px; border: 1px solid #e6eef8;")
        r_layout.addWidget(self.lbl_patient_detail)

        # Visits table
        visits_actions = QHBoxLayout()
        visits_actions.addStretch()
        self.btn_export_visits = QPushButton("Xuất lượt khám CSV")
        self.btn_export_visits.clicked.connect(self.export_visits_csv)
        visits_actions.addWidget(self.btn_export_visits)
        r_layout.addLayout(visits_actions)

        self.table_visits = QTableWidget(0, 4)
        self.table_visits.setHorizontalHeaderLabels(["Số hồ sơ", "Ngày", "Phòng khám", "Bác sĩ"])
        self.table_visits.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_visits.verticalHeader().setVisible(False)
        self.table_visits.setAlternatingRowColors(True)
        r_layout.addWidget(self.table_visits)

        splitter.addWidget(right)
        splitter.setSizes([500, 420])
        p_layout.addWidget(splitter)

        tabs.addTab(self.patients_tab, "Bệnh nhân")

        # ---------------- Sessions tab ----------------
        self.sessions_tab = QWidget()
        s_layout = QVBoxLayout(self.sessions_tab)
        s_layout.setSpacing(8)

        role_layout = QHBoxLayout()
        self.role_combo = QComboBox()
        self.role_combo.setEditable(False)
        self.role_combo.addItem("-- Chọn role --")
        # populate roles from users table
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT role FROM users")
            roles = [r[0] for r in cur.fetchall() if r[0]]
            conn.close()
            for r in roles:
                self.role_combo.addItem(r)
        except Exception:
            pass

        self.btn_load_sessions = QPushButton("Tải phiên")
        self.btn_load_sessions.clicked.connect(self.load_sessions_by_role)
        self.btn_refresh_roles = QPushButton("Tải lại role")
        self.btn_refresh_roles.clicked.connect(self.reload_roles)
        self.btn_export_sessions = QPushButton("Xuất CSV")
        self.btn_export_sessions.clicked.connect(self.export_sessions_csv)

        role_layout.addWidget(QLabel("Role:"))
        role_layout.addWidget(self.role_combo)
        role_layout.addWidget(self.btn_load_sessions)
        role_layout.addWidget(self.btn_refresh_roles)
        role_layout.addStretch()
        role_layout.addWidget(self.btn_export_sessions)
        s_layout.addLayout(role_layout)

        self.table_sessions = QTableWidget(0, 3)
        self.table_sessions.setHorizontalHeaderLabels(["Tài khoản", "Thời gian đăng nhập", "Thời gian đăng xuất"])
        self.table_sessions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sessions.verticalHeader().setVisible(False)
        self.table_sessions.setAlternatingRowColors(True)
        s_layout.addWidget(self.table_sessions)

        tabs.addTab(self.sessions_tab, "Phiên làm việc")

        # Load initial patient list
        self.load_patients()

    # ---------- Patients helpers ----------
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
                cur.execute("SELECT id, ho_ten, ngay_sinh, dien_thoai, dia_chi FROM benh_nhan WHERE ho_ten LIKE ? OR dien_thoai LIKE ? ORDER BY ho_ten", (q, q))
            else:
                cur.execute("SELECT id, ho_ten, ngay_sinh, dien_thoai, dia_chi FROM benh_nhan ORDER BY ho_ten")
            rows = cur.fetchall()
        finally:
            conn.close()

        self.table_patients.setRowCount(0)
        for r in rows:
            row = self.table_patients.rowCount()
            self.table_patients.insertRow(row)
            for c, v in enumerate(r):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_patients.setItem(row, c, item)
        self.lbl_patient_count.setText(f"Tổng: {len(rows)} bệnh nhân")

    def on_patient_selected(self, row, col):
        try:
            item = self.table_patients.item(row, 0)
            if not item:
                return
            pid = int(item.text())
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT ho_ten, ngay_sinh, dien_thoai, dia_chi FROM benh_nhan WHERE id = ?", (pid,))
                r = cur.fetchone()
                if r:
                    ho_ten, ns, dt, dc = r
                    detail = (
                        f"<b>ID:</b> {pid}<br>"
                        f"<b>Họ tên:</b> {ho_ten}<br>"
                        f"<b>Ngày sinh:</b> {ns}<br>"
                        f"<b>Điện thoại:</b> {dt}<br>"
                        f"<b>Địa chỉ:</b> {dc}"
                    )
                    self.lbl_patient_detail.setText(detail)
                else:
                    self.lbl_patient_detail.setText("Không tìm thấy thông tin bệnh nhân")

                # Load visits
                cur.execute("SELECT ma_hoso, ngay_tiep_don, phong_kham, bac_si_kham FROM tiep_don WHERE benh_nhan_id = ? ORDER BY ngay_tiep_don DESC", (pid,))
                visits = cur.fetchall()
            finally:
                conn.close()

            self.table_visits.setRowCount(0)
            for vr in visits:
                r2 = self.table_visits.rowCount()
                self.table_visits.insertRow(r2)
                for c2, v2 in enumerate(vr):
                    it = QTableWidgetItem(str(v2) if v2 is not None else "")
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    self.table_visits.setItem(r2, c2, it)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin bệnh nhân:\n{e}")

    def export_patients_csv(self):
        # Ask file path
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV bệnh nhân", os.path.join(os.getcwd(), "output", "patients.csv"), "CSV Files (*.csv)")
            if not path:
                return
            rows = []
            for r in range(self.table_patients.rowCount()):
                rows.append([self.table_patients.item(r, c).text() if self.table_patients.item(r, c) else "" for c in range(self.table_patients.columnCount())])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow([self.table_patients.horizontalHeaderItem(c).text() for c in range(self.table_patients.columnCount())])
                w.writerows(rows)
            QMessageBox.information(self, "Hoàn tất", f"Đã xuất {len(rows)} bệnh nhân ra {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất CSV:\n{e}")

    def export_visits_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV lượt khám", os.path.join(os.getcwd(), "output", "visits.csv"), "CSV Files (*.csv)")
            if not path:
                return
            rows = []
            for r in range(self.table_visits.rowCount()):
                rows.append([self.table_visits.item(r, c).text() if self.table_visits.item(r, c) else "" for c in range(self.table_visits.columnCount())])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow([self.table_visits.horizontalHeaderItem(c).text() for c in range(self.table_visits.columnCount())])
                w.writerows(rows)
            QMessageBox.information(self, "Hoàn tất", f"Đã xuất {len(rows)} lượt khám ra {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất CSV:\n{e}")

    # ---------- Sessions helpers ----------
    def reload_roles(self):
        try:
            self.role_combo.clear()
            self.role_combo.addItem("-- Chọn role --")
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT role FROM users")
            roles = [r[0] for r in cur.fetchall() if r[0]]
            conn.close()
            for r in roles:
                self.role_combo.addItem(r)
        except Exception:
            pass

    def load_sessions_by_role(self):
        role = self.role_combo.currentText()
        if not role or role == "-- Chọn role --":
            QMessageBox.information(self, "Chọn role", "Vui lòng chọn role (ví dụ: tieptan, bac_si, admin)")
            return
        try:
            rows = get_sessions_by_role(role)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải phiên:\n{e}")
            return

        self.table_sessions.setRowCount(0)
        for r in rows:
            row = self.table_sessions.rowCount()
            self.table_sessions.insertRow(row)
            for c, v in enumerate(r):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_sessions.setItem(row, c, item)

    def export_sessions_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV phiên", os.path.join(os.getcwd(), "output", "sessions.csv"), "CSV Files (*.csv)")
            if not path:
                return
            rows = []
            for r in range(self.table_sessions.rowCount()):
                rows.append([self.table_sessions.item(r, c).text() if self.table_sessions.item(r, c) else "" for c in range(self.table_sessions.columnCount())])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow([self.table_sessions.horizontalHeaderItem(c).text() for c in range(self.table_sessions.columnCount())])
                w.writerows(rows)
            QMessageBox.information(self, "Hoàn tất", f"Đã xuất {len(rows)} phiên ra {path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất CSV:\n{e}")

