from flask import Response
from app.url_helpers import abs_url

def build_robots_txt():
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n\n"
        f"Sitemap: {abs_url('seo.sitemap')}"
    )


def generate_robots_response():
    return Response(build_robots_txt(), mimetype="text/plain")


# from flask import Response, url_for


# def generate_robots_response():
#     robots_txt = (
#         "User-agent: *\n"
#         "Allow: /\n"
#         "Disallow: /admin/\n\n"
#         f"Sitemap: {url_for('seo.sitemap', _external=True)}\n"
#     )

#     return Response(
#         robots_txt,
#         mimetype="text/plain"
#     )