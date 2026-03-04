from flask import Response, url_for


def generate_robots_txt():
    robots_txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n\n"
        f"Sitemap: {url_for('seo.sitemap', _external=True)}"
    )

    return Response(robots_txt, mimetype="text/plain")