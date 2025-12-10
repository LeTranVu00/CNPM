from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

def get_font_name():
    """Trả về tên font để sử dụng trong PDF"""
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    
    # Kiểm tra xem có font Times New Roman không
    times_font = os.path.join(font_dir, 'times.ttf')
    times_bold = os.path.join(font_dir, 'timesbd.ttf')
    
    if os.path.exists(times_font) and os.path.exists(times_bold):
        try:
            pdfmetrics.registerFont(TTFont('TimesNewRoman', times_font))
            pdfmetrics.registerFont(TTFont('TimesNewRomanBold', times_bold))
            return 'TimesNewRoman', 'TimesNewRomanBold'
        except:
            pass
            
    # Nếu không có Times New Roman hoặc có lỗi, dùng font mặc định
    return 'Helvetica', 'Helvetica-Bold'

def generate_chi_dinh_pdf(data, output_path):
    """
    Tạo file PDF phiếu chỉ định dịch vụ
    
    Args:
        data: dict chứa thông tin phiếu chỉ định
        output_path: đường dẫn lưu file PDF
    """
    # Lấy tên font để sử dụng
    normal_font, bold_font = get_font_name()
    
    # Tạo document với page size A4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Khởi tạo story chứa các elements
    story = []
    
    # Định nghĩa styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='TitleVN',
        fontName=bold_font,
        fontSize=16,
        alignment=1,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='NormalVN',
        fontName=normal_font,
        fontSize=12,
        leading=16
    ))
    styles.add(ParagraphStyle(
        name='HeaderVN',
        fontName=bold_font,
        fontSize=13,
        alignment=1,
        spaceAfter=10
    ))
    
    # Thêm tiêu đề
    story.append(Paragraph("PHIẾU CHỈ ĐỊNH DỊCH VỤ", styles['TitleVN']))
    
    # Thông tin phiếu
    story.append(Paragraph(f"Số phiếu chỉ định: {data['so_chi_dinh']}", styles['NormalVN']))
    story.append(Paragraph(f"Số phiếu khám: {data['so_phieu_kham']}", styles['NormalVN']))
    story.append(Paragraph(f"Ngày lập: {data['ngay_lap']}", styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    # Thông tin bệnh nhân
    story.append(Paragraph("THÔNG TIN BỆNH NHÂN", styles['HeaderVN']))
    bn_data = [
        ['Họ và tên:', data['ho_ten'], 'Giới tính:', data['gioi_tinh']],
        ['Ngày sinh:', data['ngay_sinh'], 'Tuổi:', data['tuoi']],
        ['Địa chỉ:', data['dia_chi'], 'Điện thoại:', data['dien_thoai']],
        ['Đối tượng:', data['doi_tuong'], 'Nghề nghiệp:', data['nghe_nghiep']]
    ]
    t = Table(bn_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), normal_font),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.white),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    
    # Thông tin chỉ định
    story.append(Paragraph("DANH SÁCH DỊCH VỤ CHỈ ĐỊNH", styles['HeaderVN']))
    def format_vnd(x):
        """Format a numeric value into Vietnamese style with dot thousand separator.

        If the value looks like a 'small' unit (e.g. 50 meaning 50.000 VND),
        normalize by multiplying by 1000 when value < 1000. This preserves
        existing large numbers (already in VND) while ensuring printed values
        always show ".000" for typical price entries.
        """
        try:
            v = float(x)
            # If value is less than 1000, assume it's expressed in thousands (e.g. 50 -> 50.000)
            if abs(v) < 1000:
                v = v * 1000
            return "{:,.0f}".format(v).replace(',', '.')
        except Exception:
            return '0'

    dv_data = [['STT', 'Tên dịch vụ', 'Số lượng', 'Đơn giá', 'Thành tiền']]
    for idx, dv in enumerate(data['dich_vu'], 1):
        dv_data.append([
            str(idx),
            dv['ten_dich_vu'],
            str(dv['so_luong']),
            format_vnd(dv['don_gia']),
            format_vnd(dv['thanh_tien'])
        ])
    # Thêm hàng tổng tiền
    dv_data.append(['', '', '', 'Tổng tiền:', format_vnd(data['tong_tien'])])
    
    t = Table(dv_data, colWidths=[0.5*inch, 3*inch, 1*inch, 1.2*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), normal_font),
        ('FONTNAME', (0,0), (-1,0), bold_font),  # Header row in bold
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),  # STT centered
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),  # Numbers right-aligned
        ('ALIGN', (1,0), (1,-1), 'LEFT'),  # Tên dịch vụ left-aligned
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-2), 0.25, colors.black),
        ('LINEBELOW', (3,-1), (-1,-1), 0.25, colors.black),  # Underline tổng tiền
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Khám lâm sàng và chẩn đoán
    if data.get('kham_lam_sang'):
        story.append(Paragraph("Khám lâm sàng:", styles['NormalVN']))
        story.append(Paragraph(data['kham_lam_sang'], styles['NormalVN']))
        story.append(Spacer(1, 12))
    
    if data.get('chan_doan'):
        story.append(Paragraph("Chẩn đoán:", styles['NormalVN']))
        story.append(Paragraph(data['chan_doan'], styles['NormalVN']))
        story.append(Spacer(1, 12))
        
    # Thông tin bác sĩ và chữ ký
    story.append(Spacer(1, 20))
    bs_info = Table([
        ['Người lập phiếu', '', 'Bác sĩ chỉ định'],
        ['(Ký và ghi rõ họ tên)', '', '(Ký và ghi rõ họ tên)'],
        ['', '', ''],
        ['', '', ''],
        [data['nguoi_lap'], '', data['bac_si_chi_dinh']]
    ], colWidths=[2*inch, 2*inch, 2.5*inch])
    bs_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), normal_font),
        ('FONTNAME', (0,0), (-1,0), bold_font),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(bs_info)
    
    # Build PDF document
    doc.build(story)

def print_chi_dinh(phieu_data, output_dir="output"):
    """
    In phiếu chỉ định dịch vụ ra file PDF
    
    Args:
        phieu_data: dict chứa thông tin phiếu chỉ định
        output_dir: thư mục chứa file PDF output (mặc định là "output")
    
    Returns:
        str: đường dẫn đến file PDF đã tạo
    """
    # Tạo tên file dựa trên số chỉ định và thời gian
    filename = f"chi_dinh_{phieu_data['so_chi_dinh']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Đảm bảo thư mục output tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Đường dẫn đầy đủ đến file output
    output_path = os.path.join(output_dir, filename)
    
    # Tạo file PDF
    generate_chi_dinh_pdf(phieu_data, output_path)
    
    return output_path