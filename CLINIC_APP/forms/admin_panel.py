from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QTabWidget, QHeaderView, QMessageBox, QSplitter, QComboBox, QFileDialog, QDateTimeEdit
)
from forms.dat_lich_kham_form import DatLichKhamForm
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database import get_connection, get_sessions_by_role
import csv, os


class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.last_appointment_count = 0
        self.setFont(QFont("Arial", 10))
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Đặt lịch khám — Quản lý lịch hẹn & phiên làm việc")
        title.setStyleSheet("font-weight: bold; font-size: 15pt; color: #0b63a7;")
        layout.addWidget(title)

        # ---------------- Appointment tab ----------------
        self.appointment_tab = QWidget()
        a_layout = QVBoxLayout(self.appointment_tab)
        a_layout.setSpacing(6)

        self.table_appointments = QTableWidget(0, 7)
        self.table_appointments.setHorizontalHeaderLabels([
            "ID", "Họ tên", "Ngày & Giờ", "Bác sĩ", "Phòng khám", "Ghi chú", "Trạng thái"
        ])
        self.table_appointments.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_appointments.verticalHeader().setVisible(False)
        self.table_appointments.setAlternatingRowColors(True)
        self.table_appointments.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_appointments.setStyleSheet(
            "QTableWidget { border: 1px solid #ddd; font-size: 14px; }"
            "QHeaderView::section { background-color: #1976d2; color: white; font-weight: bold; border: none; }"
            "QTableWidget::item:selected { background-color: #1976d2; color: white; }"
        )
        a_layout.addWidget(self.table_appointments)

        self.btn_reload_appointments = QPushButton("Tải lại lịch hẹn")
        self.btn_reload_appointments.clicked.connect(self.load_appointments)
        a_layout.addWidget(self.btn_reload_appointments)

        # Thêm QLabel để hiển thị hướng dẫn cho QDateTimeEdit
        self.lbl_filter_date = QLabel("Chọn ngày giờ để lọc lịch hẹn:")
        self.filter_date_from = QDateTimeEdit()
        self.filter_date_from.setCalendarPopup(True)
        self.filter_date_from.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.filter_date_to = QDateTimeEdit()
        self.filter_date_to.setCalendarPopup(True)
        self.filter_date_to.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.btn_filter_appointments = QPushButton("Lọc lịch hẹn")
        self.btn_filter_appointments.clicked.connect(self.filter_appointments)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.lbl_filter_date)
        filter_layout.addWidget(self.filter_date_from)
        filter_layout.addWidget(self.filter_date_to)
        filter_layout.addWidget(self.btn_filter_appointments)
        self.appointment_tab.layout().addLayout(filter_layout)

        # Khởi tạo tabs sau tiêu đề
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 8px 16px; }")
        layout.addWidget(tabs)

        # Thêm các tab vào tabs (sau khi tabs đã được khởi tạo)
        tabs.addTab(self.appointment_tab, "Lịch hẹn đã đặt")
        self.dat_lich_kham_form = DatLichKhamForm()
        tabs.addTab(self.dat_lich_kham_form, "Tạo lịch hẹn")

        # Tab Quản lý bệnh nhân
        self.patients_tab = QWidget()
        p_layout = QVBoxLayout(self.patients_tab)
        p_layout.setSpacing(6)

        # Thêm nút vào tab Quản lý bệnh nhân
        self.btn_add_patient = QPushButton("Thêm bệnh nhân")
        self.btn_edit_patient = QPushButton("Sửa thông tin")
        self.btn_delete_patient = QPushButton("Xóa bệnh nhân")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_add_patient)
        button_layout.addWidget(self.btn_edit_patient)
        button_layout.addWidget(self.btn_delete_patient)
        p_layout.addLayout(button_layout)

        self.table_patients = QTableWidget(0, 5)
        self.table_patients.setHorizontalHeaderLabels(["STT", "Họ tên", "Ngày sinh", "Điện thoại", "Địa chỉ"])
        self.table_patients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_patients.verticalHeader().setVisible(False)
        self.table_patients.setAlternatingRowColors(True)
        p_layout.addWidget(self.table_patients)
        self.patients_tab.setLayout(p_layout)
        tabs.addTab(self.patients_tab, "Quản lý bệnh nhân")

        # Tab Phiên làm việc của nhân viên
        self.sessions_tab = QWidget()
        s_layout = QVBoxLayout(self.sessions_tab)
        s_layout.setSpacing(6)

        # Thêm nút vào tab Phiên làm việc của nhân viên
        self.btn_refresh_sessions = QPushButton("Làm mới")
        self.btn_export_sessions = QPushButton("Xuất báo cáo")
        button_layout_sessions = QHBoxLayout()
        button_layout_sessions.addWidget(self.btn_refresh_sessions)
        button_layout_sessions.addWidget(self.btn_export_sessions)
        s_layout.addLayout(button_layout_sessions)

        self.table_sessions = QTableWidget(0, 3)
        self.table_sessions.setHorizontalHeaderLabels(["Tài khoản", "Thời gian đăng nhập", "Thời gian đăng xuất"])
        self.table_sessions.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sessions.verticalHeader().setVisible(False)
        self.table_sessions.setAlternatingRowColors(True)
        s_layout.addWidget(self.table_sessions)
        self.sessions_tab.setLayout(s_layout)
        tabs.addTab(self.sessions_tab, "Phiên làm việc của nhân viên")

        # Tự động reload khi chuyển sang tab 'Lịch hẹn đã đặt'
        tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, idx):
        tab_text = self.sender().tabText(idx)
        if tab_text == "Lịch hẹn đã đặt":
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM lich_hen")
                count = cur.fetchone()[0]
            except Exception:
                count = 0
            finally:
                conn.close()
            if count != self.last_appointment_count:
                self.load_appointments()
                self.last_appointment_count = count

    def init_ui(self):
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

        # Hàng tìm kiếm / các hành động
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

        # Splitter: danh sách bên trái, chi tiết bên phải
        splitter = QSplitter(Qt.Horizontal)

        # Bên trái: danh sách bệnh nhân
        self.table_patients = QTableWidget(0, 5)
        self.table_patients.setHorizontalHeaderLabels(["ID", "Họ tên", "Ngày sinh", "Điện thoại", "Địa chỉ"])
        self.table_patients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_patients.verticalHeader().setVisible(False)
        self.table_patients.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_patients.setAlternatingRowColors(True)
        self.table_patients.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #e0e0e0;
                font-size: 14px;
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

        # Bên phải: chi tiết bệnh nhân + lượt khám
        right = QWidget()
        r_layout = QVBoxLayout(right)
        r_layout.setSpacing(6)

        self.detail_title = QLabel("Chi tiết bệnh nhân")
        self.detail_title.setStyleSheet("font-weight: bold; color: #0b63a7;")
        r_layout.addWidget(self.detail_title)

        # Nhãn chi tiết đã định dạng
        self.lbl_patient_detail = QLabel("Chọn một bệnh nhân để xem chi tiết")
        self.lbl_patient_detail.setWordWrap(True)
        self.lbl_patient_detail.setStyleSheet("background: #f7f9fb; padding: 8px; border: 1px solid #e6eef8;")
        r_layout.addWidget(self.lbl_patient_detail)

        # Bảng lượt khám
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
        # Tải các role từ bảng users
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

        # Tải danh sách bệnh nhân ban đầu
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
        for idx, r in enumerate(rows, 1):
            row = self.table_patients.rowCount()
            self.table_patients.insertRow(row)
            # Cột 0: STT (số thứ tự)
            stt_item = QTableWidgetItem(str(idx))
            stt_item.setData(Qt.UserRole, r[0])  # Store ID invisibly
            stt_item.setFlags(stt_item.flags() ^ Qt.ItemIsEditable)
            self.table_patients.setItem(row, 0, stt_item)
            # Các cột 1-4: họ tên, ngày sinh, điện thoại, địa chỉ
            for c, v in enumerate(r[1:], 1):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_patients.setItem(row, c, item)
        self.lbl_patient_count.setText(f"Tổng: {len(rows)} bệnh nhân")

    def on_patient_selected(self, row, col):
        try:
            item = self.table_patients.item(row, 0)
            if not item:
                return
            pid = item.data(Qt.UserRole)
            conn = get_connection()
            cur = conn.cursor()
            try:
                # Tải thông tin cơ bản bệnh nhân
                cur.execute("SELECT ho_ten, ngay_sinh, dien_thoai, dia_chi, so_cccd FROM benh_nhan WHERE id = ?", (pid,))
                r = cur.fetchone()
                if r:
                    ho_ten, ns, dt, dc, cccd = r
                    # Chuẩn bị phần tiêu đề chi tiết (thông tin cơ bản)
                    header_html = (
                        f"<b>ID:</b> {pid}<br>"
                        f"<b>Họ tên:</b> {ho_ten}<br>"
                        f"<b>Ngày sinh:</b> {ns or '—'}<br>"
                        f"<b>Điện thoại:</b> {dt or '—'}<br>"
                        f"<b>Địa chỉ:</b> {dc or '—'}<br>"
                        f"<b>CCCD:</b> {cccd or '—'}"
                    )
                else:
                    self.lbl_patient_detail.setText("Không tìm thấy thông tin bệnh nhân")
                    visits = []

                # Tải các lần khám (phieu_kham) và chi tiết liên quan (chi_tiet_phieu_kham, don_thuoc)
                cur.execute("SELECT id, so_phieu, ngay_lap, bac_si, phong_kham FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY datetime(ngay_lap) DESC", (pid,))
                pk_rows = cur.fetchall()
                visits = []
                for pk in pk_rows:
                    pkid, so_phieu, ngay_lap, bac_si, phong_kham = pk
                    # Chi tiết mới nhất cho lần khám này
                    cur.execute("SELECT chan_doan, ket_luan, icd10, di_ung_thuoc, ghi_chu_kham FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (pkid,))
                    detail_row = cur.fetchone() or ('', '', '', '', '')
                    chan_doan, ket_luan, icd10, di_ung_thuoc, ghi_chu_kham = detail_row

                    # Đơn thuốc
                    cur.execute("SELECT id, ngay_ke, so_ngay, ngay_tai_kham, chan_doan, loi_dan FROM don_thuoc WHERE phieu_kham_id = ? ORDER BY ngay_ke DESC", (pkid,))
                    pres_list = []
                    for p in cur.fetchall():
                        don_id, ngay_ke, so_ngay, ngay_tai_kham, don_chan_doan, loi_dan = p
                        cur.execute("SELECT ten_thuoc, so_luong, sang, trua, chieu, toi, lieu_dung, ghi_chu FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (don_id,))
                        meds = cur.fetchall()
                        pres_list.append({
                            'id': don_id,
                            'ngay_ke': ngay_ke,
                            'so_ngay': so_ngay,
                            'ngay_tai_kham': ngay_tai_kham,
                            'chan_doan': don_chan_doan,
                            'loi_dan': loi_dan,
                            'meds': meds,
                        })

                    visits.append({
                        'id': pkid,
                        'so_phieu': so_phieu,
                        'ngay_lap': ngay_lap,
                        'bac_si': bac_si,
                        'phong_kham': phong_kham,
                        'chan_doan': chan_doan,
                        'ket_luan': ket_luan,
                        'icd10': icd10,
                        'di_ung_thuoc': di_ung_thuoc,
                        'ghi_chu_kham': ghi_chu_kham,
                        'don_thuoc': pres_list,
                    })
            finally:
                conn.close()

            # Điền bảng lượt khám (tóm tắt)
            self.table_visits.setRowCount(0)
            for vr in visits:
                r2 = self.table_visits.rowCount()
                self.table_visits.insertRow(r2)
                vals = [vr.get('so_phieu') or '', vr.get('ngay_lap') or '', vr.get('phong_kham') or '', vr.get('bac_si') or '']
                for c2, v2 in enumerate(vals):
                    it = QTableWidgetItem(str(v2) if v2 is not None else "")
                    it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                    self.table_visits.setItem(r2, c2, it)

            # Chuẩn bị HTML chi tiết: hiển thị thông tin cơ bản + chi tiết lần khám mới nhất và đơn thuốc
            detail_html = header_html
            if visits:
                latest = visits[0]
                detail_html += f"<hr><b>Ngày khám:</b> {latest.get('ngay_lap') or '—'} — <b>Số phiếu:</b> {latest.get('so_phieu') or '—'}<br>"
                detail_html += f"<b>Bác sĩ:</b> {latest.get('bac_si') or '—'} — <b>Phòng:</b> {latest.get('phong_kham') or '—'}<br><br>"
                detail_html += f"<b>Chẩn đoán:</b> {latest.get('chan_doan') or '—'}<br>"
                detail_html += f"<b>Kết luận:</b> {latest.get('ket_luan') or '—'}<br>"
                detail_html += f"<b>Ghi chú khám:</b> {latest.get('ghi_chu_kham') or '—'}<br>"

                # Các đơn thuốc
                if latest.get('don_thuoc'):
                    detail_html += "<div style='margin-top:8px; padding:8px; background:#f8f9fb; border:1px solid #e9eef6;'>"
                    for d in latest.get('don_thuoc'):
                        detail_html += f"<div style='margin-bottom:6px;'><small class='text-muted'>Ngày kê: {d.get('ngay_ke') or '—'} — Ngày tái khám: {d.get('ngay_tai_kham') or '—'}</small><br>"
                        detail_html += f"<b>Hướng dẫn:</b> {d.get('loi_dan') or '—'}<ul>"
                        for m in d.get('meds'):
                            # m: (tên_thuốc, số_lượng, sáng, trưa, chiều, tối, liều_dùng, ghi_chú)
                            ten_thuoc = m[0]
                            so_luong = m[1]
                            lieu = m[6] or ''
                            ghi = m[7] or ''
                            sep = ' | ' if lieu and ghi else ''
                            detail_html += f"<li>{ten_thuoc} — số lượng: {so_luong} — liều: {lieu}{sep}{ghi}</li>"
                        detail_html += "</ul></div>"
                    detail_html += "</div>"

            self.lbl_patient_detail.setText(detail_html)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin bệnh nhân:\n{e}")

    def export_patients_csv(self):
        # Hỏi đường dẫn file
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

    def filter_appointments(self):
        date_from = self.filter_date_from.dateTime().toString("yyyy-MM-dd HH:mm")
        date_to = self.filter_date_to.dateTime().toString("yyyy-MM-dd HH:mm")
        conn = get_connection()
        cur = conn.cursor()
        try:
            if date_from and date_to:
                cur.execute(
                    "SELECT id, ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai FROM lich_hen WHERE ngay_gio BETWEEN ? AND ? ORDER BY id ASC",
                    (date_from, date_to)
                )
            elif date_from:
                cur.execute(
                    "SELECT id, ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai FROM lich_hen WHERE ngay_gio >= ? ORDER BY id ASC",
                    (date_from,)
                )
            elif date_to:
                cur.execute(
                    "SELECT id, ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai FROM lich_hen WHERE ngay_gio <= ? ORDER BY id ASC",
                    (date_to,)
                )
            else:
                cur.execute("SELECT id, ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai FROM lich_hen ORDER BY id ASC")
            rows = cur.fetchall()
        finally:
            conn.close()
        self.table_appointments.setRowCount(0)
        for r in rows:
            row = self.table_appointments.rowCount()
            self.table_appointments.insertRow(row)
            for c, v in enumerate(r[:6]):
                item = QTableWidgetItem(str(v) if v is not None else "")
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_appointments.setItem(row, c, item)
            status_item = QTableWidgetItem("Đã đặt lịch")
            status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
            self.table_appointments.setItem(row, 6, status_item)

