import os
import uuid
from datetime import datetime, timedelta
import secrets

import logging
import requests

from flask import  render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image



from . import admin
from app.forms import PostForm, NewsletterForm, DeleteForm, LogoutForm, LoginForm, ActionForm, ForgotPasswordForm, ResetPasswordForm
from app.extensions import db
from app.models import Comment, NewsletterSubscriber, Post, Category, Admin
from app.newsletter.services import get_active_subscribers, send_new_post_notification
# from app import mail
# from flask_mail import Message

from app.services.brevo_email import send_email
from app.newsletter.utils import generate_unsubscribe_token


# from flask_mail import Message
# from app import mail

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


# =========================
# IMAGE PROCESSING FUNCTION
# =========================
def process_image(file):
    try:
        os.makedirs(
            current_app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        img = Image.open(file)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        MAX_WIDTH = 1200

        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / float(img.width)
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

        filename = f"{uuid.uuid4().hex}.webp"
        save_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        img.save(save_path, "WEBP", quality=80, optimize=True)

        return filename

    except Exception as e:
        print("Image processing error:", e)
        return None


# =========================
# ADMIN LOGIN
# =========================
@admin.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        admin_user = Admin.query.filter_by(
            username=form.username.data
        ).first()

        if admin_user and check_password_hash(
            admin_user.password_hash,
            form.password.data
        ):
            login_user(admin_user)

            next_page = request.args.get("next")

            if not next_page or next_page == url_for("admin.login"):
                next_page = url_for("admin.dashboard")

            flash("Logged in successfully!", "success")
            return redirect(next_page)

        flash("Invalid username or password", "danger")

    return render_template("admin/login.html", form=form)

# ====================================
# RESET TOKEN GENERATION AND VERIFICATION
# ====================================

def generate_reset_token(admin_user):
    token = secrets.token_urlsafe(32)

    admin_user.reset_token = token
    admin_user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)

    db.session.commit()

    return token



def verify_reset_token(token):
    admin_user = Admin.query.filter_by(reset_token=token).first()

    if not admin_user:
        return None

    if not admin_user.reset_token_expires:
        return None

    if datetime.utcnow() > admin_user.reset_token_expires:
        return None

    return admin_user



# ===============================
# FORGOT PASSWORD
# ===============================
@admin.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if not email:
            flash("Please enter your email address.", "danger")
            return render_template("admin/forgot_password.html", form=form)

        admin_user = Admin.query.filter_by(email=email).first()

        # Always show the same message whether the email exists or not.
        # This prevents people from discovering the admin email address.
        if admin_user:
            token = secrets.token_urlsafe(32)

            admin_user.reset_token = token
            admin_user.reset_token_expires = (
                datetime.utcnow() + timedelta(minutes=30)
            )

            db.session.commit()

            reset_link = url_for(
                "admin.reset_password",
                token=token,
                _external=True
            )

            api_key = os.getenv("BREVO_API_KEY")
            sender_email = os.getenv("MAIL_DEFAULT_SENDER")

            if not api_key or not sender_email:
                print("Missing Brevo configuration")
                flash(
                    "Unable to send the reset email right now. Please try again later.",
                    "danger"
                )
                return render_template(
                    "admin/forgot_password.html",
                    form=form
                )

            headers = {
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json"
            }

            html_content = render_template(
                "emails/admin_password_reset.html",
                admin=admin_user,
                reset_link=reset_link
            )

            text_content = f"""
Hello,

A request was made to reset your admin password.

Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
Vertex Prime Digital
"""

            data = {
                "sender": {
                    "name": "Vertex Prime Digital",
                    "email": sender_email.strip()
                },
                "to": [
                    {
                        "email": admin_user.email
                    }
                ],
                "subject": "Admin Password Reset",
                "textContent": text_content,
                "htmlContent": html_content
            }

            try:
                response = requests.post(
                    BREVO_URL,
                    headers=headers,
                    json=data,
                    timeout=15
                )

                print("Password reset email status:", response.status_code)
                print("Brevo response:", response.text)

                if response.status_code not in (200, 201):
                    # Remove token if email wasn't successfully sent
                    admin_user.reset_token = None
                    admin_user.reset_token_expires = None
                    db.session.commit()

                    flash(
                        "Unable to send the reset email right now. Please try again later.",
                        "danger"
                    )

                    return render_template(
                        "admin/forgot_password.html", form=form
                    )

            except requests.RequestException as e:
                print(f"Brevo error: {e}")

                admin_user.reset_token = None
                admin_user.reset_token_expires = None
                db.session.commit()

                flash(
                    "Unable to send the reset email right now. Please try again later.",
                    "danger"
                )

                return render_template(
                    "admin/forgot_password.html", form=form
                )

        flash(
            "If an account with that email exists, a password reset link has been sent.",
            "info"
        )

        return redirect(url_for("admin.login"))

    return render_template("admin/forgot_password.html", form=form)


# ===========================
# RESET PASSWORD
# ===============================

@admin.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()

    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    admin_user = Admin.query.filter_by(
        reset_token=token
    ).first()

    if not admin_user:
        flash(
            "This password reset link is invalid or has expired.",
            "danger"
        )
        return redirect(url_for("admin.login"))

    # Check token expiration
    if (
        not admin_user.reset_token_expires
        or admin_user.reset_token_expires < datetime.utcnow()
    ):
        admin_user.reset_token = None
        admin_user.reset_token_expires = None
        db.session.commit()

        flash(
            "This password reset link has expired. Please request a new one.",
            "danger"
        )

        return redirect(url_for("admin.forgot_password"))

    # Validate the Flask-WTF form
    if form.validate_on_submit():

        admin_user.password_hash = generate_password_hash(
            form.password.data
        )

        # Invalidate the token immediately after successful use
        admin_user.reset_token = None
        admin_user.reset_token_expires = None

        db.session.commit()

        flash(
            "Your password has been reset successfully. You can now log in.",
            "success"
        )

        return redirect(url_for("admin.login"))

    return render_template(
        "admin/reset_password.html",
        form=form
    )

    

# =========================
# ADMIN LOGOUT
# =========================
@admin.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    # flash("You have been logged out successfully.", "success")
    return redirect(url_for("admin.login"))


# =========================
# DASHBOARD
# =========================
@admin.route("/dashboard")
@login_required
def dashboard():
    
    posts = Post.query.order_by(Post.created_at.desc()).all()
    subscriber_count = NewsletterSubscriber.query.filter_by(is_active=True).count()
    pending_comments = Comment.query.filter_by(is_approved=False).count()

    delete_form = DeleteForm()
    # logout_form = LogoutForm()

    return render_template(
        "admin/dashboard.html",
        posts=posts,
        subscriber_count=subscriber_count,
        delete_form=delete_form,
        # logout_form=logout_form,
        pending_comments=pending_comments
    )


# =========================
# CREATE POST
# =========================
@admin.route("/posts/create", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        filename = None

        if form.featured_image.data:
            filename = process_image(form.featured_image.data)

        post = Post(
            title=form.title.data,
            slug="",
            excerpt=form.excerpt.data,
            content=form.content.data,
            featured_image=filename,
            category_id=form.category.data,
            author_id=current_user.id,
            status=form.status.data,
            is_featured=form.is_featured.data,
        )

        post.generate_unique_slug()
        post.prepare_post()

        if form.status.data == "published":
            post.published_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

        #  Send notification safely
        if post.status == "published":
            try:
                # from app.newsletter.utils import send_new_post_notification
                with current_app.app_context():
                    result = send_new_post_notification(post)
                if result.get("failed"):
                    flash(f"Post created but failed to send notifications to: {result['failed']}", "warning")
                else:
                    flash("Post created and notifications sent successfully!", "success")
            except Exception:
                logging.exception("Failed to send post notifications")
                flash("Post created but failed to send notifications.", "warning")
        else:
            flash("Post created successfully!", "success")

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/create_post.html", form=form)


# =========================
# EDIT POST
# =========================
@admin.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]

    was_published = post.status == "published"

    if form.validate_on_submit():

        if form.featured_image.data:
            if post.featured_image:
                old_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"],
                    post.featured_image
                )
                if os.path.exists(old_path):
                    os.remove(old_path)

            post.featured_image = process_image(form.featured_image.data)

        post.title = form.title.data
        post.generate_unique_slug()
        post.excerpt = form.excerpt.data
        post.content = form.content.data
        post.category_id = form.category.data
        post.status = form.status.data
        post.is_featured = form.is_featured.data
        post.updated_at = datetime.utcnow()

        # Handle publish state properly
        if form.status.data == "published" and not was_published:
            post.published_at = datetime.utcnow()

        if form.status.data != "published":
            post.published_at = None

        post.prepare_post()

        db.session.commit()

        # Notify only if transitioning to published
        if post.status == "published" and not was_published:
            send_new_post_notification(post)

        flash("Post updated successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/edit_post.html", form=form, post=post)


# =========================
# DELETE POST
# =========================
@admin.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.featured_image:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.featured_image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully!", "success")
    return redirect(url_for("admin.dashboard"))



# =========================
# COMPOSE NEWSLETTER    
# =========================
@admin.route("/newsletter/compose", methods=["GET", "POST"])
@login_required
def compose_newsletter():
    form = NewsletterForm()

    if form.validate_on_submit():
        subject = form.subject.data
        content = form.content.data
        subscribers = get_active_subscribers()

        if not subscribers:
            flash("No active subscribers.", "warning")
            return redirect(url_for("admin.dashboard"))

        failed = []

        # Wrap in app context for safe url_for(_external=True)
        with current_app.app_context():
            for subscriber in subscribers:
                try:
                    if not subscriber.email:
                        failed.append("Invalid email")
                        continue

                    token = generate_unsubscribe_token(subscriber.email)
                    unsubscribe_link = url_for(
                        'newsletter.unsubscribe',
                        token=token,
                        _external=True
                    )

                    html_content = f"""
                    {content}
                    <p>
                        <a href="{unsubscribe_link}">Unsubscribe</a>
                    </p>
                    """

                    status, res = send_email(subscriber.email, subject, html_content)

                    if status not in (200, 201):
                        failed.append(subscriber.email)
                        logging.warning(f"Failed to send to {subscriber.email}: {res}")
                    else:
                        logging.info(f"Sent to {subscriber.email}")

                except Exception as e:
                    logging.exception(f"Error sending to {subscriber.email}")
                    failed.append(subscriber.email)

        # Flash summary
        success_count = len(subscribers) - len(failed)
        if failed:
            flash(f"Sent to {success_count} subscribers. Failed: {failed}", "warning")
        else:
            flash(f"Sent to all {success_count} subscribers!", "success")

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/compose_newsletter.html", form=form)

@admin.route("/comments")
@login_required
def manage_comments():
    form = ActionForm()

    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template("admin/manage_comments.html", comments=comments, form=form)



@admin.route("/comments/<int:comment_id>/toggle", methods=["POST"])
@login_required
def toggle_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    comment.is_approved = not comment.is_approved
    db.session.commit()

    flash("Comment status updated.", "success")
    return redirect(url_for("admin.manage_comments"))




@admin.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted successfully.", "danger")
    return redirect(url_for("admin.manage_comments"))
# from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app.admin import admin
from app.extensions import db
from app.models import NewsletterSubscriber

# View all subscribers
@admin.route("/subscribers/emails")
@login_required
def view_subscriber_emails():
    # Fetch full subscriber objects from DB
    subscribers = NewsletterSubscriber.query.order_by(
        NewsletterSubscriber.subscribed_at.desc()
    ).all()
    
    return render_template(
        "admin/subscriber_emails.html",
        subscribers=subscribers  # pass objects, not strings
    )

# Delete a subscriber
@admin.route("/subscribers/<int:subscriber_id>/delete", methods=["POST"])
@login_required
def delete_subscriber(subscriber_id):
    subscriber = NewsletterSubscriber.query.get_or_404(subscriber_id)
    
    db.session.delete(subscriber)
    db.session.commit()
    
    flash(f"Subscriber {subscriber.email} deleted successfully.", "success")
    return redirect(url_for("admin.view_subscriber_emails"))