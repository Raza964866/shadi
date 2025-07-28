#!/usr/bin/env python3
"""
Database initialization script for AlwaysData deployment
Run this script to set up the database tables
"""

import os
from app import create_app, db
from flask_migrate import upgrade

def init_database():
    """Initialize the database with all tables"""
    try:
        # Create app instance
        app = create_app('production')
        
        with app.app_context():
            # Run database migrations
            upgrade()
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Initializing database...")
    if init_database():
        print("✅ Database initialization completed!")
    else:
        print("❌ Database initialization failed!")
