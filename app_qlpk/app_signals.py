from PyQt5.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Global application signals used for cross-form updates."""
    data_changed = pyqtSignal()
    medicine_exported = pyqtSignal()


app_signals = AppSignals()
