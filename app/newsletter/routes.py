from flask import Blueprint, request, jsonify, flash, redirect, url_for
from datetime import datetime
from . import newsletter
from app import db
from app.models import NewsletterSubscriber
from .utils import verify_unsubscribe_token




@newsletter.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email') or request.json.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    subscriber = NewsletterSubscriber.query.filter_by(email=email).first()

    if subscriber:
        if subscriber.is_active:
            return jsonify({"message": "You are already subscribed."}), 200
        else:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.subscribed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({"message": "Welcome back! Subscription reactivated."}), 200

    new_subscriber = NewsletterSubscriber(email=email)
    db.session.add(new_subscriber)
    db.session.commit()

    return jsonify({"message": "Successfully subscribed!"}), 201


@newsletter.route("/unsubscribe/<token>")
def unsubscribe(token):
    email = verify_unsubscribe_token(token)

    if not email:
        flash("Invalid or expired unsubscribe link.", "danger")
        return redirect(url_for("main.blog"))

    subscriber = NewsletterSubscriber.query.filter_by(email=email).first()

    if subscriber:
        subscriber.is_active = False
        db.session.commit()
        flash("You have successfully unsubscribed.", "success")

    return redirect(url_for("main.blog"))