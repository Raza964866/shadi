from app import create_app, db
from app.models import Admin

app = create_app('production')

with app.app_context():
    # Check if admin exists
    admin = Admin.query.filter_by(email='syedrazah76@gmail.com').first()
    if admin:
        print("✅ Admin user exists!")
        print(f"Email: {admin.email}")
        print(f"ID: {admin.id}")
        print(f"Created at: {admin.created_at}")
    else:
        print("❌ Admin user does not exist!")
    
    # Count total admins
    total_admins = Admin.query.count()
    print(f"Total admin users: {total_admins}")
