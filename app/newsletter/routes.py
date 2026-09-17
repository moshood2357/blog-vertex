

import os
from app import csrf
from flask import Blueprint, request, jsonify, flash, redirect, url_for, abort
from datetime import datetime
from . import newsletter
from app import db
from app.models import NewsletterSubscriber
from .utils import verify_unsubscribe_token



from app.newsletter.scheduler import send_weekly_newsletter



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

    return redirect(url_for("main.blog"))


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




@newsletter.route("/run-weekly-newsletter", methods=["POST"])
@csrf.exempt
def run_weekly_newsletter():
    secret = request.headers.get("X-Cron-Secret", "")
    expected = os.getenv("CRON_SECRET", "")

    if not expected or secret != expected:
        abort(403)

    result = send_weekly_newsletter()
    return jsonify(result), 200