from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Property, Tenant, Landlord
from .serializers import PropertySerializer, TenantSerializer, LandlordSerializer
import json
import requests
from django.views.generic import TemplateView
from .utils import *


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

class TenantListCreate(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

class TenantRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

class WhatsAppWebhook(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data  # Automatically parsed JSON from request body
        incoming_message = payload['messages'][0]
        sender_number = incoming_message['from']
        message_text = incoming_message['text']['body']
        return self.handle_message(message_text, sender_number)
    
    def handle_message(self, message, sender_number):
        """ Process the incoming message. """
        try:
            landlord = Landlord.objects.get(whatsapp_number=sender_number)
            self.send_whatsapp_message(sender_number, f"Welcome back, {landlord.name}!")
        except Landlord.DoesNotExist:
            self.prompt_for_name(sender_number)
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
    def prompt_for_name(self, sender_number):
        """ Send a message prompting the user for their name. """
        self.send_whatsapp_message(sender_number, "Welcome! I am \"Le Bailleur\", your rent management automatic assistant. If you are a landlord searching for a way to seamlessly get notified and notify your tenants when rents are due, we are going to take your property and tenant information to effectively track your rents and notify both you and your tenants when rents are due. Please start by entering your name")
    
    def handle_name_response(self, name, sender_number):
        """ Handle the response containing the user's name. """
        landlord = Landlord.objects.create(whatsapp_number=sender_number, name=name)
        self.send_whatsapp_message(sender_number, f"Thank you, {name}! You are now logged in.")
    
    def prompt_for_property_name(self, sender_number):
        """ Send a message prompting the user for their property name. """
        self.send_whatsapp_message(sender_number, "Please enter the name of the property you'll like to manage"

    def prompt_for_property_adress(self, sender_number):
        """ Send a message prompting the user for their property name. """
        self.send_whatsapp_message(sender_number, "Please enter the adress (Country-town-quarter-PO. Box) of the property")

    def handle_name_response(self, property_name, property_adress, landlord.name, sender_number):
        property = Property.objects.create(name=property_name, adress=property_adress, landlord=landlord.name)

    