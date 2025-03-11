from django.urls import path
from . import views

urlpatterns = [
    path('export-database/', views.export_database, name='export_database'),
    path('reset-database/', views.reset_database, name='reset_database'),
]
