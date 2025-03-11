from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from faculties.models import Faculty
from faculties.forms import FacultyForm


def faculty_list(request):
    """View to display all faculties"""
    faculties = Faculty.objects.all().order_by('name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        faculties = faculties.filter(name__icontains=search_query) | faculties.filter(code__icontains=search_query)

    # Pagination
    paginator = Paginator(faculties, 10)  # 10 faculties per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Initialize the form for the create modal
    form = FacultyForm()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'form': form,
        'total_count': faculties.count(),
    }

    return render(request, 'faculties/faculty_list.html', context)


@require_POST
def faculty_create(request):
    """View to create a new faculty"""
    form = FacultyForm(request.POST)

    if form.is_valid():
        form.save()
        messages.success(request, 'تم إنشاء الكلية بنجاح')
        return redirect('faculty_list')

    # If form is invalid, return to the list page with the form errors
    faculties = Faculty.objects.all().order_by('name')
    paginator = Paginator(faculties, 10)
    page_obj = paginator.get_page(1)

    context = {
        'page_obj': page_obj,
        'form': form,
        'total_count': faculties.count(),
    }

    messages.error(request, 'حدثت مشكلة أثناء إنشاء الكلية، يرجى التحقق من البيانات المدخلة')
    return render(request, 'faculties/faculty_list.html', context)


@require_POST
def faculty_delete(request, pk):
    """View to delete a faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)

    try:
        faculty_name = faculty.name
        faculty.delete()
        messages.success(request, f'تم حذف الكلية "{faculty_name}" بنجاح')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('faculty_list')
    except Exception as e:
        messages.error(request, f'حدثت مشكلة أثناء حذف الكلية: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('faculty_list')
