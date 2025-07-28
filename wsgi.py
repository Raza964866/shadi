#!/usr/bin/python3
"""
WSGI configuration for AlwaysData deployment.
This file configures the Flask application for production use.
"""

import sys
import os

# Add your project directory to sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import your Flask application
from app import create_app

# Create application instance
application = create_app('production')

if __name__ == "__main__":
    application.run()
