from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed
from flask_ckeditor import CKEditorField


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    slug = StringField("Slug")
    excerpt = TextAreaField("Excerpt")
    content = CKEditorField("Content", validators=[DataRequired()])
    featured_image = FileField("Featured Image", validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'])
    ])

    category = SelectField("Category", coerce=int)
    status = SelectField("Status", choices=[
        ("draft", "Draft"),
        ("published", "Published")
    ])

    is_featured = BooleanField("Feature this post")

    submit = SubmitField("Publish Post")
