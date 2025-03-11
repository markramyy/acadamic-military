from django.urls import path
from . import views

urlpatterns = [
    path('', views.faculty_list, name='faculty_list'),
    path('create/', views.faculty_create, name='faculty_create'),
    path('delete/<int:pk>/', views.faculty_delete, name='faculty_delete'),
]
