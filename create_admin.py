#!/usr/bin/env python3
"""
Admin Creation Script for Shadi Flask Application
This script creates admin users in the database.
"""

import os
import sys
from getpass import getpass
from werkzeug.security import generate_password_hash

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import create_app, db
from app.models import Admin

def create_admin():
    """Create a new admin user"""
    
    # Create Flask app instance
    app = create_app('development')  # or 'production' depending on your setup
    
    with app.app_context():
        print("=== Admin Creation Script ===")
        print("This script will create a new admin user for the Shadi application.\n")
        
        # Get admin details
        while True:
            username = input("Enter admin username: ").strip()
            if not username:
                print("Username cannot be empty. Please try again.")
                continue
            
            # Check if username already exists
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:
                print(f"Username '{username}' already exists. Please choose a different username.")
                continue
            break
        
        while True:
            email = input("Enter admin email: ").strip()
            if not email:
                print("Email cannot be empty. Please try again.")
                continue
            
            # Basic email validation
            if '@' not in email or '.' not in email:
                print("Please enter a valid email address.")
                continue
            
            # Check if email already exists
            existing_admin = Admin.query.filter_by(email=email).first()
            if existing_admin:
                print(f"Email '{email}' already exists. Please choose a different email.")
                continue
            break
        
        while True:
            password = getpass("Enter admin password (minimum 8 characters): ")
            if len(password) < 8:
                print("Password must be at least 8 characters long. Please try again.")
                continue
            
            confirm_password = getpass("Confirm password: ")
            if password != confirm_password:
                print("Passwords do not match. Please try again.")
                continue
            break
        
        # Create admin user
        try:
            hashed_password = generate_password_hash(password)
            
            new_admin = Admin(
                username=username,
                email=email,
                password=hashed_password,
                is_active=True
            )
            
            db.session.add(new_admin)
            db.session.commit()
            
            print(f"\n✅ Admin user '{username}' created successfully!")
            print(f"Email: {email}")
            print("\nYou can now login to the admin panel with these credentials.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating admin user: {str(e)}")
            return False
    
    return True

def list_admins():
    """List all existing admin users"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=== Existing Admin Users ===")
        
        admins = Admin.query.all()
        
        if not admins:
            print("No admin users found.")
            return
        
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Active':<8} {'Created'}")
        print("-" * 80)
        
        for admin in admins:
            status = "Yes" if admin.is_active else "No"
            created = admin.created_at.strftime("%Y-%m-%d") if hasattr(admin, 'created_at') and admin.created_at else "N/A"
            print(f"{admin.id:<5} {admin.username:<20} {admin.email:<30} {status:<8} {created}")

def update_admin_password():
    """Update an existing admin's password"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=== Update Admin Password ===")
        
        # List existing admins first
        admins = Admin.query.all()
        if not admins:
            print("No admin users found.")
            return
        
        print("Existing admin users:")
        for admin in admins:
            print(f"ID: {admin.id}, Username: {admin.username}, Email: {admin.email}")
        
        while True:
            try:
                admin_id = int(input("\nEnter admin ID to update: "))
                admin = Admin.query.get(admin_id)
                if not admin:
                    print("Admin not found. Please try again.")
                    continue
                break
            except ValueError:
                print("Please enter a valid admin ID.")
                continue
        
        print(f"Updating password for admin: {admin.username} ({admin.email})")
        
        while True:
            password = getpass("Enter new password (minimum 8 characters): ")
            if len(password) < 8:
                print("Password must be at least 8 characters long. Please try again.")
                continue
            
            confirm_password = getpass("Confirm new password: ")
            if password != confirm_password:
                print("Passwords do not match. Please try again.")
                continue
            break
        
        try:
            admin.password = generate_password_hash(password)
            db.session.commit()
            print(f"\n✅ Password updated successfully for admin '{admin.username}'!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error updating password: {str(e)}")

def delete_admin():
    """Delete an existing admin user"""
    
    app = create_app('development')
    
    with app.app_context():
        print("=== Delete Admin User ===")
        
        # List existing admins first
        admins = Admin.query.all()
        if not admins:
            print("No admin users found.")
            return
        
        if len(admins) == 1:
            print("⚠️  Warning: Only one admin user exists. Deleting it will leave no admin access!")
        
        print("Existing admin users:")
        for admin in admins:
            print(f"ID: {admin.id}, Username: {admin.username}, Email: {admin.email}")
        
        while True:
            try:
                admin_id = int(input("\nEnter admin ID to delete: "))
                admin = Admin.query.get(admin_id)
                if not admin:
                    print("Admin not found. Please try again.")
                    continue
                break
            except ValueError:
                print("Please enter a valid admin ID.")
                continue
        
        print(f"⚠️  You are about to delete admin: {admin.username} ({admin.email})")
        confirmation = input("Type 'DELETE' to confirm: ")
        
        if confirmation != 'DELETE':
            print("Deletion cancelled.")
            return
        
        try:
            db.session.delete(admin)
            db.session.commit()
            print(f"\n✅ Admin user '{admin.username}' deleted successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error deleting admin: {str(e)}")

def main():
    """Main function to handle user choices"""
    
    while True:
        print("\n" + "="*50)
        print("         ADMIN MANAGEMENT SYSTEM")
        print("="*50)
        print("1. Create new admin user")
        print("2. List all admin users") 
        print("3. Update admin password")
        print("4. Delete admin user")
        print("5. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            create_admin()
        elif choice == '2':
            list_admins()
        elif choice == '3':
            update_admin_password()
        elif choice == '4':
            delete_admin()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1-5.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
