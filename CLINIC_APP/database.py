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
    # Bảng bác sĩ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bac_si (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            chuyen_khoa TEXT
        )
    """)

    # New unified staff table (nhan_su) to support multiple roles: Bác sĩ, Tiếp tân, Dược sĩ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nhan_su (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            chuc_vu TEXT NOT NULL DEFAULT 'Bác sĩ',
            phong_kham TEXT
        )
    """)
    
    # Migration: if nhan_su has old 'chuyen_khoa' column, rename it to 'phong_kham'
    try:
        cursor.execute("PRAGMA table_info(nhan_su)")
        cols = [r[1] for r in cursor.fetchall()]
        if 'chuyen_khoa' in cols and 'phong_kham' not in cols:
            print("Migrating nhan_su: renaming chuyen_khoa → phong_kham...")
            conn.execute('BEGIN')
            cursor.execute("""
                CREATE TABLE nhan_su_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ten TEXT NOT NULL,
                    chuc_vu TEXT NOT NULL DEFAULT 'Bác sĩ',
                    phong_kham TEXT
                )
            """)
            cursor.execute("""
                INSERT INTO nhan_su_new (id, ten, chuc_vu, phong_kham)
                SELECT id, ten, chuc_vu, chuyen_khoa FROM nhan_su
            """)
            cursor.execute("DROP TABLE nhan_su")
            cursor.execute("ALTER TABLE nhan_su_new RENAME TO nhan_su")
            conn.commit()
            print("✅ Migration complete: nhan_su column renamed")
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"⚠️ Migration warning: {e}")
    
    # If nhan_su is empty but bac_si has data, migrate existing doctors into nhan_su
    try:
        cursor.execute("SELECT COUNT(*) FROM nhan_su")
        cnt_n = cursor.fetchone()[0]
        if cnt_n == 0:
            cursor.execute("SELECT COUNT(*) FROM bac_si")
            cnt_b = cursor.fetchone()[0]
            if cnt_b > 0:
                cursor.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) SELECT ten, 'Bác sĩ', chuyen_khoa FROM bac_si")
                print(f"Migrated {cnt_b} rows from bac_si to nhan_su")
    except Exception:
        # If any error (e.g., bac_si doesn't exist), ignore and continue
        pass

    # Bảng phòng khám
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phong_kham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            vi_tri TEXT
        )
    """)

    # Không tạo dữ liệu mẫu - cho phép người dùng nhập thông tin thực vào
    # Bảng lịch hẹn (đặt lịch khám)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lich_hen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benh_nhan_id INTEGER,
            ho_ten TEXT NOT NULL,
            ngay_gio TEXT NOT NULL,
            bac_si TEXT,
            loai_kham TEXT,
            ghi_chu TEXT,
            trang_thai TEXT DEFAULT 'chờ duyệt',
            FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
        )
    """)

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
    # Nếu thiếu cột chieu_cao (phiên bản cũ của DB), thêm vào
    if 'chieu_cao' not in existing_cols:
        try:
            cursor.execute("ALTER TABLE tiep_don ADD COLUMN chieu_cao REAL")
            print("Đã thêm cột 'chieu_cao' vào bảng tiep_don")
        except Exception:
            pass
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

    # Đảm bảo cột chieu_cao có trong chi_tiet_phieu_kham (migration cho DB cũ)
    cursor.execute("PRAGMA table_info(chi_tiet_phieu_kham)")
    _existing = [r[1] for r in cursor.fetchall()]
    if 'chieu_cao' not in _existing:
        try:
            cursor.execute("ALTER TABLE chi_tiet_phieu_kham ADD COLUMN chieu_cao REAL")
            print("Đã thêm cột 'chieu_cao' vào bảng chi_tiet_phieu_kham")
        except Exception:
            pass

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
            da_xuat INTEGER DEFAULT 0,
            xuat_boi_user_id INTEGER,
            ngay_xuat TEXT,
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

    # Migration: ensure don_mau has columns expected by forms/don_thuoc.py
    cursor.execute("PRAGMA table_info(don_mau)")
    _cols = [r[1] for r in cursor.fetchall()]
    # Add commonly referenced columns if missing
    if 'chan_doan' not in _cols:
        try:
            cursor.execute("ALTER TABLE don_mau ADD COLUMN chan_doan TEXT")
            print("Đã thêm cột 'chan_doan' vào bảng don_mau")
        except Exception:
            pass
    if 'loi_dan' not in _cols:
        try:
            cursor.execute("ALTER TABLE don_mau ADD COLUMN loi_dan TEXT")
            print("Đã thêm cột 'loi_dan' vào bảng don_mau")
        except Exception:
            pass
    if 'bac_si' not in _cols:
        try:
            cursor.execute("ALTER TABLE don_mau ADD COLUMN bac_si TEXT")
            print("Đã thêm cột 'bac_si' vào bảng don_mau")
        except Exception:
            pass
    if 'quay_thuoc' not in _cols:
        try:
            cursor.execute("ALTER TABLE don_mau ADD COLUMN quay_thuoc TEXT")
            print("Đã thêm cột 'quay_thuoc' vào bảng don_mau")
        except Exception:
            pass
    if 'nguoi_lap_phieu' not in _cols:
        try:
            cursor.execute("ALTER TABLE don_mau ADD COLUMN nguoi_lap_phieu TEXT")
            print("Đã thêm cột 'nguoi_lap_phieu' vào bảng don_mau")
        except Exception:
            pass

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

    # Migration: ensure don_thuoc has dispensing columns
    cursor.execute("PRAGMA table_info(don_thuoc)")
    _don_cols = [r[1] for r in cursor.fetchall()]
    if 'da_xuat' not in _don_cols:
        try:
            cursor.execute("ALTER TABLE don_thuoc ADD COLUMN da_xuat INTEGER DEFAULT 0")
            print("Đã thêm cột 'da_xuat' vào bảng don_thuoc")
        except Exception:
            pass
    if 'xuat_boi_user_id' not in _don_cols:
        try:
            cursor.execute("ALTER TABLE don_thuoc ADD COLUMN xuat_boi_user_id INTEGER")
            print("Đã thêm cột 'xuat_boi_user_id' vào bảng don_thuoc")
        except Exception:
            pass
    if 'ngay_xuat' not in _don_cols:
        try:
            cursor.execute("ALTER TABLE don_thuoc ADD COLUMN ngay_xuat TEXT")
            print("Đã thêm cột 'ngay_xuat' vào bảng don_thuoc")
        except Exception:
            pass

    # Migration: ensure don_thuoc_bo_sung has xuat_thuoc column
    cursor.execute("PRAGMA table_info(don_thuoc_bo_sung)")
    _don_bo_sung_cols = [r[1] for r in cursor.fetchall()]
    if 'xuat_thuoc' not in _don_bo_sung_cols:
        try:
            cursor.execute("ALTER TABLE don_thuoc_bo_sung ADD COLUMN xuat_thuoc INTEGER DEFAULT 0")
            print("Đã thêm cột 'xuat_thuoc' vào bảng don_thuoc_bo_sung")
        except Exception as e:
            print(f"Lỗi khi thêm cột 'xuat_thuoc': {e}")
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

    # Bảng lịch sử xuất thuốc
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lich_su_xuat_thuoc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            don_thuoc_id INTEGER NOT NULL,
            dac_si TEXT,
            ho_ten_benh_nhan TEXT,
            so_cccd TEXT,
            xuat_boi TEXT NOT NULL,
            thoi_gian_xuat TEXT NOT NULL,
            ghi_chu TEXT,
            FOREIGN KEY (don_thuoc_id) REFERENCES don_thuoc(id) ON DELETE CASCADE
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
            created_at TEXT,
            full_name TEXT
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

    # Bảng tiếp tân (receptionist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tiep_tan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            user_id INTEGER UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()

    # Backup and drop legacy tables `bac_si` and `tiep_tan` if they exist.
    # We export CSV backups into data/backups for safety before dropping.
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'data', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for tbl in ('bac_si', 'tiep_tan'):
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
                if cursor.fetchone():
                    # export to CSV
                    cursor.execute(f"SELECT * FROM {tbl}")
                    rows = cursor.fetchall()
                    cols = [d[0] for d in cursor.description] if cursor.description else []
                    if rows:
                        out_path = os.path.join(backup_dir, f"{tbl}_backup_{timestamp}.csv")
                        try:
                            import csv as _csv
                            with open(out_path, 'w', newline='', encoding='utf-8') as f:
                                writer = _csv.writer(f)
                                writer.writerow(cols)
                                writer.writerows(rows)
                        except Exception:
                            pass
                    # drop table
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
                        conn.commit()
                    except Exception:
                        pass
            except Exception:
                # ignore errors per-table and continue with next table
                pass
    except Exception:
        # best-effort backup/drop; ignore failures
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
    
    # Migration: Rename phong_kham to loai_kham in lich_hen table
    cursor.execute("PRAGMA table_info(lich_hen)")
    existing_cols_lich_hen = [r[1] for r in cursor.fetchall()]
    
    if 'phong_kham' in existing_cols_lich_hen and 'loai_kham' not in existing_cols_lich_hen:
        try:
            # SQLite doesn't support direct ALTER COLUMN RENAME in older versions
            # Use CREATE TABLE AS SELECT approach
            cursor.execute("""
                CREATE TABLE lich_hen_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benh_nhan_id INTEGER,
                    ho_ten TEXT NOT NULL,
                    ngay_gio TEXT NOT NULL,
                    bac_si TEXT,
                    loai_kham TEXT,
                    ghi_chu TEXT,
                    trang_thai TEXT DEFAULT 'chờ duyệt',
                    FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
                )
            """)
            cursor.execute("""
                INSERT INTO lich_hen_new (id, benh_nhan_id, ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu, trang_thai)
                SELECT id, benh_nhan_id, ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai FROM lich_hen
            """)
            cursor.execute("DROP TABLE lich_hen")
            cursor.execute("ALTER TABLE lich_hen_new RENAME TO lich_hen")
            conn.commit()
            print("✅ Đã migrate cột phong_kham → loai_kham trong bảng lich_hen")
        except Exception as e:
            print(f"⚠️ Lỗi khi migrate lich_hen: {e}")
        
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


def sync_users_to_nhan_su():
    """Ensure users with staff roles in `users` table are present in `nhan_su`.

    This is a best-effort sync: it maps known role codes to display roles
    and inserts a `nhan_su` row if one with same name+role doesn't exist.
    """
    role_map = {
        'bacsi': 'Bác sĩ',
        'tieptan': 'Tiếp tân',
        'duocsi': 'Dược sĩ',
        'doctor': 'Bác sĩ',
        'reception': 'Tiếp tân'
    }
    # normalize role keys (remove non-alphanumeric and lowercase) before lookup
    conn = get_connection()
    cur = conn.cursor()
    try:
        try:
            cur.execute("SELECT username, role, full_name FROM users")
            users = cur.fetchall()
        except Exception:
            # users table might not exist or full_name column missing
            try:
                cur.execute("SELECT username, role FROM users")
                users = [(r[0], r[1], None) for r in cur.fetchall()]
            except Exception:
                return

        for username, role, full_name in users:
            # normalize role string: remove non-alphanumeric and lowercase
            role_norm = ''.join(ch for ch in (role or '').lower() if ch.isalnum())
            mapped = role_map.get(role_norm)
            if not mapped:
                continue
            display_name = full_name if full_name else username
            try:
                cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = ?", (display_name, mapped))
                if cur.fetchone():
                    continue
                cur.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, ?, ?)", (display_name, mapped, None))
            except Exception:
                # ignore insertion errors and continue
                continue
        conn.commit()
    finally:
        conn.close()


def get_prescriptions_for_patient(benh_nhan_id: int):
    """Return all prescriptions (don_thuoc) for a given patient id with their items.

    Returns list of dicts: {id, phieu_kham_id, ngay_ke, so_ngay, tong_tien, bac_si, da_xuat, ngay_xuat, items:[{ten_thuoc, ma_thuoc, so_luong, don_vi}]}
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        q = """
            SELECT dt.id, dt.phieu_kham_id, dt.ngay_ke, dt.so_ngay, dt.tong_tien, dt.bac_si, dt.da_xuat, dt.ngay_xuat
            FROM don_thuoc dt
            JOIN phieu_kham pk ON dt.phieu_kham_id = pk.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY dt.ngay_ke DESC
        """
        cur.execute(q, (benh_nhan_id,))
        rows = cur.fetchall()
        results = []
        for r in rows:
            don_id = r[0]
            cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong, don_vi FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (don_id,))
            items = [dict(ma_thuoc=i[0], ten_thuoc=i[1], so_luong=i[2], don_vi=i[3]) for i in cur.fetchall()]
            results.append({
                'id': don_id,
                'phieu_kham_id': r[1],
                'ngay_ke': r[2],
                'so_ngay': r[3],
                'tong_tien': r[4],
                'bac_si': r[5],
                'da_xuat': bool(r[6]) if r[6] is not None else False,
                'ngay_xuat': r[7],
                'items': items,
            })
        return results
    finally:
        conn.close()


def mark_prescription_dispensed(don_thuoc_id: int, dispensed_by_username: str = None, dispensed_at: str = None) -> bool:
    """Mark a prescription as dispensed: set da_xuat=1, xuat_boi_user_id (if username provided), ngay_xuat.
    Also decrement stock in danh_muc_thuoc according to chi_tiet_don_thuoc quantities.
    Returns True on success.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        user_id = None
        if dispensed_by_username:
            try:
                cur.execute("SELECT id FROM users WHERE username = ?", (dispensed_by_username,))
                r = cur.fetchone()
                if r:
                    user_id = r[0]
            except Exception:
                user_id = None

        if not dispensed_at:
            dispensed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update prescription
        if user_id:
            cur.execute("UPDATE don_thuoc SET da_xuat = 1, xuat_boi_user_id = ?, ngay_xuat = ? WHERE id = ?", (user_id, dispensed_at, don_thuoc_id))
        else:
            cur.execute("UPDATE don_thuoc SET da_xuat = 1, ngay_xuat = ? WHERE id = ?", (dispensed_at, don_thuoc_id))

        # Decrement stock
        cur.execute("SELECT ma_thuoc, so_luong FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (don_thuoc_id,))
        for ma_thuoc, so_luong in cur.fetchall():
            if not ma_thuoc:
                continue
            try:
                cur.execute("UPDATE danh_muc_thuoc SET ton_kho = COALESCE(ton_kho,0) - ? WHERE ma_thuoc = ?", (so_luong or 0, ma_thuoc))
            except Exception:
                pass

        conn.commit()
        return True
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


def create_user(username: str, password: str, role: str = 'user', full_name: str = None) -> bool:
    """Create a new user. If role is 'bac_si' and full_name provided, optionally create a bac_si record.

    Note: full_name parameter was added to support saving doctor's real name when registering.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        pw = _hash_password(password)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Attempt to insert with full_name column if it exists
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at, full_name) VALUES (?, ?, ?, ?, ?)",
                (username, pw, role, now, full_name),
            )
        except Exception:
            # Fallback if full_name column does not exist
            cur.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, pw, role, now),
            )
        conn.commit()
        # If role corresponds to staff, insert into `nhan_su` so staff management picks it up
        try:
            # map common role codes to display names used in nhan_su.chuc_vu
            role_map = {
                'bacsi': 'Bác sĩ',
                'tieptan': 'Tiếp tân',
                'duocsi': 'Dược sĩ',
                'doctor': 'Bác sĩ',
                'reception': 'Tiếp tân'
            }
            import app_signals
            # normalize incoming role string (remove underscores/other non-alnum, lower)
            role_norm = ''.join(ch for ch in (role or '').lower() if ch.isalnum())
            mapped = role_map.get(role_norm)
            display_name = full_name if full_name else username
            if mapped:
                try:
                    cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = ?", (display_name, mapped))
                    if not cur.fetchone():
                        cur.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, ?, ?)", (display_name, mapped, None))
                except Exception:
                    # best-effort: ignore failure to insert into nhan_su
                    pass
            # Emit user_created signal for UI updates (emit even if not mapped)
            try:
                app_signals.app_signals.user_created.emit(username, role, display_name)
            except Exception:
                pass
        except Exception:
            pass
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


def get_user_fullname(username: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    try:
        try:
            cur.execute("SELECT full_name FROM users WHERE username = ?", (username,))
            r = cur.fetchone()
            return r[0] if r and r[0] else ''
        except Exception:
            return ''
    finally:
        conn.close()


def update_user_fullname(username: str, full_name: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
        except Exception:
            pass
        cur.execute("UPDATE users SET full_name = ? WHERE username = ?", (full_name, username))
        conn.commit()
        return True
    finally:
        conn.close()


def add_bac_si(ten: str, chuyen_khoa: str = None) -> bool:
    """Insert a doctor into `nhan_su` with chuc_vu='Bác sĩ' if not exists (by exact name)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = 'Bác sĩ'", (ten,))
        if cur.fetchone():
            return False
        cur.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, 'Bác sĩ', ?)", (ten, chuyen_khoa))
        conn.commit()
        return True
    finally:
        conn.close()


def bac_si_exists(ten: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = 'Bác sĩ'", (ten,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def add_tiep_tan(ten: str, username: str = None) -> bool:
    """Insert a receptionist into `nhan_su` with chuc_vu='Tiếp tân'. If username provided, use full_name if available."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        display_name = ten
        if username:
            try:
                cur.execute("SELECT full_name FROM users WHERE username = ?", (username,))
                r = cur.fetchone()
                if r and r[0]:
                    display_name = r[0]
            except Exception:
                pass
        cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = 'Tiếp tân'", (display_name,))
        if cur.fetchone():
            return False
        cur.execute("INSERT INTO nhan_su (ten, chuc_vu, phong_kham) VALUES (?, 'Tiếp tân', NULL)", (display_name,))
        conn.commit()
        return True
    finally:
        conn.close()


def tiep_tan_exists(ten: str = None, username: str = None) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        if username:
            try:
                cur.execute("SELECT full_name FROM users WHERE username = ?", (username,))
                r = cur.fetchone()
                if not r:
                    return False
                name = r[0] if r[0] else username
            except Exception:
                name = username
            cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = 'Tiếp tân'", (name,))
            return cur.fetchone() is not None
        if ten:
            cur.execute("SELECT id FROM nhan_su WHERE ten = ? AND chuc_vu = 'Tiếp tân'", (ten,))
            return cur.fetchone() is not None
        return False
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


def save_xuat_thuoc_history(don_thuoc_id: int, bac_si: str, ho_ten_benh_nhan: str, so_cccd: str, xuat_boi: str, ghi_chu: str = ""):
    """Lưu lịch sử xuất thuốc."""
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()
    try:
        thoi_gian_xuat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("""
            INSERT INTO lich_su_xuat_thuoc 
            (don_thuoc_id, dac_si, ho_ten_benh_nhan, so_cccd, xuat_boi, thoi_gian_xuat, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (don_thuoc_id, bac_si, ho_ten_benh_nhan, so_cccd, xuat_boi, thoi_gian_xuat, ghi_chu))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving xuat thuoc history: {e}")
        return False
    finally:
        conn.close()


def get_xuat_thuoc_history(limit: int = 100):
    """Lấy lịch sử xuất thuốc."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, don_thuoc_id, dac_si, ho_ten_benh_nhan, so_cccd, xuat_boi, thoi_gian_xuat, ghi_chu
            FROM lich_su_xuat_thuoc
            ORDER BY thoi_gian_xuat DESC
            LIMIT ?
        """, (limit,))
        return cur.fetchall()
    finally:
        conn.close()


def get_supplementary_prescriptions_for_patient(benh_nhan_id: int):
    """Return all supplementary prescriptions (don_thuoc_bo_sung) for a given patient id with their items.
    
    Returns list of dicts: {id, phieu_kham_id, ngay_ke, so_ngay, tong_tien, bac_si, xuat_thuoc, items:[{ten_thuoc, ma_thuoc, so_luong, don_vi}]}
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        q = """
            SELECT dtbs.id, dtbs.phieu_kham_id, dtbs.ngay_ke, dtbs.so_ngay, dtbs.tong_tien, dtbs.bac_si, COALESCE(dtbs.xuat_thuoc, 0) as xuat_thuoc
            FROM don_thuoc_bo_sung dtbs
            JOIN phieu_kham pk ON dtbs.phieu_kham_id = pk.id
            WHERE pk.benh_nhan_id = ?
            ORDER BY dtbs.ngay_ke DESC
        """
        cur.execute(q, (benh_nhan_id,))
        rows = cur.fetchall()
        results = []
        for r in rows:
            don_id = r[0]
            cur.execute("SELECT ma_thuoc, ten_thuoc, so_luong, don_vi FROM chi_tiet_don_thuoc_bo_sung WHERE don_thuoc_bo_sung_id = ?", (don_id,))
            items = [dict(ma_thuoc=i[0], ten_thuoc=i[1], so_luong=i[2], don_vi=i[3]) for i in cur.fetchall()]
            results.append({
                'id': don_id,
                'phieu_kham_id': r[1],
                'ngay_ke': r[2],
                'so_ngay': r[3],
                'tong_tien': r[4],
                'bac_si': r[5],
                'xuat_thuoc': bool(r[6]) if r[6] is not None else False,
                'items': items,
            })
        return results
    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("✅ Database và các bảng đã được tạo thành công!")

