# Authentication utilities
import random
import string
from flask_mail import Message
from flask import current_app
from app import mail


def generate_verification_code(length=6):
    """Generate a random verification code"""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(email, code):
    """Send verification code to user's email"""
    try:
        msg = Message(
            subject='Your Matrimonial Site Verification Code',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f'''
Hello,

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Matrimonial Site Team
'''
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {str(e)}')
        return False


def verify_payment_amount(amount, payment_type='premium'):
    """Verify if payment amount is correct for the service type"""
    payment_rates = {
        'premium': 500,  # PKR 500 for premium access
        'basic': 200     # PKR 200 for basic access
    }
    return payment_rates.get(payment_type, 500) == int(amount)
