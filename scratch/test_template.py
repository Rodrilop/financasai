import os
import requests
from dotenv import load_dotenv

load_dotenv('backend/.env')

token = os.getenv("WHATSAPP_CLOUD_TOKEN")
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
target_number = "5513974096837" 

url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "messaging_product": "whatsapp",
    "to": target_number,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {
            "code": "en_US"
        }
    }
}

resp = requests.post(url, json=payload, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
