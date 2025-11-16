import sys
sys.path.append(r'c:\app_qlpk')
from database import get_connection
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
