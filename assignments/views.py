from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db import models

from core.utils import randomly_assign_researches
from faculties.models import Faculty
from assignments.models import Student, Assignment
from researches.models import Research
from assignments.forms import BulkStudentCreationForm, StudentFilterForm


def student_stats(request):
    """Display statistics about students by faculty and gender"""
    # Get statistics
    faculty_stats = Faculty.objects.annotate(
        student_count=Count('students'),
        male_count=Count('students', filter=models.Q(students__gender='M')),
        female_count=Count('students', filter=models.Q(students__gender='F'))
    )

    # Filter by faculty if specified
    filter_form = StudentFilterForm(request.GET)
    selected_faculty = None
    selected_gender = None

    if filter_form.is_valid():
        if filter_form.cleaned_data['faculty']:
            selected_faculty = filter_form.cleaned_data['faculty']
            faculty_stats = faculty_stats.filter(id=selected_faculty.id)

        if filter_form.cleaned_data['gender']:
            selected_gender = filter_form.cleaned_data['gender']
            if selected_gender == 'M':
                faculty_stats = faculty_stats.filter(students__gender='M').distinct()
            elif selected_gender == 'F':
                faculty_stats = faculty_stats.filter(students__gender='F').distinct()

    # Calculate totals
    total_students = sum(stat.student_count for stat in faculty_stats)
    total_male = sum(stat.male_count for stat in faculty_stats)
    total_female = sum(stat.female_count for stat in faculty_stats)

    context = {
        'faculty_stats': faculty_stats,
        'filter_form': filter_form,
        'selected_faculty': selected_faculty,
        'selected_gender': selected_gender,
        'total_students': total_students,
        'total_male': total_male,
        'total_female': total_female,
    }

    return render(request, 'assignments/student_stats.html', context)


def student_create(request):
    """Create multiple students with sequential serial numbers"""
    form = BulkStudentCreationForm()

    if request.method == 'POST':
        form = BulkStudentCreationForm(request.POST)
        if form.is_valid():
            faculty = form.cleaned_data['faculty']
            count = form.cleaned_data['count']
            start_number = form.cleaned_data.get('start_number') or 1
            gender = form.cleaned_data['gender']  # Get the gender

            # Create students in batch using a transaction for performance
            try:
                with transaction.atomic():
                    # Find highest existing serial number for this faculty to avoid duplicates
                    existing_students = Student.objects.filter(faculty=faculty)
                    highest_serial = existing_students.order_by('-serial_number').first()

                    if highest_serial and highest_serial.serial_number.isdigit():
                        start_number = max(start_number, int(highest_serial.serial_number) + 1)

                    created_count = 0
                    for i in range(count):
                        serial_number = str(start_number + i)
                        # Check if student with this serial already exists
                        if not Student.objects.filter(faculty=faculty, serial_number=serial_number).exists():
                            Student.objects.create(
                                faculty=faculty,
                                serial_number=serial_number,
                                name=f"طالب {serial_number}" if gender == 'M' else f"طالبة {serial_number}",  # Update name based on gender
                                gender=gender  # Set the gender
                            )
                            created_count += 1

                    gender_text = "طالب" if gender == 'M' else "طالبة"
                    messages.success(
                        request,
                        f"تم إنشاء {created_count} {gender_text} بنجاح للكلية {faculty.name} بأرقام تسلسلية من {start_number} إلى {start_number + created_count - 1}"
                    )
                    return redirect('student_stats')
            except Exception as e:
                messages.error(request, f"حدث خطأ أثناء إنشاء الطلاب: {str(e)}")

    context = {
        'form': form,
    }

    return render(request, 'assignments/student_create.html', context)


@require_POST
def student_delete_all(request, faculty_id):
    """Delete all students for a specific faculty"""
    faculty = get_object_or_404(Faculty, id=faculty_id)

    try:
        count = Student.objects.filter(faculty=faculty).count()
        Student.objects.filter(faculty=faculty).delete()
        messages.success(request, f"تم حذف جميع الطلاب ({count}) من كلية {faculty.name} بنجاح")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('student_stats')
    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء حذف الطلاب: {str(e)}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('student_stats')


def assignment_list(request):
    """View to display all assignments"""
    assignments = Assignment.objects.select_related('student', 'research', 'student__faculty').all().order_by('-assigned_date')

    # Filter by faculty if specified
    faculty_filter = request.GET.get('faculty', None)
    research_filter = request.GET.get('research', None)

    if faculty_filter:
        assignments = assignments.filter(student__faculty_id=faculty_filter)

    if research_filter:
        assignments = assignments.filter(research_id=research_filter)

    # Pagination
    paginator = Paginator(assignments, 25)  # 25 assignments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get faculties and researches for filters
    faculties = Faculty.objects.all()
    researches = Research.objects.all()

    # Statistics
    assignment_count = assignments.count()
    student_count = Student.objects.count()
    unassigned_students = Student.objects.exclude(id__in=Assignment.objects.values('student')).count()

    context = {
        'page_obj': page_obj,
        'total_count': assignment_count,
        'faculties': faculties,
        'researches': researches,
        'faculty_filter': int(faculty_filter) if faculty_filter and faculty_filter.isdigit() else None,
        'research_filter': int(research_filter) if research_filter and research_filter.isdigit() else None,
        'student_count': student_count,
        'unassigned_students': unassigned_students,
    }

    return render(request, 'assignments/assignment_list.html', context)


@transaction.atomic
@require_POST
def assignment_randomize(request):
    """View to randomly assign researches to students"""
    try:
        # Get all students and researches
        students = Student.objects.filter(assignments=None)  # Only unassigned students
        researches = Research.objects.all()

        if not students or not researches:
            messages.warning(request, "لا يوجد طلاب بدون تعيينات أو لا توجد بحوث متاحة للتعيين.")
            return redirect('assignment_list')

        # Delete existing assignments if requested
        if request.POST.get('clear_existing', False) == 'true':
            removed_count = Assignment.objects.all().count()
            Assignment.objects.all().delete()
            messages.success(request, f"تم حذف {removed_count} تعيين سابق.")
            # Now get all students since we've cleared assignments
            students = Student.objects.all()

        # Get group size
        group_size = int(request.POST.get('group_size', 1))

        # Perform the random assignment with group size
        success_count, error_count = randomly_assign_researches(students, researches, group_size=group_size)

        # Show message
        if group_size > 1:
            messages.success(
                request,
                f"تم تعيين البحوث بشكل عشوائي لـ {success_count} طالب في مجموعات من {group_size} طلاب لكل بحث (من نفس الكلية). "
                f"فشل التعيين لـ {error_count} طالب."
            )
        else:
            messages.success(
                request,
                f"تم تعيين البحوث بشكل عشوائي لـ {success_count} طالب بنجاح. فشل التعيين لـ {error_count} طالب."
            )

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء تعيين البحوث: {str(e)}")

    return redirect('assignment_list')


@require_POST
def assignment_delete_all(request):
    """View to delete all assignments"""
    try:
        count = Assignment.objects.count()
        Assignment.objects.all().delete()
        messages.success(request, f"تم حذف جميع التعيينات ({count}) بنجاح.")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        return redirect('assignment_list')

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء حذف التعيينات: {str(e)}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('assignment_list')
