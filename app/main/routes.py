from flask import jsonify, render_template, flash, redirect, url_for, request, session
from . import main
from app.models import Post, Comment, NewsletterSubscriber
from app.extensions import db
from app.forms import CommentForm, NewsletterSignupForm
from datetime import datetime


# =========================
# BLOG HOME (PAGINATED)
# =========================
@main.route("/")
def blog():
    posts = (
        Post.query
        .filter_by(status="published")
        .order_by(Post.published_at.desc())
        .paginate(page=request.args.get("page", 1, type=int), per_page=3)
    )

    newsletter_form = NewsletterSignupForm()

    return render_template(
        "main/home.html",
        posts=posts,
        now=datetime.utcnow(),
        form=newsletter_form
    )


# =========================
# POST DETAIL
# =========================
@main.route("/post/<slug>", methods=["GET", "POST"])
def post_detail(slug):
    post = Post.query.filter_by(slug=slug, status="published").first_or_404()

    # Safe view increment
    if request.method == "GET":
        post.views = (post.views or 0) + 1
        db.session.commit()

    form = CommentForm()

    # Comment submission (moderated)
    if form.validate_on_submit():
        comment = Comment(
            post_id=post.id,
            name=form.name.data,
            email=form.email.data,
            content=form.content.data,
            is_approved=False  # IMPORTANT: moderation enabled
        )

        db.session.add(comment)
        db.session.commit()

        flash("Comment submitted for approval.", "success")
        return redirect(url_for("main.post_detail", slug=post.slug))

    # Only show approved comments
    approved_comments = (
        Comment.query
        .filter(Comment.post_id == post.id, Comment.is_approved.is_(True))
        .order_by(Comment.created_at.desc())
        .all()
    )

    return render_template(
        "main/post_detail.html",
        post=post,
        form=form,
        comments=approved_comments
    )


# =========================
# LIKE POST (NO LOGIN REQUIRED)
# =========================
@main.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Initialize session storage
    if "liked_posts" not in session:
        session["liked_posts"] = []

    # Prevent duplicate likes in same session
    if post_id in session["liked_posts"]:
        return jsonify({
            "likes": post.likes_count or 0,
            "message": "Already liked"
        }), 200

    post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()

    session["liked_posts"].append(post_id)
    session.modified = True

    return jsonify({
        "likes": post.likes_count,
        "message": "Liked successfully"
    }), 200


@main.route("/post/<int:post_id>/comment", methods=["POST"])
def submit_comment(post_id):
    post = Post.query.get_or_404(post_id)

    name = request.form.get("name")
    email = request.form.get("email")
    content = request.form.get("content")

    if not name or not email or not content:
        return jsonify({"status": "error", "message": "All fields are required."})

    comment = Comment(
        post_id=post.id,
        name=name,
        email=email,
        content=content,
        is_approved=False  # Moderation enabled
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "status": "success",
        "name": comment.name,
        "content": comment.content
    })




# =========================
# NEWSLETTER SUBSCRIPTION
# =========================
@main.route("/subscribe", methods=["POST"])
def subscribe_newsletter():
    form = NewsletterSignupForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Honeypot spam protection
        if form.honeypot.data:
            return redirect(request.referrer or url_for("main.blog"))

        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            flash("You're already subscribed!", "info")
            return redirect(request.referrer or url_for("main.blog"))

        new_subscriber = NewsletterSubscriber(email=email)
        db.session.add(new_subscriber)
        db.session.commit()

        flash("Subscribed successfully!", "success")
        return redirect(request.referrer or url_for("main.blog"))

    flash("Please enter a valid email.", "danger")
    return redirect(request.referrer or url_for("main.blog"))