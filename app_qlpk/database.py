import os
import sqlite3
from datetime import datetime
import os as _os
import hashlib
import binascii
import secrets

# 🟢 SỬA: Đảm bảo thư mục data tồn tại trước khi trỏ đường dẫn
DB_FOLDER = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

DB_NAME = os.path.join(DB_FOLDER, "clinic.db")


def get_connection():
    """
    Tạo kết nối đến database với các thiết lập tối ưu
    """
    try:
        conn = sqlite3.connect(DB_NAME,
                               timeout=20.0,
                               isolation_level=None,
                               check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    except sqlite3.Error as e:
        print(f"Lỗi khi kết nối database: {e}")
        raise


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Bảng Bệnh Nhân
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benh_nhan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten TEXT NOT NULL,
            gioi_tinh TEXT,
            ngay_sinh TEXT,
            tuoi INTEGER,
            dia_chi TEXT,
            dien_thoai TEXT,
            so_cccd TEXT,
            doi_tuong TEXT,
            nghe_nghiep TEXT,
            nguoi_gioi_thieu TEXT,
            loai_kham TEXT
        )
    """)

    # 2. Bảng Phiếu Khám
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phieu_kham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            so_phieu TEXT,
            benh_nhan_id INTEGER,
            ngay_lap TEXT,
            bac_si TEXT,
            phong_kham TEXT,
            tong_tien REAL DEFAULT 0,
            FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
        )
    """)
    # (Code migration cũ của phieu_kham giữ nguyên nhưng bỏ qua nếu không cần thiết để code gọn)

    # 3. Bảng Chỉ định (Tạo bảng trước rồi mới migration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_dinh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            so_chi_dinh TEXT,
            phieu_kham_id INTEGER,
            ten_dich_vu TEXT,
            so_luong INTEGER DEFAULT 1,
            don_gia REAL,
            thanh_tien REAL,
            FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id)
        )
    """)

    # 🟢 SỬA: Chuyển migration xuống SAU khi tạo bảng để tránh lỗi nếu bảng chưa có
    cursor.execute("PRAGMA table_info(chi_dinh)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'kham_lam_sang' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_dinh ADD COLUMN kham_lam_sang TEXT")
            print("Đã thêm cột 'kham_lam_sang' vào bảng chi_dinh")
        except Exception:
            pass
    if 'chan_doan_ban_dau' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_dinh ADD COLUMN chan_doan_ban_dau TEXT")
            print("Đã thêm cột 'chan_doan_ban_dau' vào bảng chi_dinh")
        except Exception:
            pass

    # 4. Bảng Tiếp Đón
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiep_don (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hoso TEXT,
            benh_nhan_id INTEGER,
            ngay_tiep_don TEXT,
            phong_kham TEXT,
            bac_si_kham TEXT,
            tinh_trang TEXT,
            tien_kham REAL,
            nv_tiepdon TEXT,
            huyet_ap TEXT,
            nhiet_do REAL,
            chieu_cao REAL,
            can_nang REAL,
            nhip_tho INTEGER,
            nhip_tim INTEGER,
            da_kham INTEGER DEFAULT 0,
            FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
        )
    """)

    cursor.execute("PRAGMA table_info(tiep_don)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'nhip_tho' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN nhip_tho INTEGER")
        except Exception:
            pass
    if 'nhip_tim' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN nhip_tim INTEGER")
        except Exception:
            pass
    if 'da_kham' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN da_kham INTEGER DEFAULT 0")
        except Exception:
            pass

    # 5. Bảng Chi tiết phiếu khám
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_phieu_kham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phieu_kham_id INTEGER NOT NULL,
            nhiet_do REAL,
            nhip_tim INTEGER,
            huyet_ap TEXT,
            nhip_tho INTEGER,
            can_nang REAL,
            chieu_cao REAL,
            di_ung_thuoc TEXT,
            tien_su_ban_than TEXT,
            tien_su_gia_dinh TEXT,
            benh_kem_theo TEXT,
            icd10 TEXT,
            chidinh_cls TEXT,
            kham_lam_sang TEXT,
            chan_doan TEXT,
            ket_luan TEXT,
            ghi_chu_kham TEXT,
            FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE
        )
    """)
    # Migration cho chi_tiet_phieu_kham
    cursor.execute("PRAGMA table_info(chi_tiet_phieu_kham)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'ghi_chu_kham' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_tiet_phieu_kham ADD COLUMN ghi_chu_kham TEXT")
        except Exception:
            pass
    if 'chidinh_cls' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_tiet_phieu_kham ADD COLUMN chidinh_cls TEXT")
        except Exception:
            pass

    # 6. Bảng Thanh Toán
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thanh_toan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay TEXT,
            loai TEXT,
            mo_ta TEXT,
            so_tien REAL
        )
    """)

    # 7. Bảng Đơn Thuốc & Danh mục
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS don_thuoc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phieu_kham_id INTEGER NOT NULL,
            ngay_ke TEXT NOT NULL,
            so_ngay INTEGER,
            ngay_tai_kham TEXT,
            tong_tien REAL DEFAULT 0,
            loai_don TEXT,
            chan_doan TEXT,
            di_ung_thuoc TEXT,
            loi_dan TEXT,
            bac_si TEXT,
            quay_thuoc TEXT,
            nguoi_lap_phieu TEXT,
            FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS danh_muc_icd10 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS danh_muc_thuoc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_thuoc TEXT UNIQUE NOT NULL,
            ten_thuoc TEXT NOT NULL,
            don_vi TEXT,
            gia_thuoc REAL DEFAULT 0,
            ton_kho INTEGER DEFAULT 0
        )
    """)
    # Migration danh_muc_thuoc
    cursor.execute("PRAGMA table_info(danh_muc_thuoc)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'gia_thuoc' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE danh_muc_thuoc ADD COLUMN gia_thuoc REAL DEFAULT 0")
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nhap_thuoc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay TEXT,
            ma_thuoc TEXT,
            ten_thuoc TEXT,
            don_vi TEXT,
            so_luong_nhap INTEGER,
            FOREIGN KEY (ma_thuoc) REFERENCES danh_muc_thuoc(ma_thuoc)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_don_thuoc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            don_thuoc_id INTEGER NOT NULL,
            ma_thuoc TEXT,
            ten_thuoc TEXT NOT NULL,
            so_luong INTEGER NOT NULL,
            don_vi TEXT,
            sang TEXT,
            trua TEXT,
            chieu TEXT, 
            toi TEXT,
            lieu_dung TEXT,
            ghi_chu TEXT,
            FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id) ON DELETE CASCADE,
            FOREIGN KEY (ma_thuoc) REFERENCES danh_muc_thuoc(ma_thuoc)
        )
    """)

    # Các bảng mẫu đơn
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS don_mau (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_mau TEXT,
            ngay_tao TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_don_mau (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            don_mau_id INTEGER NOT NULL,
            ma_thuoc TEXT,
            ten_thuoc TEXT NOT NULL,
            so_luong INTEGER NOT NULL,
            don_vi TEXT,
            sang TEXT,
            trua TEXT,
            chieu TEXT,
            toi TEXT,
            lieu_dung TEXT,
            ghi_chu TEXT,
            FOREIGN KEY (don_mau_id) REFERENCES don_mau(id) ON DELETE CASCADE
        )
    """)

    # Đơn thuốc bổ sung
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS don_thuoc_bo_sung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phieu_kham_id INTEGER NOT NULL,
            ngay_ke TEXT NOT NULL,
            so_ngay INTEGER,
            ngay_tai_kham TEXT,
            tong_tien REAL DEFAULT 0,
            loai_don TEXT,
            chan_doan TEXT,
            di_ung_thuoc TEXT,
            loi_dan TEXT,
            bac_si TEXT,
            quay_thuoc TEXT,
            nguoi_lap_phieu TEXT,
            FOREIGN KEY (phieu_kham_id) REFERENCES phieu_kham(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_don_thuoc_bo_sung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            don_thuoc_bo_sung_id INTEGER NOT NULL,
            ma_thuoc TEXT,
            ten_thuoc TEXT NOT NULL,
            so_luong INTEGER NOT NULL,
            don_vi TEXT,
            sang TEXT,
            trua TEXT,
            chieu TEXT,
            toi TEXT,
            lieu_dung TEXT,
            ghi_chu TEXT,
            FOREIGN KEY (don_thuoc_bo_sung_id) REFERENCES don_thuoc_bo_sung(id) ON DELETE CASCADE,
            FOREIGN KEY (ma_thuoc) REFERENCES danh_muc_thuoc(ma_thuoc)
        )
    """)

    # Bảng Users và Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    ''')
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, login_time TEXT, logout_time TEXT)")

    # Bảng Dịch Vụ (cho ChiDinhDichVu.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dich_vu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_dich_vu TEXT,
            don_gia REAL
        )
    """)

    conn.commit()

    # --- DATA SEEDING ---
    # 1. Tạo admin
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        try:
            create_user('admin', 'admin', role='admin')
            print("Đã tạo user 'admin' mặc định.")
        except Exception:
            pass

    # 2. Tạo thuốc mẫu
    cursor.execute("SELECT COUNT(*) FROM danh_muc_thuoc")
    if cursor.fetchone()[0] == 0:
        sample_drugs = [
            ("10-417", "ABc", "viên", 10),
            ("10-23", "acyclovir 200", "viên", 20),
            ("10-134", "adalat", "viên", 20),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO danh_muc_thuoc (ma_thuoc, ten_thuoc, don_vi, ton_kho) VALUES (?, ?, ?, ?)",
            sample_drugs)
        conn.commit()

    # 3. Tạo dịch vụ mẫu (Quan trọng cho ChiDinhDichVu.py)
    cursor.execute("SELECT COUNT(*) FROM dich_vu")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO dich_vu (ten_dich_vu, don_gia) VALUES (?, ?)", [
            ("Khám tổng quát", 50000), ("Siêu âm", 150000), ("Xét nghiệm máu", 80000)
        ])
        conn.commit()

    conn.close()


def add_payment(loai, mo_ta, so_tien, ngay=None):
    if ngay is None:
        ngay = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO thanh_toan (ngay, loai, mo_ta, so_tien) VALUES (?, ?, ?, ?)",
                    (ngay, loai, mo_ta, so_tien))
        conn.commit()
    finally:
        conn.close()


# --- User Auth Helpers ---
def _hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"


def _verify_password(stored: str, password: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split('$')
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return secrets.compare_digest(dk, expected)
    except Exception:
        return False


def create_user(username: str, password: str, role: str = 'user') -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        pw = _hash_password(password)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    (username, pw, role, now))
        conn.commit()
        return True
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        r = cur.fetchone()
        if not r: return False
        return _verify_password(r[0], password)
    finally:
        conn.close()


def get_user_role(username: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE username = ?", (username,))
        r = cur.fetchone()
        return r[0] if r else ''
    finally:
        conn.close()


def start_user_session(username: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO user_sessions (username, login_time) VALUES (?, ?)", (username, now))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def end_user_session(session_id: int) -> None:
    if not session_id: return
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("UPDATE user_sessions SET logout_time = ? WHERE id = ?", (now, session_id))
        conn.commit()
    finally:
        conn.close()


def get_sessions_by_role(role: str, limit: int = 500):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username FROM users WHERE role = ?", (role,))
        users = [r[0] for r in cur.fetchall()]
        if not users: return []
        q = f"SELECT username, login_time, logout_time FROM user_sessions WHERE username IN ({','.join(['?'] * len(users))}) ORDER BY id DESC LIMIT ?"
        params = users + [limit]
        cur.execute(q, params)
        return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("✅ Database và các bảng đã được tạo thành công!")