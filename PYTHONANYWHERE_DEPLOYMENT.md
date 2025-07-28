# PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere free account (3GB storage, 1 web app)
- Your project files uploaded to PythonAnywhere

## Step-by-Step Deployment

### 1. Upload Files
- Upload all project files to your PythonAnywhere account
- You can use the "Upload a file" feature in the Files tab
- Or clone directly from GitHub: `git clone https://github.com/Raza964866/shadi.git`

### 2. Set Up Virtual Environment
In a Bash console:
```bash
cd ~/shadi
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Database Setup (SQLite for Free Account)
PythonAnywhere free accounts only support SQLite. Update your config:

In `config.py`, modify the ProductionConfig:
```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///shadi.db'
```

### 4. Database Migration
```bash
source venv/bin/activate
export FLASK_APP=run.py
flask db upgrade
python create_admin.py
```

### 5. Configure Web Application
1. Go to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Set the source code path to: `/home/yourusername/shadi`
6. Set the working directory to: `/home/yourusername/shadi`
7. Edit the WSGI configuration file to use `wsgi_pythonanywhere.py` content
8. Set virtualenv path to: `/home/yourusername/shadi/venv`

### 6. Static Files Configuration
In the Web tab, add static files mapping:
- URL: `/static/`
- Directory: `/home/yourusername/shadi/app/static/`

### 7. Environment Variables
In the Web tab, go to "Environment variables" and add:
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 8. File Permissions
```bash
chmod 755 ~/shadi/app/static/images/
mkdir -p ~/shadi/app/static/images/payment_proofs/
chmod 755 ~/shadi/app/static/images/payment_proofs/
```

## Important Notes for Free Account
- **Database**: Only SQLite supported (MySQL requires paid plan)
- **Storage**: 3GB limit
- **CPU**: Limited CPU seconds per day
- **Always On**: Not available (app sleeps after inactivity)
- **Custom Domains**: Not available

## Testing
1. Click "Reload" in the Web tab
2. Visit your app at: `https://yourusername.pythonanywhere.com`

## Troubleshooting
- Check error logs in the Web tab
- Ensure all paths use forward slashes
- Verify virtual environment is activated
- Check file permissions for upload directories
