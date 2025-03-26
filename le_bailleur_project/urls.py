"""
URL configuration for le_bailleur_project project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('properties.urls')),
    path('', include('landing_page.urls')),

]
