import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import create_user, get_connection

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
