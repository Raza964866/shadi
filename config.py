import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_that_no_one_will_ever_guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:Door%401234@localhost/shadi'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Upload settings
    UPLOAD_FOLDER = 'app/static/uploads/profiles'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'syedrazah76@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'dswo gubk ocba qduy'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'syedrazah76@gmail.com'
    
    # JazzCash API configuration
    JAZZCASH_MERCHANT_ID = os.environ.get('JAZZCASH_MERCHANT_ID') or 'MC123456'  # Replace with your actual Merchant ID
    JAZZCASH_PASSWORD = os.environ.get('JAZZCASH_PASSWORD') or 'your_password'  # Replace with your actual password
    JAZZCASH_INTEGRITY_SALT = os.environ.get('JAZZCASH_INTEGRITY_SALT') or 'your_salt'  # Replace with your actual integrity salt
    JAZZCASH_API_URL = 'https://sandbox.jazzcash.com.pk/ApplicationAPI/API/Payment/DoTransaction'  # Use production URL for live
    JAZZCASH_INQUIRY_URL = 'https://sandbox.jazzcash.com.pk/ApplicationAPI/API/Payment/DoInquiry'  # Use production URL for live
    JAZZCASH_RETURN_URL = os.environ.get('JAZZCASH_RETURN_URL') or 'http://localhost:5000/payment/callback'
    JAZZCASH_VERSION = '1.1'
    JAZZCASH_LANGUAGE = 'EN'
    JAZZCASH_CURRENCY = 'PKR'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'mysql://root:Door%401234@localhost/shadi'

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
