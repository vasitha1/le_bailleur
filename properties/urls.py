from django.urls import path  
from . import views  

app_name = 'properties'
urlpatterns = [
    path('d11c683a-1ec0-4a7d-b69f-d99cb67ceed0', views.HomeView.as_view(), name='home'),
    path('properties/', views.PropertyListCreate.as_view(), name='property-list-create'),  
    path('properties/<int:pk>/', views.PropertyRetrieveUpdateDestroy.as_view(), name='property-retrieve-update-destroy'),  
    path('tenants/', views.TenantListCreate.as_view(), name='tenant-list-create'),  
    path('tenants/<int:pk>/', views.TenantRetrieveUpdateDestroy.as_view(), name='tenant-retrieve-update-destroy'),  
    path('landlords/create/', views.CreateLandlord.as_view(), name='create_landlord'),  
    path('landlords/', views.LandlordList.as_view(), name='list_landlords'), 
    path('webhook/', views.WhatsAppWebhook.as_view(), name='whatsapp_webhook'), 

]  