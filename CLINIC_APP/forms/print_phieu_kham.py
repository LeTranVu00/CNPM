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

def generate_phieu_kham_pdf(data, output_path):
    """
    Tạo file PDF phiếu khám bệnh
    
    Args:
        data: dict chứa thông tin phiếu khám
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
    story.append(Paragraph("PHIẾU KHÁM BỆNH", styles['TitleVN']))
    
    # Thông tin phiếu khám
    story.append(Paragraph(f"Số phiếu: {data['so_phieu']}", styles['NormalVN']))
    story.append(Paragraph(f"Ngày lập: {data['ngay_lap']}", styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    # Thông tin bệnh nhân
    story.append(Paragraph("THÔNG TIN BỆNH NHÂN", styles['HeaderVN']))
    bn_data = [
        ['Họ và tên:', data['ho_ten'], 'Giới tính:', data['gioi_tinh']],
        ['Ngày sinh:', data['ngay_sinh'], 'Tuổi:', data['tuoi']],
        ['Địa chỉ:', data['dia_chi'], 'Điện thoại:', data['dien_thoai']],
    ]
    t = Table(bn_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'TimesNewRoman'),
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
    
    # Thông tin khám bệnh
    story.append(Paragraph("THÔNG TIN KHÁM BỆNH", styles['HeaderVN']))
    
    # Dấu hiệu sinh tồn
    vital_data = [
        ['Nhiệt độ:', data['nhiet_do'], 'Huyết áp:', data['huyet_ap']],
        ['Nhịp tim:', data['nhip_tim'], 'Nhịp thở:', data['nhip_tho']],
        ['Cân nặng:', data['can_nang'], 'Chiều cao:', data['chieu_cao']],
    ]
    t = Table(vital_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'TimesNewRoman'),
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
    
    # Tiền sử
    story.append(Paragraph("Dị ứng thuốc: " + data['di_ung_thuoc'], styles['NormalVN']))
    story.append(Paragraph("Tiền sử bản thân: " + data['tien_su_ban_than'], styles['NormalVN']))
    story.append(Paragraph("Tiền sử gia đình: " + data['tien_su_gia_dinh'], styles['NormalVN']))
    story.append(Paragraph("Bệnh kèm theo: " + data['benh_kem_theo'], styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    # Khám lâm sàng và chẩn đoán
    story.append(Paragraph("Khám lâm sàng:", styles['NormalVN']))
    story.append(Paragraph(data['kham_lam_sang'], styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Chẩn đoán:", styles['NormalVN']))
    story.append(Paragraph(data['chan_doan'], styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("ICD-10: " + data['icd10'], styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Kết luận:", styles['NormalVN']))
    story.append(Paragraph(data['ket_luan'], styles['NormalVN']))
    story.append(Spacer(1, 12))
    
    # Thông tin bác sĩ
    story.append(Spacer(1, 20))
    bs_info = Table([
        ['', '', 'Bác sĩ khám bệnh'],
        ['', '', '(Ký và ghi rõ họ tên)'],
        ['', '', ''],
        ['', '', data['bac_si']]
    ], colWidths=[2*inch, 2*inch, 2.5*inch])
    bs_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), normal_font),
        ('FONTNAME', (2,0), (2,0), bold_font),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(bs_info)
    
    # Tạo tài liệu PDF
    doc.build(story)

def print_phieu_kham(phieu_data, output_dir="output"):
    """
    In phiếu khám ra file PDF
    
    Args:
        phieu_data: dict chứa thông tin phiếu khám
        output_dir: thư mục chứa file PDF output (mặc định là "output")
    
    Returns:
        str: đường dẫn đến file PDF đã tạo
    """
    # Tạo tên file dựa trên số phiếu và thời gian
    filename = f"phieu_kham_{phieu_data['so_phieu']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Đảm bảo thư mục output tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Đường dẫn đầy đủ đến file output
    output_path = os.path.join(output_dir, filename)
    
    # Tạo file PDF
    generate_phieu_kham_pdf(phieu_data, output_path)
    
    return output_path