from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('faculties/', include('faculties.urls')),
    path('researches/', include('researches.urls')),
    path('assignments/', include('assignments.urls')),
]
