import os
import requests
from flask import current_app, render_template, url_for
from datetime import datetime
from app.models import NewsletterSubscriber
from app.newsletter.utils import generate_unsubscribe_token
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

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
    - Search engine optimization (SEO)
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
            max_tokens=400
        )

        text = response.choices[0].message.content.strip()

        title = "Weekly Insight 🚀"
        content = text
        tip = ""

        if "Title:" in text:
            title = text.split("Title:")[1].split("\n")[0].strip()

        if "Content:" in text:
            content = text.split("Content:")[1].split("Tip:")[0].strip()

        if "Tip:" in text:
            tip = text.split("Tip:")[1].strip()

        return {"title": title, "content": content, "tip": tip}

    except Exception as e:
        print(f"❌ AI Error: {e}")
        return {
            "title": "Stay Consistent 🚀",
            "content": "Success comes from showing up every day. Focus on small improvements and keep building momentum.",
            "tip": "Choose one important task today and complete it fully."
        }


# =========================
# SEND WEEKLY NEWSLETTER
# =========================
def send_weekly_newsletter():
    app = current_app._get_current_object()

    with app.app_context():
        try:
            subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()

            if not subscribers:
                print("⚠️ No subscribers found")
                return

            newsletter = generate_ai_newsletter()

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

            for sub in subscribers:
                try:
                    token = generate_unsubscribe_token(sub.email)

                    unsubscribe_link = url_for(
                        "newsletter.unsubscribe",
                        token=token,
                        _external=True
                    )

                    text_content = f"""
Hello {getattr(sub, 'name', 'there')},

{newsletter['content']}

💡 Tip:
{newsletter['tip']}

👉 Visit: https://vertexprimedigital.com
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
                        "to": [{"email": sub.email.strip()}],
                        "subject": f"🚀 {newsletter['title']}",
                        "textContent": text_content,
                        "htmlContent": html_content
                    }

                    response = requests.post(
                        BREVO_URL,
                        headers=headers,
                        json=data
                    )

                    print(f"📧 Sending to: {sub.email}")
                    print("STATUS:", response.status_code)
                    print("RESPONSE:", response.text)

                    if response.status_code not in (200, 201):
                        failed.append(sub.email)

                except Exception as e:
                    print(f"❌ Failed for {sub.email}: {e}")
                    failed.append(sub.email)

            if failed:
                print(f"⚠️ Failed emails: {failed}")
            else:
                print(f"✅ [{datetime.utcnow()}] Newsletter sent successfully!")

        except Exception as e:
            print(f"❌ Newsletter Error: {e}")


# =========================
# SCHEDULER
# =========================
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