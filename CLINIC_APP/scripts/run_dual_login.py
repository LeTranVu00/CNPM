import subprocess
import os

def run_dual_login():
    """
    Chạy đồng thời hai phiên bản ứng dụng:
    - Một phiên đăng nhập với vai trò tiếp tân.
    - Một phiên đăng nhập với vai trò bác sĩ.
    """
    # Đường dẫn đến Python interpreter
    python_executable = os.path.join(os.environ['LOCALAPPDATA'], "Programs", "Python", "Python312", "python.exe")

    # Đường dẫn đến file main.py
    app_path = os.path.abspath("c:/clinic_app/main.py")

    # Chạy hai tiến trình với các tham số khác nhau
    try:
        subprocess.Popen([python_executable, app_path, "--role", "tieptan"], shell=True)
        subprocess.Popen([python_executable, app_path, "--role", "bac_si"], shell=True)
        print("Đã khởi chạy hai phiên bản ứng dụng: tiếp tân và bác sĩ.")
    except Exception as e:
        print(f"Lỗi khi chạy ứng dụng: {e}")

if __name__ == "__main__":
    run_dual_login()