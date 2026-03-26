import os
from dotenv import load_dotenv

from flask import Flask, render_template, send_from_directory
from datetime import datetime
from flask_ckeditor import CKEditor
from flask_compress import Compress
from flask_wtf import CSRFProtect

from app.forms.auth_forms import LogoutForm
from .extensions import db, migrate, login_manager

# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================
load_dotenv()

# Make sure BREVO_API_KEY is available
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
if not BREVO_API_KEY or not MAIL_DEFAULT_SENDER:
    raise RuntimeError("Environment variables BREVO_API_KEY or MAIL_DEFAULT_SENDER not set!")

ckeditor = CKEditor()
csrf = CSRFProtect()


def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # =========================
    # FILE UPLOAD CONFIG
    # =========================
    upload_folder = os.path.join(app.root_path, "static", "uploads")
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # =========================
    # INIT EXTENSIONS
    # =========================
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    Compress(app)

    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'info'

    # =========================
    # IMPORT MODELS
    # =========================
    from .models import Admin, Category, Post, Comment, NewsletterSubscriber

    @login_manager.user_loader
    def load_user(admin_id):
        return Admin.query.get(int(admin_id))

    # =========================
    # ROUTES
    # =========================
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    @app.context_processor
    def inject_logout_form():
        return dict(logout_form=LogoutForm())

    # =========================
    # REGISTER BLUEPRINTS
    # =========================
    from .main import main as main_bp
    from .admin import admin as admin_bp
    from .seo import seo as seo_bp
    from .newsletter import newsletter as newsletter_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seo_bp)
    app.register_blueprint(newsletter_bp, url_prefix="/newsletter")

    # =========================
    # START SCHEDULER (SAFE)
    # =========================
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app