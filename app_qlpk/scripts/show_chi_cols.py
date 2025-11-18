import sys
import os

from app_qlpk.database import get_connection

# --- FIX: Tự động tìm thư mục gốc dự án (Thay thế đường dẫn cứng c:\app_qlpk) ---
# 1. Lấy đường dẫn tuyệt đối của file script này
current_file = os.path.abspath(__file__)
# 2. Lấy thư mục chứa script (scripts/)
current_dir = os.path.dirname(current_file)
# 3. Lấy thư mục cha (app_qlpk/) - Nơi chứa database.py
project_root = os.path.dirname(current_dir)

# 4. Thêm vào sys.path để Python tìm thấy module
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import database

# --- CODE KIỂM TRA DB ---
conn = get_connection()
cur = conn.cursor()

print("\n--- KIỂM TRA CẤU TRÚC BẢNG ---")

# 1. Chi tiết phiếu khám
cur.execute("PRAGMA table_info('chi_tiet_phieu_kham')")
cols = [c[1] for c in cur.fetchall()]
print(f'chi_tiet_phieu_kham columns ({len(cols)}) = {cols}')

# 2. Tiếp đón
cur.execute("PRAGMA table_info('tiep_don')")
cols_td = [c[1] for c in cur.fetchall()]
print(f'tiep_don columns ({len(cols_td)}) = {cols_td}')

# 3. Phiếu khám
cur.execute("PRAGMA table_info('phieu_kham')")
cols_pk = [c[1] for c in cur.fetchall()]
print(f'phieu_kham columns ({len(cols_pk)}) = {cols_pk}')

conn.close()