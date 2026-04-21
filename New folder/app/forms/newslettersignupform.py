from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from wtforms import HiddenField
from flask_ckeditor import CKEditorField
from app.models import NewsletterSubscriber


class NewsletterForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    content = CKEditorField("Content", validators=[DataRequired()])
    submit = SubmitField("Send Newsletter")




class NewsletterSignupForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Length(max=120, message="Email is too long.")
        ]
    )

    honeypot = HiddenField() 

    submit = SubmitField("Subscribe")

    def validate_email(self, field):
        email = field.data.strip().lower()

        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            raise ValidationError("This email is already subscribed.")