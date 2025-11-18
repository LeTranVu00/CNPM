import sys
import os

# --- FIX: Cấu hình đường dẫn động (Hoạt động trên macOS/Windows/Linux) ---
# 1. Lấy đường dẫn file hiện tại: .../app_qlpk/scripts/list_patient_details.py
current_file = os.path.abspath(__file__)
# 2. Lấy thư mục chứa script: .../app_qlpk/scripts
current_dir = os.path.dirname(current_file)
# 3. Lấy thư mục gốc dự án: .../app_qlpk (Nơi chứa database.py)
project_root = os.path.dirname(current_dir)

# 4. Thêm vào đầu danh sách sys.path để ưu tiên tìm module ở đây
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import Database ---
try:
    from database import get_connection
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print(f"ℹ️  Đường dẫn project_root tính toán được: {project_root}")
    sys.exit(1)


def inspect_patient(pid):
    conn = get_connection()
    cur = conn.cursor()
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
        cur.execute('SELECT chan_doan, COALESCE(di_ung_thuoc, di_ung, "") FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (pk[0],))
        det = cur.fetchone()
        print(' detail=', det)
    conn.close()

if __name__ == "__main__":
    # change pid as needed
    inspect_patient(7)
    # print a few more patient ids to help selection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, ho_ten FROM benh_nhan LIMIT 12')
    print('--- PATIENTS ---')
    for r in cur.fetchall():
        print(r)
    conn.close()
