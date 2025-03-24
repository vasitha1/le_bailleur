import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json


def send_whatsapp_message(phone_number, message):
    """Function to send a message via WhatsApp."""
    headers = {'Authorization': settings.WHATSAPP_TOKEN}
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': phone_number,
        'type': 'text',
        'text': {'body': message}
    }
    
    try:
        response = requests.post(settings.WHATSAPP_URL, headers=headers, json=payload)
        print(f"Response Status Code: {response.status_code}")  # for debugging
        print(f"Response Content: {response.text}")  # For debugging
        
        if response.status_code == 200:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            return response_json
        else:
            print(f"Error: Non-200 response code")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None

def subscribe_to_webhook():  
    """Subscribe your app to the WhatsApp Business Account webhooks."""  
    url = f"https://graph.facebook.com/v12.0/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/subscribed_apps"  
    headers = {  
        'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',  # Ensure you set ACCESS_TOKEN in settings.py  
        'Content-Type': 'application/json'  
    }  
    data = {  
        "app_id": settings.WHATSAPP_APP_ID  # Set YOUR_APP_ID in settings.py  
    }  
    
    response = requests.post(url, headers=headers, json=data)  
    
    if response.status_code == 200:  
        print("Successfully subscribed to webhook.")  
    else:  
        print(f"Error subscribing to webhook: {response.status_code}, {response.text}")  


def get_or_create_session(whatsapp_number):
    """
    Get or create a session for the given WhatsApp number.
    Always reset or update the session to ensure it's current.
    """
    from .models import Session  # Import here to avoid circular imports

    try:
        session = Session.objects.get(whatsapp_number=whatsapp_number)
    except Session.DoesNotExist:
        # Create new session if it doesn't exist
        session = Session.objects.create(
            whatsapp_number=whatsapp_number,
            current_state='welcome',
        )
    
    # Always update the last activity
    session.last_activity = timezone.now()
    session.save()
    
    return session


def check_session_expiry(session):
    """
    Check if session has expired due to inactivity.
    Returns True if session has expired, False otherwise.
    """
    # Define inactivity timeout (10 minutes)
    INACTIVITY_TIMEOUT = timezone.timedelta(minutes=10)
    
    # Check if session is expired
    if timezone.now() - session.last_activity > INACTIVITY_TIMEOUT:
        # Send expiry message
        send_whatsapp_message(
            session.whatsapp_number,
            "Your session has expired due to 10 minutes of inactivity. Restarting session."
        )
        
        return True
    
    return False

    
def generate_receipt_number():
    """Generate a unique receipt number."""
    return f"RCP-{uuid.uuid4().hex[:8].upper()}"

def format_menu(title, options):
    """Format a menu with options."""
    menu_text = f"{title}\n\n"
    for key, value in options.items():
        menu_text += f"Type {key} to {value}\n"
    
    return menu_text

def landlord_main_menu(landlord_name=""):
    """Generate the main menu for landlords."""
    title = f"Welcome Back {landlord_name}" if landlord_name else "Thank you for registering your first tenant."
    
    options = {
        "1": "register another property or delete an existing one",
        "2": "register another rent entity or delete an existing one",
        "3": "register another tenant or delete an existing one",
        "4": "see the rent status of all tenants in your property",
        "5": "see the rent status of all owing tenants in your property",
        "6": "see the rent status of the tenant of a particular rent entity",
        "7": "visit our website and learn more about how to manage this property",
        "8": "contact customer support",
        "9": "signal rent payment and update the status of a tenant",
        "10": "exit"
    }
    
    return format_menu(title, options)
