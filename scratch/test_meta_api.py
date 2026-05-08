import os
import requests
from dotenv import load_dotenv

# Carrega as variaveis do .env local
load_dotenv('backend/.env')

token = os.getenv("WHATSAPP_CLOUD_TOKEN")
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
target_number = "5513974096837" 

print("--- Diagnostico Meta API ---")
print(f"Phone Number ID: {phone_id}")
if token:
    print(f"Token (inicio): {token[:20]}...")
else:
    print("Token: NAO ENCONTRADO NO .ENV")

url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "messaging_product": "whatsapp",
    "to": target_number,
    "type": "text",
    "text": {"body": "Teste de conexao direta Finan\u00e7asAI. Se voce recebeu isso, o Token e o ID estao corretos!"}
}

try:
    print("\nEnviando mensagem de teste...")
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("SUCESSO! A Meta aceitou o envio.")
    else:
        print("ERRO DA META:")
        print(resp.text)
except Exception as e:
    print(f"ERRO DE CONEXAO: {e}")
