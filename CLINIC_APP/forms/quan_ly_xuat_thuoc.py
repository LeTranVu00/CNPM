from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from database import get_connection, get_prescriptions_for_patient, mark_prescription_dispensed
from database import get_user_role, save_xuat_thuoc_history, get_supplementary_prescriptions_for_patient
from app_signals import app_signals
from signals import app_signals as signal_app_signals

class QuanLyXuatThuoc(QWidget):
    """Form cho dược sĩ để xuất thuốc dựa trên đơn bác sĩ kê."""
    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.username = username
        self.current_pres = []
        self.current_pres_bo_sung = []
        self.setWindowTitle("Quản lý Xuất thuốc")
        self.init_ui()
        self.load_patients()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("QUẢN LÝ XUẤT THUỐC")
        header.setStyleSheet('font-weight:bold; font-size:14pt; color:#1565c0')
        layout.addWidget(header)

        controls = QHBoxLayout()
        lbl = QLabel("Chọn bệnh nhân:")
        self.combo_patient = QComboBox()
        self.combo_patient.setEditable(True)
        self.combo_patient.setMinimumWidth(300)
        btn_load = QPushButton("Tải đơn")
        btn_load.clicked.connect(self.load_prescriptions_for_selected)
        controls.addWidget(lbl)
        controls.addWidget(self.combo_patient)
        controls.addWidget(btn_load)
        controls.addStretch()
        layout.addLayout(controls)

        # Tạo tab widget cho các đơn thuốc và đơn thuốc bổ sung
        self.tabs = QTabWidget()
        
        # Tab 1: Đơn thuốc thường
        tab_regular = QWidget()
        tab_regular_layout = QVBoxLayout(tab_regular)
        
        # Bảng các đơn thuốc
        # Bỏ cột ID khỏi hiển thị; lưu `don_id` vào Qt.UserRole của ô 'Ngày kê'
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ngày kê", "Bác sĩ", "Tổng tiền", "Trạng thái"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMaximumHeight(150)
        tab_regular_layout.addWidget(self.table)
        
        self.tabs.addTab(tab_regular, "Đơn Thuốc Thường")
        
        # Tab 2: Đơn thuốc bổ sung
        tab_supplement = QWidget()
        tab_supplement_layout = QVBoxLayout(tab_supplement)
        
        self.table_bo_sung = QTableWidget(0, 4)
        self.table_bo_sung.setHorizontalHeaderLabels(["Ngày kê", "Bác sĩ", "Tổng tiền", "Trạng thái"])
        self.table_bo_sung.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_bo_sung.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_bo_sung.setMaximumHeight(150)
        tab_supplement_layout.addWidget(self.table_bo_sung)
        
        self.tabs.addTab(tab_supplement, "Đơn Thuốc Bổ Sung")
        
        layout.addWidget(self.tabs)

        # Nhãn cho bảng chi tiết thuốc
        drug_label = QLabel("Danh mục tất cả thuốc (Tồn kho sẽ cập nhật khi xuất):")
        drug_label.setStyleSheet('font-weight:bold; font-size:11pt; color:#333')
        layout.addWidget(drug_label)

        # Bảng tất cả thuốc kèm thông tin tồn kho
        self.table_drugs = QTableWidget(0, 5)
        self.table_drugs.setHorizontalHeaderLabels(["Tên thuốc", "Mã thuốc", "Đơn vị", "Tồn kho", "Ghi chú"])
        self.table_drugs.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_drugs.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_drugs.setAlternatingRowColors(True)
        layout.addWidget(self.table_drugs)

        # Khu vực chi tiết
        detail_label = QLabel("Ghi chú:")
        detail_label.setStyleSheet('font-weight:bold; font-size:11pt; color:#333')
        layout.addWidget(detail_label)
        
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMinimumHeight(100)
        layout.addWidget(self.detail)

        # Các nút hành động
        actions = QHBoxLayout()
        self.btn_view = QPushButton("Xem chi tiết")
        self.btn_view.clicked.connect(self.view_selected)
        self.btn_xuat = QPushButton("Xuất thuốc")
        self.btn_xuat.clicked.connect(self.dispense_selected)
        actions.addStretch()
        actions.addWidget(self.btn_view)
        actions.addWidget(self.btn_xuat)
        layout.addLayout(actions)
        
        # Kết nối signal cho đơn thuốc bổ sung
        try:
            app_signals.don_bo_sung_printed.connect(self.on_don_bo_sung_printed)
        except Exception:
            pass

    def load_patients(self):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, ho_ten, so_cccd FROM benh_nhan ORDER BY ho_ten")
            rows = cur.fetchall()
            self.patients = rows
            self.combo_patient.clear()
            self.combo_patient.addItem("")
            for r in rows:
                self.combo_patient.addItem(f"{r[1]} ({r[2]})", userData=r[0])
        finally:
            conn.close()

    def load_prescriptions_for_selected(self):
        idx = self.combo_patient.currentIndex()
        if idx <= 0:
            QMessageBox.warning(self, "Chọn bệnh nhân", "Vui lòng chọn bệnh nhân trước khi tải đơn.")
            return
        patient_id = self.combo_patient.currentData()
        
        # Tải các đơn thuốc thường
        pres = get_prescriptions_for_patient(patient_id)
        self.table.setRowCount(0)
        self.current_pres = pres
        for p in pres:
            r = self.table.rowCount()
            self.table.insertRow(r)
            # Lưu don_id vào data của ô 'Ngày kê' và hiển thị ngày ở cột 0
            date_item = QTableWidgetItem(str(p['ngay_ke'] or ''))
            date_item.setData(Qt.UserRole, p['id'])
            self.table.setItem(r, 0, date_item)

            # Hiển thị tên bác sĩ là người đang đăng nhập nếu có, nếu không thì dùng giá trị trong record
            display_doctor = p.get('bac_si') or ''
            try:
                if getattr(self, 'username', None):
                    conn_d = get_connection()
                    cur_d = conn_d.cursor()
                    cur_d.execute("SELECT full_name FROM users WHERE username = ?", (self.username,))
                    rown = cur_d.fetchone()
                    conn_d.close()
                    if rown and rown[0]:
                        display_doctor = rown[0]
            except Exception:
                pass

            self.table.setItem(r, 1, QTableWidgetItem(str(display_doctor)))

            # Tính tổng tiền cho đơn hiện tại: sum(so_luong * gia_thuoc) từ chi_tiet_don_thuoc
            try:
                conn2 = get_connection()
                cur2 = conn2.cursor()
                cur2.execute("""
                    SELECT SUM(ct.so_luong * COALESCE(dmt.gia_thuoc, 0))
                    FROM chi_tiet_don_thuoc ct
                    LEFT JOIN danh_muc_thuoc dmt ON ct.ma_thuoc = dmt.ma_thuoc
                    WHERE ct.don_thuoc_id = ?
                """, (p['id'],))
                total_row = cur2.fetchone()
                total_amount = total_row[0] or 0
                conn2.close()
            except Exception:
                total_amount = p.get('tong_tien', 0) or 0

            try:
                total_text = f"{float(total_amount):,.0f}"
            except Exception:
                total_text = str(total_amount)

            self.table.setItem(r, 2, QTableWidgetItem(total_text))
            status_text = "Đã xuất" if p.get('da_xuat') else "Chưa xuất"
            self.table.setItem(r, 3, QTableWidgetItem(status_text))
        
        # Tải các đơn thuốc bổ sung
        pres_bo_sung = get_supplementary_prescriptions_for_patient(patient_id)
        self.table_bo_sung.setRowCount(0)
        self.current_pres_bo_sung = pres_bo_sung
        for p in pres_bo_sung:
            r = self.table_bo_sung.rowCount()
            self.table_bo_sung.insertRow(r)
            # Lưu don_id vào data của ô 'Ngày kê' và hiển thị ngày ở cột 0
            date_item_b = QTableWidgetItem(str(p['ngay_ke'] or ''))
            date_item_b.setData(Qt.UserRole, p['id'])
            self.table_bo_sung.setItem(r, 0, date_item_b)

            # Hiển thị tên bác sĩ là người đang đăng nhập nếu có, nếu không thì dùng giá trị trong record
            display_doctor = p.get('bac_si') or ''
            try:
                if getattr(self, 'username', None):
                    conn_d = get_connection()
                    cur_d = conn_d.cursor()
                    cur_d.execute("SELECT full_name FROM users WHERE username = ?", (self.username,))
                    rown = cur_d.fetchone()
                    conn_d.close()
                    if rown and rown[0]:
                        display_doctor = rown[0]
            except Exception:
                pass

            self.table_bo_sung.setItem(r, 1, QTableWidgetItem(str(display_doctor)))
            # Tính tổng tiền cho đơn bổ sung
            try:
                conn3 = get_connection()
                cur3 = conn3.cursor()
                cur3.execute("""
                    SELECT SUM(ct.so_luong * COALESCE(dmt.gia_thuoc, 0))
                    FROM chi_tiet_don_thuoc_bo_sung ct
                    LEFT JOIN danh_muc_thuoc dmt ON ct.ma_thuoc = dmt.ma_thuoc
                    WHERE ct.don_thuoc_bo_sung_id = ?
                """, (p['id'],))
                total_row = cur3.fetchone()
                total_amount = total_row[0] or 0
                conn3.close()
            except Exception:
                total_amount = p.get('tong_tien', 0) or 0

            try:
                total_text = f"{float(total_amount):,.0f}"
            except Exception:
                total_text = str(total_amount)

            self.table_bo_sung.setItem(r, 2, QTableWidgetItem(total_text))
            status_text = "Đã xuất" if p.get('xuat_thuoc') else "Chưa xuất"
            self.table_bo_sung.setItem(r, 3, QTableWidgetItem(status_text))

    def view_selected(self):
        # Kiểm tra tab đang hoạt động
        active_tab = self.tabs.currentIndex()
        
        if active_tab == 0:
            # Tab đơn thuốc thường
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Chọn đơn", "Vui lòng chọn một đơn thuốc để xem chi tiết.")
                return
            # don_id được lưu trong Qt.UserRole của ô 'Ngày kê'
            date_item = self.table.item(row, 0)
            try:
                don_id = int(date_item.data(Qt.UserRole))
            except Exception:
                don_id = None
            pres = next((p for p in self.current_pres if p['id'] == don_id), None)
        elif active_tab == 1:
            # Tab đơn thuốc bổ sung
            row = self.table_bo_sung.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Chọn đơn", "Vui lòng chọn một đơn thuốc bổ sung để xem chi tiết.")
                return
            # don_id được lưu trong Qt.UserRole của ô 'Ngày kê' (bảng bổ sung)
            date_item = self.table_bo_sung.item(row, 0)
            try:
                don_id = int(date_item.data(Qt.UserRole))
            except Exception:
                don_id = None
            pres = next((p for p in self.current_pres_bo_sung if p['id'] == don_id), None)
        else:
            QMessageBox.warning(self, "Chọn đơn", "Vui lòng chọn đơn thuốc trước.")
            return
        
        if not pres:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy đơn thuốc đã chọn.")
            return
        
        # Lưu đơn hiện tại để sử dụng sau
        self.current_prescription = pres
        
        # Tải tất cả thuốc từ bảng `danh_muc_thuoc`
        self.load_all_drugs()
        
        # Tính tổng tiền từ giá thuốc trong danh mục nhân với số lượng
        total_amount = 0
        conn = get_connection()
        cur = conn.cursor()
        try:
            if active_tab == 0:
                cur.execute("""
                    SELECT ct.so_luong, dmt.gia_thuoc 
                    FROM chi_tiet_don_thuoc ct 
                    LEFT JOIN danh_muc_thuoc dmt ON ct.ma_thuoc = dmt.ma_thuoc 
                    WHERE ct.don_thuoc_id = ?
                """, (don_id,))
            else:
                cur.execute("""
                    SELECT ct.so_luong, dmt.gia_thuoc 
                    FROM chi_tiet_don_thuoc_bo_sung ct 
                    LEFT JOIN danh_muc_thuoc dmt ON ct.ma_thuoc = dmt.ma_thuoc 
                    WHERE ct.don_thuoc_bo_sung_id = ?
                """, (don_id,))
            
            price_details = cur.fetchall()
            for so_luong, gia_thuoc in price_details:
                if gia_thuoc and so_luong:
                    total_amount += float(gia_thuoc) * int(so_luong)
        finally:
            conn.close()

        # Cập nhật văn bản chi tiết
        lines = [f"Đơn ID: {pres['id']}", f"Ngày kê: {pres['ngay_ke']}", f"Bác sĩ kê đơn: {pres['bac_si']}", f"Tổng tiền: {total_amount:,.0f} VND"]
        
        if active_tab == 0:
            lines.append(f"Đã xuất: {'Có' if pres.get('da_xuat') else 'Chưa'}")
            if pres.get('ngay_xuat'):
                lines.append(f"Ngày xuất: {pres.get('ngay_xuat')}")
        else:
            lines.append(f"Đã xuất: {'Có' if pres.get('xuat_thuoc') else 'Chưa'}")
        
        # Lấy chi tiết thuốc
        conn = get_connection()
        cur = conn.cursor()
        try:
            if active_tab == 0:
                cur.execute("""
                    SELECT ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu 
                    FROM chi_tiet_don_thuoc 
                    WHERE don_thuoc_id = ?
                """, (don_id,))
            else:
                cur.execute("""
                    SELECT ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu 
                    FROM chi_tiet_don_thuoc_bo_sung 
                    WHERE don_thuoc_bo_sung_id = ?
                """, (don_id,))
            
            drug_details = cur.fetchall()
            
            if drug_details:
                lines.append("\nCHI TIẾT THUỐC:")
                for drug in drug_details:
                    ten_thuoc, so_luong, don_vi, sang, trua, chieu, toi, lieu_dung, ghi_chu = drug
                    lines.append(f"- {ten_thuoc}: {so_luong} {don_vi or ''}")
                    
                    # Liều dùng
                    lieu_info = []
                    if sang and sang.strip(): lieu_info.append(f"Sáng: {sang.strip()}")
                    if trua and trua.strip(): lieu_info.append(f"Trưa: {trua.strip()}")
                    if chieu and chieu.strip(): lieu_info.append(f"Chiều: {chieu.strip()}")
                    if toi and toi.strip(): lieu_info.append(f"Tối: {toi.strip()}")
                    
                    if lieu_info:
                        lines.append(f"  Liều dùng: {' | '.join(lieu_info)}")
                    
                    # Hướng dẫn sử dụng chung
                    if lieu_dung and lieu_dung.strip():
                        lines.append(f"  Hướng dẫn: {lieu_dung.strip()}")
                    
                    # Ghi chú
                    if ghi_chu and ghi_chu.strip():
                        lines.append(f"  Ghi chú: {ghi_chu.strip()}")
                    
                    lines.append("")  # Dòng trống giữa các thuốc
        finally:
            conn.close()
        
        self.detail.setPlainText('\n'.join(lines))

    def load_all_drugs(self):
        """Load all drugs from danh_muc_thuoc table."""
        self.table_drugs.setRowCount(0)
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT ma_thuoc, ten_thuoc, don_vi, ton_kho FROM danh_muc_thuoc ORDER BY ten_thuoc")
            drugs = cur.fetchall()
            
            # Xây dựng dict tên thuốc trong đơn hiện tại để tra nhanh
            drug_in_pres = {}
            if hasattr(self, 'current_prescription'):
                for item in self.current_prescription.get('items', []):
                    ma = item.get('ma_thuoc')
                    if ma:
                        drug_in_pres[ma] = f"{item.get('ten_thuoc', '')} - {item.get('so_luong', 0)} {item.get('don_vi', '')}"
            
            for drug in drugs:
                ma_thuoc = drug[0]
                ten_thuoc = drug[1]
                don_vi = drug[2]
                ton_kho = drug[3] or 0
                
                r = self.table_drugs.rowCount()
                self.table_drugs.insertRow(r)
                self.table_drugs.setItem(r, 0, QTableWidgetItem(ten_thuoc))
                self.table_drugs.setItem(r, 1, QTableWidgetItem(str(ma_thuoc or '')))
                self.table_drugs.setItem(r, 2, QTableWidgetItem(str(don_vi or '')))
                
                # Tồn kho item - để dễ cập nhật
                ton_kho_item = QTableWidgetItem(str(ton_kho))
                ton_kho_item.setData(Qt.UserRole, ma_thuoc)  # Store ma_thuoc for later reference
                self.table_drugs.setItem(r, 3, ton_kho_item)
                
                # Ghi chú: show drug details if it's in the current prescription
                ghi_chu = ""
                if ma_thuoc in drug_in_pres:
                    ghi_chu = drug_in_pres[ma_thuoc]
                self.table_drugs.setItem(r, 4, QTableWidgetItem(ghi_chu))
        finally:
            conn.close()
        
        self.table_drugs.resizeColumnsToContents()

    def dispense_selected(self):
        # Check which tab is active
        active_tab = self.tabs.currentIndex()
        
        if active_tab == 0:
            # Regular prescriptions
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Chọn đơn", "Vui lòng chọn một đơn thuốc để xuất.")
                return
            # don_id được lưu trong Qt.UserRole của ô 'Ngày kê'
            date_item = self.table.item(row, 0)
            try:
                don_id = int(date_item.data(Qt.UserRole))
            except Exception:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy ID đơn trên hàng đã chọn.")
                return
            # Status now in column 3
            status_text = self.table.item(row, 3).text()
            if status_text and status_text == "Đã xuất":
                QMessageBox.information(self, "Đã xuất", "Đơn này đã được xuất trước đó.")
                return
            
            # Confirm
            ok = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xuất các thuốc trong đơn này?", QMessageBox.Yes | QMessageBox.No)
            if ok != QMessageBox.Yes:
                return
            
            try:
                # Get current patient info
                patient_id = self.combo_patient.currentData()
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT ho_ten, so_cccd FROM benh_nhan WHERE id = ?", (patient_id,))
                patient_info = cur.fetchone()
                
                # Get prescription info
                cur.execute("SELECT bac_si FROM don_thuoc WHERE id = ?", (don_id,))
                pres_info = cur.fetchone()
                conn.close()
                
                ho_ten = patient_info[0] if patient_info else "Unknown"
                so_cccd = patient_info[1] if patient_info else ""
                bac_si = pres_info[0] if pres_info else "Unknown"
                
                success = mark_prescription_dispensed(don_id, dispensed_by_username=self.username)
                if success:
                    # Save history
                    save_xuat_thuoc_history(
                        don_thuoc_id=don_id,
                        bac_si=bac_si,
                        ho_ten_benh_nhan=ho_ten,
                        so_cccd=so_cccd,
                        xuat_boi=self.username,
                        ghi_chu=""
                    )
                    
                    # Update stock in the drug table immediately
                    self.update_drug_table_after_dispense(don_id)
                    
                    QMessageBox.information(self, "Hoàn thành", "Đã xuất thuốc và cập nhật tồn kho.")
                    
                    # Emit signal để cập nhật doanh thu
                    try:
                        app_signals.medication_dispensed.emit()
                    except Exception:
                        pass
                    
                    self.load_prescriptions_for_selected()
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể xuất thuốc. Vui lòng thử lại.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi xuất thuốc: {e}")
        
        elif active_tab == 1:
            # Supplementary prescriptions
            row = self.table_bo_sung.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Chọn đơn", "Vui lòng chọn một đơn thuốc bổ sung để xuất.")
                return
            # don_id được lưu trong Qt.UserRole của ô 'Ngày kê' (bảng bổ sung)
            date_item = self.table_bo_sung.item(row, 0)
            try:
                don_id = int(date_item.data(Qt.UserRole))
            except Exception:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy ID đơn trên hàng đã chọn.")
                return
            # Status now in column 3 for supplementary table
            status_text = self.table_bo_sung.item(row, 3).text()
            if status_text and status_text == "Đã xuất":
                QMessageBox.information(self, "Đã xuất", "Đơn bổ sung này đã được xuất trước đó.")
                return
            
            # Confirm
            ok = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xuất các thuốc trong đơn bổ sung này?", QMessageBox.Yes | QMessageBox.No)
            if ok != QMessageBox.Yes:
                return
            
            try:
                self.dispense_supplementary_prescription(don_id)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi xuất thuốc: {e}")

    def dispense_supplementary_prescription(self, don_bo_sung_id):
        """Mark supplementary prescription as exported and update stock."""
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            # Get patient info
            patient_id = self.combo_patient.currentData()
            cur.execute("SELECT ho_ten, so_cccd FROM benh_nhan WHERE id = ?", (patient_id,))
            patient_info = cur.fetchone()
            ho_ten = patient_info[0] if patient_info else "Unknown"
            so_cccd = patient_info[1] if patient_info else ""
            
            # Get supplementary prescription info
            cur.execute("SELECT bac_si FROM don_thuoc_bo_sung WHERE id = ?", (don_bo_sung_id,))
            pres_info = cur.fetchone()
            bac_si = pres_info[0] if pres_info else "Unknown"
            
            # Get medicine details
            cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong FROM chi_tiet_don_thuoc_bo_sung WHERE don_thuoc_bo_sung_id = ?", (don_bo_sung_id,))
            medicines = cur.fetchall()
            
            # Check stock availability
            insufficient = []
            updates = []
            
            for ma_thuoc, ten_thuoc, so_luong in medicines:
                if not ma_thuoc:
                    continue
                
                cur.execute("SELECT ton_kho FROM danh_muc_thuoc WHERE ma_thuoc = ?", (ma_thuoc,))
                result = cur.fetchone()
                if not result:
                    insufficient.append(f"{ten_thuoc} - Không tìm thấy trong danh mục")
                    continue
                
                ton_kho = result[0] or 0
                if ton_kho < so_luong:
                    insufficient.append(f"{ten_thuoc} - Tồn kho: {ton_kho}, cần: {so_luong}")
                else:
                    updates.append((ton_kho - so_luong, ma_thuoc))
            
            # If insufficient and no valid updates, abort
            if insufficient and not updates:
                QMessageBox.warning(self, "Lỗi", "Các thuốc không đủ tồn kho:\n" + "\n".join(insufficient))
                return
            
            # Ask user if there are partial shortages
            if insufficient and updates:
                reply = QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    "Các thuốc không đủ tồn kho:\n" + "\n".join(insufficient) + "\n\nBạn có muốn tiếp tục xuất những thuốc đủ tồn kho không?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # Update stock
            try:
                conn.execute("BEGIN")
                for new_ton_kho, ma_thuoc in updates:
                    cur.execute("""
                        UPDATE danh_muc_thuoc 
                        SET ton_kho = ? 
                        WHERE ma_thuoc = ?
                    """, (new_ton_kho, ma_thuoc))
                
                # Mark as exported
                cur.execute("UPDATE don_thuoc_bo_sung SET xuat_thuoc = 1 WHERE id = ?", (don_bo_sung_id,))
                
                conn.commit()
                
                msg = f"Đã xuất thành công {len(updates)} loại thuốc"
                if insufficient:
                    msg += f"\n(Không thể xuất {len(insufficient)} loại do tồn kho không đủ)"
                
                QMessageBox.information(self, "Hoàn tất", msg)
                
                # Emit signal để cập nhật doanh thu
                try:
                    app_signals.medication_dispensed.emit()
                except Exception:
                    pass
                
                # Update drug table
                self.update_drug_table_after_dispense(don_bo_sung_id, is_supplementary=True)
                
                # Reload prescriptions
                self.load_prescriptions_for_selected()
                
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật tồn kho: {e}")
                return
        
        finally:
            if conn:
                conn.close()

    def update_drug_table_after_dispense(self, don_id, is_supplementary=False):
        """Update drug table with new stock values after dispensing."""
        if not hasattr(self, 'current_prescription'):
            return
        
        conn = get_connection()
        cur = conn.cursor()
        try:
            if is_supplementary:
                # Get the drugs that were just dispensed from supplementary prescription
                cur.execute("""
                    SELECT ma_thuoc, so_luong FROM chi_tiet_don_thuoc_bo_sung WHERE don_thuoc_bo_sung_id = ?
                """, (don_id,))
            else:
                # Get the drugs that were just dispensed from regular prescription
                cur.execute("""
                    SELECT ma_thuoc, so_luong FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?
                """, (don_id,))
            
            dispensed_drugs = cur.fetchall()
            
            # Update each drug in the table
            for row in range(self.table_drugs.rowCount()):
                ma_thuoc_cell = self.table_drugs.item(row, 1)
                if ma_thuoc_cell:
                    ma_thuoc = ma_thuoc_cell.text()
                    
                    # Get updated stock from database
                    cur.execute("SELECT ton_kho FROM danh_muc_thuoc WHERE ma_thuoc = ?", (ma_thuoc,))
                    result = cur.fetchone()
                    if result:
                        new_stock = result[0] or 0
                        # Update the table cell
                        self.table_drugs.setItem(row, 3, QTableWidgetItem(str(new_stock)))
        finally:
            conn.close()

    def on_don_bo_sung_printed(self, benh_nhan_id):
        """Handle signal when supplementary prescription is printed."""
        # If current patient is the one with the printed prescription, reload
        if self.combo_patient.currentData() == benh_nhan_id:
            self.load_prescriptions_for_selected()
            # Switch to supplementary prescriptions tab
            self.tabs.setCurrentIndex(1)
            QMessageBox.information(self, "Thông báo", "Đơn thuốc bổ sung mới đã được cập nhật. Bạn có thể xuất ngay.")
