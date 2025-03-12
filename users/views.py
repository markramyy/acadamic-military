import os
import csv
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from django.db import connection

from faculties.models import Faculty
from researches.models import Research
from assignments.models import Assignment, Student


def export_database(request):
    """
    View to export all database tables (Faculty, Research, Student, Assignment) as CSV files
    with course information
    """
    if request.method == 'POST':
        # Get course information
        course_number = request.POST.get('course_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Validate form data
        if not course_number or not start_date or not end_date:
            messages.error(request, 'يرجى إدخال جميع بيانات الدورة المطلوبة')
            return redirect('export_database')

        # Format dates for filenames (replace hyphens with underscores)
        start_date_formatted = start_date.replace('-', '_')
        end_date_formatted = end_date.replace('-', '_')

        # Create export directory if it doesn't exist
        export_dir = os.path.join(settings.BASE_DIR, 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Create a timestamp for unique filenames
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        exported_files = []

        # Export Faculties
        faculty_file = os.path.join(export_dir, f'faculties_{timestamp}.csv')
        with open(faculty_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Code'])
            for faculty in Faculty.objects.all():
                writer.writerow([faculty.name, faculty.code])
        exported_files.append(faculty_file)

        # Export Researches
        research_file = os.path.join(export_dir, f'researches_{timestamp}.csv')
        with open(research_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['اسم البحث'])
            for research in Research.objects.all():
                writer.writerow([research.name])
        exported_files.append(research_file)

        # Export Students
        student_file = os.path.join(export_dir, f'students_{timestamp}.csv')
        with open(student_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Serial Number', 'Faculty', 'Gender'])
            for student in Student.objects.all():
                writer.writerow([
                    student.name,
                    student.serial_number,
                    student.faculty.name,
                    'ذكر' if student.gender == 'M' else 'أنثى'
                ])
        exported_files.append(student_file)

        # Export Assignments
        assignment_file = os.path.join(export_dir, f'assignments_{timestamp}.csv')
        with open(assignment_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Student', 'Serial Number', 'Faculty', 'Research', 'Assigned Date'])
            for assignment in Assignment.objects.all():
                writer.writerow([
                    assignment.student.name,
                    assignment.student.serial_number,
                    assignment.student.faculty.name,
                    assignment.research.name,
                    assignment.assigned_date
                ])
        exported_files.append(assignment_file)

        # Export Course Information
        course_info_file = os.path.join(export_dir, f'course_info_{timestamp}.csv')
        with open(course_info_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Course Number', 'Start Date', 'End Date', 'Export Date'])
            writer.writerow([
                course_number,
                start_date,
                end_date,
                timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
        exported_files.append(course_info_file)

        # Create a zip file containing all CSVs
        import zipfile
        # Use ASCII filename for the zip to ensure cross-platform compatibility
        ascii_zip_filename = f'military_course_{course_number}_{start_date_formatted}_{end_date_formatted}.zip'
        zip_filepath = os.path.join(export_dir, ascii_zip_filename)

        # Create the zip file with more compatible settings
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            # Add each file with its original name inside the zip
            for file in exported_files:
                # Add the file with a readable name that works across platforms
                zip_ref.write(file, os.path.basename(file))

            # Also add a readme file explaining the Arabic filename
            readme_content = f"""
            هذا الملف يحتوي على بيانات:
            الدورة العسكرية {course_number}
            من تاريخ {start_date}
            إلى تاريخ {end_date}
            """
            readme_path = os.path.join(export_dir, "readme.txt")
            with open(readme_path, 'w', encoding='utf-8-sig') as readme_file:
                readme_file.write(readme_content)
            zip_ref.write(readme_path, "readme.txt")
            try:
                os.remove(readme_path)
            except Exception:
                pass

        # Serve the zip file for download
        with open(zip_filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')

            # Use a display filename that's both Arabic-friendly and cross-platform
            display_filename = f'military_course_{course_number}_{start_date_formatted}_{end_date_formatted}.zip'

            # Set a simpler content disposition for better cross-platform support
            response['Content-Disposition'] = f'attachment; filename="{display_filename}"'

            # Clean up individual CSV files
            for file in exported_files:
                if os.path.exists(file):
                    os.remove(file)

            # Clean up zip file after serving
            try:
                os.remove(zip_filepath)
            except Exception:
                pass  # Ignore errors if file can't be deleted immediately

            return response

    return render(request, 'users/export_database.html')


def reset_database(request):
    """
    View to reset the database after authentication
    Requires admin credentials to proceed
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user and user.is_superuser:
            # Reset database in correct order to respect foreign key constraints
            try:
                with connection.cursor() as cursor:
                    # First delete assignments (which depend on students and researches)
                    cursor.execute('DELETE FROM assignments_assignment')

                    # Then delete students (which depend on faculties)
                    cursor.execute('DELETE FROM assignments_student')

                    # Now it's safe to delete researches (no dependencies)
                    cursor.execute('DELETE FROM researches_research')

                    # Now it's safe to delete faculties (no remaining dependencies)
                    cursor.execute('DELETE FROM faculties_faculty')

                    # Finally delete users (except the current user)
                    current_user_id = user.id
                    cursor.execute('DELETE FROM users_user WHERE id != %s', [current_user_id])

                # Reload mock data
                call_command('load_mock')
                messages.success(request, 'تم إعادة تعيين قاعدة البيانات بنجاح.')
                return redirect(reverse('home'))

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إعادة تعيين قاعدة البيانات: {str(e)}')
        else:
            messages.error(request, 'بيانات الاعتماد غير صالحة أو صلاحيات غير كافية')

    return render(request, 'users/reset_database.html')
