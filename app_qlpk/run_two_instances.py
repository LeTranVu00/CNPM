#!/usr/bin/env python3
"""
Script để chạy 2 instance của ứng dụng cùng lúc.
Một instance cho bác sĩ, một instance cho tiếp tân.
"""

import sys
import subprocess
import time

def run_app_instance(instance_name):
    """Chạy một instance của main_app.py"""
    print(f"✓ Đang khởi động {instance_name}...")
    try:
        subprocess.Popen([sys.executable, "main.py"], cwd=r"c:\app_qlpk")
    except Exception as e:
        print(f"✗ Lỗi khi khởi động {instance_name}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Khởi động 2 instance của ứng dụng")
    print("=" * 60)
    print()
    
    # Chạy instance 1 (Bác sĩ)
    run_app_instance("Instance 1 - Bác sĩ")
    time.sleep(2)
    
    # Chạy instance 2 (Tiếp tân)
    run_app_instance("Instance 2 - Tiếp tân")
    time.sleep(1)
    
    print()
    print("=" * 60)
    print("Đã khởi động xong 2 instance!")
    print()
    print("Hướng dẫn đăng nhập:")
    print("  Instance 1: Đăng nhập với tài khoản bác sĩ")
    print("    Username: bacsi")
    print("    Password: bacsi123")
    print()
    print("  Instance 2: Đăng nhập với tài khoản tiếp tân")
    print("    Username: tieptan")
    print("    Password: tieptan123")
    print("=" * 60)
