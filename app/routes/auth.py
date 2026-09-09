from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import db, User, Owner, Admin

auth_bp = Blueprint('auth', __name__)

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                if request.is_json:
                    return jsonify({'error': 'Authentication required', 'success': False}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            
            user = db.session.get(User, user_id)
            if not user or user.status != 'active':
                session.clear()
                flash('Your account is invalid or suspended.', 'danger')
                return redirect(url_for('auth.login'))
                
            if role:
                roles = [role] if isinstance(role, str) else role
                if user.role not in roles:
                    if request.is_json:
                        return jsonify({'error': 'Access forbidden for your role', 'success': False}), 403
                    flash('You do not have permission to view that resource.', 'danger')
                    if user.role == 'traveler':
                        return redirect(url_for('traveler.dashboard'))
                    elif user.role == 'owner':
                        return redirect(url_for('owner.dashboard'))
                    elif user.role == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    return redirect(url_for('main.index'))
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/login/<role_type>', methods=['GET', 'POST'])
def login(role_type=None):
    if session.get('user_id'):
        user_role = session.get('user_role')
        if user_role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user_role == 'owner':
            return redirect(url_for('owner.dashboard'))
        return redirect(url_for('traveler.dashboard'))
        
    # Determine requested role from path or query string (defaults to 'traveler')
    active_role = role_type or request.args.get('role', 'traveler').lower()
    if active_role not in ['traveler', 'owner', 'admin']:
        active_role = 'traveler'

    if request.method == 'POST':
        is_api = request.is_json
        data = request.get_json() if is_api else request.form
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        selected_role = (data.get('role') or role_type or '').strip().lower()
        
        if not email or not password:
            error_msg = 'Please provide both email and password.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('login.html', email=email, active_role=selected_role)
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            error_msg = 'Invalid email or password.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 401
            flash(error_msg, 'danger')
            return render_template('login.html', email=email, active_role=selected_role)
            
        # Role Enforcement: Check that the account matches the selected login portal
        if selected_role in ['traveler', 'owner', 'admin']:
            if user.role != selected_role:
                portal_names = {'traveler': 'Traveler Login', 'owner': 'Owner Login', 'admin': 'Admin Login'}
                account_names = {'traveler': 'Traveler', 'owner': 'Property/Vehicle Owner', 'admin': 'Platform Administrator'}
                error_msg = f"Access restricted: This account is registered as a {account_names.get(user.role, user.role)}. Please sign in through the {portal_names.get(user.role)} portal."
                if is_api:
                    return jsonify({'success': False, 'message': error_msg}), 403
                flash(error_msg, 'warning')
                return render_template('login.html', email=email, active_role=selected_role)
            
        if user.status != 'active':
            error_msg = 'Your account has been suspended. Please contact UniRent support.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 403
            flash(error_msg, 'danger')
            return render_template('login.html', email=email, active_role=selected_role)
            
        # Store in session
        session['user_id'] = user.user_id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email
        
        target = request.args.get('next')
        if not target:
            if user.role == 'admin':
                target = url_for('admin.dashboard')
            elif user.role == 'owner':
                target = url_for('owner.dashboard')
            else:
                target = url_for('traveler.dashboard')
                
        if is_api:
            return jsonify({
                'success': True,
                'message': f'Welcome back, {user.full_name}!',
                'redirect': target,
                'user': user.to_dict()
            })
            
        flash(f'Welcome back, {user.full_name}!', 'success')
        return redirect(target)
        
    return render_template('login.html', active_role=active_role)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        is_api = request.is_json
        data = request.get_json() if is_api else request.form
        
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role = data.get('role', 'traveler').strip().lower()
        district = data.get('district', 'Ernakulam').strip()
        business_name = data.get('business_name', '').strip()
        
        # CRITICAL VALIDATION: Public registration only allows traveler and owner.
        if role not in ['traveler', 'owner']:
            error_msg = 'Public registration is restricted to Travelers and Owners only. Admin registration is disabled.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('register.html', data=data)
            
        if not full_name or not email or not phone or not password:
            error_msg = 'Please fill in all required fields.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('register.html', data=data)
            
        if password != confirm_password:
            error_msg = 'Passwords do not match.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('register.html', data=data)
            
        if len(password) < 6:
            error_msg = 'Password must be at least 6 characters long.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'danger')
            return render_template('register.html', data=data)
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error_msg = 'An account with this email address already exists. Please log in.'
            if is_api:
                return jsonify({'success': False, 'message': error_msg}), 409
            flash(error_msg, 'danger')
            return render_template('register.html', data=data)
            
        # Create user
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            status='active'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # get new_user.user_id
        
        # If owner, create Owner profile
        if role == 'owner':
            owner_profile = Owner(
                user_id=new_user.user_id,
                business_name=business_name or f"{full_name}'s Heritage Rentals",
                district=district if district in ['Ernakulam', 'Thrissur'] else 'Ernakulam',
                kyc_status='verified',  # Active for demo convenience
                bio=f"Verified heritage host operating in {district}, Kerala."
            )
            db.session.add(owner_profile)
            
        db.session.commit()
        
        # Log user in directly
        session['user_id'] = new_user.user_id
        session['user_role'] = new_user.role
        session['user_name'] = new_user.full_name
        session['user_email'] = new_user.email
        
        redirect_url = url_for('owner.dashboard') if role == 'owner' else url_for('traveler.dashboard')
        
        if is_api:
            return jsonify({
                'success': True,
                'message': f'Registration successful! Welcome to UniRent, {full_name}.',
                'redirect': redirect_url,
                'user': new_user.to_dict()
            }), 201
            
        flash(f'Account created successfully! Welcome to UniRent, {full_name}.', 'success')
        return redirect(redirect_url)
        
    return render_template('register.html')


@auth_bp.route('/demo-login/<role>')
def demo_login(role):
    """Convenience endpoint to seamlessly test any of the 3 roles."""
    role = role.lower()
    user = None
    if role == 'admin':
        user = User.query.filter_by(role='admin').first()
    elif role == 'owner':
        user = User.query.filter_by(role='owner').first()
    elif role == 'traveler':
        user = User.query.filter_by(role='traveler').first()
        
    if user:
        session['user_id'] = user.user_id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email
        flash(f"Switched to demo role: {user.role.capitalize()} ({user.full_name})", "info")
        
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'owner':
            return redirect(url_for('owner.dashboard'))
        else:
            return redirect(url_for('traveler.dashboard'))
            
    flash(f"No demo user found for role '{role}'. Please seed database first.", "warning")
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/me')
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False, 'user': None})
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'logged_in': False, 'user': None})
    return jsonify({
        'logged_in': True,
        'user': user.to_dict()
    })
