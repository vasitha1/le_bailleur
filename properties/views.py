from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.utils import timezone
from django.db import transaction
from dateutil.relativedelta import relativedelta
from .models import Property, Tenant, Landlord, RentEntity, Session, PaymentReceipt
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
import sys

class HomeView(TemplateView):
    template_name = 'le_bailleur_templates/index.html'

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
    
    VERIFY_TOKEN = '7e5de035-f7ed-4737-b2bf-fc71b9cb1e63'  # Your verification token
        
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
    
    def post(self, request, *args, **kwargs):
        """Handle incoming WhatsApp webhook messages."""
        try:
            # Parse incoming JSON payload
            payload = json.loads(request.body)
            logging.info("Received webhook POST payload")
            logging.debug(f"Payload content: {payload}")
            
            # Check for the correct WhatsApp message structure
            # WhatsApp messages come in a specific format according to the API
            if 'object' in payload and payload['object'] == 'whatsapp_business_account':
                for entry in payload.get('entry', []):
                    for change in entry.get('changes', []):
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            messages = value.get('messages', [])
                            
                            if not messages:
                                logging.info("No messages found in payload")
                                continue
                                
                            for message in messages:
                                message_type = message.get('type')
                                sender_id = message.get('from')
                                
                                logging.info(f"Processing message from: {sender_id}, type: {message_type}")
                                
                                if message_type == 'text':
                                    message_text = message.get('text', {}).get('body', '')
                                    logging.info(f"Message content: {message_text}")
                                    
                                    # Process the message
                                    response = self.process_message(message_text, sender_id)
                                    
                                    # Log the complete message for debugging
                                    with open("message_log.json", "a") as log_file:
                                        log_file.write(json.dumps(message) + "\n")
                                elif message_type in ['image', 'audio', 'video', 'document']:
                                    # Handle media messages if needed
                                    logging.info(f"Received {message_type} message from {sender_id}")
                                    # You can implement media handling here
                                else:
                                    logging.info(f"Received unsupported message type: {message_type}")
                
                # Always return 200 OK for webhook deliveries
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
            logging.warning("Invalid payload structure")
            return Response({'status': 'Invalid payload structure'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}", exc_info=True)
            # Still return 200 OK to acknowledge receipt (WhatsApp expects this)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)
    
    def process_message(self, message_text, sender_number):
        """Process incoming messages and prepare a response."""
        logging.info(f"Processing message: {message_text} from sender {sender_number}")
        
        # Implement your message processing logic here
        # You could add NLP, chatbot functionality, or business logic
        
        # Example: Echo the message back (for testing)
        # You would replace this with your actual business logic
        response_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": sender_number,
            "type": "text",
            "text": {
                "body": f"You said: {message_text}"
            }
        }
        
        # NOTE: This doesn't actually send the message back
        # You would need to make an API call to the WhatsApp API to send a response
        # Example: self.send_whatsapp_response(response_data)
        
        return {"status": "Message processed successfully", "response_prepared": response_data}
    
    # def process_message(self, message_text, sender_number):
    #     """Process incoming messages based on session state."""
    #     # Get or create session
    #     session = get_or_create_session(sender_number)
        
    #     # Check if session has expired (except for welcome state)
    #     if session.current_state != 'welcome' and check_session_expiry(session):
    #         # If session expired, reset to welcome state for new users
    #         return {'status': 'session_expired'}
        
    #     # Process message based on current state
    #     handler_method = getattr(self, f"handle_{session.current_state}", None)
        
    #     if handler_method and callable(handler_method):
    #         return handler_method(message_text, sender_number, session)
    #     else:
    #         # Fallback to welcome if state handler not found
    #         session.current_state = 'welcome'
    #         session.save()
    #         return self.handle_welcome(message_text, sender_number, session)
    
    def handle_welcome(self, message_text, sender_number, session):
        """Handle the welcome state - first contact with the app."""
        # Check if this is a returning user
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            session.is_landlord = True
            session.current_state = 'main_menu'
            session.save()
            
            # Send the main menu for returning landlords
            menu_text = landlord_main_menu(landlord.name)
            send_whatsapp_message(sender_number, menu_text)
            return {'status': 'returning_landlord'}
        except Landlord.DoesNotExist:
            pass
        
        try:
            tenant = Tenant.objects.get(whatsapp_number=sender_number)
            session.is_landlord = False
            session.current_state = 'tenant_menu'
            session.save()
            
            # Send the tenant menu
            tenant_menu = format_menu(
                f"Welcome back {tenant.name}! What would you like to do today?",
                {
                    "1": "check your rent status",
                    "2": "view your payment history",
                    "3": "contact your landlord",
                    "4": "exit"
                }
            )
            send_whatsapp_message(sender_number, tenant_menu)
            return {'status': 'returning_tenant'}
        except Tenant.DoesNotExist:
            pass
        
        # New user - send welcome message
        welcome_message = (
            "Welcome! I am \"Le Bailleur\", your rent management automatic assistant. "
            "I can help you track rent payments, send notifications, and manage your properties.\n\n"
            "Please type:\n"
            "1 - If you are a landlord\n"
            "2 - If you are a tenant"
        )
        send_whatsapp_message(sender_number, welcome_message)
        session.current_state = 'user_type_selection'
        session.save()
        
        return {'status': 'welcome_sent'}
    
    def handle_user_type_selection(self, message_text, sender_number, session):
        """Handle user type selection (landlord or tenant)."""
        message_text = message_text.strip()
        
        if message_text == '1':
            # User is a landlord
            session.is_landlord = True
            session.current_state = 'landlord_name'
            session.save()
            
            send_whatsapp_message(
                sender_number, 
                "Great! Let's set up your landlord account. Please enter your full name:"
            )
            return {'status': 'landlord_selected'}
            
        elif message_text == '2':
            # User is a tenant
            session.is_landlord = False
            session.current_state = 'tenant_info'
            session.save()
            
            send_whatsapp_message(
                sender_number, 
                "Please contact your landlord to register you in their property. "
                "Once they have added you as a tenant, you'll receive a confirmation message."
            )
            return {'status': 'tenant_selected'}
            
        else:
            # Invalid selection
            send_whatsapp_message(
                sender_number, 
                "Invalid response, please type only '1' if you are a landlord or '2' if you are a tenant."
            )
            return {'status': 'invalid_selection'}
    
    def handle_landlord_name(self, message_text, sender_number, session):
        """Handle collecting landlord name."""
        name = message_text.strip()
        
        if not name:
            send_whatsapp_message(sender_number, "Please enter a valid name.")
            return {'status': 'invalid_name'}
        
        # Store name in session context for later use
        session.context_data['landlord_name'] = name
        session.current_state = 'landlord_creation'
        session.save()
        
        # Create the landlord
        landlord = Landlord.objects.create(
            name=name,
            whatsapp_number=sender_number
        )
        
        # Move to property registration
        send_whatsapp_message(
            sender_number, 
            f"Thank you, {name}! Now let's add your first property. Please enter the property name:"
        )
        session.current_state = 'property_name'
        session.save()
        
        return {'status': 'landlord_created'}
    
    def handle_property_name(self, message_text, sender_number, session):
        """Handle collecting property name."""
        property_name = message_text.strip()
        
        if not property_name:
            send_whatsapp_message(sender_number, "Please enter a valid property name.")
            return {'status': 'invalid_property_name'}
        
        # Store property name in session context
        session.context_data['property_name'] = property_name
        session.current_state = 'property_address'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "Please enter the property address (Country-town-quarter-PO. Box):"
        )
        
        return {'status': 'property_name_received'}
    
    def handle_property_address(self, message_text, sender_number, session):
        """Handle collecting property address."""
        property_address = message_text.strip()
        
        if not property_address:
            send_whatsapp_message(sender_number, "Please enter a valid property address.")
            return {'status': 'invalid_property_address'}
        
        # Get the landlord
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
        except Landlord.DoesNotExist:
            # This shouldn't happen, but just in case
            session.current_state = 'welcome'
            session.save()
            return self.handle_welcome(message_text, sender_number, session)
        
        # Create the property
        property_name = session.context_data.get('property_name')
        property_obj = Property.objects.create(
            name=property_name,
            address=property_address,
            landlord=landlord
        )
        
        # Move to rent entity registration
        send_whatsapp_message(
            sender_number, 
            "Property registered successfully! Now let's add a rent entity. "
            "What are you renting out? (e.g., apartment, room, shop, etc.)"
        )
        session.current_state = 'rent_entity_name'
        session.context_data['property_id'] = property_obj.id
        session.save()
        
        return {'status': 'property_created'}
    
    def handle_rent_entity_name(self, message_text, sender_number, session):
        """Handle collecting rent entity name."""
        rent_entity_name = message_text.strip()
        
        if not rent_entity_name:
            send_whatsapp_message(sender_number, "Please enter a valid rent entity name.")
            return {'status': 'invalid_rent_entity_name'}
        
        # Store rent entity name in session context
        session.context_data['rent_entity_name'] = rent_entity_name
        session.current_state = 'rent_entity_price'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            f"What is the monthly rent amount for this {rent_entity_name}? (Enter numbers only)"
        )
        
        return {'status': 'rent_entity_name_received'}
    
    def handle_rent_entity_price(self, message_text, sender_number, session):
        """Handle collecting rent entity price."""
        try:
            rent_amount = float(message_text.strip())
            if rent_amount <= 0:
                raise ValueError("Rent amount must be positive")
        except ValueError:
            send_whatsapp_message(sender_number, "Please enter a valid rent amount (numbers only).")
            return {'status': 'invalid_rent_amount'}
        
        # Create the rent entity
        try:
            property_id = session.context_data.get('property_id')
            property_obj = Property.objects.get(id=property_id)
            
            rent_entity_name = session.context_data.get('rent_entity_name')
            rent_entity = RentEntity.objects.create(
                name=rent_entity_name,
                rent_amount=rent_amount,
                property=property_obj
            )
            
            # Store rent entity ID in session context
            session.context_data['rent_entity_id'] = rent_entity.id
            session.current_state = 'tenant_name'
            session.save()
            
            send_whatsapp_message(
                sender_number, 
                f"Great! Now let's add a tenant for this {rent_entity_name}. What is the tenant's name?"
            )
            
            return {'status': 'rent_entity_created'}
            
        except Property.DoesNotExist:
            send_whatsapp_message(
                sender_number, 
                "Sorry, there was an error with your property information. Let's start again."
            )
            session.current_state = 'property_name'
            session.save()
            return {'status': 'property_not_found'}
    
    def handle_tenant_name(self, message_text, sender_number, session):
        """Handle collecting tenant name."""
        tenant_name = message_text.strip()
        
        if not tenant_name:
            send_whatsapp_message(sender_number, "Please enter a valid tenant name.")
            return {'status': 'invalid_tenant_name'}
        
        # Store tenant name in session context
        session.context_data['tenant_name'] = tenant_name
        session.current_state = 'tenant_whatsapp'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "What is the tenant's WhatsApp number? (Include country code, e.g., +1234567890)"
        )
        
        return {'status': 'tenant_name_received'}
    
    def handle_tenant_whatsapp(self, message_text, sender_number, session):
        """Handle collecting tenant WhatsApp number."""
        tenant_whatsapp = message_text.strip()
        
        # Basic validation for WhatsApp number
        if not tenant_whatsapp.startswith('+') or len(tenant_whatsapp) < 10:
            send_whatsapp_message(
                sender_number, 
                "Please enter a valid WhatsApp number including country code (e.g., +1234567890)."
            )
            return {'status': 'invalid_whatsapp_number'}
        
        # Store tenant WhatsApp in session context
        session.context_data['tenant_whatsapp'] = tenant_whatsapp
        session.current_state = 'payment_cycle_start'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "When did the tenant's payment cycle start? (Enter date in format YYYY-MM-DD)"
        )
        
        return {'status': 'tenant_whatsapp_received'}
    
    def handle_payment_cycle_start(self, message_text, sender_number, session):
        """Handle collecting payment cycle start date."""
        try:
            start_date = timezone.datetime.strptime(message_text.strip(), '%Y-%m-%d').date()
        except ValueError:
            send_whatsapp_message(
                sender_number, 
                "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-03-01)."
            )
            return {'status': 'invalid_start_date'}
        
        # Store start date in session context
        session.context_data['start_date'] = message_text.strip()
        session.current_state = 'bills_due_date'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "When is the bills due date? (Enter date in format YYYY-MM-DD)"
        )
        
        return {'status': 'start_date_received'}
    
    def handle_bills_due_date(self, message_text, sender_number, session):
        """Handle collecting bills due date."""
        try:
            bills_date = timezone.datetime.strptime(message_text.strip(), '%Y-%m-%d').date()
        except ValueError:
            send_whatsapp_message(
                sender_number, 
                "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-03-15)."
            )
            return {'status': 'invalid_bills_date'}
        
        # Store bills date in session context
        session.context_data['bills_date'] = message_text.strip()
        session.current_state = 'last_payment_date'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "When was the last payment made? (Enter date in format YYYY-MM-DD, or type 'none' if no payment yet)"
        )
        
        return {'status': 'bills_date_received'}
    
    def handle_last_payment_date(self, message_text, sender_number, session):
        """Handle collecting last payment date."""
        message_text = message_text.strip().lower()
        
        if message_text == 'none':
            session.context_data['last_payment'] = None
        else:
            try:
                last_payment = timezone.datetime.strptime(message_text, '%Y-%m-%d').date()
                session.context_data['last_payment'] = message_text
            except ValueError:
                send_whatsapp_message(
                    sender_number, 
                    "Please enter a valid date in format YYYY-MM-DD (e.g., 2025-02-15) or type 'none'."
                )
                return {'status': 'invalid_last_payment_date'}
        
        session.current_state = 'payment_cycle_months'
        session.save()
        
        send_whatsapp_message(
            sender_number, 
            "How many months has the tenant paid for? (Enter a number)"
        )
        
        return {'status': 'last_payment_received'}
    
    def handle_payment_cycle_months(self, message_text, sender_number, session):
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
                # Get the rent entity
                rent_entity_id = session.context_data.get('rent_entity_id')
                rent_entity = RentEntity.objects.get(id=rent_entity_id)
                
                # Get dates from session context
                start_date = timezone.datetime.strptime(
                    session.context_data.get('start_date'), '%Y-%m-%d'
                ).date()
                bills_date = timezone.datetime.strptime(
                    session.context_data.get('bills_date'), '%Y-%m-%d'
                ).date()
                
                last_payment = None
                if session.context_data.get('last_payment'):
                    last_payment = timezone.datetime.strptime(
                        session.context_data.get('last_payment'), '%Y-%m-%d'
                    ).date()
                
                # Create tenant
                tenant = Tenant.objects.create(
                    rent_entity=rent_entity,
                    name=session.context_data.get('tenant_name'),
                    whatsapp_number=session.context_data.get('tenant_whatsapp'),
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
                
                # Send main menu to landlord
                menu_text = landlord_main_menu(rent_entity.property.landlord.name)
                send_whatsapp_message(sender_number, menu_text)
                
                # Update session state
                session.current_state = 'main_menu'
                session.save()
                
                return {'status': 'tenant_created'}
                
        except Exception as e:
            print(f"Error creating tenant: {str(e)}")
            send_whatsapp_message(
                sender_number, 
                "Sorry, there was an error creating the tenant. Let's try again."
            )
            session.current_state = 'tenant_name'
            session.save()
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
