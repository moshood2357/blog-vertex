import os
from flask import Flask, app, render_template, send_from_directory
from datetime import datetime
from flask_ckeditor import CKEditor
from flask_compress import Compress
from flask_mail import Mail, Message
from flask_wtf import CSRFProtect

from app.forms.auth_forms import LogoutForm
from .extensions import db, migrate, login_manager

ckeditor = CKEditor()
csrf = CSRFProtect()
mail = Mail()


def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Mail config from environment variables
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 2525))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = (
        os.getenv('MAIL_DEFAULT_SENDER_NAME'),
        os.getenv('MAIL_DEFAULT_SENDER_EMAIL')
    )

    # Configure upload folder safely
    upload_folder = os.path.join(app.root_path, "static", "uploads")
    app.config['UPLOAD_FOLDER'] = upload_folder
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Init extensions
    db.init_app(app)
    Compress(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    ckeditor.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'admin.login'  
    login_manager.login_message_category = 'info'

    # Import models
    from .models import Admin, Category, Post, Comment, NewsletterSubscriber
    

    @login_manager.user_loader
    def load_user(admin_id):
        return Admin.query.get(int(admin_id))

    # -------------------------
    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

   

    # Context processor for current time
    @app.context_processor
    def _inject_now():
        return {"now": datetime.utcnow()}
    
    @app.context_processor
    def inject_logout_form():
        return dict(logout_form=LogoutForm())
    

    
    
    @app.route('/test-mail')
    def test_mail():
        try:
            msg = Message(
            "Test Email",
            recipients=["any_email@example.com"],
            body="Testing Mailtrap connection"
        )
            mail.send(msg)
            return "Email sent!"
        except Exception as e:
            return f"Mail failed: {e}"

    # Register blueprints
    from .main import main as main_bp
    from .admin import admin as admin_bp
    from .seo import seo as seo_bp
    from .newsletter import newsletter as newsletter_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seo_bp)
    app.register_blueprint(newsletter_bp, url_prefix="/newsletter")

    return app