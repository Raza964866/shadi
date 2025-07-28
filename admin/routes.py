from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app.models import User, UserProfile, Payment, Admin
from app import db
from functools import wraps
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
import uuid
from PIL import Image

# Create admin blueprint with template folder pointing to this module's templates
admin = Blueprint('admin', __name__, 
                 url_prefix='/admin',
                 template_folder='templates',
                 static_folder='static')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if admin is logged in via session
        if 'admin_id' not in session:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.login'))
        
        # Verify admin still exists in database
        from app.models import Admin
        admin_user = Admin.query.get(session['admin_id'])
        if not admin_user:
            session.pop('admin_id', None)
            flash('Admin session expired.', 'error')
            return redirect(url_for('admin.login'))
            
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
def index():
    """Redirect /admin to /admin/login"""
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        admin_user = Admin.query.filter_by(email=email).first()
        if admin_user and admin_user.check_password(password):
            session['admin_id'] = admin_user.id
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('admin/login.html')

@admin.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_profiles = UserProfile.query.count()
    approved_profiles = UserProfile.query.filter_by(is_approved=True).count()
    pending_profiles = UserProfile.query.filter_by(is_approved=False).count()
    total_payments = Payment.query.count()
    verified_payments = Payment.query.filter_by(verified=True).count()
    pending_payments = Payment.query.filter_by(verified=False).count()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_profiles=total_profiles,
                         approved_profiles=approved_profiles,
                         pending_profiles=pending_profiles,
                         total_payments=total_payments,
                         verified_payments=verified_payments,
                         pending_payments=pending_payments)

# USER MANAGEMENT
@admin.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        # Delete related profiles and payments first
        UserProfile.query.filter_by(user_id=user_id).delete()
        Payment.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    return redirect(url_for('admin.users'))

# PROFILE MANAGEMENT
@admin.route('/profiles')
@admin_required
def profiles():
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = UserProfile.query.options(joinedload(UserProfile.user))
    
    # Filter out empty profiles (profiles with no full_name or basic information)
    query = query.filter(
        UserProfile.full_name.isnot(None),
        UserProfile.full_name != ''
    )
    
    if status == 'approved':
        query = query.filter_by(is_approved=True)
    elif status == 'pending':
        query = query.filter_by(is_approved=False)
    
    profiles = query.order_by(UserProfile.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/profiles.html', profiles=profiles, current_status=status)

@admin.route('/profiles/<int:profile_id>/approve', methods=['POST'])
@admin_required
def approve_profile(profile_id):
    try:
        profile = UserProfile.query.get_or_404(profile_id)
        profile.is_approved = True
        db.session.commit()
        flash(f'Profile for {profile.full_name} approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving profile: {str(e)}', 'error')
    return redirect(url_for('admin.profiles'))

@admin.route('/profiles/<int:profile_id>/reject', methods=['POST'])
@admin_required
def reject_profile(profile_id):
    try:
        profile = UserProfile.query.get_or_404(profile_id)
        profile.is_approved = False
        db.session.commit()
        flash(f'Profile for {profile.full_name} rejected!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting profile: {str(e)}', 'error')
    return redirect(url_for('admin.profiles'))

@admin.route('/profiles/<int:profile_id>/delete', methods=['POST'])
@admin_required
def delete_profile(profile_id):
    try:
        profile = UserProfile.query.get_or_404(profile_id)
        profile_name = profile.full_name
        db.session.delete(profile)
        db.session.commit()
        flash(f'Profile for {profile_name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting profile: {str(e)}', 'error')
    return redirect(url_for('admin.profiles'))

# PAYMENT MANAGEMENT
@admin.route('/payments')
@admin_required
def payments():
    print(f"DEBUG: Admin payments route accessed. Session: {dict(session)}")
    print(f"DEBUG: Admin ID in session: {session.get('admin_id')}")
    
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Payment.query.options(joinedload(Payment.user))
    
    if status == 'verified':
        query = query.filter_by(verified=True)
    elif status == 'rejected':
        query = query.filter_by(rejected=True)
    elif status == 'pending':
        query = query.filter_by(verified=False, rejected=False)
    
    payments = query.order_by(Payment.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    print(f"DEBUG: Found {payments.total} payments")
    return render_template('admin/payments.html', payments=payments, current_status=status)

@admin.route('/payments/<int:payment_id>/verify', methods=['POST'])
@admin_required
def verify_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        payment.verified = True
        payment.rejected = False  # Clear rejection status when approving
        payment.admin_notes = f"Manually verified by admin on {datetime.utcnow()}"
        db.session.commit()
        flash(f'Payment {payment.transaction_id} verified successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error verifying payment: {str(e)}', 'error')
    return redirect(url_for('admin.payments'))

@admin.route('/payments/<int:payment_id>/reject', methods=['POST'])
@admin_required
def reject_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        payment.verified = False
        payment.rejected = True  # Set explicit rejection status
        payment.admin_notes = f"Rejected by admin on {datetime.utcnow()}"
        
        # Also update user profile status if they have one
        user_profile = UserProfile.query.filter_by(user_id=payment.user_id).first()
        if user_profile:
            user_profile.is_approved = False  # Reject profile when payment is rejected
            
        db.session.commit()
        flash(f'Payment {payment.transaction_id} rejected!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting payment: {str(e)}', 'error')
    return redirect(url_for('admin.payments'))

@admin.route('/payments/<int:payment_id>/delete', methods=['POST'])
@admin_required
def delete_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        transaction_id = payment.transaction_id
        db.session.delete(payment)
        db.session.commit()
        flash(f'Payment {transaction_id} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting payment: {str(e)}', 'error')
    return redirect(url_for('admin.payments'))

# PROFILE VISIBILITY MANAGEMENT
@admin.route('/profiles/<int:profile_id>/add_to_matches', methods=['POST'])
@admin_required
def add_profile_to_matches(profile_id):
    try:
        profile = UserProfile.query.get_or_404(profile_id)
        profile.show_in_matches = True
        db.session.commit()
        flash(f'Profile "{profile.full_name}" added to find match page!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding profile to matches: {str(e)}', 'error')
    return redirect(url_for('admin.profiles'))

@admin.route('/profiles/<int:profile_id>/remove_from_matches', methods=['POST'])
@admin_required
def remove_profile_from_matches(profile_id):
    try:
        profile = UserProfile.query.get_or_404(profile_id)
        profile.show_in_matches = False
        db.session.commit()
        flash(f'Profile "{profile.full_name}" removed from find match page!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing profile from matches: {str(e)}', 'error')
    return redirect(url_for('admin.profiles'))

# INDIVIDUAL PROFILE MANAGEMENT
@admin.route('/profiles/<int:profile_id>/view')
@admin_required
def view_profile(profile_id):
    """View detailed information about a specific profile"""
    profile = UserProfile.query.options(joinedload(UserProfile.user)).get_or_404(profile_id)
    return render_template('admin/view_profile.html', profile=profile)

@admin.route('/profiles/<int:profile_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_profile(profile_id):
    """Edit an existing profile"""
    profile = UserProfile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        try:
            # Update profile fields
            profile.full_name = request.form.get('full_name', '').strip()
            profile.age = int(request.form.get('age', 0)) if request.form.get('age') else None
            profile.gender = request.form.get('gender', '').strip()
            profile.marital_status = request.form.get('marital_status', '').strip()
            profile.religion = request.form.get('religion', '').strip()
            profile.caste = request.form.get('caste', '').strip()
            profile.cnic = request.form.get('cnic', '').strip()
            profile.occupation = request.form.get('occupation', '').strip()
            profile.location = request.form.get('location', '').strip()
            profile.phone = request.form.get('phone', '').strip()
            profile.bio = request.form.get('bio', '').strip()
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    if allowed_file(file.filename):
                        filename = save_uploaded_file(file, 'profiles')
                        if filename:
                            profile.image_url = f'images/profiles/{filename}'
                    else:
                        flash('Invalid file type. Please upload JPG, JPEG, PNG, or GIF files.', 'error')
                        return render_template('admin/edit_profile.html', profile=profile)
            
            db.session.commit()
            flash(f'Profile for {profile.full_name} updated successfully!', 'success')
            return redirect(url_for('admin.view_profile', profile_id=profile.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('admin/edit_profile.html', profile=profile)

# ADD NEW PROFILE FUNCTIONALITY
@admin.route('/profiles/create', methods=['GET', 'POST'])
@admin_required
def create_profile():
    """Create a new profile independently (without user account)"""
    if request.method == 'POST':
        try:
            # Validate required fields
            full_name = request.form.get('full_name', '').strip()
            if not full_name:
                flash('Full name is required.', 'error')
                return render_template('admin/create_profile.html')
            
            # Create new profile
            new_profile = UserProfile(
                user_id=None,  # Admin-created profiles don't have associated users
                full_name=full_name,
                age=int(request.form.get('age', 0)) if request.form.get('age') else None,
                gender=request.form.get('gender', '').strip(),
                marital_status=request.form.get('marital_status', '').strip(),
                religion=request.form.get('religion', '').strip(),
                caste=request.form.get('caste', '').strip(),
                cnic=request.form.get('cnic', '').strip(),
                occupation=request.form.get('occupation', '').strip(),
                location=request.form.get('location', '').strip(),
                phone=request.form.get('phone', '').strip(),
                bio=request.form.get('bio', '').strip(),
                is_approved=True,  # Admin-created profiles are approved by default
                show_in_matches=request.form.get('show_in_matches') == 'on'
            )
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    if allowed_file(file.filename):
                        filename = save_uploaded_file(file, 'profiles')
                        if filename:
                            new_profile.image_url = f'images/profiles/{filename}'
                    else:
                        flash('Invalid file type. Please upload JPG, JPEG, PNG, or GIF files.', 'error')
                        return render_template('admin/create_profile.html')
            
            db.session.add(new_profile)
            db.session.commit()
            
            flash(f'Profile for {full_name} created successfully!', 'success')
            return redirect(url_for('admin.view_profile', profile_id=new_profile.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating profile: {str(e)}', 'error')
    
    return render_template('admin/create_profile.html')

# HELPER FUNCTIONS
def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder):
    """Save uploaded file and return filename"""
    try:
        # Get file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        # Generate unique filename
        filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_ext}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('app', 'static', 'images', folder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Resize image if it's too large
        try:
            with Image.open(filepath) as img:
                # Resize if larger than 800x800
                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    img.save(filepath, optimize=True, quality=85)
        except Exception as e:
            print(f"Image resize error: {e}")
        
        return filename
    except Exception as e:
        print(f"File upload error: {e}")
        return None
