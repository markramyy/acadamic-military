from django.urls import path
from core.dashboard import dashboard
from core import views

urlpatterns = [
    path('', dashboard, name='home'),
    path('export/assignments/pdf/', views.export_assignments_pdf, name='export_assignments_pdf'),
    path('export/assignments/csv/', views.export_assignments_csv, name='export_assignments_csv'),
]
