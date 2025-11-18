import sys
sys.path.append(r'c:\app_qlpk')
from database import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("PRAGMA table_info('chi_tiet_phieu_kham')")
cols = [c[1] for c in cur.fetchall()]
print('chi_tiet_phieu_kham columns =', cols)
cur.execute("PRAGMA table_info('tiep_don')")
print('tiep_don columns =', [c[1] for c in cur.fetchall()])
cur.execute("PRAGMA table_info('phieu_kham')")
print('phieu_kham columns =', [c[1] for c in cur.fetchall()])
conn.close()
