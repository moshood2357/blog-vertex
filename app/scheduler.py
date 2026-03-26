import os
import requests
from flask import current_app, render_template, url_for
from datetime import datetime
from app.models import NewsletterSubscriber
from openai import OpenAI

client = OpenAI()
BREVO_URL = "https://api.brevo.com/v3/smtp/email"


# =========================
# AI CONTENT GENERATOR
# =========================
def generate_ai_newsletter():
    prompt = """
    Choose a random topic related to:
    - technology
    - personal growth
    - business
    - productivity
    - Website development
    - Website design
    - Digital marketing
    - SEO
    - Social media strategies
    - Entrepreneurship
    - Remote work best practices
    - Emerging tech trends (AI, blockchain, etc.)
    - Career development tips
    - Mindset and motivation
    - Time management techniques
    - Wellness and work-life balance
    - Leadership and team building
    - Content creation strategies
    - Online business growth hacks
    - E-commerce tips
    - Digital transformation insights
    - Future of work predictions
    - Cybersecurity basics
    - Data privacy tips
    - Software development best practices
    - Web design trends
    - User experience (UX) principles
    - Mobile app development trends
    - UI/UX design tips
    - UI/UX design trends
    - Digital marketing trends

    Then write a short, engaging weekly newsletter.

    Requirements:
    - Title
    - 4–5 short paragraphs
    - Friendly and inspiring tone
    - Simple English
    - Add a short actionable tip at the end

    Format strictly as:
    Title: ...
    Content: ...
    Tip: ...
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional newsletter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )

        text = response.choices[0].message.content.strip()
        title = text.split("Title:")[1].split("\n")[0].strip() if "Title:" in text else "Weekly Insight 🚀"
        content = text.split("Content:")[1].split("Tip:")[0].strip() if "Content:" in text else text
        tip = text.split("Tip:")[1].strip() if "Tip:" in text else ""

        return {"title": title, "content": content, "tip": tip}

    except Exception as e:
        print(f"AI Error: {e}")
        return {
            "title": "Stay Consistent 🚀",
            "content": "Success comes from showing up every day. Focus on small improvements and keep building momentum.",
            "tip": "Choose one important task today and complete it fully."
        }


# =========================
# SEND WEEKLY NEWSLETTER TO ALL SUBSCRIBERS (BREVO)
# =========================
def send_weekly_newsletter():
    app = current_app._get_current_object()
    with app.app_context():
        try:
            subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()
            if not subscribers:
                print("No active subscribers found.")
                return

            newsletter = generate_ai_newsletter()
            failed_emails = []

            api_key = os.getenv("BREVO_API_KEY")
            sender_email = app.config.get("MAIL_DEFAULT_SENDER")

            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }

            for sub in subscribers:
                try:
                    # Generate unsubscribe link if you have one
                    unsubscribe_link = url_for("newsletter.unsubscribe", token=sub.email, _external=True)
                    post_link = url_for("main.post_detail", slug="", _external=True)

                    text_content = f"""
Hello {getattr(sub, 'name', 'there')},

{newsletter['content']}

💡 Tip:
{newsletter['tip']}

👉 Visit our website: https://vertexprimedigital.com
Date: {datetime.utcnow().strftime('%Y-%m-%d')}
"""

                    html_content = render_template(
                        "emails/newsletter.html",
                        subscriber=sub,
                        newsletter=newsletter,
                        unsubscribe_link=unsubscribe_link
                    )

                    data = {
                        "sender": {
                            "name": "Vertex Prime Digital",
                            "email": sender_email
                        },
                        "to": [{"email": sub.email}],
                        "subject": f"🚀 {newsletter['title']}",
                        "textContent": text_content,
                        "htmlContent": html_content
                    }

                    response = requests.post(BREVO_URL, headers=headers, json=data)

                    print(f"📧 Sending to {sub.email} | STATUS: {response.status_code}")

                    if response.status_code not in (200, 201):
                        failed_emails.append(sub.email)

                except Exception as e:
                    print(f"❌ Failed to send to {sub.email}: {e}")
                    failed_emails.append(sub.email)

            if failed_emails:
                print(f"⚠️ Newsletter sent with failures: {failed_emails}")
            else:
                print(f"✅ [{datetime.utcnow()}] Newsletter sent successfully to all subscribers.")

        except Exception as e:
            print(f"❌ Newsletter Error: {e}")


# =========================
# SCHEDULER
# =========================
from apscheduler.schedulers.background import BackgroundScheduler

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=send_weekly_newsletter,
        trigger="cron",
        day_of_week="mon",
        hour=9,
        minute=0
    )
    scheduler.start()

    if app.debug:
        import atexit
        atexit.register(lambda: scheduler.shutdown())