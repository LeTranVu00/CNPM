from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# Check benh_nhan table
cursor.execute("SELECT id, ho_ten FROM benh_nhan LIMIT 5")
print("=== Bệnh nhân ===")
for id, name in cursor.fetchall():
    print(f"ID: {id}, Name: {name}")

# Check tiep_don table for ma_hoso
cursor.execute("SELECT benh_nhan_id, ma_hoso FROM tiep_don WHERE benh_nhan_id IN (SELECT id FROM benh_nhan LIMIT 5)")
print("\n=== Tiếp đón (ma_hoso) ===")
for bn_id, ma_hoso in cursor.fetchall():
    print(f"Patient ID: {bn_id}, Ma_hoso: {ma_hoso}")

conn.close()
