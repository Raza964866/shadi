from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_code = db.Column(db.String(10), nullable=True)
    verification_code_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    full_name = db.Column(db.String(150))
    age = db.Column(db.Integer)  # Added age field
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))  # New marital status field
    religion = db.Column(db.String(50))  # New religion field
    caste = db.Column(db.String(50))
    cnic = db.Column(db.String(20))  # National ID number
    occupation = db.Column(db.String(200))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval status
    show_in_matches = db.Column(db.Boolean, default=False)  # Admin controls visibility in find_match page
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('profiles', lazy=True))
    

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), default='manual')  # manual, easypaisa, etc
    sender_number = db.Column(db.String(15))  # Number from which payment was sent
    receiver_number = db.Column(db.String(15))  # Admin's payment number
    purpose = db.Column(db.String(50), default='full_access')  # full_access
    transaction_id = db.Column(db.String(100))  # User provided transaction reference
    payment_proof_image = db.Column(db.String(255))  # Screenshot of payment proof
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    verified = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)  # Explicitly rejected by admin
    admin_notes = db.Column(db.Text)  # Admin can add verification notes
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('payments', lazy=True))
    
    @property
    def status(self):
        """Return the current status of the payment"""
        if self.verified:
            return 'Verified'
        elif self.rejected:
            return 'Rejected'
        else:
            return 'Pending'
    

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)
