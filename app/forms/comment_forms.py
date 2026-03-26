from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class CommentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[
        DataRequired(),
        Email(message="Enter a valid email address"),
        Length(max=150)
    ])
    content = TextAreaField("Comment", validators=[DataRequired()])