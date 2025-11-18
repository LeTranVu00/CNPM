from PyQt5.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Global application signals used for cross-form updates."""

    # 🟢 SỬA: Thêm signal này vì ChiDinhDichVu.py và TiepDonKham.py cần dùng
    patient_selected = pyqtSignal(int)

    data_changed = pyqtSignal()
    medicine_exported = pyqtSignal()


app_signals = AppSignals()