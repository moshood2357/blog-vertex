import os
import requests
from flask import current_app

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def send_email(to_email, subject, html_content):
    api_key = os.getenv("BREVO_API_KEY")

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "Vertex Prime Digital",
            "email": current_app.config.get("MAIL_DEFAULT_SENDER")
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    response = requests.post(BREVO_URL, headers=headers, json=data)

    return response.status_code, response.json()