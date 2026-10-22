from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from app.models import db, User, Owner, Admin
from app.utils.validators import (
    validate_full_name,
    validate_email,
    validate_phone,
    validate_password,
    validate_kyc,
    validate_owner_fields,
    KYC_PATTERNS
)


auth_bp = Blueprint('auth', __name__)


# ============================================================
# LOGIN REQUIRED DECORATOR
# ============================================================

def login_required(role=None):

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):

            user_id = session.get('user_id')

            if not user_id:

                if request.is_json:
                    return jsonify({
                        'error': 'Authentication required',
                        'success': False
                    }), 401

                flash(
                    'Please log in to access this page.',
                    'warning'
                )

                return redirect(
                    url_for(
                        'auth.login',
                        next=request.path
                    )
                )

            user = db.session.get(User, user_id)

            if not user or user.status != 'active':

                session.clear()

                flash(
                    'Your account is invalid or suspended.',
                    'danger'
                )

                return redirect(
                    url_for('auth.login')
                )

            if role:

                roles = [role] if isinstance(role, str) else role

                if user.role not in roles:

                    if request.is_json:

                        return jsonify({
                            'error': 'Access forbidden for your role',
                            'success': False
                        }), 403

                    flash(
                        'You do not have permission to view that resource.',
                        'danger'
                    )

                    if user.role == 'traveler':
                        return redirect(
                            url_for('traveler.dashboard')
                        )

                    elif user.role == 'owner':
                        return redirect(
                            url_for('owner.dashboard')
                        )

                    elif user.role == 'admin':
                        return redirect(
                            url_for('admin.dashboard')
                        )

                    return redirect(
                        url_for('main.index')
                    )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/login/<role_type>', methods=['GET', 'POST'])
def login(role_type=None):

    if session.get('user_id'):

        user_role = session.get('user_role')

        if user_role == 'admin':
            return redirect(
                url_for('admin.dashboard')
            )

        elif user_role == 'owner':
            return redirect(
                url_for('owner.dashboard')
            )

        return redirect(
            url_for('traveler.dashboard')
        )

    # Determine requested role from path or query string
    active_role = (
        role_type
        or request.args.get('role', 'traveler').lower()
    )

    if active_role not in [
        'traveler',
        'owner',
        'admin'
    ]:
        active_role = 'traveler'

    if request.method == 'POST':

        is_api = request.is_json

        data = (
            request.get_json()
            if is_api
            else request.form
        )

        email = data.get(
            'email',
            ''
        ).strip().lower()

        password = data.get(
            'password',
            ''
        )

        selected_role = (
            data.get('role')
            or role_type
            or ''
        ).strip().lower()

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        if not email or not password:

            error_msg = (
                'Please provide both email and password.'
            )

            if is_api:

                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 400

            flash(
                error_msg,
                'danger'
            )

            return render_template(
                'login.html',
                email=email,
                active_role=selected_role
            )

        # ----------------------------------------------------
        # Find user
        # ----------------------------------------------------

        user = User.query.filter_by(
            email=email
        ).first()

        if not user or not user.check_password(password):

            error_msg = (
                'Invalid email or password.'
            )

            if is_api:

                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 401

            flash(
                error_msg,
                'danger'
            )

            return render_template(
                'login.html',
                email=email,
                active_role=selected_role
            )

        # ----------------------------------------------------
        # Role enforcement
        # ----------------------------------------------------

        if selected_role in [
            'traveler',
            'owner',
            'admin'
        ]:

            if user.role != selected_role:

                portal_names = {
                    'traveler': 'Traveler Login',
                    'owner': 'Owner Login',
                    'admin': 'Admin Login'
                }

                account_names = {
                    'traveler': 'Traveler',
                    'owner': 'Property/Vehicle Owner',
                    'admin': 'Platform Administrator'
                }

                error_msg = (
                    f"Access restricted: This account is "
                    f"registered as a "
                    f"{account_names.get(user.role, user.role)}. "
                    f"Please sign in through the "
                    f"{portal_names.get(user.role)} portal."
                )

                if is_api:

                    return jsonify({
                        'success': False,
                        'message': error_msg
                    }), 403

                flash(
                    error_msg,
                    'warning'
                )

                return render_template(
                    'login.html',
                    email=email,
                    active_role=selected_role
                )

        # ----------------------------------------------------
        # Account status
        # ----------------------------------------------------

        if user.status != 'active':

            error_msg = (
                'Your account has been suspended. '
                'Please contact UniRent support.'
            )

            if is_api:

                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 403

            flash(
                error_msg,
                'danger'
            )

            return render_template(
                'login.html',
                email=email,
                active_role=selected_role
            )

        # ----------------------------------------------------
        # Store session
        # ----------------------------------------------------

        session['user_id'] = user.user_id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email

        # ----------------------------------------------------
        # Determine redirect
        # ----------------------------------------------------

        target = request.args.get('next')

        if not target:

            if user.role == 'admin':

                target = url_for(
                    'admin.dashboard'
                )

            elif user.role == 'owner':

                target = url_for(
                    'owner.dashboard'
                )

            else:

                target = url_for(
                    'traveler.dashboard'
                )

        # ----------------------------------------------------
        # API response
        # ----------------------------------------------------

        if is_api:

            return jsonify({
                'success': True,
                'message': (
                    f'Welcome back, {user.full_name}!'
                ),
                'redirect': target,
                'user': user.to_dict()
            })

        # ----------------------------------------------------
        # Normal response
        # ----------------------------------------------------

        flash(
            f'Welcome back, {user.full_name}!',
            'success'
        )

        return redirect(target)

    return render_template(
        'login.html',
        active_role=active_role
    )


# ============================================================
# REGISTRATION
# ============================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if session.get('user_id'):
        return redirect(
            url_for('main.index')
        )

    if request.method == 'POST':
        is_api = request.is_json
        data = (
            request.get_json()
            if is_api
            else request.form
        )

        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        role = data.get('role', 'traveler').strip().lower()
        kyc_document_type = data.get('kyc_document_type', '').strip().lower()
        kyc_document_number = data.get('kyc_document_number', '').strip()
        business_name = data.get('business_name', '').strip()
        district = data.get('district', 'Ernakulam').strip()

        def fail_validation(message, status_code=400):
            if is_api:
                return jsonify({
                    'success': False,
                    'message': message
                }), status_code
            flash(message, 'danger')
            return render_template(
                'register.html',
                data=data,
                kyc_patterns=KYC_PATTERNS
            )

        # 1. Role validation
        if role not in ['traveler', 'owner']:
            return fail_validation(
                'Public registration is restricted to Travelers and Owners only. '
                'Admin registration is disabled.'
            )

        # 2. Required core fields
        if not full_name or not email or not phone or not password:
            return fail_validation('Please fill in all required personal details.')

        # 3. Full legal name validation
        valid, err = validate_full_name(full_name)
        if not valid:
            return fail_validation(err)

        # 4. Email validation
        valid, err = validate_email(email)
        if not valid:
            return fail_validation(err)

        # 5. Phone validation (Indian mobile)
        valid, err, normalized_phone = validate_phone(phone)
        if not valid:
            return fail_validation(err)

        # 6. Password strength & confirmation
        valid, err = validate_password(password, confirm_password)
        if not valid:
            return fail_validation(err)

        # 7. KYC Verification Validation (Required for both Traveler and Owner)
        valid, err, cleaned_kyc_number = validate_kyc(kyc_document_type, kyc_document_number)
        if not valid:
            return fail_validation(err)

        # 8. Duplicate email check
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return fail_validation(
                'An account with this email address already exists. Please log in.',
                status_code=409
            )

        # 9. Owner-specific validations
        cleaned_biz = None
        cleaned_dist = None
        if role == 'owner':
            valid, err, cleaned_biz, cleaned_dist = validate_owner_fields(business_name, district, full_name)
            if not valid:
                return fail_validation(err)

        # ====================================================
        # CREATE USER WITH VERIFIED KYC
        # ====================================================
        new_user = User(
            full_name=full_name,
            email=email,
            phone=normalized_phone,
            role=role,
            status='active',
            kyc_document_type=kyc_document_type,
            kyc_document_number=cleaned_kyc_number,
            kyc_status='verified'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        # ====================================================
        # CREATE OWNER PROFILE
        # ====================================================
        if role == 'owner':
            owner_profile = Owner(
                user_id=new_user.user_id,
                business_name=cleaned_biz,
                district=cleaned_dist,
                kyc_status='verified',
                bio=f"Verified heritage host operating in {cleaned_dist}, Kerala."
            )
            db.session.add(owner_profile)

        # ====================================================
        # SAVE DATABASE CHANGES
        # ====================================================
        db.session.commit()

        # ====================================================
        # AUTOMATIC LOGIN
        # ====================================================
        session['user_id'] = new_user.user_id
        session['user_role'] = new_user.role
        session['user_name'] = new_user.full_name
        session['user_email'] = new_user.email

        redirect_url = (
            url_for('owner.dashboard')
            if role == 'owner'
            else url_for('traveler.dashboard')
        )

        if is_api:
            return jsonify({
                'success': True,
                'message': (
                    f'Registration successful! '
                    f'Welcome to UniRent, {full_name}.'
                ),
                'redirect': redirect_url,
                'user': new_user.to_dict()
            }), 201

        flash(
            f'Account created and KYC verified successfully! '
            f'Welcome to UniRent, {full_name}.',
            'success'
        )

        return redirect(redirect_url)

    return render_template(
        'register.html',
        kyc_patterns=KYC_PATTERNS
    )


# ============================================================
# DEMO LOGIN
# ============================================================

@auth_bp.route('/demo-login/<role>')
def demo_login(role):

    """Convenience endpoint to seamlessly test any of the 3 roles."""

    role = role.lower()

    user = None

    if role == 'admin':

        user = User.query.filter_by(
            role='admin'
        ).first()

    elif role == 'owner':

        user = User.query.filter_by(
            role='owner'
        ).first()

    elif role == 'traveler':

        user = User.query.filter_by(
            role='traveler'
        ).first()

    if user:

        session['user_id'] = user.user_id
        session['user_role'] = user.role
        session['user_name'] = user.full_name
        session['user_email'] = user.email

        flash(
            f"Switched to demo role: "
            f"{user.role.capitalize()} "
            f"({user.full_name})",
            "info"
        )

        if user.role == 'admin':

            return redirect(
                url_for('admin.dashboard')
            )

        elif user.role == 'owner':

            return redirect(
                url_for('owner.dashboard')
            )

        else:

            return redirect(
                url_for('traveler.dashboard')
            )

    flash(
        f"No demo user found for role '{role}'. "
        f"Please seed database first.",
        "warning"
    )

    return redirect(
        url_for('auth.login')
    )


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route('/logout')
def logout():

    session.clear()

    flash(
        'You have been securely logged out.',
        'info'
    )

    return redirect(
        url_for('main.index')
    )


# ============================================================
# CURRENT USER
# ============================================================

@auth_bp.route('/me')
def get_current_user():

    user_id = session.get('user_id')

    if not user_id:

        return jsonify({
            'logged_in': False,
            'user': None
        })

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            'logged_in': False,
            'user': None
        })

    return jsonify({
        'logged_in': True,
        'user': user.to_dict()
    })