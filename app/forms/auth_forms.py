from flask_wtf import FlaskForm
from wtforms import SubmitField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class DeleteForm(FlaskForm):
    pass



class LogoutForm(FlaskForm):
    submit = SubmitField("Logout")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")



class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email()
        ]
    )
    submit = SubmitField("Send Reset Link")




class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long.")
        ]
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )

    submit = SubmitField("Reset Password")