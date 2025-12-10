from main_app import MainApp
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Bypass login and open MainApp directly with admin role for testing
    window = MainApp(username="admin")
    window.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        # Allow Ctrl+C in terminal to exit the GUI process gracefully during dev
        print("Interrupted by user (KeyboardInterrupt). Exiting...")
        sys.exit(0)
