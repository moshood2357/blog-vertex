import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "mysql+pymysql://root@localhost/blog_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BLOG_NAME = "My Awesome Blog"
    SITE_URL = "https://yourdomain.com"
    # Admin credentials (for simplicity, using environment variables)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"