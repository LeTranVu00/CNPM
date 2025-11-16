import os
import sqlite3
from datetime import datetime
import os as _os
import hashlib
import binascii
import secrets

DB_NAME = os.path.join(os.path.dirname(__file__), "data", "clinic.db")


def get_connection():
    """
    Tạo kết nối đến database với các thiết lập tối ưu:
    - timeout: chờ tối đa 20 giây nếu database bị khóa
    - isolation_level: None để tự động commit
    - check_same_thread: False để cho phép truy cập từ nhiều thread
    """
    try:
        conn = sqlite3.connect(DB_NAME, 
                             timeout=20.0,
                             isolation_level=None,
                             check_same_thread=False)
        # Enable WAL mode để tối ưu hiệu suất và tránh lock
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    except sqlite3.Error as e:
        print(f"Lỗi khi kết nối database: {e}")
        raise


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Tạo bảng benh_nhan (thông tin bệnh nhân)
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
    # Nếu bảng đã tồn tại trước khi thêm cột mới, kiểm tra và thêm cột ghi_chu_kham nếu cần
    cursor.execute("PRAGMA table_info(chi_tiet_phieu_kham)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'ghi_chu_kham' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_tiet_phieu_kham ADD COLUMN ghi_chu_kham TEXT")
            print("Đã thêm cột 'ghi_chu_kham' vào bảng chi_tiet_phieu_kham")
        except Exception:
            # Nếu ALTER TABLE không khả dụng (rất hiếm), bỏ qua và để CREATE TABLE xử lý cho lần tạo mới
            pass
    # kiểm tra và thêm cột chidinh_cls nếu cần
    cursor.execute("PRAGMA table_info(chi_tiet_phieu_kham)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'chidinh_cls' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE chi_tiet_phieu_kham ADD COLUMN chidinh_cls TEXT")
            print("Đã thêm cột 'chidinh_cls' vào bảng chi_tiet_phieu_kham")
        except Exception:
            pass
    
    # Kiểm tra và thêm cột gia_thuoc vào danh_muc_thuoc nếu cần
    cursor.execute("PRAGMA table_info(danh_muc_thuoc)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'gia_thuoc' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE danh_muc_thuoc ADD COLUMN gia_thuoc REAL DEFAULT 0")
            print("Đã thêm cột 'gia_thuoc' vào bảng danh_muc_thuoc")
        except Exception:
            pass

# Bảng phiếu khám
    # Create phieu_kham WITHOUT the old 'chan_doan' column (we keep diagnosis in chi_dinh)
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

    # Migration: if an existing phieu_kham table had a 'chan_doan' column, remove it
    try:
        cursor.execute("PRAGMA table_info(phieu_kham)")
        pk_cols = [r[1] for r in cursor.fetchall()]
        if 'chan_doan' in pk_cols:
            print("Found legacy column 'chan_doan' in phieu_kham — migrating to remove it...")
            # Create a new table without the chan_doan column, copy data, replace table
            conn.execute('BEGIN')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phieu_kham_new (
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
            # Copy existing data, ignoring 'chan_doan'
            cursor.execute("""
                INSERT INTO phieu_kham_new (id, so_phieu, benh_nhan_id, ngay_lap, bac_si, phong_kham, tong_tien)
                SELECT id, so_phieu, benh_nhan_id, ngay_lap, bac_si, phong_kham, tong_tien FROM phieu_kham
            """)
            cursor.execute("DROP TABLE phieu_kham")
            cursor.execute("ALTER TABLE phieu_kham_new RENAME TO phieu_kham")
            conn.commit()
            print("Migration complete: removed 'chan_doan' from phieu_kham")
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"Warning: phieu_kham migration failed or unnecessary: {e}")

    # Bảng chỉ định dịch vụ
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

    # Kiểm tra và thêm cột kham_lam_sang và chan_doan vào chi_dinh nếu cần
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

    # Tạo bảng tiep_don (tiếp đón khám)
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
    
    # Kiểm tra và thêm các cột nhip_tho, nhip_tim vào tiep_don nếu cần
    cursor.execute("PRAGMA table_info(tiep_don)")
    existing_cols = [r[1] for r in cursor.fetchall()]
    if 'nhip_tho' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN nhip_tho INTEGER")
            print("Đã thêm cột 'nhip_tho' vào bảng tiep_don")
        except Exception:
            pass
    if 'nhip_tim' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN nhip_tim INTEGER")
            print("Đã thêm cột 'nhip_tim' vào bảng tiep_don")
        except Exception:
            pass
    # Thêm cột da_kham để đánh dấu đã khám/hủy khám nếu cần
    if 'da_kham' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN da_kham INTEGER DEFAULT 0")
            print("Đã thêm cột 'da_kham' vào bảng tiep_don")
        except Exception:
            pass

    # Bảng chi tiết phiếu khám
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

    # Bảng thanh_toan (ghi nhận thu tiền từ dịch vụ / thuốc)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thanh_toan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay TEXT,
            loai TEXT,
            mo_ta TEXT,
            so_tien REAL
        )
    """)

    # Bảng đơn thuốc
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

    # Bảng danh mục ICD10
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS danh_muc_icd10 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL
        )
    """)

    # Bảng danh mục thuốc
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

    # Bảng lịch sử nhập thuốc
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

    # Bảng chi tiết đơn thuốc
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
    
    # Bảng mẫu đơn (templates)
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

    # Bảng đơn thuốc bổ sung
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

    # Bảng chi tiết đơn thuốc bổ sung
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
    conn.commit()

    # Bảng users để quản lý đăng nhập
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    ''')
    conn.commit()

    # Nếu chưa có user nào, tạo user admin mặc định (mật khẩu 'admin')
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        try:
            # tạo admin mặc định — người dùng nên đổi mật khẩu khi lần đầu đăng nhập
            create_user('admin', 'admin', role='admin')
            print("Đã tạo user 'admin' mặc định với mật khẩu 'admin'. Vui lòng đổi mật khẩu ngay.")
        except Exception:
            pass

    # Thêm một số thuốc mẫu nếu bảng danh_muc_thuoc trống (giúp test UI chọn thuốc)
    cursor.execute("SELECT COUNT(*) FROM danh_muc_thuoc")
    dm_count = cursor.fetchone()[0]
    if dm_count == 0:
        sample_drugs = [
            ("10-417", "ABc", "viên", 10),
            ("10-493", "Acetazolamid 0,25gr", "viên", 30),
            ("10-494", "Acetazolamid 0,25gr", "viên", 40),
            ("10-495", "Acetazolamid 0,25gr", "viên", 50),
            ("10-23", "acyclovir 200", "viên", 20),
            ("10-134", "adalat", "viên", 20),
            ("10-278", "adrenalin 1mg", "ống", 80),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO danh_muc_thuoc (ma_thuoc, ten_thuoc, don_vi, ton_kho) VALUES (?, ?, ?, ?)",
            sample_drugs
        )
        conn.commit()

    # Thêm một số mã ICD10 mẫu nếu bảng danh_muc_icd10 trống
    cursor.execute("SELECT COUNT(*) FROM danh_muc_icd10")
    icd10_count = cursor.fetchone()[0]
    if icd10_count == 0:
        sample_icd10 = [
            ("J45", "Hen phế quản"),
            ("J06", "Nhiễm trùng đường hô hấp trên"),
            ("K29", "Viêm dạ dày"),
            ("M79", "Rối loạn mô mềm không phân loại ở nơi khác"),
            ("E78", "Rối loạn chuyển hóa lipoprotein và rối loạn chuyển hóa lipoprotein khác"),
            ("E11", "Bệnh tiểu đường type 2"),
            ("I10", "Tăng huyết áp (cao)"),
            ("E04", "Bệnh tuyến giáp khác"),
            ("J00", "Viêm họng cấp"),
            ("M54", "Đau lưng"),
            ("H66", "Viêm tai giữa"),
            ("B06", "Rubella"),
            ("F41", "Rối loạn lo âu"),
            ("N39", "Các rối loạn về tiểu tiện khác"),
            ("L20", "Viêm da dị ứng"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO danh_muc_icd10 (code, description) VALUES (?, ?)",
            sample_icd10
        )
        conn.commit()

    # 🧹 Chỉ reset ID nếu database trống (để không ảnh hưởng dữ liệu thật)
    cursor.execute("SELECT COUNT(*) FROM benh_nhan")
    benhnhan_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tiep_don")
    tiepdon_count = cursor.fetchone()[0]

    if benhnhan_count == 0 and tiepdon_count == 0:
        cursor.execute("DELETE FROM sqlite_sequence;")
        print("🔁 Đã reset lại ID tự động vì database đang trống.")
        
    conn.close()


    # --- Ensure user_sessions table exists for login/logout tracking ---
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, login_time TEXT, logout_time TEXT)")
        conn.commit()
        conn.close()
    except Exception:
        pass


def add_payment(loai, mo_ta, so_tien, ngay=None):
    """Thêm bản ghi thanh toán vào bảng `thanh_toan` (helper để gọi từ các form khác).

    loai: str (Ví dụ: 'Thuốc' hoặc 'Dịch vụ')
    mo_ta: str
    so_tien: float
    ngay: optional datetime string (format 'yyyy-MM-dd HH:MM:SS')
    """
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


# --- User management helpers (password hashing using PBKDF2) ---
def _hash_password(password: str, salt: bytes = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256. Returns hex(salt)$hex(hash)."""
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
        if not r:
            return False
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
    """Insert a login record and return session id."""
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
    """Set logout_time for given session id."""
    if not session_id:
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("UPDATE user_sessions SET logout_time = ? WHERE id = ?", (now, session_id))
        conn.commit()
    finally:
        conn.close()


def get_user_sessions(username: str, limit: int = 100):
    """Return list of sessions (login_time, logout_time) for user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, login_time, logout_time FROM user_sessions WHERE username = ? ORDER BY id DESC LIMIT ?", (username, limit))
        return cur.fetchall()
    finally:
        conn.close()


def get_sessions_by_role(role: str, limit: int = 500):
    """Return sessions for all users with given role."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT username FROM users WHERE role = ?", (role,))
        users = [r[0] for r in cur.fetchall()]
        if not users:
            return []
        q = f"SELECT username, login_time, logout_time FROM user_sessions WHERE username IN ({','.join(['?']*len(users))}) ORDER BY id DESC LIMIT ?"
        params = users + [limit]
        cur.execute(q, params)
        return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("✅ Database và các bảng đã được tạo thành công!")
