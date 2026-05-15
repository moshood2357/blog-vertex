import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
     "mysql+pymysql://root@localhost/blog_db"
        # "mysql+pymysql://edkrlist_blog_user:Ayinde%40123456789@localhost/edkrlist_r2_blog"
        # 
   
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BLOG_NAME = "Vertex Digital Prime Blog"
    SITE_URL = "https://blog.vertexprimedigital.com"
    # Admin credentials (for simplicity, using environment variables)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"\

    SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280
}