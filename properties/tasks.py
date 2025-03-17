from celery import shared_task  
from .models import Tenant, Landlord
from .utils import send_whatsapp_message  # Adjust based on your structure  

@shared_task
def check_due_rent_and_notify():
    """Periodically check and notify tenants about due rents."""
    tenants = Tenant.objects.all()
    for tenant in tenants:
        if tenant.is_rent_due():
            actual_due_date = tenant.calculate_actual_due_date() 
            message_tenant = f"Dear {tenant.name}, your rent of {tenant.rent_amount} is due on {actual_due_date}."
            send_whatsapp_message(tenant.whatsapp_number, message_tenant)
            message_landlord = f"Dear {landlord.name}, {tenant.name}rent of {tenant.rent_amount} is due on {actual_due_date}. Please help us confirmed that this landlord paid with the number of months paid otherwise, we will keep notifying you and the tenant too."
