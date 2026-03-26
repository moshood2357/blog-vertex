import os
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
api_key = os.getenv("BREVO_API_KEY")
sender_email = os.getenv("MAIL_DEFAULT_SENDER")

data = {
    "sender": {"name": "Vertex Prime Digital", "email": sender_email},
    "to": [{"email": "sanusimoshoodabiola@gmail.com"}],
    "subject": "Test Email from Brevo",
    "htmlContent": "<h1>Hello from Vertex Prime Digital!</h1>",
    "textContent": "Hello from Vertex Prime Digital!"
}

headers = {
    "accept": "application/json",
    "api-key": api_key,
    "content-type": "application/json"
}

resp = requests.post(BREVO_URL, headers=headers, json=data)
print(resp.status_code, resp.text)