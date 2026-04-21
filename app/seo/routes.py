import html
from flask import Response, render_template, url_for
from . import seo
from .sitemap import generate_sitemap_urls
from .robots import generate_robots_response
from app import csrf
from app.models import Post

@seo.route("/sitemap.xml")
@csrf.exempt
def sitemap():
    pages = generate_sitemap_urls(Post)

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for p in pages:
        xml.append(
            "<url>"
            f"<loc>{html.escape(p['loc'])}</loc>"
            f"<lastmod>{p['lastmod']}</lastmod>"
            f"<changefreq>{p['changefreq']}</changefreq>"
            f"<priority>{p['priority']}</priority>"
            "</url>"
        )

    xml.append('</urlset>')

    return Response("".join(xml), mimetype="application/xml")

@seo.route("/robots.txt")
@csrf.exempt
def robots():
    return generate_robots_response()


@seo.route("/seo-test")
def seo_test():
    return "SEO OK"