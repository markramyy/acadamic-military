from django.urls import path
from . import views

urlpatterns = [
    # Student management
    path('students/', views.student_stats, name='student_stats'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/delete-all/<int:faculty_id>/', views.student_delete_all, name='student_delete_all'),

    # Assignment management
    path('', views.assignment_list, name='assignment_list'),
    path('randomize/', views.assignment_randomize, name='assignment_randomize'),
    path('delete-all/', views.assignment_delete_all, name='assignment_delete_all'),
]
