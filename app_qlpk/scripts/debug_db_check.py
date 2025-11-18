import sys
sys.path.append(r'c:\app_qlpk')
from database import get_connection

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
