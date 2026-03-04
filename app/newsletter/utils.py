from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_unsubscribe_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="unsubscribe-salt")

def verify_unsubscribe_token(token, max_age=86400):  # 24 hours
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token,
            salt="unsubscribe-salt",
            max_age=max_age
        )
        return email
    except Exception:
        return None