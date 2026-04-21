import os
import requests
from flask import url_for
from app.models import NewsletterSubscriber
from app.newsletter.utils import generate_unsubscribe_token

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def get_active_subscribers():
    return NewsletterSubscriber.query.filter_by(is_active=True).all()


def send_new_post_notification(post):
    subscribers = get_active_subscribers()

    if not subscribers:
        print("⚠️ No subscribers found")
        return

    # ✅ Load environment variables safely
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")

    if not api_key:
        print("❌ Missing BREVO_API_KEY")
        return

    if not sender_email:
        print("❌ Missing MAIL_DEFAULT_SENDER")
        return

    sender_email = sender_email.strip()

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    failed = []

    for subscriber in subscribers:
        try:
            token = generate_unsubscribe_token(subscriber.email)

            unsubscribe_link = url_for(
                "newsletter.unsubscribe",
                token=token,
                _external=True
            )

            post_link = url_for(
                "main.post_detail",
                slug=post.slug,
                _external=True
            )

            html_content = f"""
            <h2>{post.title}</h2>
            <p>{post.excerpt}</p>

            <p>
                <a href="{post_link}">Read Full Post</a>
            </p>

            <hr>
            <small>
                <a href="{unsubscribe_link}">Unsubscribe</a>
            </small>
            """

            data = {
                "sender": {
                    "name": "Vertex Prime Digital",
                    "email": sender_email
                },
                "to": [
                    {"email": subscriber.email}
                ],
                "subject": f"New Post: {post.title}",
                "htmlContent": html_content
            }

            response = requests.post(
                BREVO_URL,
                headers=headers,
                json=data
            )

            # ✅ Debug logs
            print(f"📧 Sending to: {subscriber.email}")
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            if response.status_code not in (200, 201):
                failed.append(subscriber.email)

        except Exception as e:
            print(f"❌ Error sending to {subscriber.email}: {e}")
            failed.append(subscriber.email)

    # ✅ Final summary
    if failed:
        print(f"❌ Failed emails: {failed}")
    else:
        print(f"✅ All {len(subscribers)} emails sent successfully!")