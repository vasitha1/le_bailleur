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



@csrf_exempt
def whatsapp_webhook(request):
    """Handle WhatsApp webhook verification and incoming messages."""
    VERIFY_TOKEN = '7e5de035-f7ed-4737-b2bf-fc71b9cb1e63'
    
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse('Error: token verification failed', status=403)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process the incoming webhook data
            if 'object' in data and 'entry' in data:
                if data['object'] == 'whatsapp_business_account':
                    for entry in data['entry']:
                        sender_number = entry['changes'][0]['value']['metadata']['phone_number_id']
                        message_text = entry['changes'][0]['value']['messages'][0]['text']['body']
                        
                        # Import and process the message
                        from .views import WhatsAppWebhook
                        webhook_handler = WhatsAppWebhook()
                        response = webhook_handler.process_message(message_text, sender_number)
                        
                        # If you want to send a reply
                        phone_number = '23798827753'  # Consider using the sender_number instead
                        message = 'Re: Thank you Felsi!' # Use the response from process_message
                        
                        # Add code to send the response back using WhatsApp API
                        send_message(message, phone_number)
                        
            # Always return a 200 OK for webhook requests
            return HttpResponse('Success', status=200)
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return HttpResponse(f"Error: {str(e)}", status=500)
    
    return HttpResponse('Method not allowed', status=405)


def get_or_create_session(whatsapp_number):
    """Get or create a session for the given WhatsApp number."""
    from .models import Session  # Import here to avoid circular imports
    
    try:
        session = Session.objects.get(whatsapp_number=whatsapp_number)
        # Update last activity
        session.last_activity = timezone.now()
        session.save()
    except Session.DoesNotExist:
        # Create new session
        session = Session.objects.create(
            whatsapp_number=whatsapp_number,
            current_state='welcome',
        )
    
    return session

def check_session_expiry(session):
    """Check if session has expired and reset if needed."""
    if session.is_expired():
        # Send message about session expiry
        send_whatsapp_message(
            session.whatsapp_number, 
            "Your session has expired due to 10 minutes of inactivity. You have been logged out."
        )
        
        # Reset or update session as needed
        if session.is_landlord:
            # For registered users, just update the state
            session.current_state = 'logged_out'
            session.save()
            return True
        else:
            # For unregistered users, reset the session
            session.current_state = 'welcome'
            session.context_data = {}
            session.save()
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
