from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QPushButton, QDialog)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import fitz  # PyMuPDF
import os

class PDFViewer(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Xem phiếu - {os.path.basename(file_path)}")
        self.resize(900, 700)
        
        # Layout chính
        main_layout = QVBoxLayout(self)
        
        # Scroll area cho nội dung PDF
        scroll = QScrollArea()
        container = QWidget()
        vbox = QVBoxLayout(container)

        # Mở file PDF và render từng trang thành ảnh
        self.doc = fitz.open(file_path)
        for page in self.doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # độ phân giải cao
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

            label = QLabel()
            label.setPixmap(QPixmap.fromImage(img))
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)

        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        
        # Thanh công cụ với các nút
        toolbar = QHBoxLayout()
        
        # Nút In
        self.print_btn = QPushButton("In phiếu")
        self.print_btn.clicked.connect(self.print_pdf)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 5px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1084E3;
            }
        """)
        
        # Nút Đóng
        self.close_btn = QPushButton("Đóng")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0078D7;
                border: 1px solid #0078D7;
                padding: 5px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E5F3FF;
            }
        """)
        
        toolbar.addStretch()
        toolbar.addWidget(self.print_btn)
        toolbar.addWidget(self.close_btn)
        main_layout.addLayout(toolbar)
        
    def print_pdf(self):
        """In file PDF"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            try:
                # Sử dụng Adobe Reader hoặc ứng dụng mặc định để in
                import os
                os.startfile(self.file_path, "print")
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Lỗi", f"Không thể in file: {str(e)}")
