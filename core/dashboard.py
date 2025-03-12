from django.shortcuts import render
from django.core.paginator import Paginator
# from django.db.models import Count
from django.db.models import Q

from faculties.models import Faculty
from researches.models import Research
from assignments.models import Student, Assignment


def get_dashboard_stats():
    """
    Get statistics for the dashboard
    """
    stats = {
        'faculty_count': Faculty.objects.count(),
        'research_count': Research.objects.count(),
        'student_count': Student.objects.count(),
        'male_count': Student.objects.filter(gender='M').count(),
        'female_count': Student.objects.filter(gender='F').count(),
    }

    return stats


def get_faculty_research_assignments():
    """
    Get a structured representation of assignments by faculty and research
    Returns a dictionary with faculty data and the complete list of researches
    """
    faculties = Faculty.objects.all()
    researches = Research.objects.all().order_by('name')

    faculty_data = []

    for faculty in faculties:
        faculty_info = {
            'id': faculty.id,
            'name': faculty.name,
            'code': faculty.code,
            'student_count': Student.objects.filter(faculty=faculty).count(),
            'assigned_count': Assignment.objects.filter(student__faculty=faculty).count(),
            'assignments_by_research': {}
        }

        # Get assignments for this faculty grouped by research
        for research in researches:
            # Get all students from this faculty assigned to this research
            assignments = Assignment.objects.filter(
                student__faculty=faculty,
                research=research
            ).select_related('student')

            # Store assignments info
            if assignments.exists():
                faculty_info['assignments_by_research'][research.id] = {
                    'count': assignments.count(),
                    'students': [
                        {
                            'id': assignment.student.id,
                            'name': assignment.student.name,
                            'serial': assignment.student.serial_number
                        } for assignment in assignments
                    ]
                }
            else:
                faculty_info['assignments_by_research'][research.id] = {
                    'count': 0,
                    'students': []
                }

        faculty_data.append(faculty_info)

    return {
        'faculties': faculty_data,
        'researches': list(researches)
    }


def get_filtered_assignments(request, gender, faculty_param_name, research_param_name, page_param_name, serial_param_name=None):
    faculty_filter = request.GET.get(faculty_param_name)
    research_filter = request.GET.get(research_param_name)
    serial_filter = request.GET.get(serial_param_name)

    # Get assignments for this gender
    assignments = Assignment.objects.select_related(
        'student', 'student__faculty', 'research'
    ).filter(student__gender=gender).order_by('-assigned_date', 'research__name', 'student__faculty__name')

    # Apply additional filters
    if faculty_filter:
        assignments = assignments.filter(student__faculty_id=faculty_filter)

    if research_filter:
        assignments = assignments.filter(research_id=research_filter)

    # Apply serial number filter if provided
    if serial_filter and serial_filter.strip():
        # Get the exact serial number across all faculties
        assignments = assignments.filter(student__serial_number=serial_filter.strip())

    # Get unique research-group-faculty combinations
    unique_research_groups = assignments.values('research_id', 'group_id', 'student__faculty_id').distinct()

    # Paginate
    page_size = 10
    paginator = Paginator(unique_research_groups, page_size)
    page_number = request.GET.get(page_param_name, 1)
    page_obj = paginator.get_page(page_number)

    # Get assignments for current page
    if list(page_obj):
        query = Q()
        for item in page_obj:
            research_id = item['research_id']
            group_id = item['group_id']
            faculty_id = item['student__faculty_id']

            if group_id is None:
                query |= Q(research_id=research_id, group_id__isnull=True,
                           student__faculty_id=faculty_id)
            else:
                query |= Q(research_id=research_id, group_id=group_id,
                           student__faculty_id=faculty_id)

        page_assignments = assignments.filter(query).order_by('research__name', 'student__faculty__name')
        page_obj.object_list = page_assignments
    else:
        page_obj.object_list = Assignment.objects.none()

    return {
        'page_obj': page_obj,
        'faculty_filter': faculty_filter,
        'research_filter': research_filter,
        'serial_filter': serial_filter,
        'total_count': unique_research_groups.count(),
        'page_size': page_size
    }


def dashboard(request):
    # Get statistics
    stats = get_dashboard_stats()

    # Get faculty-research assignments
    faculty_research_data = get_faculty_research_assignments()

    # Get active gender tab
    active_gender = request.GET.get('gender', 'M')  # Default to male tab

    # Get filtered assignments for male and female students
    male_data = get_filtered_assignments(request, 'M', 'faculty_m', 'research_m', 'page_m', 'serial_m')
    female_data = get_filtered_assignments(request, 'F', 'faculty_f', 'research_f', 'page_f', 'serial_f')

    # Get all faculties and researches for filters
    faculties = Faculty.objects.filter(students__isnull=False).distinct().order_by('name')
    researches = Research.objects.all().order_by('name')

    context = {
        'stats': stats,
        'faculties': faculty_research_data['faculties'],
        'researches': faculty_research_data['researches'],
        'filter_faculties': faculties,
        'filter_researches': researches,

        # Male tab data
        'male_page_obj': male_data['page_obj'],
        'faculty_filter_m': male_data['faculty_filter'],
        'research_filter_m': male_data['research_filter'],
        'serial_filter_m': male_data['serial_filter'],
        'male_total_count': male_data['total_count'],
        'male_page_size': male_data['page_size'],

        # Female tab data
        'female_page_obj': female_data['page_obj'],
        'faculty_filter_f': female_data['faculty_filter'],
        'research_filter_f': female_data['research_filter'],
        'serial_filter_f': female_data['serial_filter'],
        'female_total_count': female_data['total_count'],
        'female_page_size': female_data['page_size'],

        # Active gender for tab selection
        'active_gender': active_gender,
    }

    return render(request, 'dashboard.html', context)
