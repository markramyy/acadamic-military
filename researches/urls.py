from django.urls import path
from . import views

urlpatterns = [
    path('', views.research_list, name='research_list'),
    path('create/', views.research_create, name='research_create'),
    path('delete/<int:pk>/', views.research_delete, name='research_delete'),
    path('delete-all/', views.research_delete_all, name='research_delete_all'),
    path('import/', views.research_import, name='research_import'),
    path('sample-csv/', views.research_sample_csv, name='research_sample_csv'),
]
