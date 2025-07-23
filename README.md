# Shadi Matrimonial Website

A complete matrimonial matching platform built with Flask.

## Features
- User registration and profile creation
- Profile matching system
- Admin panel for profile approval
- Payment verification system
- Email verification
- Image upload for profiles and payment proofs

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env` file
3. Run database migrations: `flask db upgrade`
4. Create admin user: `python -c "from app import create_app, db; from app.models import Admin; from werkzeug.security import generate_password_hash; app = create_app(); app.app_context().push(); admin = Admin(email='admin@example.com', password=generate_password_hash('password')); db.session.add(admin); db.session.commit()"`
5. Start the application: `python run.py`

## Admin Access
- URL: `http://localhost:5000/admin/login`
- Default credentials are set in your create_admin script

## Usage
- Users can register and create profiles
- Admin approves profiles before they appear in matching
- Payment verification system for premium access
- Users can browse and match with approved profiles
