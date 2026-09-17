import os
import requests
from flask import render_template, url_for

from app.models import NewsletterSubscriber
from app.newsletter.utils import generate_unsubscribe_token
from openai import OpenAI

client = OpenAI()

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


# =========================
# AI NEWSLETTER GENERATOR
# =========================
def generate_ai_newsletter():
    prompt = """
    Choose a random topic related to:

    - Technology
    - Personal growth
    - Business
    - Productivity
    - Website development
    - Website design
    - Digital marketing
    - SEO (Search Engine Optimization)
    - Social media strategies
    - Entrepreneurship
    - Remote work best practices
    - Emerging tech trends (AI, blockchain, cloud computing)
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
    - UX/UI principles and trends
    - Mobile app development trends
    - Digital branding strategies
    - Email marketing strategies
    - Startup growth strategies
    - Financial literacy for entrepreneurs
    - Artificial intelligence applications in business
    - Automation tools for productivity

    Then write a short weekly newsletter.

    REQUIREMENTS:
    - Title
    - 4–5 short paragraphs
    - Friendly, inspiring tone
    - Simple English
    - One actionable tip at the end

    FORMAT STRICTLY:
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
            max_tokens=500
        )

        text = response.choices[0].message.content.strip()

        title = "Weekly Insight"
        content = text
        tip = ""

        if "Title:" in text:
            title = text.split("Title:")[1].split("\n")[0].strip()

        if "Content:" in text:
            content = text.split("Content:")[1].split("Tip:")[0].strip()

        if "Tip:" in text:
            tip = text.split("Tip:")[1].strip()

        return {
        "title": title,
        "content": content,
        "tip": tip,
        "ai_generated": True
    }

    except Exception as e:
        print(f"AI Error: {e}")
        return {
        "title": "Stay Consistent 🚀",
        "content": "Small daily improvements lead to big results over time.",
        "tip": "Focus on completing one meaningful task today.",
        "ai_generated": False
    }


# =========================
# SEND NEWSLETTER
# =========================
def send_weekly_newsletter():
    try:
        subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()

        if not subscribers:
            print("No subscribers found")
            return {"status": "skipped", "reason": "no active subscribers"}

        newsletter = generate_ai_newsletter()

        api_key = os.getenv("BREVO_API_KEY", "")
        sender_email = os.getenv("MAIL_DEFAULT_SENDER", "noreply@localhost")

        if not api_key:
            print("Missing BREVO_API_KEY")
            return {"status": "error", "reason": "missing BREVO_API_KEY"}

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        sent = 0
        failed = 0

        for sub in subscribers:
            try:
                token = generate_unsubscribe_token(sub.email)

                unsubscribe_link = url_for(
                    "newsletter.unsubscribe",
                    token=token,
                    _external=True
                )

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
                    "subject": newsletter["title"],
                    "htmlContent": html_content
                }

                response = requests.post(BREVO_URL, headers=headers, json=data)
                print(f"Sent to {sub.email} - {response.status_code}")

                if response.status_code in (200, 201):
                    sent += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"Failed for {sub.email}: {e}")
                failed += 1

        return {"status": "done", "sent": sent, "failed": failed, "title": newsletter["title"], "ai_generated": newsletter.get("ai_generated")}

    except Exception as e:
        print(f"Newsletter Error: {e}")
        return {"status": "error", "reason": str(e)}