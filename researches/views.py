from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse

import pandas as pd
import csv

from .models import Research
from .forms import ResearchForm


def research_list(request):
    """View to display all researches"""
    researches = Research.objects.all().order_by('name')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        researches = researches.filter(name__icontains=search_query)

    # Pagination
    paginator = Paginator(researches, 10)  # 10 researches per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Initialize the form for the create modal
    form = ResearchForm()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'form': form,
        'total_count': researches.count(),
    }

    return render(request, 'researches/research_list.html', context)


@require_POST
def research_create(request):
    """View to create a new research"""
    form = ResearchForm(request.POST)

    if form.is_valid():
        # Check if research with this name already exists
        name = form.cleaned_data['name']
        if Research.objects.filter(name__iexact=name).exists():
            form.add_error('name', 'بحث بهذا الاسم موجود بالفعل')
            messages.error(request, 'هناك بحث بهذا الاسم موجود بالفعل')
        else:
            form.save()
            messages.success(request, 'تم إنشاء البحث بنجاح')
            return redirect('research_list')

    # If form is invalid, return to the list page with the form errors
    researches = Research.objects.all().order_by('name')
    paginator = Paginator(researches, 10)
    page_obj = paginator.get_page(1)

    context = {
        'page_obj': page_obj,
        'form': form,
        'total_count': researches.count(),
    }

    if not messages.get_messages(request):
        messages.error(request, 'حدثت مشكلة أثناء إنشاء البحث، يرجى التحقق من البيانات المدخلة')
    return render(request, 'researches/research_list.html', context)


@require_POST
def research_delete(request, pk):
    """View to delete a research"""
    research = get_object_or_404(Research, pk=pk)

    try:
        research_name = research.name
        research.delete()
        messages.success(request, f'تم حذف البحث "{research_name}" بنجاح')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('research_list')
    except Exception as e:
        messages.error(request, f'حدثت مشكلة أثناء حذف البحث: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('research_list')


@require_POST
def research_delete_all(request):
    """View to delete all researches"""
    try:
        count = Research.objects.count()
        if count == 0:
            messages.info(request, 'لا توجد بحوث لحذفها')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'لا توجد بحوث لحذفها'})
            return redirect('research_list')

        Research.objects.all().delete()
        messages.success(request, f'تم حذف {count} بحث بنجاح')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        return redirect('research_list')
    except Exception as e:
        messages.error(request, f'حدثت مشكلة أثناء حذف البحوث: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        return redirect('research_list')


@transaction.atomic
@require_POST
def research_import(request):
    """View to import researches from a file"""
    if 'file' not in request.FILES:
        messages.error(request, 'يرجى تحديد ملف للاستيراد')
        return redirect('research_list')

    file = request.FILES['file']
    file_extension = file.name.split('.')[-1].lower()
    imported_count = 0
    duplicate_count = 0
    error_count = 0

    try:
        if file_extension == 'csv':
            encodings = ['utf-8-sig', 'utf-8', 'windows-1256', 'utf-16', 'iso-8859-1']
            for encoding in encodings:
                try:
                    file.seek(0)
                    data = pd.read_csv(file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise UnicodeDecodeError("Unable to decode the CSV file with any of the attempted encodings.")
            # Strip whitespace from column names to avoid mismatches
            data.columns = data.columns.str.strip()
        elif file_extension in ['xlsx', 'xls']:
            data = pd.read_excel(file)
            data.columns = data.columns.str.strip()
        elif file_extension == 'txt':
            encodings = ['utf-8-sig', 'utf-8', 'windows-1256', 'utf-16', 'iso-8859-1']
            for encoding in encodings:
                try:
                    file.seek(0)
                    content = file.read().decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise UnicodeDecodeError("Unable to decode the text file with any of the attempted encodings.")
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            data = pd.DataFrame({'اسم البحث': lines})
        else:
            messages.error(request, f'نوع الملف {file_extension} غير مدعوم. الأنواع المدعومة هي CSV، Excel، TXT')
            return redirect('research_list')

        # Define a list of acceptable column names for the research title
        valid_keys = ['اسم البحث', 'البحث', 'البحوث', 'الابحاث العلمية', 'اسم الورقة البحثية']

        # Process the data to create Research records
        for index, row in data.iterrows():
            name = None
            # Check each possible column header until one with a value is found
            for key in valid_keys:
                name = row.get(key)
                if pd.notna(name) and str(name).strip():
                    name = str(name).strip()
                    break

            if name:
                if not Research.objects.filter(name__iexact=name).exists():
                    Research.objects.create(name=name)
                    imported_count += 1
                else:
                    duplicate_count += 1

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء استيراد الملف: {str(e)}')
        error_count += 1

    messages.success(request, f'تم استيراد {imported_count} بحث. تم تجاهل {duplicate_count} بحث مكرر.')
    return redirect('research_list')


def research_sample_csv(request):
    """Generate and return a sample CSV file for research import"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_researches.csv"'

    # Use utf-8-sig encoding to include BOM for Excel compatibility
    response.write(u'\ufeff'.encode('utf-8'))

    writer = csv.writer(response)
    writer.writerow(['اسم البحث'])  # Header row
    sample_researches = [
        'أنظمة الذكاء الاصطناعي في المجال العسكري',
        'التكنولوجيا الحديثة في الدفاع الجوي',
        'إدارة الأزمات العسكرية',
        'الأمن السيبراني والحروب الإلكترونية',
        'تطوير المعدات العسكرية'
    ]
    for research in sample_researches:
        writer.writerow([research])

    return response