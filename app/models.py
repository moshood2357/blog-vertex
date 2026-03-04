import math
from datetime import datetime
from flask_login import UserMixin
from slugify import slugify
from .extensions import db

# -------------------------
# USERS (authors who can like posts)
# -------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "author"), default="author")
    
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to track likes
    liked_posts = db.relationship(
        "Post",
        secondary="post_likes",
        back_populates="liked_by"
    )


# -------------------------
# ADMINS
# -------------------------
class Admin(db.Model, UserMixin):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    posts = db.relationship("Post", backref="author", lazy=True)


# -------------------------
# POST LIKES (association table)
# -------------------------
post_likes = db.Table(
    "post_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True)
)


# -------------------------
# CATEGORIES
# -------------------------
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", backref="category", lazy=True)


# -------------------------
# POSTS
# -------------------------
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(255))

    is_featured = db.Column(db.Boolean, default=False)
    reading_time = db.Column(db.Integer)
    likes_count = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)

    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.String(255))
    canonical_url = db.Column(db.String(255))
    og_title = db.Column(db.String(255))
    og_description = db.Column(db.String(255))
    og_image = db.Column(db.String(255))
    twitter_title = db.Column(db.String(255))
    twitter_description = db.Column(db.String(255))
    twitter_image = db.Column(db.String(255))
    is_indexed = db.Column(db.Boolean, default=True)

    author_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    comments = db.relationship(
        "Comment",
        backref="post",
        lazy=True,
        cascade="all, delete"
    )

    status = db.Column(db.Enum("draft", "published"), default="draft")
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship for likes
    liked_by = db.relationship(
        "User",
        secondary="post_likes",
        back_populates="liked_posts"
    )

    # -------------------------
    # Methods
    # -------------------------
    def calculate_reading_time(self):
        if self.content:
            self.reading_time = max(1, math.ceil(len(self.content.split()) / 200))

    def prepare_post(self):
        self.calculate_reading_time()
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description:
            self.meta_description = (self.excerpt or self.content)[:155]
        if not self.canonical_url:
            self.canonical_url = f"/blog/{self.slug}"


# -------------------------
# COMMENTS
# -------------------------
class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# NEWSLETTER SUBSCRIBERS
# -------------------------
class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)