from django.urls import path
from . import views

app_name = 'landing_page'
urlpatterns = [
    path('', views.home, name='home'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('about/', views.about, name='about'),
]