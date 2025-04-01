from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.utils import timezone
from django.db import transaction
from dateutil.relativedelta import relativedelta
from .models import Property, Tenant, Landlord, RentEntity, PaymentReceipt, WhatsAppMessage
from .serializers import (
    PropertySerializer, TenantSerializer, LandlordSerializer, 
    RentEntitySerializer, PaymentReceiptSerializer
)
from .utils import (
    send_whatsapp_message, get_or_create_session, check_session_expiry,
    landlord_main_menu, generate_receipt_number, format_menu,
)
import json
import logging  
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import sys

class CreateLandlord(generics.CreateAPIView):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer

class LandlordList(generics.ListAPIView):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer

class PropertyListCreate(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

class PropertyRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

class RentEntityListCreate(generics.ListCreateAPIView):
    queryset = RentEntity.objects.all()
    serializer_class = RentEntitySerializer

class RentEntityRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = RentEntity.objects.all()
    serializer_class = RentEntitySerializer

class TenantListCreate(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

class TenantRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

class PaymentReceiptListCreate(generics.ListCreateAPIView):
    queryset = PaymentReceipt.objects.all()
    serializer_class = PaymentReceiptSerializer


logging.basicConfig(
    filename="whatsapp_webhook.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WhatsAppWebhook(APIView):
    """Handle WhatsApp webhook messages after verification."""
    
    VERIFY_TOKEN = settings.WHATSAPP_VERIFY_TOKEN
        
    def get(self, request, *args, **kwargs):
        """Verify the webhook with GET request."""
        logging.info("Received GET request for webhook verification")
        
        # Log request details for debugging
        logging.debug("Request received: %s", repr(request))
        with open("request_log.txt", "a") as f:
            f.write(repr(request) + "\n")
        
        # Extract verification parameters
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        logging.info(f"Verification attempt - Mode: {mode}, Token: {token[:4]}..., Challenge: {challenge}")
        
        if mode == 'subscribe' and token == self.VERIFY_TOKEN:
            logging.info("Webhook verification successful")
            return HttpResponse(challenge, status=200)
        else:
            logging.warning("Webhook verification failed")
            return JsonResponse({'error': 'token verification failed'}, status=403)
    
    def post(self, request):
        current_state = 'initial'
        if current_state:
            message_text = message_text.lower()
            
            if 'hi' in ['hi', 'hello', 'start', 'hey']:
                send_whatsapp_message(sender_number, welcome_message)
                return Response({"status": "welcome_sent"})
            else:
                # Check for session expiration before handling message
                if self.is_expired(sender_number):
                    # Reset state to initial and inform user
                    self.reset_user_state(sender_number)
                    send_whatsapp_message(
                        sender_number,
                        "Your session has expired due to inactivity. Welcome back to the main menu."
                    )
            # For landlords, go directly to main menu instead of initial state
            user_type = self.get_user_type(sender_number)
                if user_type == 'landlord':
                    return self.handle_main_menu(message_text, sender_number)
                return Response({"status": "session_expired"})
                result = self.handle_message(message_text, sender_number)
        
        elif current_state == 'landlord_name':
            result = self.handle_landlord_name(message_text, sender_number)
        
        elif current_state == 'property_name':
            result = self.handle_property_name(message_text, sender_number)
        
        elif current_state == 'property_address':
            result = self.handle_property_address(message_text, sender_number)
        
        elif current_state == 'welcome':
            result = self.handle_main_menu(message_text, sender_number)

         elif current_state == 'landlord_menu':
            result = self.handle_main_menu(message_text, sender_number)
        # Add more state handlers as needed for various flows
        
        else:
            # Default handling for unknown states
            send_whatsapp_message(sender_number, welcome_message)
        
        # Reset user state
        if user_type == 'landlord':
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            landlord.current_state = 'initial'
            landlord.save()
        
        elif user_type == 'tenant':
            tenant = Tenant.objects.get(whatsapp_number=sender_number)
            tenant.current_state = 'initial'
            tenant.save()
        
        else:
            unidentified = UnidentifiedUser.objects.get(whatsapp_number=sender_number)
            unidentified.current_state = 'initial'
            unidentified.save()
        
        result = {"status": "reset_to_initial"}
        
        return Response(result)
    
    def handle_message(self, message_text, sender_number):
        """Handle the initial message to determine if user is landlord or tenant."""
        
        if message_text == "1":
            # Try to get existing landlord or create a new unidentified user
            try:
                landlord = Landlord.objects.get(whatsapp_number=sender_number)
                landlord.current_state = 'landlord_name' if not landlord.name else 'welcome'
                landlord.last_activity = timezone.now()  # Update last activity timestamp
                landlord.save()
                
                if not landlord.name:
                    send_whatsapp_message(
                        sender_number,
                        "Great! Let's set up your landlord account. Please enter your full name:"
                    )
                else:
                    send_whatsapp_message(
                        sender_number,
                        f"Welcome back, {landlord.name}! Would you like to add a new property? Please enter the property name:"
                    )
            except Landlord.DoesNotExist:
                # Create a new landlord with initial state
                landlord = Landlord.objects.create(
                    whatsapp_number=sender_number,
                    current_state='landlord_name',
                    last_activity=timezone.now()  # Set initial activity timestamp
                )
                send_whatsapp_message(
                    sender_number,
                    "Great! Let's set up your landlord account. Please enter your full name:"
                )
            return {"status": "processing_landlord"}
            
        elif message_text == "2":
            # Try to get existing tenant or create a new unidentified user
            try:
                tenant = Tenant.objects.get(whatsapp_number=sender_number)
                tenant.current_state = 'tenant_menu'
                landlord.last_activity = timezone.now()  # Update last activity timestamp
                tenant.save()
                
                send_whatsapp_message(
                    sender_number,
                    f"Welcome back, {tenant.name}! What would you like to do? Reply with:\n1. Check rent status\n2. Check bill status\n3. View payment history"
                )
            except Tenant.DoesNotExist:
                # This is a new tenant
                unidentified, created = UnidentifiedUser.objects.get_or_create(whatsapp_number=sender_number)
                unidentified.context_data['user_type'] = 'tenant'
                unidentified.current_state = 'tenant_info'
                unidentified.save()
                
                send_whatsapp_message(
                    sender_number,
                    "Please contact your landlord to register you in their property."
                )
                send_whatsapp_message(
                    sender_number, 
                    "Once they have added you as a tenant, you'll receive a confirmation message."
                )
            
            return {"status": "tenant_selected"}
            
        else:
            # Invalid selection
            send_whatsapp_message(
                sender_number,
                "Invalid response, please type only '1' if you are a landlord or '2' if you are a tenant."
            )
            return {"status": "invalid_selection"}
        
        return {"status": "message_handled"}

    def is_expired(self, sender_number):
        """Check if user session has expired (inactive for more than 10 minutes)"""
        try:
            # Try to find user in any of the user models
            for model in [Landlord, Tenant, UnidentifiedUser]:
                try:
                    user = model.objects.get(whatsapp_number=sender_number)
                    if user.last_activity:
                        # Check if last activity was more than 10 minutes ago
                        time_diff = timezone.now() - user.last_activity
                        return time_diff.total_seconds() > 600  # 10 minutes in seconds
                    return False  # No last_activity recorded
                except model.DoesNotExist:
                    continue
            return False  # User not found in any model
        except Exception as e:
            # Log the error and default to non-expired for safety
            print(f"Error checking session expiration: {e}")
            return False
    
    def reset_user_state(self, sender_number):
        """Reset user state to initial when session expires"""
        for model in [Landlord, Tenant, UnidentifiedUser]:
            try:
                user = model.objects.get(whatsapp_number=sender_number)
                user.current_state = 'initial'
                user.last_activity = timezone.now()  # Update timestamp
                user.save()
                return True
            except model.DoesNotExist:
                continue
        return False
    
    def get_user_type(self, sender_number):
        """Determine if the user is a landlord, tenant, or unidentified"""
        try:
            if Landlord.objects.filter(whatsapp_number=sender_number).exists():
                return 'landlord'
            elif Tenant.objects.filter(whatsapp_number=sender_number).exists():
                return 'tenant'
            else:
                return 'unidentified'
        except Exception:
            return 'unidentified'
    
    def handle_main_menu(self, message_text, sender_number):
        """Handle main menu options for all users"""
        user_type = self.get_user_type(sender_number)
        
        # Update last activity timestamp
        if user_type == 'landlord':
            user = Landlord.objects.get(whatsapp_number=sender_number)
        elif user_type == 'tenant':
            user = Tenant.objects.get(whatsapp_number=sender_number)
        else:
            user = UnidentifiedUser.objects.get(whatsapp_number=sender_number)
        
        user.last_activity = timezone.now()
        user.current_state = 'welcome'  # Set to main menu state
        user.save()
        
        # Send appropriate main menu based on user type
        if user_type == 'landlord':
            menu_text = (
                "Landlord Main Menu:\n"
                "1. Manage your properties\n"
                "2. Manage your rent entities\n"
                "3. Manage your tenants\n"
                "4. View Rent status for all your tenants\n"
                "5. View Rent status for all your tenants that owe\n"
                "6. View Rent status for a specific tenant\n"
                "7. Learn more about how to use the app by visiting our website"
                "8. Talk to customer support\n"
                "9. Signal rent payment\n"
                "10. Exit"
            )
        elif user_type == 'tenant':
            menu_text = (
                "Tenant Main Menu:\n"
                "1. View your rent staus\n"
                "2. Payment history\n"
                "3. Contact landlord\n"
                "4. Exit"
            )
        else:
            menu_text = (
                "Main Menu:\n"
                "1. Register as landlord\n"
                "2. Register as tenant\n"
                "3. Exit"
            )
        
        send_whatsapp_message(sender_number, menu_text)
        return {"status": "main_menu_sent"}


    def handle_landlord_name(self, message_text, sender_number):
        """Handle collecting landlord name."""
        name = message_text.strip()
        
        if not name:
            send_whatsapp_message(sender_number, "Please enter a valid name.")
            return {"status": "invalid_name"}
        
        # Check if we have an unidentified user first
        try:
            unidentified = UnidentifiedUser.objects.get(whatsapp_number=sender_number)
            
            # Now create a landlord from the unidentified user
            landlord = Landlord.objects.create(
                whatsapp_number=sender_number,
                name=name,
                current_state='property_name',
                context_data=unidentified.context_data
            )
            
            # Delete the unidentified user as we've now created a proper landlord
            unidentified.delete()
            
        except UnidentifiedUser.DoesNotExist:
            # Maybe the landlord already exists but needs name update
            try:
                landlord = Landlord.objects.get(whatsapp_number=sender_number)
                landlord.name = name
                landlord.current_state = 'property_name'
                landlord.save()
            except Landlord.DoesNotExist:
                # This shouldn't happen in normal flow, but handle it just in case
                landlord = Landlord.objects.create(
                    whatsapp_number=sender_number,
                    name=name,
                    current_state='property_name'
                )
        
        # Move to property registration
        send_whatsapp_message(
            sender_number,
            f"Thank you, {name}! Now let's add your first property. Please enter the property name:"
        )
        
        return {"status": "landlord_created"}
    
    def handle_property_name(self, message_text, sender_number):
        """Handle collecting property name."""
        property_name = message_text.strip()
        
        if not property_name:
            send_whatsapp_message(sender_number, "Please enter a valid property name.")
            return {"status": "invalid_property_name"}
        
        # Get landlord by phone number
        landlord = Landlord.objects.get(whatsapp_number=sender_number)
        
        # Store property name in context for next step
        landlord.context_data['property_name'] = property_name
        landlord.current_state = 'property_address'
        landlord.save()
        
        send_whatsapp_message(
            sender_number,
            f"Great! Now please enter the address for '{property_name}':"
        )
        
        return {"status": "property_name_saved"}
    
    def handle_property_address(self, message_text, sender_number):  
        """Handle collecting property address."""  
        address = message_text.strip()  
        
        if not address:  
            send_whatsapp_message(sender_number, "Please enter a valid address.")  
            return {"status": "invalid_address"}  
        
        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {"status": "landlord_not_found"}  
        
        # Create the property  
        property_name = landlord.context_data.get('property_name')  
        property_obj = Property.objects.create(  
            name=property_name,  
            address=address,  
            landlord=landlord  
        )  
        
        # Clear the temporary property name from context  
        if 'property_name' in landlord.context_data:  
            del landlord.context_data['property_name']  
        
        landlord.current_state = 'rent_entity'  
        landlord.save()  
        
        send_whatsapp_message(  
            sender_number,  
            f"Property '{property_name}' has been added successfully! What would you like to do next?\n1. Add another property\n2. Add rent entity to {property_name}\n3. Return to main menu"  
        )  
        
        return {"status": "property_added"}  

    def handle_rent_entity_name(self, message_text, sender_number):  
        """Handle collecting rent entity name."""  
        rent_entity_name = message_text.strip()  
        
        if not rent_entity_name:  
            send_whatsapp_message(sender_number, "Please enter a valid rent entity name.")  
            return {'status': 'invalid_rent_entity_name'}  
        
        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Store the rent entity name in context data for creation later  
        landlord.context_data['rent_entity_name'] = rent_entity_name  

        # Update current state to expect rent amount next  
        landlord.current_state = 'rent_entity_price'  
        landlord.save()  
        
        send_whatsapp_message(  
            sender_number,   
            f"What is the monthly rent amount for '{rent_entity_name}'? (Enter numbers only)"  
        )  
        
        return {'status': 'rent_entity_name_received'}  
    
    def handle_rent_entity_price(self, message_text, sender_number):  
        """Handle collecting rent entity price."""  
        try:  
            rent_amount = float(message_text.strip())  
            if rent_amount <= 0:  
                raise ValueError("Rent amount must be positive")  
        except ValueError:  
            send_whatsapp_message(sender_number, "Please enter a valid rent amount (numbers only).")  
            return {'status': 'invalid_rent_amount'}  

        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Retrieve rent entity name and property from context data  
        rent_entity_name = landlord.context_data.get('rent_entity_name')  
        property_obj_id = landlord.context_data.get('property_id')  # Assuming you save the property ID in context data.  

        if not property_obj_id:  
            send_whatsapp_message(sender_number, "Property information not found. Please start again.")  
            landlord.current_state = 'property_name'  
            landlord.save()  
            return {'status': 'property_not_found'}  

        # Get the property object  
        try:  
            property_obj = Property.objects.get(id=property_obj_id)  
        except Property.DoesNotExist:  
            send_whatsapp_message(sender_number, "Sorry, there was an error with your property information. Let's start again.")  
            landlord.current_state = 'property_name'  
            landlord.save()  
            return {'status': 'property_not_found'}  

        # Create the rent entity  
        rent_entity = RentEntity.objects.create(  
            name=rent_entity_name,  
            rent_amount=rent_amount,  
            property=property_obj  
        )  

        # Clear the rent entity name from context data if needed  
        if 'rent_entity_name' in landlord.context_data:  
            del landlord.context_data['rent_entity_name']  

        # Update landlord's state  
        landlord.current_state = 'tenant_name'  
        landlord.save()  

        send_whatsapp_message(  
            sender_number,   
            f"Great! Now let's add a tenant for this {rent_entity_name}. What is the tenant's name?"  
        )  
        
        return {'status': 'rent_entity_created'}
    
    def handle_tenant_name(self, message_text, sender_number):  
        """Handle collecting tenant name."""  
        tenant_name = message_text.strip()  
        
        if not tenant_name:  
            send_whatsapp_message(sender_number, "Please enter a valid tenant name.")  
            return {'status': 'invalid_tenant_name'}  

        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Store tenant name in landlord's context data  
        landlord.context_data['tenant_name'] = tenant_name  
        landlord.current_state = 'tenant_whatsapp'  
        landlord.save()  
        
        send_whatsapp_message(  
            sender_number,   
            "What is the tenant's WhatsApp number? (Include country code, e.g., +12364567890)"  
        )  
        
        return {'status': 'tenant_name_received'} 
    
    def handle_tenant_whatsapp(self, message_text, sender_number):  
        """Handle collecting tenant WhatsApp number."""  
        tenant_whatsapp = message_text.strip()  

        # Basic validation for WhatsApp number  
        if not tenant_whatsapp.startswith('+') or len(tenant_whatsapp) < 10:  
            send_whatsapp_message(  
                sender_number,   
                "Please enter a valid WhatsApp number including country code (e.g., +1234567890)."  
            )  
            return {'status': 'invalid_whatsapp_number'}  
        
        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Store tenant WhatsApp in context data  
        landlord.context_data['tenant_whatsapp'] = tenant_whatsapp  
        landlord.current_state = 'payment_cycle_start'  
        landlord.save()  
        
        send_whatsapp_message(  
            sender_number,   
            "When did the tenant's payment cycle start? (Enter date in format YYYY-MM-DD)"  
        )  
        
        return {'status': 'tenant_whatsapp_received'}
    
    def handle_payment_cycle_start(self, message_text, sender_number):  
        """Handle collecting payment cycle start date."""  
        try:  
            start_date = timezone.datetime.strptime(message_text.strip(), '%Y-%m-%d').date()  
        except ValueError:  
            send_whatsapp_message(  
                sender_number,   
                "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-03-01)."  
            )  
            return {'status': 'invalid_start_date'}  

        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Store start date in context data  
        landlord.context_data['start_date'] = message_text.strip()  
        landlord.current_state = 'bills_due_date'  
        landlord.save()  

        send_whatsapp_message(  
            sender_number,   
            "When is the bills due date? (Enter date in format YYYY-MM-DD)"  
        )  

        return {'status': 'start_date_received'}
        
        def handle_bills_due_date(self, message_text, sender_number):  
        """Handle collecting bills due date."""  
        try:  
            bills_date = timezone.datetime.strptime(message_text.strip(), '%Y-%m-%d').date()  
        except ValueError:  
            send_whatsapp_message(  
                sender_number,   
                "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-03-15)."  
            )  
            return {'status': 'invalid_bills_date'}  

        # Get landlord by phone number  
        try:  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
        except Landlord.DoesNotExist:  
            send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
            return {'status': 'landlord_not_found'}  

        # Store bills date in context data  
        landlord.context_data['bills_date'] = message_text.strip()  
        landlord.current_state = 'last_payment_date'  
        landlord.save()  

        send_whatsapp_message(  
            sender_number,   
            "When was the last payment made? (Enter date in format YYYY-MM-DD, or type 'none' if no payment yet)"  
        )  

        return {'status': 'bills_date_received'}

    def handle_last_payment_date(self, message_text, sender_number):  
    """Handle collecting last payment date."""  
    message_text = message_text.strip().lower()  

    # Get landlord by phone number  
    try:  
        landlord = Landlord.objects.get(whatsapp_number=sender_number)  
    except Landlord.DoesNotExist:  
        send_whatsapp_message(sender_number, "Landlord not found. Please verify your account.")  
        return {'status': 'landlord_not_found'}  

    # Handle 'none' input or parse the date  
    if message_text == 'none':  
        landlord.context_data['last_payment'] = None  
    else:  
        try:  
            last_payment = timezone.datetime.strptime(message_text, '%Y-%m-%d').date()  
            landlord.context_data['last_payment'] = last_payment  
        except ValueError:  
            send_whatsapp_message(  
                sender_number,  
                "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-02-15) or type 'none'."  
            )  
            return {'status': 'invalid_last_payment_date'}  

    # Update the landlord's current state  
    landlord.current_state = 'initial'  
    landlord.save()  

    return {'status': 'last_payment_received'}  
    
    def handle_payment_cycle_months(self, message_text, sender_number):  
    """Handle collecting payment cycle months."""  
    try:  
        months = int(message_text.strip())  
        if months < 0:  
            raise ValueError("Months must be non-negative")  
    except ValueError:  
        send_whatsapp_message(sender_number, "Please enter a valid number of months.")  
        return {'status': 'invalid_months'}  
    
    # Create the tenant with all collected information  
    try:  
        with transaction.atomic():  
            # Get landlord by phone number  
            landlord = Landlord.objects.get(whatsapp_number=sender_number)  
            
            # Get the rent entity ID from context data  
            rent_entity_id = landlord.context_data.get('rent_entity_id')  
            rent_entity = RentEntity.objects.get(id=rent_entity_id)  
            
            # Get dates from context data  
            start_date = timezone.datetime.strptime(  
                landlord.context_data.get('start_date'), '%Y-%m-%d'  
            ).date()  
            bills_date = timezone.datetime.strptime(  
                landlord.context_data.get('bills_date'), '%Y-%m-%d'  
            ).date()  
            
            last_payment = None  
            if landlord.context_data.get('last_payment'):  
                last_payment = timezone.datetime.strptime(  
                    landlord.context_data.get('last_payment'), '%Y-%m-%d'  
                ).date()  
            
            # Create tenant  
            tenant = Tenant.objects.create(  
                rent_entity=rent_entity,  
                name=landlord.context_data.get('tenant_name'),  
                whatsapp_number=landlord.context_data.get('tenant_whatsapp'),  
                start_of_payment_cycle=start_date,  
                bills_due_date=bills_date,  
                last_rent_paid=last_payment,  
                last_bill_paid=last_payment,  
                payment_cycle_months=months  
            )  
            
            # Send confirmation to the tenant  
            tenant_message = (  
                f"Dear {tenant.name}, you have been registered as a tenant by "  
                f"{rent_entity.property.landlord.name} for {rent_entity.name} at "  
                f"{rent_entity.property.name}. Your rent is {rent_entity.rent_amount} per month."  
            )  
            send_whatsapp_message(tenant.whatsapp_number, tenant_message)  
            
            # Inform the landlord and send the main menu  
            menu_text = landlord_main_menu(rent_entity.property.landlord.name)  
            send_whatsapp_message(sender_number, menu_text)  

            # Update landlord's state  
            landlord.current_state = 'main_menu'  
            landlord.save()  
            
            return {'status': 'tenant_created'}  
            
    except Exception as e:  
        print(f"Error creating tenant: {str(e)}")  
        send_whatsapp_message(  
            sender_number,   
            "Sorry, there was an error creating the tenant. Let's try again."  
        )  
        landlord.current_state = 'tenant_name'  # Reset to the previous state  
        landlord.save()  
        return {'status': 'tenant_creation_error'}  
    
    def handle_main_menu(self, message_text, sender_number, session):
        """Handle the main menu options for landlords."""
        option = message_text.strip()
        
        # Get the landlord
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
        except Landlord.DoesNotExist:
            session.current_state = 'welcome'
            session.save()
            return self.handle_welcome(message_text, sender_number, session)
        
        # Process menu option
        if option == '1':
            # Property management
            property_options = format_menu(
                "Property Management:",
                {
                    "1": "Add a new property",
                    "2": "Delete an existing property",
                    "3": "Return to main menu"
                }
            )
            send_whatsapp_message(sender_number, property_options)
            session.current_state = 'property_management'
            session.save()
            return {'status': 'property_management_selected'}
            
        elif option == '2':
            # Rent entity management
            # First check if the landlord has any properties
            if not Property.objects.filter(landlord=landlord).exists():
                send_whatsapp_message(
                    sender_number, 
                    "You need to add a property first before managing rent entities."
                )
                return {'status': 'no_properties'}
                
            # If they have properties, show the rent entity management menu
            rent_entity_options = format_menu(
                "Rent Entity Management:",
                {
                    "1": "Add a new rent entity",
                    "2": "Delete an existing rent entity",
                    "3": "Return to main menu"
                }
            )
            send_whatsapp_message(sender_number, rent_entity_options)
            session.current_state = 'rent_entity_management'
            session.save()
            return {'status': 'rent_entity_management_selected'}
            
        elif option == '3':
            # Tenant management
            # First check if the landlord has any rent entities
            properties = Property.objects.filter(landlord=landlord)
            if not properties.exists() or not RentEntity.objects.filter(property__in=properties).exists():
                send_whatsapp_message(
                    sender_number, 
                    "You need to add a property and rent entity first before managing tenants."
                )
                return {'status': 'no_rent_entities'}
                
            # If they have rent entities, show the tenant management menu
            tenant_options = format_menu(
                "Tenant Management:",
                {
                    "1": "Add a new tenant",
                    "2": "Delete an existing tenant",
                    "3": "Return to main menu"
                }
            )
            send_whatsapp_message(sender_number, tenant_options)
            session.current_state = 'tenant_management'
            session.save()
            return {'status': 'tenant_management_selected'}
            
        elif option == '4':
            # Rent status of all tenants
            # Check if landlord has multiple properties
            properties = Property.objects.filter(landlord=landlord)
            
            if properties.count() > 1:
                # List properties for selection
                property_list = "Please select a property to view tenants:\n\n"
                for i, prop in enumerate(properties, 1):
                    property_list += f"{i}. {prop.name}\n"
                
                session.context_data['property_list'] = {str(i): prop.id for i, prop in enumerate(properties, 1)}
                session.current_state = 'property_selection_all_tenants'
                session.save()
                
                send_whatsapp_message(sender_number, property_list)
                return {'status': 'property_selection_for_all_tenants'}
            elif properties.count() == 1:
                # Only one property, show all tenants
                property_obj = properties.first()
                rent_entities = RentEntity.objects.filter(property=property_obj)
                tenants = Tenant.objects.filter(rent_entity__in=rent_entities)
                
                if not tenants.exists():
                    send_whatsapp_message(
                        sender_number,
                        f"No tenants found for property: {property_obj.name}"
                    )
                else:
                    tenant_status = f"Tenant status for {property_obj.name}:\n\n"
                    for tenant in tenants:
                        # Calculate next due date
                        next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                        
                        tenant_status += (
                            f"Tenant: {tenant.name}\n"
                            f"Rent Entity: {tenant.rent_entity.name}\n"
                            f"Rent Amount: {tenant.rent_entity.rent_amount}\n"
                            f"Last Payment: {tenant.last_rent_paid or 'None'}\n"
                            f"Months Paid: {tenant.payment_cycle_months}\n"
                            f"Next Due Date: {next_due_date}\n\n"
                        )
                    
                    send_whatsapp_message(sender_number, tenant_status)
                
                # Return to main menu
                menu_text = landlord_main_menu(landlord.name)
                send_whatsapp_message(sender_number, menu_text)
                session.current_state = 'main_menu'
                session.save()
                return {'status': 'tenant_status_shown'}
            else:
                send_whatsapp_message(
                    sender_number,
                    "You don't have any properties registered yet."
                )
                return {'status': 'no_properties'}
        
        elif option == '5':
            # Rent status of all owing tenants
            # Check if landlord has multiple properties
            properties = Property.objects.filter(landlord=landlord)
            
            if properties.count() > 1:
                # List properties for selection
                property_list = "Please select a property to view owing tenants:\n\n"
                for i, prop in enumerate(properties, 1):
                    property_list += f"{i}. {prop.name}\n"
                
                session.context_data['property_list'] = {str(i): prop.id for i, prop in enumerate(properties, 1)}
                session.current_state = 'property_selection_owing_tenants'
                session.save()
                
                send_whatsapp_message(sender_number, property_list)
                return {'status': 'property_selection_for_owing_tenants'}
            elif properties.count() == 1:
                # Only one property, show owing tenants
                property_obj = properties.first()
                rent_entities = RentEntity.objects.filter(property=property_obj)
                tenants = Tenant.objects.filter(rent_entity__in=rent_entities)
                
                # Filter for owing tenants
                owing_tenants = []
                for tenant in tenants:
                    next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                    if next_due_date <= timezone.now().date():
                        owing_tenants.append(tenant)
                
                if not owing_tenants:
                    send_whatsapp_message(
                        sender_number,
                        f"No owing tenants found for property: {property_obj.name}"
                    )
                else:
                    tenant_status = f"Owing tenant status for {property_obj.name}:\n\n"
                    for tenant in owing_tenants:
                        next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                        days_overdue = (timezone.now().date() - next_due_date).days
                        
                        tenant_status += (
                            f"Tenant: {tenant.name}\n"
                            f"Rent Entity: {tenant.rent_entity.name}\n"
                            f"Rent Amount: {tenant.rent_entity.rent_amount}\n"
                            f"Due Date: {next_due_date}\n"
                            f"Days Overdue: {days_overdue}\n\n"
                        )
                    
                    send_whatsapp_message(sender_number, tenant_status)
                
                # Return to main menu
                menu_text = landlord_main_menu(landlord.name)
                send_whatsapp_message(sender_number, menu_text)
                session.current_state = 'main_menu'
                session.save()
                return {'status': 'owing_tenant_status_shown'}
            else:
                send_whatsapp_message(
                    sender_number,
                    "You don't have any properties registered yet."
                )
                return {'status': 'no_properties'}
        
        elif option == '6':
            # Rent status of specific tenant/rent entity
            # First check if landlord has any properties
            properties = Property.objects.filter(landlord=landlord)
            
            if not properties.exists():
                send_whatsapp_message(
                    sender_number,
                    "You don't have any properties registered yet."
                )
                return {'status': 'no_properties'}
            
            # Ask for tenant name
            send_whatsapp_message(
                sender_number,
                "Please enter the name of the tenant or rent entity you want to check:"
            )
            session.current_state = 'tenant_rent_entity_search'
            session.save()
            return {'status': 'tenant_rent_entity_search_started'}
        
        elif option == '7':
            # Redirect to website
            send_whatsapp_message(
                sender_number,
                "Please visit our website at https://lebailleur.com to learn more about managing your properties."
            )
            # Return to main menu
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            return {'status': 'website_redirect'}

        elif option == '8':
            # Customer support
            send_whatsapp_message(
                sender_number,
                "Please send us your query or issue, and we'll get back to you as soon as possible."
            )
            session.current_state = 'customer_support'
            session.save()
            return {'status': 'customer_support_started'}

        elif option == '9':
            # Signal rent payment
            # Check if landlord has multiple properties
            properties = Property.objects.filter(landlord=landlord)
            
            if not properties.exists():
                send_whatsapp_message(
                    sender_number,
                    "You don't have any properties registered yet."
                )
                return {'status': 'no_properties'}
            
            # Ask for tenant name
            send_whatsapp_message(
                sender_number,
                "Please enter the name of the tenant who has made a payment:"
            )
            session.current_state = 'payment_tenant_name'
            session.save()
            return {'status': 'payment_registration_started'}

        elif option == '10':
            # Exit
            send_whatsapp_message(
                sender_number,
                f"Thank you for using Le Bailleur, {landlord.name}. Your session has been closed. Send any message to start again."
            )
            session.delete()  # Delete the session
            return {'status': 'session_ended'}

        else:
            # Invalid option
            send_whatsapp_message(
                sender_number,
                "Invalid response, please type only a number (e.g., 1)."
            )
            # Resend the main menu
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            return {'status': 'invalid_option'}

    def handle_property_selection_all_tenants(self, message_text, sender_number, session):
        """Handle property selection for viewing all tenants."""
        option = message_text.strip()
        property_list = session.context_data.get('property_list', {})
        
        if option not in property_list:
            send_whatsapp_message(
                sender_number,
                "Invalid selection. Please choose from the listed properties."
            )
            return {'status': 'invalid_property_selection'}
        
        property_id = property_list[option]
        
        try:
            property_obj = Property.objects.get(id=property_id)
            rent_entities = RentEntity.objects.filter(property=property_obj)
            tenants = Tenant.objects.filter(rent_entity__in=rent_entities)
            
            if not tenants.exists():
                send_whatsapp_message(
                    sender_number,
                    f"No tenants found for property: {property_obj.name}"
                )
            else:
                tenant_status = f"Tenant status for {property_obj.name}:\n\n"
                for tenant in tenants:
                    # Calculate next due date
                    next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                    
                    tenant_status += (
                        f"Tenant: {tenant.name}\n"
                        f"Rent Entity: {tenant.rent_entity.name}\n"
                        f"Rent Amount: {tenant.rent_entity.rent_amount}\n"
                        f"Last Payment: {tenant.last_rent_paid or 'None'}\n"
                        f"Months Paid: {tenant.payment_cycle_months}\n"
                        f"Next Due Date: {next_due_date}\n\n"
                    )
                
                send_whatsapp_message(sender_number, tenant_status)
            
            # Return to main menu
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'tenant_status_shown'}
            
        except Property.DoesNotExist:
            send_whatsapp_message(
                sender_number,
                "Sorry, the selected property was not found."
            )
            return {'status': 'property_not_found'}

    def handle_property_selection_owing_tenants(self, message_text, sender_number, session):
        """Handle property selection for viewing owing tenants."""
        option = message_text.strip()
        property_list = session.context_data.get('property_list', {})
        
        if option not in property_list:
            send_whatsapp_message(
                sender_number,
                "Invalid selection. Please choose from the listed properties."
            )
            return {'status': 'invalid_property_selection'}
        
        property_id = property_list[option]
        
        try:
            property_obj = Property.objects.get(id=property_id)
            rent_entities = RentEntity.objects.filter(property=property_obj)
            tenants = Tenant.objects.filter(rent_entity__in=rent_entities)
            
            # Filter for owing tenants
            owing_tenants = []
            for tenant in tenants:
                next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                if next_due_date <= timezone.now().date():
                    owing_tenants.append(tenant)
            
            if not owing_tenants:
                send_whatsapp_message(
                    sender_number,
                    f"No owing tenants found for property: {property_obj.name}"
                )
            else:
                tenant_status = f"Owing tenant status for {property_obj.name}:\n\n"
                for tenant in owing_tenants:
                    next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                    days_overdue = (timezone.now().date() - next_due_date).days
                    
                    tenant_status += (
                        f"Tenant: {tenant.name}\n"
                        f"Rent Entity: {tenant.rent_entity.name}\n"
                        f"Rent Amount: {tenant.rent_entity.rent_amount}\n"
                        f"Due Date: {next_due_date}\n"
                        f"Days Overdue: {days_overdue}\n\n"
                    )
                
                send_whatsapp_message(sender_number, tenant_status)
            
            # Return to main menu
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'owing_tenant_status_shown'}
            
        except Property.DoesNotExist:
            send_whatsapp_message(
                sender_number,
                "Sorry, the selected property was not found."
            )
            return {'status': 'property_not_found'}

    def handle_tenant_rent_entity_search(self, message_text, sender_number, session):
        """Handle search for specific tenant or rent entity."""
        search_term = message_text.strip()
        
        if not search_term:
            send_whatsapp_message(
                sender_number,
                "Please enter a valid tenant or rent entity name."
            )
            return {'status': 'invalid_search_term'}
        
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            properties = Property.objects.filter(landlord=landlord)
            
            # Look for tenant or rent entity matches
            rent_entities = RentEntity.objects.filter(
                property__in=properties, 
                name__icontains=search_term
            )
            
            tenants = Tenant.objects.filter(
                rent_entity__property__in=properties
            ).filter(
                name__icontains=search_term
            )
            
            # Also search for tenants by rent entity
            tenants_by_rent_entity = Tenant.objects.filter(
                rent_entity__in=rent_entities
            )
            
            # Combine results
            tenants = tenants.union(tenants_by_rent_entity)
            
            if not tenants.exists():
                send_whatsapp_message(
                    sender_number,
                    f"No tenants or rent entities found matching '{search_term}'."
                )
            else:
                results = f"Search results for '{search_term}':\n\n"
                for tenant in tenants:
                    next_due_date = tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months) if tenant.last_rent_paid else tenant.start_of_payment_cycle
                    status = "Owing" if next_due_date <= timezone.now().date() else "Paid"
                    
                    results += (
                        f"Tenant: {tenant.name}\n"
                        f"Property: {tenant.rent_entity.property.name}\n"
                        f"Rent Entity: {tenant.rent_entity.name}\n"
                        f"Rent Amount: {tenant.rent_entity.rent_amount}\n"
                        f"Status: {status}\n"
                        f"Next Due Date: {next_due_date}\n\n"
                    )
                
                send_whatsapp_message(sender_number, results)
            
            # Return to main menu
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'search_results_shown'}
            
        except Landlord.DoesNotExist:
            # This shouldn't happen, but just in case
            session.current_state = 'welcome'
            session.save()
            return self.handle_welcome(message_text, sender_number, session)

    def handle_customer_support(self, message_text, sender_number, session):
        """Handle customer support queries."""
        support_message = message_text.strip()
        
        if not support_message:
            send_whatsapp_message(
                sender_number,
                "Please provide a valid message or query."
            )
            return {'status': 'invalid_support_message'}
        
        try:
            # Get landlord name for context
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            landlord_name = landlord.name
        except Landlord.DoesNotExist:
            try:
                # Try to get tenant name
                tenant = Tenant.objects.get(whatsapp_number=sender_number)
                landlord_name = tenant.name
            except Tenant.DoesNotExist:
                landlord_name = "Unknown User"
        
        # Forward the message to customer support
        admin_number = "+237698827753"  # This should be stored in settings
        forwarded_message = (
            f"Support request from {landlord_name} ({sender_number}):\n\n"
            f"{support_message}"
        )
        send_whatsapp_message(admin_number, forwarded_message)
        
        # Confirm receipt to user
        send_whatsapp_message(
            sender_number,
            "Thank you for your message. Our support team has been notified and will respond to you shortly."
        )
        
        # Return to main menu
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
        except Landlord.DoesNotExist:
            try:
                tenant = Tenant.objects.get(whatsapp_number=sender_number)
                tenant_menu = format_menu(
                    f"What would you like to do next, {tenant.name}?",
                    {
                        "1": "check your rent status",
                        "2": "view your payment history",
                        "3": "contact your landlord",
                        "4": "exit"
                    }
                )
                send_whatsapp_message(sender_number, tenant_menu)
                session.current_state = 'tenant_menu'
            except Tenant.DoesNotExist:
                session.current_state = 'welcome'
        
        session.save()
        return {'status': 'support_message_sent'}

    def handle_payment_tenant_name(self, message_text, sender_number, session):
        """Handle collecting tenant name for payment registration."""
        tenant_name = message_text.strip()
        
        if not tenant_name:
            send_whatsapp_message(
                sender_number,
                "Please enter a valid tenant name."
            )
            return {'status': 'invalid_tenant_name'}
        
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            properties = Property.objects.filter(landlord=landlord)
            
            # Look for tenant matches
            tenants = Tenant.objects.filter(
                rent_entity__property__in=properties,
                name__icontains=tenant_name
            )
            
            if not tenants.exists():
                send_whatsapp_message(
                    sender_number,
                    f"No tenants found matching '{tenant_name}'. Please try again."
                )
                return {'status': 'tenant_not_found'}
            
            if tenants.count() > 1:
                # Multiple tenants found, ask for selection
                tenant_list = "Multiple tenants found. Please select one:\n\n"
                for i, tenant in enumerate(tenants, 1):
                    tenant_list += f"{i}. {tenant.name} ({tenant.rent_entity.name} at {tenant.rent_entity.property.name})\n"
                
                session.context_data['tenant_list'] = {str(i): tenant.id for i, tenant in enumerate(tenants, 1)}
                session.current_state = 'payment_tenant_selection'
                session.save()
                
                send_whatsapp_message(sender_number, tenant_list)
                return {'status': 'multiple_tenants_found'}
            
            # Single tenant found
            tenant = tenants.first()
            session.context_data['tenant_id'] = tenant.id
            session.current_state = 'payment_months'
            session.save()
            
            send_whatsapp_message(
                sender_number,
                f"Tenant found: {tenant.name} at {tenant.rent_entity.property.name}.\n"
                f"How many months is the tenant paying for? (Enter a number)"
            )
            return {'status': 'tenant_found'}
            
        except Landlord.DoesNotExist:
            # This shouldn't happen, but just in case
            session.current_state = 'welcome'
            session.save()
            return self.handle_welcome(message_text, sender_number, session)

    def handle_payment_tenant_selection(self, message_text, sender_number, session):
        """Handle selection of tenant for payment from multiple matches."""
        option = message_text.strip()
        tenant_list = session.context_data.get('tenant_list', {})
        
        if option not in tenant_list:
            send_whatsapp_message(
                sender_number,
                "Invalid selection. Please choose from the listed tenants."
            )
            return {'status': 'invalid_tenant_selection'}
        
        tenant_id = tenant_list[option]
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            session.context_data['tenant_id'] = tenant.id
            session.current_state = 'payment_months'
            session.save()
            
            send_whatsapp_message(
                sender_number,
                f"Selected tenant: {tenant.name} at {tenant.rent_entity.property.name}.\n"
                f"How many months is the tenant paying for? (Enter a number)"
            )
            return {'status': 'tenant_selected'}
            
        except Tenant.DoesNotExist:
            send_whatsapp_message(
                sender_number,
                "Sorry, the selected tenant was not found."
            )
            return {'status': 'tenant_not_found'}

    def handle_payment_months(self, message_text, sender_number, session):
        """Handle collection of payment months."""
        try:
            months = int(message_text.strip())
            if months <= 0:
                raise ValueError("Months must be positive")
        except ValueError:
            send_whatsapp_message(
                sender_number,
                "Please enter a valid number of months (greater than 0)."
            )
            return {'status': 'invalid_months'}
        
        # Store months in session context
        session.context_data['payment_months'] = months
        session.current_state = 'payment_amount_confirmation'
        session.save()
        
        try:
            tenant_id = session.context_data.get('tenant_id')
            tenant = Tenant.objects.get(id=tenant_id)
            
            # Calculate payment amount
            payment_amount = tenant.rent_entity.rent_amount * months
            session.context_data['payment_amount'] = payment_amount
            
            send_whatsapp_message(
                sender_number,
                f"Payment Summary:\n"
                f"Tenant: {tenant.name}\n"
                f"Rent Entity: {tenant.rent_entity.name}\n"
                f"Monthly Rent: {tenant.rent_entity.rent_amount}\n"
                f"Number of Months: {months}\n"
                f"Total Amount: {payment_amount}\n\n"
                f"Is this correct? Type 1 to confirm or 2 to modify."
            )
            return {'status': 'payment_summary_shown'}
            
        except Tenant.DoesNotExist:
            send_whatsapp_message(
                sender_number,
                "Sorry, there was an error with the tenant information."
            )
            return {'status': 'tenant_not_found'}

    def handle_payment_amount_confirmation(self, message_text, sender_number, session):
        """Handle confirmation of payment amount."""
        option = message_text.strip()
        
        if option == '1':
            # Confirmed, create receipt and update tenant
            try:
                with transaction.atomic():
                    tenant_id = session.context_data.get('tenant_id')
                    tenant = Tenant.objects.get(id=tenant_id)
                    
                    payment_months = session.context_data.get('payment_months')
                    payment_amount = session.context_data.get('payment_amount')
                    
                    # Create payment receipt
                    receipt_number = generate_receipt_number()
                    
                    receipt = PaymentReceipt.objects.create(
                        tenant=tenant,
                        receipt_number=receipt_number,
                        amount=payment_amount,
                        payment_date=timezone.now().date(),
                        months_paid=payment_months
                    )
                    
                    # Update tenant payment information
                    tenant.last_rent_paid = timezone.now().date()
                    tenant.last_bill_paid = timezone.now().date()
                    tenant.payment_cycle_months = payment_months
                    tenant.save()
                    
                    # Send receipt to tenant
                    receipt_message = (
                        f"PAYMENT RECEIPT #{receipt_number}\n\n"
                        f"Tenant: {tenant.name}\n"
                        f"Property: {tenant.rent_entity.property.name}\n"
                        f"Rent Entity: {tenant.rent_entity.name}\n"
                        f"Amount Paid: {payment_amount}\n"
                        f"Months Paid: {payment_months}\n"
                        f"Payment Date: {timezone.now().date()}\n"
                        f"Next Due Date: {tenant.last_rent_paid + relativedelta(months=tenant.payment_cycle_months)}\n\n"
                        f"Thank you for your payment!"
                    )
                    
                    send_whatsapp_message(tenant.whatsapp_number, receipt_message)
                    
                    # Notify landlord
                    landlord = tenant.rent_entity.property.landlord
                    send_whatsapp_message(
                        sender_number,
                        f"Payment recorded successfully! Receipt #{receipt_number} has been sent to {tenant.name}."
                    )
                    
                    # Return to main menu
                    menu_text = landlord_main_menu(landlord.name)
                    send_whatsapp_message(sender_number, menu_text)
                    session.current_state = 'main_menu'
                    session.save()
                    
                    return {'status': 'payment_recorded'}
                    
            except Exception as e:
                print(f"Error recording payment: {str(e)}")
                send_whatsapp_message(
                    sender_number,
                    "Sorry, there was an error processing the payment. Please try again."
                )
                return {'status': 'payment_error'}
            
        elif option == '2':
            # Modify payment details
            send_whatsapp_message(
                sender_number,
                "What would you like to modify?\n"
                "1. Number of months\n"
                "2. Cancel payment registration"
            )
            session.current_state = 'payment_modification'
            session.save()
            return {'status': 'payment_modification_started'}
            
        else:
            # Invalid option
            send_whatsapp_message(
                sender_number,
                "Invalid response. Please type '1' to confirm or '2' to modify."
            )
            return {'status': 'invalid_option'}

    def handle_payment_modification(self, message_text, sender_number, session):
        """Handle modification of payment details."""
        option = message_text.strip()
        
        if option == '1':
            # Modify months
            send_whatsapp_message(
                sender_number,
                "Please enter the new number of months:"
            )
            session.current_state = 'payment_months'
            session.save()
            return {'status': 'modifying_months'}
            
        elif option == '2':
            # Cancel payment registration
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(
                sender_number,
                "Payment registration cancelled. Returning to main menu."
            )
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'payment_cancelled'}
            
        else:
            # Invalid option
            send_whatsapp_message(
                sender_number,
                "Invalid response. Please type '1' to modify months or '2' to cancel."
            )
            return {'status': 'invalid_option'}

    def handle_property_management(self, message_text, sender_number, session):
        """Handle property management options."""
        option = message_text.strip()
        
        if option == '1':
            # Add new property
            send_whatsapp_message(
                sender_number,
                "Please enter the name of the new property:"
            )
            session.current_state = 'property_name'
            session.save()
            return {'status': 'adding_property'}
            
        elif option == '2':
            # Delete property
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            properties = Property.objects.filter(landlord=landlord)
            
            if not properties.exists():
                send_whatsapp_message(
                    sender_number,
                    "You don't have any properties to delete."
                )
                # Return to main menu
                menu_text = landlord_main_menu(landlord.name)
                send_whatsapp_message(sender_number, menu_text)
                session.current_state = 'main_menu'
                session.save()
                return {'status': 'no_properties'}
            
            # List properties for deletion
            property_list = "Select a property to delete:\n\n"
            for i, prop in enumerate(properties, 1):
                property_list += f"{i}. {prop.name}\n"
            
            session.context_data['property_delete_list'] = {str(i): prop.id for i, prop in enumerate(properties, 1)}
            session.current_state = 'property_delete_selection'
            session.save()
            
            send_whatsapp_message(sender_number, property_list)
            return {'status': 'property_delete_list_shown'}
            
        elif option == '3':
            # Return to main menu
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'returned_to_main_menu'}
            
        else:
            # Invalid option
            send_whatsapp_message(
                sender_number,
                "Invalid response. Please type '1' to add, '2' to delete, or '3' to return to main menu."
            )
            return {'status': 'invalid_option'}

    def handle_property_delete_selection(self, message_text, sender_number, session):
        """Handle selection of property to delete."""
        option = message_text.strip()
        property_list = session.context_data.get('property_delete_list', {})
        
        if option not in property_list:
            send_whatsapp_message(
                sender_number,
                "Invalid selection. Please choose from the listed properties."
            )
            return {'status': 'invalid_property_selection'}
        
        property_id = property_list[option]
        
        try:
            property_obj = Property.objects.get(id=property_id)
            property_name = property_obj.name
            
            # Confirm deletion
            send_whatsapp_message(
                sender_number,
                f"Are you sure you want to delete property '{property_name}'? "
                f"This will also delete all rent entities and tenant records associated with this property.\n\n"
                f"Type 'YES' to confirm or 'NO' to cancel."
            )
            session.context_data['property_to_delete'] = property_id
            session.current_state = 'property_delete_confirmation'
            session.save()
            return {'status': 'property_delete_confirmation_requested'}
            
        except Property.DoesNotExist:
            send_whatsapp_message(
                sender_number,
                "Sorry, the selected property was not found."
            )
            return {'status': 'property_not_found'}

    def handle_property_delete_confirmation(self, message_text, sender_number, session):
        """Handle confirmation of property deletion."""
        response = message_text.strip().upper()
        
        if response == 'YES':
            # Delete the property
            try:
                property_id = session.context_data.get('property_to_delete')
                property_obj = Property.objects.get(id=property_id)
                property_name = property_obj.name
                
                # Delete the property (cascade will handle related entities)
                property_obj.delete()
                
                send_whatsapp_message(
                    sender_number,
                    f"Property '{property_name}' has been deleted successfully."
                )
                
                # Return to main menu
                landlord = Landlord.objects.get(whatsapp_number=sender_number)
                menu_text = landlord_main_menu(landlord.name)
                send_whatsapp_message(sender_number, menu_text)
                session.current_state = 'main_menu'
                session.save()
                return {'status': 'property_deleted'}
                
            except Property.DoesNotExist:
                send_whatsapp_message(
                    sender_number,
                    "Sorry, the property could not be found."
                )
                return {'status': 'property_not_found'}
                
        elif response == 'NO':
            # Cancel deletion
            send_whatsapp_message(
                sender_number,
                "Property deletion cancelled."
            )
            
            # Return to main menu
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            session.current_state = 'main_menu'
            session.save()
            return {'status': 'property_deletion_cancelled'}
            
        else:
            # Invalid response
            send_whatsapp_message(
                sender_number,
                "Invalid response. Please type 'YES' to confirm deletion or 'NO' to cancel."
            )
            return {'status': 'invalid_confirmation'}
