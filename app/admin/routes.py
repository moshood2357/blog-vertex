import os
import uuid
from datetime import datetime

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from PIL import Image



from . import admin
from app.forms import PostForm, NewsletterForm, DeleteForm, LogoutForm, LoginForm, ActionForm
from app.extensions import db
from app.models import Comment, NewsletterSubscriber, Post, Category, Admin
from app.newsletter.services import get_active_subscribers, send_new_post_notification
from app import mail
from flask_mail import Message



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

        # Send notification only if published
        if post.status == "published":
            send_new_post_notification(post)

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
from app.newsletter.utils import generate_unsubscribe_token
from flask_mail import Message
from app import mail

@admin.route("/newsletter/compose", methods=["GET", "POST"])
@login_required
def compose_newsletter():
    form = NewsletterForm()
    if form.validate_on_submit():
        subject = form.subject.data
        content = form.content.data
        subscribers = get_active_subscribers()  # returns list of active NewsletterSubscriber objects

        if not subscribers:
            flash("No active subscribers to send newsletter.", "warning")
            return redirect(url_for("admin.dashboard"))

        failed_emails = []

        for subscriber in subscribers:
            # Generate secure unsubscribe token
            token = generate_unsubscribe_token(subscriber.email)
            unsubscribe_link = url_for('newsletter.unsubscribe', token=token, _external=True)

            html_content = f"""
            {content}
            <p>Click <a href="{unsubscribe_link}">here</a> to unsubscribe.</p>
            """

            try:
                msg = Message(
                    subject=subject,
                    recipients=[subscriber.email], 
                    html=html_content
                )
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send email to {subscriber.email}: {e}")
                failed_emails.append(subscriber.email)

        if failed_emails:
            flash(f"Newsletter sent, but failed for {len(failed_emails)} emails.", "warning")
        else:
            flash(f"Newsletter sent successfully to {len(subscribers)} subscribers!", "success")

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