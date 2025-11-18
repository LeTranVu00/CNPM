# main.py <--- [LỖI CŨ] Dòng này là tên file, không được để trong code. Đã xóa/comment.

from main_app import MainApp
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # [LƯU Ý] Bypass login và mở thẳng MainApp với quyền admin để test
    # Nếu muốn chạy thật thì sửa thành gọi LoginWindow()
    window = MainApp(username="admin")
    window.show()

    sys.exit(app.exec_())