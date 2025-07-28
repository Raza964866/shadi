#!/usr/bin/python3.10

"""
WSGI configuration for PythonAnywhere deployment.
This file configures the Flask application for production use on PythonAnywhere.
"""

import sys
import os

# Add your project directory to sys.path
# Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/shadi'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables for production
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Import your Flask application
from app import create_app

# Create application instance
application = create_app('production')

if __name__ == "__main__":
    application.run()
