import sys
import os

# --- FIX: Thêm thư mục cha vào đường dẫn hệ thống ---
# Lấy đường dẫn tuyệt đối của file này: .../app_qlpk/scripts/create_sample_accounts.py
current_file_path = os.path.abspath(__file__)
# Lấy thư mục chứa nó: .../app_qlpk/scripts
current_dir = os.path.dirname(current_file_path)
# Lấy thư mục cha (root project): .../app_qlpk
parent_dir = os.path.dirname(current_dir)

# Thêm vào sys.path để Python tìm thấy file database.py
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from database import create_user, get_connection
except ImportError as e:
    print(f"Lỗi Import: {e}")
    sys.exit(1)

def ensure_user(username, password, role):
    try:
        # create_user trả về True nếu tạo mới thành công, False nếu trùng hoặc lỗi
        created = create_user(username, password, role=role)
        if created:
            print(f"✅ Đã tạo user: {username} (Quyền: {role})")
        else:
            print(f"⚠️ User {username} đã tồn tại hoặc lỗi.")
    except Exception as e:
        print(f"❌ Lỗi khi tạo user {username}: {e}")

if __name__ == '__main__':
    # Create sample accounts for testing roles
    ensure_user('bacsi', 'bacsi', 'bac_si')
    ensure_user('tieptan', 'tiep_tan', 'tiep_tan')

    # Print existing users
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, role, created_at FROM users ORDER BY id')
    rows = cur.fetchall()
    print('\nCurrent users:')
    for r in rows:
        print(f"id={r[0]}\tusername={r[1]}\trole={r[2]}\tcreated_at={r[3]}")
    conn.close()
