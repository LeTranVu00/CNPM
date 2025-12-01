import sys
import os

# ==============================================================================
# FIX LỖI IMPORT (Chèn đoạn này lên đầu file)
# ==============================================================================
# 1. Lấy đường dẫn thư mục chứa file hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Lấy đường dẫn thư mục gốc (Project Root)
# Logic cũ của bạn là lùi 1 cấp thư mục (os.path.dirname của thư mục hiện tại)
project_root = os.path.dirname(current_dir)

# 3. Thêm đường dẫn gốc vào hệ thống tìm kiếm module
if project_root not in sys.path:
    sys.path.append(project_root)
# ==============================================================================

# Bây giờ Python đã nhận diện được thư mục gốc, lệnh import sẽ hoạt động
try:
    from database import create_user, get_connection
except ImportError as e:
    print(f"❌ Lỗi Import: {e}")
    print(f"👉 Đường dẫn gốc đã thêm: {project_root}")

def ensure_user(username, password, role):
    try:
        created = create_user(username, password, role=role)
        if created:
            print(f"Created user: {username} with role {role}")
        else:
            print(f"User {username} not created (possibly exists)")
    except Exception as e:
        print(f"Could not create user {username}: {e}")

if __name__ == '__main__':
    # Create sample accounts for testing roles
    ensure_user('bacsi', 'bacsi', 'bac_si')
    ensure_user('tieptan', 'tiep_tan', 'tiep_tan')
    create_user('bacsi1', '123456', role='bac_si')
    print('Đã tạo tài khoản bác sĩ: bacsi1 / 123456')
    create_user('tieptan1', '123456', role='tieptan')
    print('Đã tạo tài khoản tiếp tân: tieptan1 / 123456')

    # Print existing users
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, role, created_at FROM users ORDER BY id')
    rows = cur.fetchall()
    print('\nCurrent users:')
    for r in rows:
        print(f"id={r[0]}\tusername={r[1]}\trole={r[2]}\tcreated_at={r[3]}")
    conn.close()
