from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Tenant, Session
from .utils import send_whatsapp_message

@shared_task
def check_due_rent_and_notify():
    """Periodically check and notify tenants about due rents."""
    tenants = Tenant.objects.all()
    
    for tenant in tenants:
        if tenant.is_rent_due():
            # Get landlord details
            landlord = tenant.rent_entity.property.landlord
            property_name = tenant.rent_entity.property.name
            rent_entity_name = tenant.rent_entity.name
            rent_amount = tenant.rent_entity.rent_amount
            
            # Format due date nicely
            actual_due_date = tenant.calculate_actual_due_date()
            formatted_date = actual_due_date.strftime("%d %B, %Y")
            
            # Notify tenant
            tenant_message = (
                f"Dear {tenant.name},\n\n"
                f"Your rent of {rent_amount} for {rent_entity_name} at {property_name} is due on {formatted_date}.\n\n"
                f"Please respond:\n"
                f"1 - If you have already paid\n"
                f"2 - To set a payment date"
            )
            send_whatsapp_message(tenant.whatsapp_number, tenant_message)
            
            # Notify landlord
            landlord_message = (
                f"Dear {landlord.name},\n\n"
                f"Tenant {tenant.name}'s rent of {rent_amount} for {rent_entity_name} at {property_name} "
                f"is due on {formatted_date}."
            )
            send_whatsapp_message(landlord.whatsapp_number, landlord_message)


@shared_task
def check_bills_due_and_notify():
    """Periodically check and notify tenants about due bills."""
    tenants = Tenant.objects.all()
    
    for tenant in tenants:
        if tenant.is_bills_due():
            # Get landlord details
            landlord = tenant.rent_entity.property.landlord
            property_name = tenant.rent_entity.property.name
            
            # Format due date nicely
            formatted_date = tenant.bills_due_date.strftime("%d %B, %Y")
            
            # Notify tenant
            tenant_message = (
                f"Dear {tenant.name},\n\n"
                f"Your bills for {property_name} are due on {formatted_date}."
            )
            send_whatsapp_message(tenant.whatsapp_number, tenant_message)
            
            # Notify landlord
            landlord_message = (
                f"Dear {landlord.name},\n\n"
                f"Tenant {tenant.name}'s bills for {property_name} are due on {formatted_date}."
            )
            send_whatsapp_message(landlord.whatsapp_number, landlord_message)


@shared_task
def expire_inactive_sessions():
    """Check for inactive sessions and expire them."""
    # Find sessions that have been inactive for more than 10 minutes
    cutoff_time = timezone.now() - timedelta(minutes=10)
    inactive_sessions = Session.objects.filter(
        last_activity__lt=cutoff_time,
        current_state__ne='logged_out'
    )
    
    for session in Session.objects.filter(last_activity__lt=cutoff_time):
        # Skip already logged out sessions
        if session.current_state == 'logged_out':
            continue
            
        # Notify the user
        send_whatsapp_message(
            session.whatsapp_number,
            "Your session has expired due to 10 minutes of inactivity. You have been logged out."
        )
        
        # Reset or update session state
        if session.is_landlord:
            session.current_state = 'logged_out'
        else:
            session.current_state = 'welcome'
            session.context_data = {}
        
        session.save()