import os
import sys
import csv
from io import BytesIO

from django.db.models import Q  # type: ignore
from django.http import HttpResponse  # type: ignore

from reportlab.lib.pagesizes import A4, landscape  # type: ignore
from reportlab.pdfbase import pdfmetrics  # type: ignore
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.lib.units import inch  # type: ignore

from assignments.models import Assignment

from bidi.algorithm import get_display  # type: ignore
import arabic_reshaper  # type: ignore
import logging

logger = logging.getLogger(__name__)


def process_arabic(text):
    """
    Reshape Arabic text and apply bidi algorithm.
    This converts input text into a form that is rendered correctly by ReportLab.
    """
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception:
        return text


def export_assignments_pdf(request):
    """Export assignments to PDF with full Arabic support."""
    gender = request.GET.get('gender', 'M')
    faculty_filter = request.GET.get('faculty')
    research_filter = request.GET.get('research')

    course_number = request.GET.get('course_number', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Fetch assignments with related data - changed ordering to faculty name first
    assignments = Assignment.objects.select_related(
        'student', 'student__faculty', 'research'
    ).filter(student__gender=gender).order_by('student__faculty__name', 'research__name')

    if faculty_filter and faculty_filter.lower() != 'none':
        assignments = assignments.filter(student__faculty_id=faculty_filter)

    if research_filter and research_filter.lower() != 'none':
        assignments = assignments.filter(research_id=research_filter)

    # Get unique research-group-faculty combinations
    unique_combinations = assignments.values(
        'research_id', 'group_id', 'student__faculty_id'
    ).distinct().order_by('student__faculty_id', 'research_id')  # Order by faculty first

    # Prepare table data; header row first
    data = []
    data.append([
        process_arabic("البحث"),
        process_arabic("الكلية"),
        process_arabic("الطلاب")
    ])

    for combo in unique_combinations:
        research_id = combo['research_id']
        group_id = combo['group_id']
        faculty_id = combo['student__faculty_id']

        query_filter = Q(research_id=research_id, student__faculty_id=faculty_id)
        if group_id is None:
            query_filter &= Q(group_id__isnull=True)
        else:
            query_filter &= Q(group_id=group_id)

        group_assignments = assignments.filter(query_filter)
        if group_assignments.exists():
            research_name = process_arabic(group_assignments[0].research.name)
            faculty_name = process_arabic(group_assignments[0].student.faculty.name)
            student_serials = process_arabic(", ".join(
                [a.student.serial_number for a in group_assignments]
            ))
            data.append([research_name, faculty_name, student_serials])

    buffer = BytesIO()

    # Register an Arabic-supporting font.
    # Use a proper path depending on the OS.
    if sys.platform.startswith('win'):
        font_path = r'C:\Windows\Fonts\arial.ttf'
    else:
        # Try user fonts directory first, then system fonts
        user_font_path = os.path.expanduser('~/Library/Fonts/Arial.ttf')
        system_font_path = '/Library/Fonts/Arial.ttf'

        if os.path.exists(user_font_path):
            font_path = user_font_path
        else:
            font_path = system_font_path

    try:
        pdfmetrics.registerFont(TTFont('Arabic', font_path))
        arabic_font = 'Arabic'
    except Exception as e:
        # Fallback if the font cannot be registered.
        logger.error(f"Error registering Arabic font: {e}")
        arabic_font = 'Helvetica'

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    # Create styles for the title text.
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName=arabic_font,
        alignment=1,  # Center alignment
        fontSize=16
    )

    gender_display = process_arabic('ذكور' if gender == 'M' else 'إناث')

    # Add course info to title if provided
    title_elements = []
    if start_date and end_date:
        title_elements.append(process_arabic(f"من {start_date} إلى {end_date}"))
    if course_number:
        course_text = gender_display + process_arabic(f"الدورة العسكرية {course_number} للـ")
        title_elements.append(course_text)

    # Create title
    course_title = " - ".join(title_elements) if title_elements else ""

    # Build document elements array
    elements = []

    # Add course title if present
    if course_title:
        course_title_paragraph = Paragraph(course_title, title_style)
        elements.append(course_title_paragraph)

    # Create the table
    table = Table(data, repeatRows=1, colWidths=[3 * inch, 2 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), arabic_font),
        ('FONTNAME', (0, 1), (-1, -1), arabic_font),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    # Update filename to include course number if provided
    if course_number:
        start_date_str = start_date.replace('-', '_') if start_date else ''
        end_date_str = end_date.replace('-', '_') if end_date else ''
        filename = f"الدورة_{course_number}_{start_date_str}_{end_date_str}_{gender}.pdf"
    else:
        filename = f"assignments_{gender}_{faculty_filter or 'all'}_{research_filter or 'all'}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_assignments_csv(request):
    """Export assignments to CSV with proper UTF-8 encoding for Arabic names."""
    gender = request.GET.get('gender', 'M')
    faculty_filter = request.GET.get('faculty')
    research_filter = request.GET.get('research')

    # Get assignments for the specified gender, with related data
    assignments = Assignment.objects.select_related(
        'student', 'student__faculty', 'research'
    ).filter(student__gender=gender).order_by('student__faculty__name', 'research__name')

    # Apply additional filters if provided
    if faculty_filter and faculty_filter.lower() != 'none':
        assignments = assignments.filter(student__faculty_id=faculty_filter)
    if research_filter and research_filter.lower() != 'none':
        assignments = assignments.filter(research_id=research_filter)

    # Define the filename using provided filters
    gender_display = 'ذكور' if gender == 'M' else 'إناث'
    filename = f"توزيع_البحوث_{gender_display}.csv"

    # URL encode the filename for Content-Disposition header
    import urllib.parse
    encoded_filename = urllib.parse.quote(filename)

    # Set content_type with charset utf-8 and add Content-Disposition header
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"

    # Write the BOM (Byte Order Mark) to help Excel detect UTF-8 encoding
    response.write('\ufeff')

    # Create CSV writer and write header row
    writer = csv.writer(response)
    writer.writerow(['البحث', 'الكلية', 'الرقم التسلسلي للطالب'])

    # Write data rows from assignments
    for assignment in assignments:
        writer.writerow([
            assignment.research.name,
            assignment.student.faculty.name,
            assignment.student.serial_number,
        ])

    return response
