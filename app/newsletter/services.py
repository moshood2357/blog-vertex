import os
import logging
import requests
from flask import url_for, current_app
from app.models import NewsletterSubscriber
from app.newsletter.utils import generate_unsubscribe_token

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

# Configure logging
logging.basicConfig(level=logging.INFO)


def get_active_subscribers():
    """Fetch all active newsletter subscribers."""
    return NewsletterSubscriber.query.filter_by(is_active=True).all()


def send_new_post_notification(post):
    """
    Sends a new post notification email to all active subscribers.
    
    Returns a summary dictionary:
        {"success": int, "failed": list}
    """
    subscribers = get_active_subscribers()
    failed = []

    if not subscribers:
        logging.warning("No active subscribers found.")
        return {"success": 0, "failed": failed}

    # Load environment variables
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("MAIL_DEFAULT_SENDER")

    if not api_key:
        logging.error(" Missing BREVO_API_KEY in environment")
        return {"success": 0, "failed": [s.email for s in subscribers]}

    if not sender_email:
        logging.error(" Missing MAIL_DEFAULT_SENDER in environment")
        return {"success": 0, "failed": [s.email for s in subscribers]}

    sender_email = sender_email.strip()
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    # Use Flask app context for url_for
    with current_app.app_context():
        for subscriber in subscribers:
            try:
                if not subscriber.email:
                    failed.append("Invalid email")
                    continue

                # Generate unsubscribe link
                token = generate_unsubscribe_token(subscriber.email)
                unsubscribe_link = url_for("newsletter.unsubscribe", token=token, _external=True)

                # Link to the blog post
                post_link = url_for("main.post_detail", slug=post.slug, _external=True)

                # Email HTML content
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
                    "to": [{"email": subscriber.email}],
                    "subject": f"New Post: {post.title}",
                    "htmlContent": html_content
                }

                # Send email with a timeout
                response = requests.post(BREVO_URL, headers=headers, json=data, timeout=10)

                logging.info(f" Sent to: {subscriber.email} | STATUS: {response.status_code}")

                if response.status_code not in (200, 201):
                    failed.append(subscriber.email)
                    logging.warning(f"Failed response: {response.text}")

            except Exception as e:
                logging.exception(f" Error sending to {subscriber.email}")
                failed.append(subscriber.email)

    success_count = len(subscribers) - len(failed)
    logging.info(f" Emails sent: {success_count} | Failed: {len(failed)}")

    return {"success": success_count, "failed": failed}