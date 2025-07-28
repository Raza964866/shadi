# AlwaysData Deployment Guide

## Prerequisites
- AlwaysData free account (100MB storage)
- Your project files uploaded to AlwaysData

## Step-by-Step Deployment

### 1. Upload Files
- Upload all project files to your AlwaysData account via SSH/SFTP
- Place files in the `/www/` directory or your preferred location

### 2. Database Setup
- Create a MySQL or PostgreSQL database in AlwaysData admin panel
- Note down database credentials (host, username, password, database name)

### 3. Environment Configuration
- Copy `.env.example` to `.env`
- Update database URL in `.env`:
  ```
  DATABASE_URL=mysql://username:password@mysql-username.alwaysdata.net/username_databasename
  ```
- Set other environment variables (SECRET_KEY, MAIL settings, etc.)

### 4. Install Dependencies
Via SSH:
```bash
pip install --user -r requirements.txt
```

### 5. Database Migration
```bash
export FLASK_APP=wsgi.py
flask db upgrade
```

### 6. Create Admin User
```bash
python create_admin.py
```

### 7. Configure Web Application
- In AlwaysData admin panel, create a new "Web" site
- Set type to "Python WSGI"
- Set path to your `wsgi.py` file
- Set Python version to 3.10

### 8. File Permissions
Ensure upload directories have proper permissions:
```bash
chmod 755 app/static/images/
chmod 755 app/static/images/payment_proofs/
```

## Important Notes
- Free plan has 100MB storage limit
- Make sure all file paths are relative to avoid issues
- Monitor resource usage to stay within limits
- Database and file storage count toward the 100MB limit

## Troubleshooting
- Check AlwaysData logs for any errors
- Verify all environment variables are set correctly
- Ensure database connection is working
- Check file permissions for uploads
