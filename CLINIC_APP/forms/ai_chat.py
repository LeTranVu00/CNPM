import os
import requests
import time
import random
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Callable, Optional
from dotenv import load_dotenv
load_dotenv()


class AIWorker(QThread):
    result = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, prompt: str, model: str = "gpt-4o-mini", max_retries: int = 6, delay: float = 2.0):
        """
        max_retries: số lần thử khi gặp 429
        delay: thời gian chờ giữa các lần retry (giây)
        """
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.max_retries = max_retries
        self.delay = delay

    def run(self):
        try:
            # pass a callback so query_ai can emit retry/status messages
            resp = query_ai(
                self.prompt,
                model=self.model,
                max_retries=self.max_retries,
                delay=self.delay,
                status_callback=lambda s: self.status.emit(s),
            )
        except Exception as e:
            resp = f"Lỗi khi gọi AI: {e}"
        self.result.emit(resp)


def query_ai(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 5,
    delay: float = 2.5,
    status_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Gọi OpenAI Chat Completions với:
    - Retry + delay khi gặp 429 (sk-proj key)
    - Giảm max_tokens để tránh rate limit
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY chưa được thiết lập. Set biến môi trường `OPENAI_API_KEY` để gọi dịch vụ AI."

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Nếu người dùng đặt biến môi trường `OPENAI_PROJECT`, gửi header đó
    openai_project = os.environ.get("OPENAI_PROJECT")
    if openai_project:
        headers["OpenAI-Project"] = openai_project
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 130,  # giảm token để giảm trọng tải và khả năng bị rate-limit
        "temperature": 0.2,
    }

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            # Nếu server trả về Retry-After, sử dụng nó khi cần
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = float(retry_after)
                    except Exception:
                        wait = delay * (2 ** (attempt - 1))
                else:
                    # exponential backoff with small jitter
                    wait = delay * (2 ** (attempt - 1)) + random.uniform(0, 1)

                if attempt < max_retries:
                    if status_callback:
                        status_callback(f"Bị giới hạn (429). Chờ {wait:.1f}s, sẽ thử lại...")
                    time.sleep(wait)
                    continue
                else:
                    return "Quá nhiều request, vui lòng thử lại sau vài giây."

            r.raise_for_status()
            data = r.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            return "Không nhận được phản hồi từ dịch vụ AI."
        except requests.exceptions.HTTPError as e:
            # Trả về thông tin lỗi thay vì raise để UI có thể hiển thị thông báo rõ ràng
            status = getattr(e.response, 'status_code', None)
            text = getattr(e.response, 'text', str(e))
            return f"Lỗi HTTP {status}: {text}"
        except requests.exceptions.RequestException as e:
            # Lỗi kết nối/timeout
            if attempt < max_retries:
                wait = delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                if status_callback:
                    status_callback(f"Lỗi kết nối, chờ {wait:.1f}s trước khi thử lại...")
                time.sleep(wait)
                continue
            return f"Lỗi kết nối khi gọi AI: {e}"

    return "Không nhận được phản hồi từ dịch vụ AI."


# -----------------------
# Class AIChatDialog giữ nguyên như trước
# -----------------------
class AIChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI - Hỏi đáp phòng khám")
        self.setMinimumSize(700, 480)
        self._worker = None
        self._last_model = "gpt-4o-mini"
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout()
        lbl = QLabel("Hỏi AI")
        v.addWidget(lbl)
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setAcceptRichText(False)
        v.addWidget(self.history, 5)
        self.input = QTextEdit()
        self.input.setPlaceholderText("Hãy hỏi bất cứ điều gì")
        self.input.setMaximumHeight(120)
        v.addWidget(self.input)
        h = QHBoxLayout()
        self.btn_send = QPushButton("Gửi")
        self.btn_send.clicked.connect(self.on_send)
        h.addWidget(self.btn_send)
        self.btn_clear = QPushButton("Xóa")
        self.btn_clear.clicked.connect(self.on_clear)
        h.addWidget(self.btn_clear)
        self.btn_close = QPushButton("Đóng")
        self.btn_close.clicked.connect(self.close)
        h.addWidget(self.btn_close)
        v.addLayout(h)
        self.setLayout(v)

    def _on_status(self, text: str):
        # Hiển thị thông báo trạng thái tạm thời ở lịch sử dưới dạng AI (nhưng style khác)
        self.append_history("ai", text)

    def append_history(self, role: str, text: str):
        if role == "user":
            self.history.append(f"<b>Bạn:</b> {text}")
        else:
            self.history.append(f"<b>AI:</b> {text}")

    def on_clear(self):
        self.input.clear()

    def on_send(self):
        prompt = self.input.toPlainText().strip()
        if not prompt:
            QMessageBox.information(self, "Chưa nhập", "Vui lòng nhập câu hỏi trước khi gửi.")
            return
        self.append_history("user", prompt)
        self.input.clear()
        self.btn_send.setEnabled(False)
        self.btn_send.setText("Đang gửi...")
        self._worker = AIWorker(prompt, model=self._last_model)
        self._worker.result.connect(self._on_result)
        self._worker.status.connect(self._on_status)
        self._worker.finished.connect(self._on_finished_thread)
        self._worker.start()

    def _on_result(self, text: str):
        self.append_history("ai", text)

    def _on_finished_thread(self):
        try:
            self._worker.deleteLater()
        except Exception:
            pass
        self._worker = None
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Gửi")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dlg = AIChatDialog()
    dlg.show()
    sys.exit(app.exec_())
