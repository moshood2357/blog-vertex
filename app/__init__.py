import os
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, render_template, send_from_directory, url_for, request, redirect
from datetime import datetime
from flask_ckeditor import CKEditor
from flask_compress import Compress
from flask_wtf import CSRFProtect

from app.forms.auth_forms import LogoutForm
from .extensions import db, migrate, login_manager

# =========================
# LOAD ENV SAFELY
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@localhost")

ckeditor = CKEditor()
csrf = CSRFProtect()




def create_app(config_class="config.Config"):
    # static_url_path='/blog/static' so that assets resolve correctly once the
    # app is reached via vertexprimedigital.com/blog/* through the Vercel proxy.
    app = Flask(__name__, static_url_path='/blog/static')
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
    from .models import Admin

    @login_manager.user_loader
    def load_user(admin_id):
        return Admin.query.get(int(admin_id))

    # =========================
    # BASIC ROUTES
    # =========================
    @app.route('/favicon.ico')
    @app.route('/blog/favicon.ico')
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
    
    @app.context_processor
    def inject_config():
        return dict(config=app.config)

    # =========================
    # ABSOLUTE URL HELPER
    # =========================
    # See app/url_helpers.py for why this replaces url_for(..., _external=True)
    # everywhere (canonical/OG/sitemap tags, and email senders). Registered as
    # a template global so it's usable in Jinja exactly like url_for().
    from .url_helpers import abs_url
    app.add_template_global(abs_url, name='abs_url')

    # =========================
    # BLUEPRINTS
    # =========================
    from .main import main as main_bp
    from .admin import admin as admin_bp
    from .seo import seo as seo_bp
    from .newsletter import newsletter as newsletter_bp

    # Public blog + sitemap/robots live under /blog so that
    # vertexprimedigital.com/blog/* (proxied by Vercel to this app) matches
    # what url_for() generates internally. Admin stays unprefixed and is
    # meant to be used directly on blog.vertexprimedigital.com/admin — it's
    # never exposed through the public domain/proxy.
    app.register_blueprint(main_bp, url_prefix="/blog")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(seo_bp, url_prefix="/blog")
    app.register_blueprint(newsletter_bp, url_prefix="/newsletter")

    # =========================
    # REDIRECT OLD SUBDOMAIN -> NEW PATH
    # =========================
    # Sends anyone (and any search engine) hitting an OLD-STYLE, unprefixed
    # URL directly on blog.vertexprimedigital.com (e.g. /post/some-slug,
    # bookmarked from before this migration) to the new
    # vertexprimedigital.com/blog/... location, 301, so indexed pages and
    # backlinks transfer their value instead of becoming orphaned duplicates.
    #
    # CRITICAL: must exempt anything already starting with /blog. Every
    # request proxied here by Vercel's rewrite also arrives with
    # Host: blog.vertexprimedigital.com (that's the literal destination
    # Vercel connects to) — without this exemption, every proxied request
    # would get redirected right back out to vertexprimedigital.com/blog/...,
    # which Vercel proxies straight back here again, looping forever
    # (this is exactly the /blog/blog/blog/... loop seen when this was
    # first tested — do not remove the /blog exemption below).
    #
    # /admin and /newsletter are also exempt so backend management and email
    # links keep working directly against this origin.
    @app.before_request
    def redirect_old_subdomain():
        if request.host == 'blog.vertexprimedigital.com' and not (
            request.path.startswith('/admin')
            or request.path.startswith('/newsletter')
            or request.path.startswith('/blog')
        ):
            path = request.path if request.path != '/' else ''
            new_url = f"{app.config['SITE_URL']}/blog{path}"
            if request.query_string:
                new_url += f"?{request.query_string.decode()}"
            return redirect(new_url, code=301)

    return app