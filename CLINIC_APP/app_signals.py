from PyQt5.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Global application signals used for cross-form updates."""
    data_changed = pyqtSignal()
    medicine_exported = pyqtSignal()
    # Signal được emit khi xuất thuốc thành công (dùng để cập nhật doanh thu)
    medication_dispensed = pyqtSignal()
    # Emitted when a new user account is created: (username, role, full_name)
    user_created = pyqtSignal(str, str, str)


app_signals = AppSignals()
