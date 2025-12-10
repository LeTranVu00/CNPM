from PyQt5.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    # emits benh_nhan_id (int)
    patient_selected = pyqtSignal(int)
    # emits benh_nhan_id (int) khi có đơn thuốc bổ sung được in
    don_bo_sung_printed = pyqtSignal(int)

app_signals = AppSignals()

# Global state to track current patient
current_patient_id = None
