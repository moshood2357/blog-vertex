from flask import url_for
from app import mail
from flask_mail import Message
from app.models import NewsletterSubscriber
from app.newsletter.utils import generate_unsubscribe_token

def get_active_subscribers():
    return NewsletterSubscriber.query.filter_by(is_active=True).all()



def send_new_post_notification(post):
    subscribers = get_active_subscribers()

    if not subscribers:
        return

    for subscriber in subscribers:
        token = generate_unsubscribe_token(subscriber.email)

        unsubscribe_link = url_for(
            "newsletter.unsubscribe",
            token=token,
            _external=True
        )

        html_content = f"""
        <h2>{post.title}</h2>
        <p>{post.excerpt}</p>

        <p>
            <a href="{url_for('main.post_detail', slug=post.slug, _external=True)}">
                Read Full Post
            </a>
        </p>

        <hr>
        <small>
            <a href="{unsubscribe_link}">Unsubscribe</a>
        </small>
        """

        msg = Message(
            subject=f"New Post: {post.title}",
            recipients=[subscriber.email],
            html=html_content
        )

        mail.send(msg)