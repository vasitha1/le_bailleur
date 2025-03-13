from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Property, Tenant, Landlord
from .serializers import PropertySerializer, TenantSerializer, LandlordSerializer
import json
import requests

# Django REST Framework views for Landlord, Property, and Tenant
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
        self.send_whatsapp_message(sender_number, "Hello! Please provide your name to get started.")
    
    def handle_name_response(self, name, sender_number):
        """ Handle the response containing the user's name. """
        landlord = Landlord.objects.create(whatsapp_number=sender_number, name=name)
        self.send_whatsapp_message(sender_number, f"Thank you, {name}! You are now logged in.")
    
    def send_whatsapp_message(self, to, message):
        url = "https://api.whatsapp.com/v1/messages"  # Adjust URL based on your provider
        headers = {
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
            'Content-Type': 'application/json'
        }
        payload = {
            'to': to,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raises an error for bad responses
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")