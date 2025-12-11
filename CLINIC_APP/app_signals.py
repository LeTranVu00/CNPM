from PyQt5.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Các signal toàn cục của ứng dụng dùng để cập nhật giữa các form."""
    data_changed = pyqtSignal()
    medicine_exported = pyqtSignal()
    # Signal được phát khi xuất thuốc thành công (dùng để cập nhật doanh thu)
    medication_dispensed = pyqtSignal()
    # Được phát khi một tài khoản người dùng mới được tạo: (username, role, full_name)
    user_created = pyqtSignal(str, str, str)


app_signals = AppSignals()
