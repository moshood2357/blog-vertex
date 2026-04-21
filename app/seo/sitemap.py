from datetime import datetime, timezone
from flask import url_for


def generate_sitemap_urls():
    from app.models import Post

    pages = []
    now = datetime.now(timezone.utc).isoformat()

    pages.append({
        "loc": url_for("main.home", _external=True),
        "lastmod": now,
        "priority": "1.0",
        "changefreq": "daily"
    })

    pages.append({
        "loc": url_for("main.blog", _external=True),
        "lastmod": now,
        "priority": "0.9",
        "changefreq": "daily"
    })

    posts = Post.query.filter_by(status="published").with_entities(
        Post.slug, Post.updated_at, Post.created_at, Post.is_featured
    ).all()

    for post in posts:
        lastmod = post.updated_at or post.created_at

        pages.append({
            "loc": url_for("main.post_detail", slug=post.slug, _external=True),
            "lastmod": lastmod.isoformat(),
            "priority": "1.0" if post.is_featured else "0.9",
            "changefreq": "weekly"
        })

    return pages