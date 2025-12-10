#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để tạo các tài khoản mẫu với các role khác nhau
"""

from database import initialize_database, create_user

# Khởi tạo database
initialize_database()

# Tạo các tài khoản mẫu
users = [
    ("admin", "admin", "admin"),           # Admin
    ("bacsi", "bacsi123", "bac_si"),       # Bác sĩ
    ("tieptan", "tieptan123", "tiep_tan")  # Tiếp tân
]

print("=" * 50)
print("Tạo tài khoản mẫu...")
print("=" * 50)

for username, password, role in users:
    try:
        create_user(username, password, role=role)
        print(f"✅ Tạo thành công: {username} (Role: {role})")
    except Exception as e:
        print(f"⚠️ Tài khoản {username} đã tồn tại hoặc lỗi: {e}")

print("=" * 50)
print("Tài khoản mẫu:")
print("  - admin / admin (Admin)")
print("  - bacsi / bacsi123 (Bác sĩ)")
print("  - tieptan / tieptan123 (Tiếp tân)")
print("=" * 50)
