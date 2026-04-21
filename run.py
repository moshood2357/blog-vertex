import os
from flask import request
from flask import send_from_directory
from app import create_app

app = create_app()

# @app.after_request
# def add_cache_headers(response):
#     # Only apply caching to requests served by Flask's static folder
#     if request.path.startswith('/static/'):
#         # Cache for 1 year (31536000 seconds)
#         response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
# #     return response
if __name__ == '__main__':
     port = int(os.environ.get('PORT', 7000))
     app.run(host='0.0.0.0', port=port, debug=True)