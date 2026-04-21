import os
import requests

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to_email, subject, html_content):
    # ✅ Load env variables
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")

    # ✅ Safety checks
    if not api_key:
        print("❌ BREVO_API_KEY is missing")
        return 500, {"error": "Missing API key"}

    if not sender_email:
        print("❌ MAIL_DEFAULT_SENDER is missing")
        return 500, {"error": "Missing sender email"}

    sender_email = sender_email.strip()

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "Vertex Prime Digital",
            "email": sender_email
        },
        "to": [
            {"email": to_email.strip()}
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(BREVO_URL, headers=headers, json=data)

        # ✅ Debug logs
        print(f"📧 Sending to: {to_email}")
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        # ✅ Always return JSON safely
        try:
            response_data = response.json()
        except Exception:
            response_data = {"raw": response.text}

        return response.status_code, response_data

    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {e}")
        return 500, {"error": str(e)}