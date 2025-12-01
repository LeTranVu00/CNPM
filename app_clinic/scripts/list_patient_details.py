import sys
import os

# ==============================================================================
# FIX LỖI IMPORT: TỰ ĐỘNG TÌM ĐƯỜNG DẪN GỐC (Thay cho đường dẫn cứng)
# ==============================================================================
# 1. Lấy đường dẫn tuyệt đối của file hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Lấy đường dẫn thư mục cha (Project Root)
# Hàm này sẽ lùi ra một cấp thư mục.
# Ví dụ: File đang ở "C:\app_qlpk\forms\login.py" -> project_root là "C:\app_qlpk"
project_root = os.path.dirname(current_dir)

# (Nếu file này nằm ngay ở thư mục gốc, bạn sửa dòng trên thành: project_root = current_dir)

# 3. Thêm đường dẫn gốc vào hệ thống tìm kiếm
if project_root not in sys.path:
    sys.path.append(project_root)
# ==============================================================================

# Bây giờ lệnh import sẽ hoạt động dù bạn để folder ở đâu
try:
    from database import get_connection
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print(f"👉 Đang tìm file 'database.py' tại: {project_root}")

conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT id, ho_ten FROM benh_nhan ORDER BY ho_ten LIMIT 50')
patients = cur.fetchall()
print('id | name | ma_hoso | phieu_kham_id | so_phieu | chan_doan | di_ung')
for pid, name in patients:
    cur.execute('SELECT ma_hoso FROM tiep_don WHERE benh_nhan_id=? AND ma_hoso IS NOT NULL ORDER BY id DESC LIMIT 1', (pid,))
    h = cur.fetchone()
    ma_hoso = h[0] if h else ''
    cur.execute('SELECT id, so_phieu FROM phieu_kham WHERE benh_nhan_id=? ORDER BY id DESC LIMIT 1', (pid,))
    pk = cur.fetchone()
    phieu_id = pk[0] if pk else None
    so_phieu = pk[1] if pk else ''
    chan = ''
    diung = ''
    if phieu_id:
        # detect allergy column
        try:
            cur.execute("PRAGMA table_info('chi_tiet_phieu_kham')")
            chi_cols = [c[1] for c in cur.fetchall()]
        except Exception:
            chi_cols = []
        if 'di_ung_thuoc' in chi_cols and 'di_ung' in chi_cols:
            cur.execute('SELECT chan_doan, COALESCE(di_ung_thuoc, di_ung) FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (phieu_id,))
        elif 'di_ung_thuoc' in chi_cols:
            cur.execute('SELECT chan_doan, di_ung_thuoc FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (phieu_id,))
        elif 'di_ung' in chi_cols:
            cur.execute('SELECT chan_doan, di_ung FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (phieu_id,))
        else:
            cur.execute('SELECT chan_doan, "" FROM chi_tiet_phieu_kham WHERE phieu_kham_id=? ORDER BY id DESC LIMIT 1', (phieu_id,))
        det = cur.fetchone()
        if det:
            chan = det[0] or ''
            diung = det[1] or ''
    print(f"{pid} | {name} | {ma_hoso} | {phieu_id} | {so_phieu} | {chan} | {diung}")
conn.close()
