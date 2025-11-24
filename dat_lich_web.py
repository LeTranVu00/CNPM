from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'clinic.db')


def get_bacsi_list():
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()
  cur.execute("SELECT ten FROM bac_si")
  bacsi = [r[0] for r in cur.fetchall()]
  conn.close()
  return bacsi

def get_phongkham_list():
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()
  cur.execute("SELECT ten FROM phong_kham")
  phongkham = [r[0] for r in cur.fetchall()]
  conn.close()
  return phongkham

# HTML form template
FORM_HTML = '''
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8">
    <title>Đặt lịch khám bệnh</title>
    <style>
      body { font-family: Arial, sans-serif; background: #f7f9fb; }
      .container { max-width: 500px; margin: 40px auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px #e0e0e0; }
      h2 { color: #1976d2; }
      label { font-weight: bold; margin-top: 12px; display: block; }
      input, select, textarea { width: 100%; padding: 8px; margin-top: 4px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 4px; }
      button { background: #1976d2; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; font-size: 15px; cursor: pointer; }
      .msg { color: green; margin-bottom: 10px; }
    </style>
  </head>
  <body>
    <div class="container">
      <h2>Đặt lịch khám bệnh</h2>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="msg">{{ messages[0] }}</div>
        {% endif %}
      {% endwith %}
      <form method="post">
        <label for="ho_ten">Họ tên bệnh nhân</label>
        <input type="text" name="ho_ten" required>
        <label for="ngay_gio">Ngày & Giờ khám</label>
        <input type="datetime-local" name="ngay_gio" required>
        <label for="bac_si">Bác sĩ</label>
        <select name="bac_si" required>
          {% for b in bacsi_list %}
            <option value="{{ b }}">{{ b }}</option>
          {% endfor %}
        </select>
        <label for="phong_kham">Phòng khám</label>
        <select name="phong_kham" required>
          {% for p in phongkham_list %}
            <option value="{{ p }}">{{ p }}</option>
          {% endfor %}
        </select>
        <label for="ghi_chu">Ghi chú</label>
        <textarea name="ghi_chu"></textarea>
        <button type="submit">Đặt lịch</button>
      </form>
    </div>
  </body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def dat_lich():
  bacsi_list = get_bacsi_list()
  phongkham_list = get_phongkham_list()
  message = None
  if request.method == 'POST':
    ho_ten = request.form['ho_ten']
    ngay_gio = request.form['ngay_gio']
    bac_si = request.form.get('bac_si', '')
    phong_kham = request.form.get('phong_kham', '')
    ghi_chu = request.form.get('ghi_chu', '')
    try:
      conn = sqlite3.connect(DB_PATH)
      cur = conn.cursor()
      cur.execute("""
          INSERT INTO lich_hen (ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, trang_thai)
          VALUES (?, ?, ?, ?, ?, ?)
      """, (ho_ten, ngay_gio, bac_si, phong_kham, ghi_chu, "Đã đặt lịch"))
      conn.commit()
      conn.close()
      message = 'Đặt lịch thành công!'
    except Exception as e:
      message = f'Lỗi: {e}'
  return render_template_string(FORM_HTML, bacsi_list=bacsi_list, phongkham_list=phongkham_list, messages=[message] if message else [])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
