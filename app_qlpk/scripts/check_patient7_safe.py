import sys
import os

# --- FIX: Tự động tìm đường dẫn thư mục gốc (app_qlpk) ---
# Lấy đường dẫn tuyệt đối của file script hiện tại
current_file_path = os.path.abspath(__file__)
# Lấy thư mục chứa script này
current_dir = os.path.dirname(current_file_path)
# Lấy thư mục cha - Nơi chứa database.py
project_root = os.path.dirname(current_dir)

# Thêm vào sys.path nếu chưa có để Python tìm thấy database.py
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from database import get_connection
except ImportError:
    print("❌ Không tìm thấy module 'database'. Kiểm tra lại cấu trúc thư mục.")
    sys.exit(1)

# --- LOGIC CHÍNH (Code gốc của bạn) ---
conn = get_connection()
cur = conn.cursor()
pid = 7

print('PATIENT', pid)
cur.execute('SELECT ho_ten FROM benh_nhan WHERE id = ?', (pid,))
p = cur.fetchone()
print(' name=', p[0] if p else None)
cur.execute('SELECT ma_hoso FROM tiep_don WHERE benh_nhan_id=? AND ma_hoso IS NOT NULL ORDER BY id DESC LIMIT 1', (pid,))
h = cur.fetchone()
print(' ma_hoso=', h[0] if h else None)
cur.execute('SELECT id, so_phieu FROM phieu_kham WHERE benh_nhan_id=? ORDER BY id DESC LIMIT 1', (pid,))
pk = cur.fetchone()
print(' phieu_kham=', pk)
if pk:
    cur.execute("PRAGMA table_info('chi_tiet_phieu_kham')")
    chi_cols = [c[1] for c in cur.fetchall()]
    if 'di_ung_thuoc' in chi_cols and 'di_ung' in chi_cols:
        cur.execute('SELECT chan_doan, COALESCE(di_ung_thuoc, di_ung) FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (pk[0],))
    elif 'di_ung_thuoc' in chi_cols:
        cur.execute('SELECT chan_doan, di_ung_thuoc FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (pk[0],))
    elif 'di_ung' in chi_cols:
        cur.execute('SELECT chan_doan, di_ung FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (pk[0],))
    else:
        cur.execute('SELECT chan_doan, "" FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (pk[0],))
    det = cur.fetchone()
    print(' detail=', det)
conn.close()
