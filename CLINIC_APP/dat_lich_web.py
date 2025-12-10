from flask import Flask, render_template_string, request, redirect, url_for, flash, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'clinic.db')


def get_bacsi_list():
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()
  cur.execute("SELECT ten FROM nhan_su WHERE chuc_vu='Bác sĩ' ORDER BY ten ASC")
  bacsi = [r[0] for r in cur.fetchall()]
  conn.close()
  return bacsi

def get_loai_kham_list():
  # Return predefined visit types
  return ["Khám tư vấn", "Tái khám", "Khám theo yêu cầu"]


def get_recent_appointments(limit=5):
  conn = sqlite3.connect(DB_PATH)
  cur = conn.cursor()
  try:
    cur.execute("SELECT ho_ten, ngay_gio, bac_si, loai_kham, trang_thai, dien_thoai, dia_chi FROM lich_hen ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
  except Exception:
    rows = []
  finally:
    conn.close()
  return rows

# HTML form template
FORM_HTML = '''
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Đặt lịch khám bệnh</title>
    <!-- Bootstrap CSS (CDN) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons (CDN) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <style>
      body { font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; background: #f3f6fb; }
      .booking-card { max-width: 820px; margin: 48px auto; background: #fff; padding: 28px; border-radius: 12px; box-shadow: 0 6px 24px rgba(13,38,76,0.08); }
      .brand { color: #0d6efd; font-weight: 700; }
      .form-label { font-weight: 600; }
      .muted { color: #6b7280; font-size: 0.9rem; }
      .btn-primary { background-image: linear-gradient(90deg,#0d6efd,#5aa9ff); border: 0; }
      .required::after { content: " *"; color: #d63384; }
      @media (max-width: 576px) { .booking-card { margin: 20px; padding: 18px; } }
    </style>
  </head>
  <body>
    <div class="booking-card container">
      <div class="row align-items-center mb-3">
        <div class="col-sm-9">
          <h3 class="mb-0 brand">Phòng khám - Đặt lịch khám</h3>
          <div class="muted">Chọn bác sĩ, phòng khám và thời gian phù hợp — chúng tôi sẽ thông báo xác nhận.</div>
        </div>
        <div class="col-sm-3 text-sm-end mt-3 mt-sm-0">
          <div class="d-flex justify-content-end gap-2 align-items-center">
            <a href="/ehr" class="btn btn-outline-primary btn-sm">Xem hồ sơ bệnh án</a>
            <a href="/my_appointments" class="btn btn-outline-secondary btn-sm">Lịch hẹn của tôi</a>
          </div>
        </div>
      </div>

      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert alert-success alert-dismissible fade show" role="alert">
            <strong>{{ messages[0] }}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        {% endif %}
      {% endwith %}

      <form method="post">
          <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label required" for="ho_ten">Họ tên bệnh nhân</label>
            <input class="form-control" id="ho_ten" name="ho_ten" placeholder="Hãy nhập họ và tên" required>
          </div>
          <div class="col-md-6">
            <label class="form-label required" for="ngay_gio">Ngày & Giờ khám</label>
            <input class="form-control" id="ngay_gio" name="ngay_gio" type="datetime-local" required>
          </div>

          <div class="col-md-6">
            <label class="form-label" for="dien_thoai">Số điện thoại</label>
            <input class="form-control" id="dien_thoai" name="dien_thoai" placeholder="Số điện thoại (không bắt buộc)">
          </div>
          <div class="col-md-6">
            <label class="form-label" for="dia_chi">Địa chỉ</label>
            <input class="form-control" id="dia_chi" name="dia_chi" placeholder="Địa chỉ (không bắt buộc)">
          </div>

          <div class="col-md-6">
            <label class="form-label required" for="bac_si">Bác sĩ</label>
            <select class="form-select" id="bac_si" name="bac_si" required>
              <option value="" disabled selected>Chọn bác sĩ...</option>
              {% for b in bacsi_list %}
                <option value="{{ b }}">{{ b }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label required" for="loai_kham">Loại khám</label>
            <select class="form-select" id="loai_kham" name="loai_kham" required>
              <option value="" disabled selected>Chọn loại khám...</option>
              {% for k in loai_kham_list %}
                <option value="{{ k }}">{{ k }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="col-12">
            <label class="form-label" for="ghi_chu">Ghi chú</label>
            <textarea class="form-control" id="ghi_chu" name="ghi_chu" rows="3" placeholder="Triệu chứng, lưu ý đặc biệt... (không bắt buộc)"></textarea>
          </div>

          <div class="col-12 text-end">
            <button type="submit" class="btn btn-primary btn-lg">Đặt lịch</button>
          </div>
        </div>
      </form>
      <!-- Recent appointments -->
      <div class="mt-4">
        <h6 class="mb-2">Lịch hẹn gần đây</h6>
        {% if recent_appointments %}
          <div class="table-responsive">
            <table class="table table-sm table-bordered">
              <thead class="table-light"><tr><th>Họ tên</th><th>SĐT</th><th>Địa chỉ</th><th>Ngày & giờ</th><th>Bác sĩ</th><th>Loại khám</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {% for r in recent_appointments %}
                  <tr><td>{{ r[0] }}</td><td>{{ r[5] or '—' }}</td><td>{{ r[6] or '—' }}</td><td>{{ r[1] }}</td><td>{{ r[2] or '—' }}</td><td>{{ r[3] or '—' }}</td><td>{{ r[4] or '—' }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% else %}
          <div class="muted">Chưa có lịch hẹn gần đây.</div>
        {% endif %}
      </div>
    </div>

      <!-- Contact / Footer -->
      <div class="mt-4 text-center text-muted small">
        <strong>Liên hệ với chúng tôi</strong>
          <div class="d-inline-flex gap-3 ms-3 align-items-center" style="margin-left:12px;">
            <a href="mailto:vult8073@ut.edu.vn" class="text-decoration-none text-dark" title="Gửi email"><i class="bi bi-envelope-fill" style="font-size:18px"></i> <span class="ms-1">vult8073@ut.edu.vn</span></a>
          <a href="tel:+840123456789" class="text-decoration-none text-dark" title="Gọi điện"><i class="bi bi-telephone-fill" style="font-size:18px"></i> <span class="ms-1">+84 0123 456 789</span></a>
          <a href="https://www.facebook.com/vuleisme12" class="text-decoration-none text-dark" target="_blank" title="Facebook"><i class="bi bi-facebook" style="font-size:18px"></i> <span class="ms-1">/Vũ đẹp trai</span></a>
          <a href="https://zalo.me/+840123456789" class="text-decoration-none text-dark" target="_blank" title="Zalo"><i class="bi bi-chat-dots-fill" style="font-size:18px"></i> <span class="ms-1">Zalo</span></a>
        </div>
      </div>

    <!-- Bootstrap JS (CDN) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''


MY_APPTS_HTML = '''
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Lịch hẹn của tôi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <style>.container{max-width:980px;margin:32px auto}.muted{color:#6b7280}</style>
  </head>
  <body>
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 class="mb-0">Lịch hẹn của tôi</h4>
          <div class="muted">Nhập họ tên (và nếu có, số CCCD) để quản lý lịch hẹn của bạn.</div>
        </div>
        <div><a class="btn btn-outline-secondary btn-sm" href="/">Quay về đặt lịch</a></div>
      </div>

      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert alert-info">{{ messages[0] }}</div>
        {% endif %}
      {% endwith %}

      <form method="post" class="row g-3 mb-3">
        <div class="col-md-6">
          <label class="form-label">Họ và tên</label>
          <input class="form-control" name="ho_ten" placeholder="Họ và tên" required value="{{ ho_ten or '' }}">
        </div>
        <div class="col-md-4">
          <label class="form-label">Số CCCD (không bắt buộc)</label>
          <input class="form-control" name="so_cccd" placeholder="Số CCCD" value="{{ so_cccd or '' }}">
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100" type="submit">Tìm</button>
        </div>
      </form>

      {% if appointments is defined and appointments %}
        <div class="table-responsive">
          <table class="table table-sm table-bordered">
            <thead class="table-light"><tr><th>Họ tên</th><th>Ngày & giờ</th><th>Bác sĩ</th><th>Loại khám</th><th>Trạng thái</th><th>Người đặt</th><th>Hành động</th></tr></thead>
            <tbody>
              {% for a in appointments %}
                <tr>
                  <td>{{ a[1] }}</td>
                  <td>{{ a[2] }}</td>
                  <td>{{ a[3] or '—' }}</td>
                  <td>{{ a[4] or '—' }}</td>
                  <td>{{ a[5] or '—' }}</td>
                  <td>{{ a[6] or '—' }}</td>
                  <td>
                    <form method="post" action="/my_appointments/cancel/{{ a[0] }}" style="display:inline-block;">
                      <button class="btn btn-sm btn-danger" type="submit" onclick="return confirm('Bạn có chắc muốn hủy lịch này?')">Hủy</button>
                    </form>
                    <a class="btn btn-sm btn-outline-primary" href="/my_appointments/edit/{{ a[0] }}">Sửa</a>
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% elif appointments is defined %}
        <div class="muted">Không tìm thấy lịch hẹn nào cho thông tin đã cung cấp.</div>
      {% endif %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def dat_lich():
  bacsi_list = get_bacsi_list()
  loai_kham_list = get_loai_kham_list()
  recent_appointments = get_recent_appointments(5)

  if request.method == 'POST':
    ho_ten = request.form.get('ho_ten', '').strip()
    ngay_gio = request.form.get('ngay_gio', '')
    dien_thoai = request.form.get('dien_thoai', '').strip()
    dia_chi = request.form.get('dia_chi', '').strip()
    bac_si = request.form.get('bac_si', '')
    loai_kham = request.form.get('loai_kham', '')
    ghi_chu = request.form.get('ghi_chu', '').strip()

    if not ho_ten or not ngay_gio:
      flash('Vui lòng nhập đầy đủ tên và thời gian hẹn.')
      return redirect(url_for('dat_lich'))

    try:
      conn = sqlite3.connect(DB_PATH)
      cur = conn.cursor()
      cur.execute("""
        INSERT INTO lich_hen (ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu, trang_thai, dien_thoai, dia_chi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      """, (ho_ten, ngay_gio, bac_si, loai_kham, ghi_chu, "Đã đặt lịch", dien_thoai, dia_chi))
      conn.commit()
      conn.close()
      flash('Đặt lịch thành công!')
      # Redirect to avoid duplicate form submission
      return redirect(url_for('dat_lich'))
    except Exception as e:
      # Bubble up a friendly error message
      flash(f'Không thể lưu lịch hẹn: {e}')
      return redirect(url_for('dat_lich'))

  return render_template_string(FORM_HTML, bacsi_list=bacsi_list, loai_kham_list=loai_kham_list, recent_appointments=recent_appointments)


def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DB_PATH)
  return db


@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()


@app.route('/my_appointments', methods=['GET', 'POST'])
def my_appointments():
  ho_ten = None
  so_cccd = None
  appointments = []
  if request.method == 'POST':
    ho_ten = request.form.get('ho_ten', '').strip()
    so_cccd = request.form.get('so_cccd', '').strip()
    db = get_db()
    cur = db.cursor()
    query = "SELECT id, ho_ten, ngay_gio, bac_si, loai_kham, trang_thai, nguoi_dat FROM lich_hen WHERE ho_ten LIKE ?"
    params = [f"%{ho_ten}%"]
    if so_cccd:
      query += " AND so_cccd = ?"
      params.append(so_cccd)
    cur.execute(query, params)
    appointments = cur.fetchall()
  return render_template_string(MY_APPTS_HTML, appointments=appointments, ho_ten=ho_ten, so_cccd=so_cccd)


@app.route('/my_appointments/cancel/<int:lid>', methods=['POST'])
def my_appointments_cancel(lid):
  db = get_db()
  cur = db.cursor()
  cur.execute("UPDATE lich_hen SET trang_thai = ? WHERE id = ?", ('Đã hủy', lid))
  db.commit()
  flash('Đã hủy lịch hẹn.')
  return redirect(url_for('my_appointments'))


@app.route('/my_appointments/edit/<int:lid>', methods=['GET', 'POST'])
def my_appointments_edit(lid):
  db = get_db()
  cur = db.cursor()
  if request.method == 'POST':
    ho_ten_new = request.form.get('ho_ten', '').strip()
    ngay_gio = request.form.get('ngay_gio')
    ghi_chu = request.form.get('ghi_chu')
    cur.execute('UPDATE lich_hen SET ho_ten = ?, ngay_gio = ?, ghi_chu = ? WHERE id = ?', (ho_ten_new, ngay_gio, ghi_chu, lid))
    db.commit()
    flash('Cập nhật lịch hẹn thành công.')
    return redirect(url_for('my_appointments'))
  cur.execute('SELECT id, ho_ten, ngay_gio, bac_si, loai_kham, trang_thai, ghi_chu, nguoi_dat FROM lich_hen WHERE id = ?', (lid,))
  row = cur.fetchone()
  if not row:
    flash('Không tìm thấy lịch hẹn.')
    return redirect(url_for('my_appointments'))
  edit_html = '''
  <!doctype html>
  <html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Sửa lịch hẹn</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
  </head>
  <body><div class="container" style="max-width:680px;margin:32px auto;">
  <h4>Sửa lịch hẹn</h4>
  <form method="post">
    <div class="mb-3">
      <label class="form-label required">Họ và tên</label>
      <input name="ho_ten" class="form-control" value="{{ ho_ten }}" required>
    </div>
    <div class="mb-3">
      <label class="form-label">Ngày & giờ</label>
      <div class="input-group">
        <input id="ngay_gio_input" name="ngay_gio" type="datetime-local" class="form-control" value="{{ ngay_gio }}">
        <button type="button" class="btn btn-outline-secondary" id="picker_btn" title="Chọn ngày"><i class="bi bi-calendar"></i></button>
      </div>
    </div>
    <div class="mb-3"><label class="form-label">Ghi chú</label><textarea name="ghi_chu" class="form-control">{{ ghi_chu }}</textarea></div>
    <button class="btn btn-primary">Lưu</button>
    <a class="btn btn-outline-secondary" href="/my_appointments">Hủy</a>
  </form>
  </div>
  <script>
    (function(){
      var btn = document.getElementById('picker_btn');
      var inp = document.getElementById('ngay_gio_input');
      if(btn && inp){
        btn.addEventListener('click', function(e){
          // Try to open native picker if available, otherwise focus
          if(typeof inp.showPicker === 'function'){
            try{ inp.showPicker(); return; }catch(e){}
          }
          inp.focus();
        });
      }
    })();
  </script>
  </body></html>
  '''
  return render_template_string(edit_html, ho_ten=row[1], ngay_gio=row[2], ghi_chu=row[6])


# Helper functions for EHR search
def find_patient_by_name_cccd(ho_ten, so_cccd):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, ho_ten, ngay_sinh, dien_thoai, so_cccd FROM benh_nhan WHERE ho_ten = ? AND so_cccd = ? LIMIT 1", (ho_ten, so_cccd))
    row = cur.fetchone()
    conn.close()
    return row


def find_patients_by_partial_name(name_part, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Use LIKE search for partial match; keep parameterized queries
    q = "SELECT id, ho_ten, ngay_sinh, dien_thoai, so_cccd FROM benh_nhan WHERE ho_ten LIKE ? ORDER BY ho_ten LIMIT ?"
    cur.execute(q, (f"%{name_part}%", limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_patient_visits(pid):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # get phieu_kham (visits) for patient
    cur.execute("SELECT id, so_phieu, ngay_lap, bac_si, phong_kham FROM phieu_kham WHERE benh_nhan_id = ? ORDER BY datetime(ngay_lap) DESC", (pid,))
    visits = []
    pk_rows = cur.fetchall()
    for pk in pk_rows:
        pkid, so_phieu, ngay_lap, bac_si, phong_kham = pk
        # latest detailed exam record for this visit
        cur.execute("SELECT chan_doan, ket_luan, icd10, di_ung_thuoc, ghi_chu_kham FROM chi_tiet_phieu_kham WHERE phieu_kham_id = ? ORDER BY id DESC LIMIT 1", (pkid,))
        detail = cur.fetchone() or ('', '', '', '', '')
        chan_doan, ket_luan, icd10, di_ung_thuoc, ghi_chu_kham = detail

        # prescriptions for this visit
        cur.execute("SELECT id, ngay_ke, so_ngay, ngay_tai_kham, chan_doan, loi_dan FROM don_thuoc WHERE phieu_kham_id = ? ORDER BY ngay_ke DESC", (pkid,))
        pres_rows = []
        for p in cur.fetchall():
            don_id, ngay_ke, so_ngay, ngay_tai_kham, don_chan_doan, loi_dan = p
            cur.execute("SELECT ten_thuoc, so_luong, sang, trua, chieu, toi, lieu_dung, ghi_chu FROM chi_tiet_don_thuoc WHERE don_thuoc_id = ?", (don_id,))
            meds = cur.fetchall()
            pres_rows.append({
                'id': don_id,
                'ngay_ke': ngay_ke,
                'so_ngay': so_ngay,
                'ngay_tai_kham': ngay_tai_kham,
                'chan_doan': don_chan_doan,
                'loi_dan': loi_dan,
                'meds': meds,
            })

        visits.append({
            'id': pkid,
            'so_phieu': so_phieu,
            'ngay_lap': ngay_lap,
            'bac_si': bac_si,
            'phong_kham': phong_kham,
            'chan_doan': chan_doan,
            'ket_luan': ket_luan,
            'icd10': icd10,
            'di_ung_thuoc': di_ung_thuoc,
            'ghi_chu_kham': ghi_chu_kham,
            'don_thuoc': pres_rows,
        })

    conn.close()
    return visits


# EHR (hồ sơ bệnh án) search template + route
EHR_TEMPLATE = r'''
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hồ sơ bệnh án - Tìm kiếm</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <style>.container{max-width:980px;margin:32px auto}.muted{color:#6b7280}</style>
  </head>
  <body>
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h4 class="mb-0">Xem hồ sơ bệnh án</h4>
          <div class="muted">Nhập họ tên và số CCCD để tra cứu lịch sử khám</div>
        </div>
        <div><a class="btn btn-outline-secondary btn-sm" href="/">Quay về đặt lịch</a></div>
      </div>

      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert alert-warning">{{ messages[0] }}</div>
        {% endif %}
      {% endwith %}

      <form method="post" class="row g-3 align-items-end">
        <div class="col-md-6">
          <label class="form-label required">Họ và tên</label>
          <input class="form-control" name="ho_ten" placeholder="Họ và tên" required>
        </div>
          <div class="col-md-4">
            <label class="form-label required">Số CCCD</label>
            <input class="form-control" name="so_cccd" pattern="\d{9,12}" title="Số CCCD: 9-12 chữ số" placeholder="Số căn cước công dân" required>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100" type="submit">Tìm hồ sơ</button>
        </div>
      </form>

      {% if patient %}
        <hr class="my-4">
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="card-title">{{ patient[1] }} <small class="text-muted">(CCCD: {{ patient[4] or '—' }})</small></h5>
            <div class="mb-2 muted">Ngày sinh: {{ patient[2] or '—' }} — SĐT: {{ patient[3] or '—' }}</div>
            <div class="text-muted small">Tổng lượt khám: {{ visits|length }}</div>
          </div>
        </div>

        {% if visits %}
          {% for v in visits %}
            <div class="card mb-3">
              <div class="card-header">
                <strong>Ngày khám:</strong> {{ v.ngay_lap }} — <strong>Số phiếu:</strong> {{ v.so_phieu or '—' }}
                <div class="float-end text-muted small">Bác sĩ: {{ v.bac_si or '—' }} • Phòng: {{ v.phong_kham or '—' }}</div>
              </div>
              <div class="card-body">
                <p><strong>Chẩn đoán:</strong> {{ v.chan_doan or '—' }}</p>
                <p><strong>Kết luận:</strong> {{ v.ket_luan or '—' }}</p>
                <p><strong>Ghi chú khám:</strong> {{ v.ghi_chu_kham or '—' }}</p>

                {% if v.don_thuoc %}
                  <div class="mt-3">
                    <h6>Đơn thuốc</h6>
                    {% for d in v.don_thuoc %}
                      <div class="border rounded p-2 mb-2 bg-light">
                        <div class="small text-muted">Ngày kê: {{ d.ngay_ke or '—' }} — Ngày tái khám: {{ d.ngay_tai_kham or '—' }}</div>
                        <div><strong>Hướng dẫn:</strong> {{ d.loi_dan or '—' }}</div>
                        <ul class="mb-0">
                          {% for m in d.meds %}
                            <li>{{ m[0] }} — số lượng: {{ m[1] }} — liều: {{ m[6] or '' }} {{ "|" if m[6] and m[7] else '' }} {{ m[7] or '' }}</li>
                          {% endfor %}
                        </ul>
                      </div>
                    {% endfor %}
                  </div>
                {% endif %}
              </div>
            </div>
          {% endfor %}
        {% endif %}
      {% endif %}

      {% if candidates %}
        <hr>
        <h5>Những bản ghi khả dĩ</h5>
        <div class="list-group mb-3">
          {% for c in candidates %}
            <a href="{{ url_for('ehr_by_id', pid=c[0]) }}" class="list-group-item list-group-item-action">{{ c[1] }} — ID:{{ c[0] }} — {{ c[4] or 'CCCD trống' }} — {{ c[2] or '—' }}</a>
          {% endfor %}
        </div>
      {% endif %}

    </div>
    <!-- Contact / Footer -->
      <div class="mt-4 text-center text-muted small">
        <strong>Liên hệ với chúng tôi</strong>
        <div class="d-inline-flex gap-3 ms-3 align-items-center" style="margin-left:12px;">
          <a href="mailto:vult8073@ut.edu.vn" class="text-decoration-none text-dark" title="Gửi email"><i class="bi bi-envelope-fill" style="font-size:18px"></i> <span class="ms-1">vult8073@ut.edu.vn</span></a>
          <a href="tel:+840123456789" class="text-decoration-none text-dark" title="Gọi điện"><i class="bi bi-telephone-fill" style="font-size:18px"></i> <span class="ms-1">+84 0123 456 789</span></a>
          <a href="https://www.facebook.com/vuleisme12" class="text-decoration-none text-dark" target="_blank" title="Facebook"><i class="bi bi-facebook" style="font-size:18px"></i> <span class="ms-1">/Vũ đẹp trai</span></a>
          <a href="https://zalo.me/+840123456789" class="text-decoration-none text-dark" target="_blank" title="Zalo"><i class="bi bi-chat-dots-fill" style="font-size:18px"></i> <span class="ms-1">Zalo</span></a>
        </div>
      </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''


@app.route('/ehr', methods=['GET', 'POST'])
def ehr_search():
    patient = None
    visits = None
    candidates = None

    if request.method == 'POST':
        ho_ten = request.form.get('ho_ten', '').strip()
        so_cccd = request.form.get('so_cccd', '').strip()

        # Allow partial-name search: prefer exact (name+cccd) match first, else try to find partial name candidates
        if not ho_ten:
            flash('Vui lòng nhập họ tên để tìm hồ sơ.')
            return redirect(url_for('ehr_search'))

        # if CCCD provided attempt exact match
        if so_cccd:
            row = find_patient_by_name_cccd(ho_ten, so_cccd)
            if row:
                patient = row
                visits = get_patient_visits(patient[0])
            else:
                # not exact found -- fall through to partial search
                candidates = find_patients_by_partial_name(ho_ten)
                if not candidates:
                    flash('Không tìm thấy bệnh nhân khớp với thông tin cung cấp.')
                    return redirect(url_for('ehr_search'))
        else:
            # partial name search
            candidates = find_patients_by_partial_name(ho_ten)
            if len(candidates) == 1:
                patient = candidates[0]
                visits = get_patient_visits(patient[0])
                candidates = None
            elif len(candidates) == 0:
                flash('Không tìm thấy bệnh nhân khớp với tên cung cấp.')
                return redirect(url_for('ehr_search'))

    return render_template_string(EHR_TEMPLATE, patient=patient, visits=visits, candidates=candidates)


@app.route('/ehr/patient/<int:pid>', methods=['GET'])
def ehr_by_id(pid):
    row = None
    try:
      conn = sqlite3.connect(DB_PATH)
      cur = conn.cursor()
      cur.execute("SELECT id, ho_ten, ngay_sinh, dien_thoai, so_cccd FROM benh_nhan WHERE id = ? LIMIT 1", (pid,))
      row = cur.fetchone()
      conn.close()
    except Exception:
      row = None

    if not row:
      flash('Không tìm thấy bệnh nhân.')
      return redirect(url_for('ehr_search'))

    visits = get_patient_visits(pid)
    return render_template_string(EHR_TEMPLATE, patient=row, visits=visits, candidates=None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
