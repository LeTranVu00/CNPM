#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa dữ liệu mẫu và chuẩn bị database cho dữ liệu thực
"""

from database import get_connection, initialize_database

def clear_sample_data():
    """Xóa tất cả dữ liệu từ các bảng chính."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Xóa dữ liệu từ các bảng (không xóa bảng)
        tables_to_clear = [
            'bac_si',
            'phong_kham',
            'benh_nhan',
            'phieu_kham',
            'chi_tiet_phieu_kham',
            'don_thuoc',
            'chi_tiet_don_thuoc',
            'don_thuoc_bo_sung',
            'chi_tiet_don_thuoc_bo_sung',
            'chi_dinh',
            'tiep_don',
            'lich_hen',
            'nhap_thuoc',
            'danh_muc_thuoc',
            'thanh_toan'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✓ Xóa dữ liệu bảng: {table}")
            except Exception as e:
                print(f"⚠ Lỗi xóa bảng {table}: {e}")
        
        conn.commit()
        print("\n" + "="*50)
        print("✓ Đã xóa tất cả dữ liệu mẫu")
        print("="*50)
        
    except Exception as e:
        print(f"✗ Lỗi: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*50)
    print("XÓA DỮ LIỆU MẪU")
    print("="*50)
    
    # Khởi tạo database trước
    initialize_database()
    
    confirm = input("\nBạn chắc chắn muốn xóa tất cả dữ liệu? (yes/no): ").strip().lower()
    if confirm == "yes":
        clear_sample_data()
        print("\nBây giờ bạn có thể:")
        print("1. Chạy ứng dụng (main.py)")
        print("2. Đăng nhập với tài khoản admin/admin")
        print("3. Sử dụng tab 'Quản lý Nhân Sự' để thêm bác sĩ")
        print("4. Sử dụng tab 'Quản lý Lịch Hẹn' để thêm lịch hẹn")
    else:
        print("Đã hủy!")
