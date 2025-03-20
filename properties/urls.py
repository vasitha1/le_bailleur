from django.urls import path  
from . import views, utils

app_name = 'properties'  

urlpatterns = [  
    # Home view  
    path('d11c683a-1ec0-4a7d-b69f-d99cb67ceed0/', views.HomeView.as_view(), name='home'),  
    
    # Property management  
    path('properties/', views.PropertyListCreate.as_view(), name='property-list-create'),  
    path('properties/<int:pk>/', views.PropertyRetrieveUpdateDestroy.as_view(), name='property-retrieve-update-destroy'),  

    # Rent entity management  
    path('rent-entities/', views.RentEntityListCreate.as_view(), name='rent-entity-list-create'),  
    path('rent-entities/<int:pk>/', views.RentEntityRetrieveUpdateDestroy.as_view(), name='rent-entity-retrieve-update-destroy'),  

    # Tenant management  
    path('tenants/', views.TenantListCreate.as_view(), name='tenant-list-create'),  
    path('tenants/<int:pk>/', views.TenantRetrieveUpdateDestroy.as_view(), name='tenant-retrieve-update-destroy'),  

    # Landlord management  
    path('landlords/create/', views.CreateLandlord.as_view(), name='create_landlord'),  
    path('landlords/', views.LandlordList.as_view(), name='list_landlords'),   

     # For webhook verification and basic message processing
    path('webhook/', utils.whatsapp_webhook, name='whatsapp_webhook'),
    
    # For your full class-based implementation
    path('api/webhook/', views.WhatsAppWebhook.as_view(), name='whatsapp_api_webhook'),
]    