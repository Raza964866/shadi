from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, UserProfile, Payment, db
from app.utils.auth import generate_verification_code, send_verification_email
from app.jazzcash_client import JazzCashClient
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os

# Create user blueprint
user = Blueprint('user', __name__)

@user.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@user.route('/about')
def about():
    """About page"""
    return render_template('about_us.html')

@user.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('user.contact'))
    return render_template('contact_us.html')

@user.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """User registration with email verification"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username') 
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not email or not username or not password:
            flash('Please fill in all fields', 'error')
            return render_template('sign_up.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('sign_up.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('sign_up.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('sign_up.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('sign_up.html')
        
        # Generate verification code
        verification_code = generate_verification_code()
        verification_expires = datetime.utcnow() + timedelta(minutes=10)
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
            verification_code=verification_code,
            verification_code_expires=verification_expires,
            email_verified=False
        )
        
        try:
            db.session.add(new_user)
            db.session.flush()  # Get user ID
            
            # Create empty profile
            profile = UserProfile(user_id=new_user.id)
            db.session.add(profile)
            db.session.commit()
            
            # Send verification email
            if send_verification_email(email, verification_code):
                flash('Registration successful! Please check your email for verification code.', 'success')
                return redirect(url_for('user.verify_email_form', email=email))
            else:
                flash('Registration successful but failed to send verification email. Please contact support.', 'warning')
                return redirect(url_for('user.login'))
                
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")  # Debug logging
            import traceback
            traceback.print_exc()  # Print full traceback
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('sign_up.html')
            
    return render_template('sign_up.html')

@user.route('/verify_email', methods=['GET', 'POST'])
def verify_email_form():
    """Email verification form with comprehensive validation"""
    email = request.args.get('email') or request.form.get('email')
    
    if request.method == 'POST':
        verification_code = request.form.get('verification_code', '').strip()
        
        # Comprehensive validation
        validation_errors = []
        
        # Check if email is provided
        if not email:
            validation_errors.append('Email is required')
            
        # Check if verification code is provided
        if not verification_code:
            validation_errors.append('Please enter the verification code')
        
        # Validate verification code format
        elif len(verification_code) != 6:
            validation_errors.append('Verification code must be exactly 6 digits')
        
        # Check if verification code contains only digits
        elif not verification_code.isdigit():
            validation_errors.append('Verification code must contain only numbers')
        
        # If there are validation errors, display them and return
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('verify_email.html', email=email)
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found. Please register again.', 'error')
            return redirect(url_for('user.sign_up'))
        
        # Check if email is already verified
        if user.email_verified:
            flash('Email is already verified. You can log in now.', 'info')
            return redirect(url_for('user.login'))
        
        # Check if verification code exists for user
        if not user.verification_code:
            flash('No verification code found. Please request a new code.', 'error')
            return render_template('verify_email.html', email=email)
        
        # Check if verification code has expired
        if not user.verification_code_expires or datetime.utcnow() > user.verification_code_expires:
            flash('Verification code has expired. Please request a new code.', 'error')
            return render_template('verify_email.html', email=email)
        
        # Check if verification code matches
        if user.verification_code != verification_code:
            flash('Invalid verification code. Please check and try again.', 'error')
            return render_template('verify_email.html', email=email)
        
        # All validations passed - verify the email
        try:
            user.email_verified = True
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()
            
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('user.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during verification. Please try again.', 'error')
            return render_template('verify_email.html', email=email)
    
    return render_template('verify_email.html', email=email)

@user.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification code"""
    email = request.form.get('email')
    
    if not email:
        flash('Email is required', 'error')
        return redirect(url_for('user.sign_up'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('user.sign_up'))
    
    if user.email_verified:
        flash('Email is already verified', 'info')
        return redirect(url_for('user.login'))
    
    # Generate new verification code
    verification_code = generate_verification_code()
    verification_expires = datetime.utcnow() + timedelta(minutes=10)
    
    user.verification_code = verification_code
    user.verification_code_expires = verification_expires
    db.session.commit()
    
    # Send verification email
    if send_verification_email(email, verification_code):
        flash('New verification code sent to your email', 'success')
    else:
        flash('Failed to send verification email. Please try again.', 'error')
    
    return redirect(url_for('user.verify_email_form', email=email))

@user.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            if not user.email_verified:
                flash('Please verify your email before logging in', 'warning')
                return redirect(url_for('user.verify_email_form', email=email))
            
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user.index'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@user.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('user.index'))



@user.route('/profile')
@login_required
def view_profile():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('profile.html', profile=profile)

@user.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        marital_status = request.form.get('marital_status')
        religion = request.form.get('religion')
        caste = request.form.get('caste')
        occupation = request.form.get('occupation')
        location = request.form.get('location')
        bio = request.form.get('bio')
        phone = request.form.get('phone')
        
        # Update profile
        if profile:
            profile.full_name = full_name
            profile.age = int(age) if age else None
            profile.gender = gender
            profile.marital_status = marital_status
            profile.religion = religion
            profile.caste = caste
            profile.occupation = occupation
            profile.location = location
            profile.bio = bio
            profile.phone = phone
        else:
            profile = UserProfile(
                user_id=current_user.id,
                full_name=full_name,
                age=int(age) if age else None,
                gender=gender,
                marital_status=marital_status,
                religion=religion,
                caste=caste,
                occupation=occupation,
                location=location,
                bio=bio,
                phone=phone
            )
            db.session.add(profile)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.view_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('edit_profile.html', profile=profile)

@user.route('/find_match')
@login_required  
def find_match():
    # Check if user has made payment for full access
    payment = Payment.query.filter_by(user_id=current_user.id, verified=True, purpose='full_access').first()
    has_full_access = payment is not None
    
    # Get search parameters
    gender = request.args.get('gender')
    religion = request.args.get('religion')
    location = request.args.get('location')
    caste = request.args.get('caste')
    marital_status = request.args.get('marital_status')
    occupation = request.args.get('occupation')
    family_background = request.args.get('family_background')
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    
    # Build query - only show approved profiles that admin wants to show in matches
    # Use LEFT JOIN to include admin-created profiles (user_id=None)
    query = UserProfile.query.outerjoin(User).filter(
        # Exclude current user's profile (if they have one)
        (UserProfile.user_id != current_user.id) | (UserProfile.user_id == None),
        UserProfile.is_approved == True,  # Only approved profiles
        UserProfile.show_in_matches == True  # Only profiles admin wants to show
    )
    
    # Apply filters
    if gender:
        query = query.filter(UserProfile.gender == gender)
    if religion:
        query = query.filter(UserProfile.religion == religion)
    if location:
        query = query.filter(UserProfile.location.ilike(f'%{location}%'))
    if caste:
        query = query.filter(UserProfile.caste.ilike(f'%{caste}%'))
    if marital_status:
        query = query.filter(UserProfile.marital_status == marital_status)
    if occupation:
        query = query.filter(UserProfile.occupation.ilike(f'%{occupation}%'))
    if family_background:
        query = query.filter(UserProfile.bio.ilike(f'%{family_background}%'))
    if min_age:
        query = query.filter(UserProfile.age >= min_age)
    if max_age:
        query = query.filter(UserProfile.age <= max_age)
    
    profiles = query.limit(50).all()
    
    # Get unique filter options from the database for dropdowns
    all_profiles = UserProfile.query.filter(
        UserProfile.is_approved == True,
        UserProfile.show_in_matches == True
    ).all()
    
    # Extract unique values for filters
    genders = list(set([p.gender for p in all_profiles if p.gender]))
    religions = list(set([p.religion for p in all_profiles if p.religion]))
    locations = list(set([p.location.split(',')[0].strip() for p in all_profiles if p.location]))
    castes = list(set([p.caste for p in all_profiles if p.caste]))
    marital_statuses = list(set([p.marital_status for p in all_profiles if p.marital_status]))
    occupations = list(set([p.occupation for p in all_profiles if p.occupation]))
    family_backgrounds = list(set([p.bio for p in all_profiles if p.bio]))
    
    # Sort the lists
    genders.sort()
    religions.sort()
    locations.sort()
    castes.sort()
    marital_statuses.sort()
    occupations.sort()
    family_backgrounds.sort()
    
    return render_template('find_match.html', 
                         profiles=profiles, 
                         has_full_access=has_full_access,
                         genders=genders,
                         religions=religions,
                         locations=locations,
                         castes=castes,
                         marital_statuses=marital_statuses,
                         occupations=occupations,
                         family_backgrounds=family_backgrounds,
                         current_filters={
                             'gender': gender,
                             'religion': religion,
                             'location': location,
                             'caste': caste,
                             'marital_status': marital_status,
                             'occupation': occupation,
                             'family_background': family_background,
                             'min_age': min_age,
                             'max_age': max_age
                         })

@user.route('/profile/<int:profile_id>')
@login_required
def view_other_profile(profile_id):
    # Check if user has made payment
    payment = Payment.query.filter_by(user_id=current_user.id, verified=True).first()
    has_premium = payment is not None
    
    profile = UserProfile.query.get_or_404(profile_id)
    # Handle admin-created profiles (user_id can be None)
    profile_user = None
    if profile.user_id:
        profile_user = User.query.get(profile.user_id)
    
    if not has_premium:
        # Show limited info for free users
        return render_template('profile_limited.html', profile=profile)
    
    return render_template('profile_detail.html', profile_user=profile_user, profile=profile)

@user.route('/payment', methods=['GET'])
@login_required
def payment():
    """Show payment page for full access (3 PKR)"""
    # Check if user already has full access
    existing_payment = Payment.query.filter_by(
        user_id=current_user.id, 
        verified=True, 
        purpose='full_access'
    ).first()
    
    if existing_payment:
        flash('You already have full access to all features!', 'info')
        return redirect(url_for('user.find_match'))
    
    return render_template('payment.html')

@user.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process manual payment submission with proof upload"""
    try:
        # Get form data
        sender_number = request.form.get('sender_number', '').strip()
        receiver_number = request.form.get('receiver_number', '').strip()
        transaction_id = request.form.get('transaction_id', '').strip()
        amount = float(request.form.get('amount', 3))
        purpose = request.form.get('purpose', 'full_access')
        
        # Validation
        if not sender_number:
            flash('Your mobile number is required', 'error')
            return redirect(url_for('user.payment'))
        
        if not receiver_number:
            flash('Receiver mobile number is required', 'error')
            return redirect(url_for('user.payment'))
            
        if not transaction_id:
            flash('Transaction ID/Reference is required', 'error')
            return redirect(url_for('user.payment'))
        
        if len(sender_number) != 11 or not sender_number.isdigit():
            flash('Please enter a valid 11-digit mobile number', 'error')
            return redirect(url_for('user.payment'))
        
        if not sender_number.startswith('03'):
            flash('Mobile number should start with 03', 'error')
            return redirect(url_for('user.payment'))
        
        # Accept any positive amount - validation removed for flexibility
        
        # Check if user already has verified payment
        existing_payment = Payment.query.filter_by(
            user_id=current_user.id, 
            verified=True, 
            purpose=purpose
        ).first()
        
        if existing_payment:
            flash('You already have full access!', 'info')
            return redirect(url_for('user.find_match'))
        
        # Handle payment proof image upload
        payment_proof_image = None
        if 'payment_proof' in request.files:
            file = request.files['payment_proof']
            if file and file.filename != '':
                # Check if file has allowed extension
                allowed_extensions = {'png', 'jpg', 'jpeg'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    filename = secure_filename(file.filename)
                    # Create unique filename
                    unique_filename = f"payment_{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                    
                    # Create the upload directory if it doesn't exist
                    upload_dir = os.path.join('app', 'static', 'images', 'payment_proofs')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    # Store relative URL for database
                    payment_proof_image = f'images/payment_proofs/{unique_filename}'
                else:
                    flash('Invalid file format. Please upload PNG, JPG or JPEG files only.', 'error')
                    return redirect(url_for('user.payment'))
            else:
                flash('Payment proof screenshot is required', 'error')
                return redirect(url_for('user.payment'))
        else:
            flash('Payment proof screenshot is required', 'error')
            return redirect(url_for('user.payment'))
        
        # Create payment record as unverified initially (requires admin approval)
        new_payment = Payment(
            user_id=current_user.id,
            amount=amount,
            payment_method='manual',
            sender_number=sender_number,
            receiver_number=receiver_number,
            purpose=purpose,
            transaction_id=transaction_id,
            payment_proof_image=payment_proof_image,
            verified=False  # Will be verified by admin
        )
        
        db.session.add(new_payment)
        db.session.commit()
        
        flash(f'Payment submitted successfully! Your payment will be verified by admin within 24 hours. Transaction ID: {transaction_id}', 'success')
        return redirect(url_for('user.payment_status'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Payment submission failed. Please try again.', 'error')
        return redirect(url_for('user.payment'))

@user.route('/payment_status')
@login_required
def payment_status():
    """Show payment status page"""
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.timestamp.desc()).all()
    return render_template('payment_status.html', payments=payments)

# Removed conflicting admin routes - these should be in admin blueprint only

@user.route('/send_profile', methods=['GET', 'POST'])
@login_required
def send_profile():
    """Send profile / Create profile page - requires payment"""
    # Check if user already has a profile
    existing_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    # If user already has a profile, redirect them to edit instead of creating new
    if existing_profile:
        flash('You already have a profile! You can update it here.', 'info')
        return redirect(url_for('user.edit_profile'))
    
    # Check if user has made payment for full access
    payment = Payment.query.filter_by(user_id=current_user.id, verified=True, purpose='full_access').first()
    has_full_access = payment is not None
    
    if not has_full_access and request.method == 'POST':
        flash('Please pay to create your profile and unlock all features!', 'warning')
        return redirect(url_for('user.payment'))
    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.form.get('fullName')
            age = request.form.get('age')
            city = request.form.get('city')
            phone = request.form.get('phone')
            gender = request.form.get('gender')
            marital_status = request.form.get('marital_status')
            occupation = request.form.get('occupation')
            cnic = request.form.get('cnic')
            religion = request.form.get('religion')
            caste = request.form.get('caste')
            address = request.form.get('address')
            family_background = request.form.get('family')
            
            # Handle image upload
            image_url = None
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename != '':
                    # Check if file has allowed extension
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(file.filename)
                        # Create unique filename
                        unique_filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                        
                        # Create the upload directory if it doesn't exist
                        upload_dir = os.path.join('app', 'static', 'images', 'profiles')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(upload_dir, unique_filename)
                        file.save(file_path)
                        
                        # Store relative URL for database
                        image_url = f'images/profiles/{unique_filename}'
                        print(f"DEBUG - Image saved: {image_url}")
            
            
            # Basic validation - check for both None and empty strings
            required_fields = {
                'Full Name': full_name,
                'Age': age,
                'City': city, 
                'Phone': phone,
                'Gender': gender,
                'Occupation': occupation,
                'CNIC': cnic
            }
            
            missing_fields = []
            for field_name, field_value in required_fields.items():
                if not field_value or not field_value.strip():
                    missing_fields.append(field_name)
            
            if missing_fields:
                flash(f'Please fill in these required fields: {", ".join(missing_fields)}', 'error')
                return render_template('send_profile.html')
            
            # At this point, user doesn't have a profile (checked above), so create new one
            new_profile = UserProfile(
                user_id=current_user.id,  # Link to logged-in user
                full_name=full_name,
                age=int(age) if age else None,
                gender=gender,  # Gender now collected from the form
                marital_status=marital_status,
                religion=religion,
                caste=caste,
                cnic=cnic,
                occupation=occupation,
                location=f"{city}, {address}" if address else city,
                phone=phone,
                bio=family_background,  # Using family background as bio
                image_url=image_url,  # Store image URL
                is_approved=False  # Profiles require admin approval
            )
            
            db.session.add(new_profile)
            flash('Profile created successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('user.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Profile creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Failed to create profile: {str(e)}', 'error')
            
    return render_template('send_profile.html', has_full_access=has_full_access)
