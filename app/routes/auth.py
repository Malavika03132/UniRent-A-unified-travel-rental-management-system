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

        # ----------------------------------------------------
        # Basic registration fields only
        # ----------------------------------------------------

        full_name = data.get(
            'full_name',
            ''
        ).strip()

        email = data.get(
            'email',
            ''
        ).strip().lower()

        phone = data.get(
            'phone',
            ''
        ).strip()

        password = data.get(
            'password',
            ''
        )

        confirm_password = data.get(
            'confirm_password',
            ''
        )

        role = data.get(
            'role',
            'traveler'
        ).strip().lower()

        # ----------------------------------------------------
        # Public registration only allows Traveler and Owner
        # ----------------------------------------------------

        if role not in [
            'traveler',
            'owner'
        ]:

            error_msg = (
                'Public registration is restricted to '
                'Travelers and Owners only. '
                'Admin registration is disabled.'
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
                'register.html',
                data=data
            )

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        if (
            not full_name
            or not email
            or not phone
            or not password
        ):

            error_msg = (
                'Please fill in all required fields.'
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
                'register.html',
                data=data
            )

        # ----------------------------------------------------
        # Password confirmation
        # ----------------------------------------------------

        if password != confirm_password:

            error_msg = (
                'Passwords do not match.'
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
                'register.html',
                data=data
            )

        # ----------------------------------------------------
        # Password length
        # ----------------------------------------------------

        if len(password) < 6:

            error_msg = (
                'Password must be at least 6 characters long.'
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
                'register.html',
                data=data
            )

        # ----------------------------------------------------
        # Check duplicate email
        # ----------------------------------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            error_msg = (
                'An account with this email address '
                'already exists. Please log in.'
            )

            if is_api:

                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 409

            flash(
                error_msg,
                'danger'
            )

            return render_template(
                'register.html',
                data=data
            )

        # ====================================================
        # CREATE USER
        # ====================================================

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            status='active'
        )

        new_user.set_password(password)

        db.session.add(new_user)

        # Get new user ID
        db.session.flush()

        # ====================================================
        # CREATE OWNER PROFILE
        # ====================================================

        if role == 'owner':

            owner_profile = Owner(
                user_id=new_user.user_id,

                # Default business name.
                # Owner can provide actual listing/business
                # information later when adding a property
                # or vehicle.

                business_name=(
                    f"{full_name}'s Heritage Rentals"
                ),

                # Default operational district.
                # Specific property/vehicle location will be
                # entered during listing creation.

                district='Ernakulam',

                # Existing demo status retained so that
                # current owner functionality is not affected.

                kyc_status='verified',

                bio=(
                    f"Heritage host operating in Kerala."
                )
            )

            db.session.add(
                owner_profile
            )

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

        # ====================================================
        # REDIRECT
        # ====================================================

        redirect_url = (
            url_for('owner.dashboard')
            if role == 'owner'
            else url_for('traveler.dashboard')
        )

        # ====================================================
        # API RESPONSE
        # ====================================================

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

        # ====================================================
        # NORMAL RESPONSE
        # ====================================================

        flash(
            f'Account created successfully! '
            f'Welcome to UniRent, {full_name}.',
            'success'
        )

        return redirect(
            redirect_url
        )

    return render_template(
        'register.html'
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