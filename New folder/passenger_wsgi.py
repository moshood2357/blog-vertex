# import os
# from app import create_app

# Create the Flask app
# app = create_app()

# Apply caching headers to static files
# @app.after_request
# def add_cache_headers(response):
#     # Only apply caching to requests served by Flask's static folder
#     if request.path.startswith('/static/'):
#         # Cache for 1 year (31536000 seconds)
#         response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
#     return response

# Determine debug mode from environment variable (default False)
# debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 7000))
#     app.run(host='0.0.0.0', port=port, debug=debug_mode)




# This script is the entry point for running the web application.# It imports the Flask application instance from the 'app' package
# and starts the development server on port 7000 with debug mode enabled.






import sys
import os
from flask import request
from app import create_app

# Add your project directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Create Flask app instance
application = create_app()  # Passenger expects the callable to be named 'application'

# Optional: Add caching headers for static files
@application.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        # Cache static files for 1 year (31536000 seconds)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response