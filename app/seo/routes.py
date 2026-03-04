from flask import Blueprint, render_template, Response
from .sitemap import generate_sitemap_urls
from .robots import generate_robots_txt  

seo = Blueprint("seo", __name__)


@seo.route("/sitemap.xml")
def sitemap():
    pages = generate_sitemap_urls()
    sitemap_xml = render_template("seo/sitemap.xml", pages=pages)
    return Response(sitemap_xml, mimetype="application/xml")


@seo.route("/robots.txt")
def robots():
    return generate_robots_txt()   # call the function to generate robots.txt