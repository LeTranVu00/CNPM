import os
import sqlite3

DB_NAME = os.path.join(os.path.dirname(__file__), "data", "clinic.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


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
            doi_tuong TEXT,
            nghe_nghiep TEXT,
            nguoi_gioi_thieu TEXT,
            loai_kham TEXT
        )
    """)

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
            loai_kham TEXT,
            tien_kham REAL,
            nv_tiepdon TEXT,
            cap_cuu INTEGER DEFAULT 0,
            huyet_ap TEXT,
            nhiet_do REAL,
            chieu_cao REAL,
            can_nang REAL,
            FOREIGN KEY (benh_nhan_id) REFERENCES benh_nhan(id)
        )
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("✅ Database và các bảng đã được tạo thành công!")
