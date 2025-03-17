import requests  # Make sure this is imported at the top of utils.py
import json
from django.conf import settings


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
        print(f"Response Status Code: {response.status_code}") #for debugging
        print(f"Response Content: {response.text}") #For debugging
        
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