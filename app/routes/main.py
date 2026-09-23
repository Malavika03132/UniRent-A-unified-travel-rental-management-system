from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    jsonify,
    current_app,
    send_file
)

from datetime import datetime
import uuid
import hmac
import hashlib
from io import BytesIO

import razorpay

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models import (
    db,
    Property,
    Vehicle,
    Review,
    Booking,
    Payment,
    User
)


main_bp = Blueprint('main', __name__)


# ============================================================================
# RAZORPAY CLIENT
# ============================================================================

def get_razorpay_client():
    return razorpay.Client(
        auth=(
            current_app.config['RAZORPAY_KEY_ID'],
            current_app.config['RAZORPAY_KEY_SECRET']
        )
    )


# ============================================================================
# HOME
# ============================================================================

@main_bp.route('/')
def index():

    featured_stays = (
        Property.query
        .filter_by(approval_status='approved')
        .order_by(
            Property.featured.desc(),
            Property.property_id.desc()
        )
        .limit(6)
        .all()
    )

    popular_vehicles = (
        Vehicle.query
        .filter_by(approval_status='approved')
        .order_by(
            Vehicle.featured.desc(),
            Vehicle.vehicle_id.desc()
        )
        .limit(6)
        .all()
    )

    recent_reviews = (
        Review.query
        .order_by(Review.review_id.desc())
        .limit(4)
        .all()
    )

    stays_count = (
        Property.query
        .filter_by(approval_status='approved')
        .count()
    )

    vehicles_count = (
        Vehicle.query
        .filter_by(approval_status='approved')
        .count()
    )

    return render_template(
        'index.html',
        featured_stays=featured_stays,
        popular_vehicles=popular_vehicles,
        recent_reviews=recent_reviews,
        stays_count=stays_count,
        vehicles_count=vehicles_count
    )


# ============================================================================
# STAYS
# ============================================================================

@main_bp.route('/stays')
def stays():

    district = request.args.get(
        'district',
        ''
    ).strip()

    property_type = request.args.get(
        'type',
        ''
    ).strip()

    min_price = request.args.get(
        'min_price',
        type=float
    )

    max_price = request.args.get(
        'max_price',
        type=float
    )

    guests = request.args.get(
        'guests',
        type=int
    )

    sort_by = request.args.get(
        'sort',
        'newest'
    ).strip()

    search_q = request.args.get(
        'q',
        ''
    ).strip()

    query = Property.query.filter_by(
        approval_status='approved'
    )

    if district and district in [
        'Ernakulam',
        'Thrissur'
    ]:
        query = query.filter(
            Property.district == district
        )

    if property_type:
        query = query.filter(
            Property.property_type.ilike(
                f"%{property_type}%"
            )
        )

    if min_price is not None:
        query = query.filter(
            Property.price_per_night >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Property.price_per_night <= max_price
        )

    if guests:
        query = query.filter(
            Property.guest_capacity >= guests
        )

    if search_q:
        query = query.filter(
            (Property.property_name.ilike(f"%{search_q}%")) |
            (Property.address.ilike(f"%{search_q}%")) |
            (Property.description.ilike(f"%{search_q}%"))
        )

    if sort_by == 'price_asc':

        query = query.order_by(
            Property.price_per_night.asc()
        )

    elif sort_by == 'price_desc':

        query = query.order_by(
            Property.price_per_night.desc()
        )

    elif sort_by == 'rating':

        query = query.order_by(
            Property.featured.desc(),
            Property.price_per_night.desc()
        )

    else:

        query = query.order_by(
            Property.property_id.desc()
        )

    stays_list = query.all()

    return render_template(
        'stays.html',
        stays=stays_list,
        selected_district=district,
        selected_type=property_type,
        min_price=min_price,
        max_price=max_price,
        guests=guests,
        sort_by=sort_by,
        search_q=search_q
    )


# ============================================================================
# STAY DETAILS
# ============================================================================

@main_bp.route('/stays/<int:property_id>')
def stay_details(property_id):

    prop = db.session.get(
        Property,
        property_id
    )

    if not prop:
        abort(404)

    if (
        prop.approval_status != 'approved'
        and session.get('user_role') not in ['admin', 'owner']
    ):
        abort(404)

    similar_stays = (
        Property.query
        .filter(
            Property.approval_status == 'approved',
            Property.property_id != prop.property_id,
            Property.district == prop.district
        )
        .limit(3)
        .all()
    )

    reviews = (
        prop.reviews
        .order_by(Review.review_id.desc())
        .all()
    )

    return render_template(
        'stay-details.html',
        property=prop,
        similar_stays=similar_stays,
        reviews=reviews
    )


# ============================================================================
# VEHICLES
# ============================================================================

@main_bp.route('/vehicles')
def vehicles():

    district = request.args.get(
        'district',
        ''
    ).strip()

    v_type = request.args.get(
        'type',
        ''
    ).strip().lower()

    delivery = request.args.get(
        'delivery'
    )

    min_price = request.args.get(
        'min_price',
        type=float
    )

    max_price = request.args.get(
        'max_price',
        type=float
    )

    sort_by = request.args.get(
        'sort',
        'newest'
    ).strip()

    search_q = request.args.get(
        'q',
        ''
    ).strip()

    query = Vehicle.query.filter_by(
        approval_status='approved'
    )

    if district and district in [
        'Ernakulam',
        'Thrissur'
    ]:

        query = query.filter(
            Vehicle.district == district
        )

    if v_type and v_type in [
        'car',
        'bike',
        'scooter'
    ]:

        query = query.filter(
            Vehicle.vehicle_type == v_type
        )

    if delivery == '1':

        query = query.filter(
            Vehicle.delivery_available.is_(True)
        )

    if min_price is not None:

        query = query.filter(
            Vehicle.price_per_day >= min_price
        )

    if max_price is not None:

        query = query.filter(
            Vehicle.price_per_day <= max_price
        )

    if search_q:

        query = query.filter(
            (Vehicle.vehicle_name.ilike(f"%{search_q}%")) |
            (Vehicle.model.ilike(f"%{search_q}%")) |
            (Vehicle.pickup_location.ilike(f"%{search_q}%"))
        )

    if sort_by == 'price_asc':

        query = query.order_by(
            Vehicle.price_per_day.asc()
        )

    elif sort_by == 'price_desc':

        query = query.order_by(
            Vehicle.price_per_day.desc()
        )

    else:

        query = query.order_by(
            Vehicle.vehicle_id.desc()
        )

    vehicles_list = query.all()

    return render_template(
        'vehicles.html',
        vehicles=vehicles_list,
        selected_district=district,
        selected_type=v_type,
        selected_delivery=delivery,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        search_q=search_q
    )


# ============================================================================
# VEHICLE DETAILS
# ============================================================================

@main_bp.route('/vehicles/<int:vehicle_id>')
def vehicle_details(vehicle_id):

    veh = db.session.get(
        Vehicle,
        vehicle_id
    )

    if not veh:
        abort(404)

    if (
        veh.approval_status != 'approved'
        and session.get('user_role') not in ['admin', 'owner']
    ):
        abort(404)

    similar_vehicles = (
        Vehicle.query
        .filter(
            Vehicle.approval_status == 'approved',
            Vehicle.vehicle_id != veh.vehicle_id,
            Vehicle.vehicle_type == veh.vehicle_type
        )
        .limit(3)
        .all()
    )

    reviews = (
        veh.reviews
        .order_by(Review.review_id.desc())
        .all()
    )

    return render_template(
        'vehicle-details.html',
        vehicle=veh,
        similar_vehicles=similar_vehicles,
        reviews=reviews
    )


# ============================================================================
# ABOUT
# ============================================================================

@main_bp.route('/about')
def about():

    return render_template(
        'about.html'
    )


# ============================================================================
# HOW IT WORKS
# ============================================================================

@main_bp.route('/how-it-works')
def how_it_works():

    return render_template(
        'how-it-works.html'
    )


# ============================================================================
# CONTACT
# ============================================================================

@main_bp.route(
    '/contact',
    methods=['GET', 'POST']
)
def contact():

    if request.method == 'POST':

        flash(
            'Thank you for reaching out to UniRent. '
            'Our Kerala concierge team will contact you shortly.',
            'success'
        )

        return redirect(
            url_for('main.contact')
        )

    return render_template(
        'contact.html'
    )


# ============================================================================
# BOOKING PAGE
# ============================================================================

@main_bp.route('/booking')
def booking():

    listing_type = request.args.get(
        'type',
        'property'
    )

    item_id = request.args.get(
        'id',
        type=int
    )

    item = None

    if listing_type == 'property':

        item = db.session.get(
            Property,
            item_id
        )

    elif listing_type == 'vehicle':

        item = db.session.get(
            Vehicle,
            item_id
        )

    if not item:

        flash(
            'Please select a valid property or vehicle to book.',
            'warning'
        )

        return redirect(
            url_for('main.stays')
        )

    start_date = request.args.get(
        'start',
        ''
    )

    end_date = request.args.get(
        'end',
        ''
    )

    return render_template(
        'booking.html',
        listing_type=listing_type,
        item=item,
        start_date=start_date,
        end_date=end_date
    )


# ============================================================================
# PAYMENT PAGE
# ============================================================================

@main_bp.route('/payment')
def payment():

    booking_id = request.args.get(
        'booking_id',
        type=int
    )

    booking_ref = request.args.get(
        'ref'
    )

    booking_obj = None

    # Find booking by ID
    if booking_id:

        booking_obj = db.session.get(
            Booking,
            booking_id
        )

    # Find booking by reference
    elif booking_ref:

        booking_obj = (
            Booking.query
            .filter_by(
                booking_reference=booking_ref
            )
            .first()
        )

    if not booking_obj:

        flash(
            'Booking record not found.',
            'warning'
        )

        return redirect(
            url_for('main.index')
        )

    # Check if booking is already genuinely paid
    is_already_paid = (
        booking_obj.booking_status == 'confirmed'
        and booking_obj.payment is not None
        and booking_obj.payment.payment_status in (
            'successful',
            'approved',
            'completed'
        )
    )

    if is_already_paid:

        flash(
            'This booking has already been paid. '
            'Your confirmation is ready.',
            'info'
        )

        return redirect(
            url_for(
                'main.confirmation',
                booking_id=booking_obj.booking_id
            )
        )

    return render_template(
        'payment.html',
        booking=booking_obj
    )


# ============================================================================
# RAZORPAY - CREATE ORDER
# ============================================================================

@main_bp.route(
    '/api/create-order',
    methods=['POST']
)
def create_razorpay_order():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        booking_ref = str(
            data.get(
                'booking_reference',
                ''
            )
        ).strip()

        if not booking_ref:

            return jsonify({
                'success': False,
                'message': 'Booking reference is required.'
            }), 400

        booking_obj = (
            Booking.query
            .filter_by(
                booking_reference=booking_ref
            )
            .first()
        )

        if not booking_obj:

            return jsonify({
                'success': False,
                'message': 'Booking record not found.'
            }), 404

        # Prevent creation of another Razorpay order
        # for a booking that has already been paid.
        if (
            booking_obj.booking_status == 'confirmed'
            and booking_obj.payment is not None
            and booking_obj.payment.payment_status in (
                'successful',
                'approved',
                'completed'
            )
        ):

            return jsonify({
                'success': False,
                'message': 'This booking has already been paid.'
            }), 400

        # Amount MUST come from database.
        amount_paise = int(
            round(
                float(booking_obj.total_amount) * 100
            )
        )

        if amount_paise < 100:

            return jsonify({
                'success': False,
                'message': 'Payment amount must be at least ₹1.'
            }), 400

        client = get_razorpay_client()

        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': booking_obj.booking_reference
        })

        return jsonify({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount_paise,
            'currency': 'INR',
            'key_id': current_app.config[
                'RAZORPAY_KEY_ID'
            ],
            'booking_reference':
                booking_obj.booking_reference
        }), 200

    except razorpay.errors.BadRequestError as error:

        print(
            'Razorpay BadRequestError:',
            str(error)
        )

        return jsonify({
            'success': False,
            'message': 'Razorpay rejected the order request.',
            'error': str(error)
        }), 400

    except razorpay.errors.AuthenticationError as error:

        print(
            'Razorpay AuthenticationError:',
            str(error)
        )

        return jsonify({
            'success': False,
            'message': 'Razorpay authentication failed.',
            'error': str(error)
        }), 401

    except Exception as error:

        print(
            'Razorpay order creation error:',
            str(error)
        )

        return jsonify({
            'success': False,
            'message': 'Unable to create Razorpay order.',
            'error': str(error)
        }), 500


# ============================================================================
# PAYMENT PROCESS
# EXISTING DEMO / SANDBOX PAYMENT
# ============================================================================
#
# This route is kept because your existing UniRent project already uses it.
# The new Razorpay Standard Checkout will use:
#
#     /api/create-order
#     /api/verify-payment
#
# instead.
#
# ============================================================================

@main_bp.route(
    '/payment/process',
    methods=['POST']
)
def process_demo_payment():

    print(
        "\n============================================================"
    )

    print(
        "              UNIRENT PAYMENT PROCESS"
    )

    print(
        "============================================================"
    )

    try:

        data = request.get_json(
            silent=True
        ) or {}

        print(
            "Received payment data:",
            data
        )

        booking_ref = str(
            data.get(
                'booking_reference',
                ''
            )
        ).strip()

        payment_method = str(
            data.get(
                'payment_method',
                'card'
            )
        ).strip().lower()

        if not booking_ref:

            return jsonify({
                'success': False,
                'message': 'Booking reference is missing.'
            }), 400

        allowed_methods = [
            'card',
            'upi',
            'netbanking'
        ]

        if payment_method not in allowed_methods:

            return jsonify({
                'success': False,
                'message':
                    'Invalid payment method. '
                    f'Allowed methods: {", ".join(allowed_methods)}'
            }), 400

        # ----------------------------------------------------------
        # Find booking
        # ----------------------------------------------------------

        booking_obj = (
            Booking.query
            .filter_by(
                booking_reference=booking_ref
            )
            .first()
        )

        if not booking_obj:

            return jsonify({
                'success': False,
                'message': 'Booking record not found.'
            }), 404

        print(
            f"Processing booking: "
            f"ID={booking_obj.booking_id}, "
            f"Ref={booking_obj.booking_reference}, "
            f"Amount={booking_obj.total_amount}"
        )

        # ----------------------------------------------------------
        # Check if genuinely already paid
        # ----------------------------------------------------------

        existing_payment = booking_obj.payment

        if (
            existing_payment
            and existing_payment.payment_status in (
                'successful',
                'approved',
                'completed'
            )
            and booking_obj.booking_status == 'confirmed'
        ):

            txn_id = getattr(
                existing_payment,
                'transaction_reference',
                getattr(
                    existing_payment,
                    'transaction_id',
                    ''
                )
            )

            print(
                "Booking is already confirmed and paid. "
                "Txn:",
                txn_id
            )

            return jsonify({
                'success': True,
                'already_paid': True,
                'booking_id':
                    booking_obj.booking_id,
                'booking_reference':
                    booking_obj.booking_reference,
                'transaction_id':
                    txn_id,
                'message':
                    'Payment has already been completed.'
            }), 200

        # ----------------------------------------------------------
        # Generate unique demo transaction ID
        # ----------------------------------------------------------

        transaction_id = (
            f"TXN-RPY-{uuid.uuid4().hex[:12].upper()}"
        )

        # ----------------------------------------------------------
        # Create or update Payment record
        # ----------------------------------------------------------

        if existing_payment:

            existing_payment.amount = (
                booking_obj.total_amount
            )

            existing_payment.payment_method = (
                payment_method
            )

            existing_payment.transaction_reference = (
                transaction_id
            )

            existing_payment.payment_status = (
                'successful'
            )

            existing_payment.payment_date = (
                datetime.utcnow()
            )

        else:

            new_payment = Payment(
                booking_id=booking_obj.booking_id,
                amount=booking_obj.total_amount,
                payment_method=payment_method,
                transaction_reference=transaction_id,
                payment_status='successful',
                payment_date=datetime.utcnow()
            )

            db.session.add(
                new_payment
            )

        # ----------------------------------------------------------
        # Confirm booking
        # ----------------------------------------------------------

        booking_obj.booking_status = (
            'confirmed'
        )

        # ----------------------------------------------------------
        # Commit transaction to MySQL
        # ----------------------------------------------------------

        db.session.commit()

        print(
            "Payment record and confirmed booking "
            "committed successfully to database."
        )

        # ----------------------------------------------------------
        # Safe print helper
        # ----------------------------------------------------------

        def safe_print(*args, **kwargs):

            try:

                print(
                    *args,
                    **kwargs
                )

            except Exception:

                try:

                    clean_args = [
                        str(a)
                        .encode(
                            'ascii',
                            errors='replace'
                        )
                        .decode('ascii')
                        for a in args
                    ]

                    print(
                        *clean_args,
                        **kwargs
                    )

                except Exception:

                    pass

        # ----------------------------------------------------------
        # Prepare confirmation email
        # ----------------------------------------------------------

        email_sent = False

        try:

            user = getattr(
                booking_obj,
                'user',
                None
            )

            user_email = (
                getattr(
                    user,
                    'email',
                    None
                )
                if user
                else None
            )

            user_name = (
                getattr(
                    user,
                    'full_name',
                    'Valued Traveler'
                )
                if user
                else 'Valued Traveler'
            )

            # Get listing name safely
            listing_name = 'UniRent Rental'

            if booking_obj.listing_type == 'property':

                property_obj = db.session.get(
                    Property,
                    booking_obj.property_id
                )

                if property_obj:

                    listing_name = (
                        property_obj.property_name
                    )

            elif booking_obj.listing_type == 'vehicle':

                vehicle_obj = db.session.get(
                    Vehicle,
                    booking_obj.vehicle_id
                )

                if vehicle_obj:

                    listing_name = (
                        vehicle_obj.vehicle_name
                    )

            duration_unit = (
                'night(s)'
                if booking_obj.listing_type == 'property'
                else 'day(s)'
            )

            booking_dates = (
                f"{booking_obj.start_date.strftime('%b %d, %Y')} "
                f"to "
                f"{booking_obj.end_date.strftime('%b %d, %Y')} "
                f"({booking_obj.total_days} {duration_unit})"
            )

            total_amount_display = (
                f"Rs. "
                f"{float(booking_obj.total_amount):,.2f}"
            )

            subject = (
                f"UniRent Booking Confirmation - "
                f"{booking_obj.booking_reference}"
            )

            email_body = f"""Hello {user_name},

Your UniRent booking has been successfully confirmed!

Here are your verified reservation details:
--------------------------------------------------
Traveler Name     : {user_name}
Booking Reference : {booking_obj.booking_reference}
Property / Vehicle: {listing_name}
Booking Dates     : {booking_dates}
Total Amount      : {total_amount_display}
Payment Method    : {payment_method.upper()}
Transaction ID    : {transaction_id}
Booking Status    : Successfully Confirmed
--------------------------------------------------

We look forward to hosting you for an unforgettable Kerala experience.
You can view and print your booking receipt anytime from your traveler portal.

Thank you for choosing UniRent Kerala!

Warm regards,
UniRent Kerala Team
Heritage Stays & Vehicle Rentals
"""

            if user_email:

                try:

                    mail = (
                        current_app
                        .extensions
                        .get('mail')
                    )

                    if (
                        mail
                        and (
                            current_app.config.get(
                                'MAIL_USERNAME'
                            )
                            or current_app.config.get(
                                'TESTING'
                            )
                        )
                    ):

                        from flask_mail import Message

                        message = Message(
                            subject=subject,
                            recipients=[user_email],
                            body=email_body,
                            sender=current_app.config.get(
                                'MAIL_DEFAULT_SENDER',
                                'noreply@unirent.com'
                            )
                        )

                        mail.send(
                            message
                        )

                        email_sent = True

                        safe_print(
                            "Confirmation email successfully "
                            "sent via Flask-Mail to:",
                            user_email
                        )

                    else:

                        safe_print(
                            "------------------------------------------------------------"
                        )

                        safe_print(
                            "DEMO EMAIL DISPATCH "
                            "(Flask-Mail Simulator):"
                        )

                        safe_print(
                            f"To: {user_email}"
                        )

                        safe_print(
                            f"Subject: {subject}"
                        )

                        safe_print(
                            email_body
                        )

                        safe_print(
                            "------------------------------------------------------------"
                        )

                        email_sent = True

                except Exception as email_error:

                    safe_print(
                        f"Notice: SMTP delivery failed "
                        f"({email_error}). "
                        "Logging email content:"
                    )

                    safe_print(
                        email_body
                    )

                    email_sent = False

            else:

                safe_print(
                    "No traveler email found for booking."
                )

        except Exception as email_outer_err:

            safe_print(
                f"Email preparation notice: "
                f"{email_outer_err}"
            )

            email_sent = False

        print(
            "============================================================"
        )

        print(
            "PAYMENT PROCESSED SUCCESSFULLY"
        )

        print(
            "Booking ID:",
            booking_obj.booking_id
        )

        print(
            "Booking Ref:",
            booking_obj.booking_reference
        )

        print(
            "Transaction:",
            transaction_id
        )

        print(
            "Email sent:",
            email_sent
        )

        print(
            "============================================================\n"
        )

        return jsonify({

            'success': True,

            'booking_id':
                booking_obj.booking_id,

            'booking_reference':
                booking_obj.booking_reference,

            'transaction_id':
                transaction_id,

            'email_sent':
                email_sent,

            'message':
                'Payment successful! '
                'Your booking is confirmed.'

        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            "\n============================================================"
        )

        print(
            "PAYMENT ERROR:",
            str(error)
        )

        print(
            "============================================================\n"
        )

        return jsonify({

            'success': False,

            'message':
                'Unable to process payment. '
                'Please try again.',

            'error':
                str(error)

        }), 500


# ============================================================================
# RAZORPAY - VERIFY PAYMENT
# ============================================================================

@main_bp.route(
    '/api/verify-payment',
    methods=['POST']
)
def verify_razorpay_payment():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        razorpay_order_id = str(
            data.get(
                'razorpay_order_id',
                ''
            )
        ).strip()

        razorpay_payment_id = str(
            data.get(
                'razorpay_payment_id',
                ''
            )
        ).strip()

        razorpay_signature = str(
            data.get(
                'razorpay_signature',
                ''
            )
        ).strip()

        booking_ref = str(
            data.get(
                'booking_reference',
                ''
            )
        ).strip()

        # ----------------------------------------------------------
        # Validate required fields
        # ----------------------------------------------------------

        if not all([
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature,
            booking_ref
        ]):

            return jsonify({
                'success': False,
                'message':
                    'Required payment verification fields are missing.'
            }), 400

        # ----------------------------------------------------------
        # Find booking
        # ----------------------------------------------------------

        booking_obj = (
            Booking.query
            .filter_by(
                booking_reference=booking_ref
            )
            .first()
        )

        if not booking_obj:

            return jsonify({
                'success': False,
                'message': 'Booking record not found.'
            }), 404

        # ----------------------------------------------------------
        # Generate HMAC SHA256 signature
        # ----------------------------------------------------------

        message = (
            razorpay_order_id
            + '|'
            + razorpay_payment_id
        )

        generated_signature = hmac.new(
            current_app.config[
                'RAZORPAY_KEY_SECRET'
            ].encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # ----------------------------------------------------------
        # Safely compare signatures
        # ----------------------------------------------------------

        if not hmac.compare_digest(
            generated_signature,
            razorpay_signature
        ):

            print(
                'Razorpay signature verification failed.'
            )

            return jsonify({
                'success': False,
                'message':
                    'Payment signature verification failed.'
            }), 400

        # ----------------------------------------------------------
        # Check existing successful payment
        # ----------------------------------------------------------

        existing_payment = booking_obj.payment

        if (
            existing_payment
            and existing_payment.payment_status
            in (
                'successful',
                'approved',
                'completed'
            )
        ):

            return jsonify({
                'success': True,
                'already_paid': True,
                'booking_id':
                    booking_obj.booking_id,
                'booking_reference':
                    booking_obj.booking_reference,
                'transaction_id':
                    existing_payment.transaction_reference,
                'message':
                    'Payment has already been verified.'
            }), 200

        # ----------------------------------------------------------
        # Create or update Payment record
        # ----------------------------------------------------------

        if existing_payment:

            payment_record = existing_payment

            payment_record.amount = (
                booking_obj.total_amount
            )

            payment_record.payment_method = (
                'razorpay'
            )

            payment_record.transaction_reference = (
                razorpay_payment_id
            )

            payment_record.payment_status = (
                'successful'
            )

            payment_record.payment_date = (
                datetime.utcnow()
            )

            payment_record.gateway_response = (
                f'Razorpay Order: '
                f'{razorpay_order_id}'
            )

        else:

            payment_record = Payment(
                booking_id=booking_obj.booking_id,
                amount=booking_obj.total_amount,
                payment_method='razorpay',
                transaction_reference=razorpay_payment_id,
                payment_status='successful',
                payment_date=datetime.utcnow(),
                gateway_response=(
                    f'Razorpay Order: '
                    f'{razorpay_order_id}'
                )
            )

            db.session.add(
                payment_record
            )

        # ----------------------------------------------------------
        # Confirm booking
        # ----------------------------------------------------------

        booking_obj.booking_status = (
            'confirmed'
        )

        # ----------------------------------------------------------
        # Save to MySQL
        # ----------------------------------------------------------

        db.session.commit()

        print(
            '============================================================'
        )

        print(
            'RAZORPAY PAYMENT VERIFIED SUCCESSFULLY'
        )

        print(
            'Booking ID:',
            booking_obj.booking_id
        )

        print(
            'Booking Ref:',
            booking_obj.booking_reference
        )

        print(
            'Razorpay Order ID:',
            razorpay_order_id
        )

        print(
            'Razorpay Payment ID:',
            razorpay_payment_id
        )

        print(
            '============================================================'
        )

        return jsonify({

            'success': True,

            'booking_id':
                booking_obj.booking_id,

            'booking_reference':
                booking_obj.booking_reference,

            'transaction_id':
                razorpay_payment_id,

            'message':
                'Payment verified successfully.'

        }), 200

    except Exception as error:

        db.session.rollback()

        print(
            'Razorpay verification error:',
            str(error)
        )

        return jsonify({
            'success': False,
            'message':
                'Unable to verify payment.',
            'error':
                str(error)
        }), 500


# ============================================================================
# BOOKING CONFIRMATION
# ============================================================================

@main_bp.route('/confirmation')
def confirmation():

    booking_id = request.args.get(
        'booking_id',
        type=int
    )

    booking_ref = request.args.get(
        'ref'
    )

    booking_obj = None

    # Find by booking ID
    if booking_id:

        booking_obj = db.session.get(
            Booking,
            booking_id
        )

    # Find by booking reference
    elif booking_ref:

        booking_obj = (
            Booking.query
            .filter_by(
                booking_reference=booking_ref
            )
            .first()
        )

    if not booking_obj:

        flash(
            'Booking record not found.',
            'warning'
        )

        return redirect(
            url_for('main.index')
        )

    return render_template(
        'confirmation.html',
        booking=booking_obj
    )


# ============================================================================
# DOWNLOAD BOOKING RECEIPT
# ============================================================================

@main_bp.route(
    '/confirmation/<int:booking_id>/download-receipt'
)
def download_receipt(booking_id):

    # ----------------------------------------------------------
    # Find booking
    # ----------------------------------------------------------

    booking = db.session.get(
        Booking,
        booking_id
    )

    if not booking:

        flash(
            'Booking record not found.',
            'warning'
        )

        return redirect(
            url_for('main.index')
        )

    # ----------------------------------------------------------
    # Create PDF in memory
    # ----------------------------------------------------------

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # ----------------------------------------------------------
    # Header
    # ----------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        22
    )

    pdf.drawString(
        50,
        height - 60,
        "UniRent"
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        height - 78,
        "Heritage Stays & Vehicle Rentals"
    )

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawRightString(
        width - 50,
        height - 60,
        "PAYMENT RECEIPT"
    )

    pdf.line(
        50,
        height - 95,
        width - 50,
        height - 95
    )

    # ----------------------------------------------------------
    # Booking Details
    # ----------------------------------------------------------

    y = height - 130

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Booking Details"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        f"Booking Reference: "
        f"{booking.booking_reference}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Booking Status: "
        f"{booking.booking_status.capitalize()}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Start Date: "
        f"{booking.start_date.strftime('%d %B %Y')}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"End Date: "
        f"{booking.end_date.strftime('%d %B %Y')}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Total Days: "
        f"{booking.total_days}"
    )

    # ----------------------------------------------------------
    # Rental Details
    # ----------------------------------------------------------

    y -= 45

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Rental Details"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    listing_name = "UniRent Rental"

    if booking.listing_type == 'property':

        property_obj = db.session.get(
            Property,
            booking.property_id
        )

        if property_obj:

            listing_name = (
                property_obj.property_name
            )

        pdf.drawString(
            50,
            y,
            "Rental Type: Heritage Stay"
        )

        y -= 20

        pdf.drawString(
            50,
            y,
            f"Property: {listing_name}"
        )

    elif booking.listing_type == 'vehicle':

        vehicle_obj = db.session.get(
            Vehicle,
            booking.vehicle_id
        )

        if vehicle_obj:

            listing_name = (
                vehicle_obj.vehicle_name
            )

        pdf.drawString(
            50,
            y,
            "Rental Type: Vehicle"
        )

        y -= 20

        pdf.drawString(
            50,
            y,
            f"Vehicle: {listing_name}"
        )

    else:

        pdf.drawString(
            50,
            y,
            "Rental details unavailable."
        )

    # ----------------------------------------------------------
    # Payment Details
    # ----------------------------------------------------------

    y -= 45

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Payment Details"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    payment = booking.payment

    if payment:

        pdf.drawString(
            50,
            y,
            f"Payment Method: "
            f"{payment.payment_method.upper()}"
        )

        y -= 20

        pdf.drawString(
            50,
            y,
            f"Transaction ID: "
            f"{payment.transaction_reference}"
        )

        y -= 20

        pdf.drawString(
            50,
            y,
            f"Payment Status: "
            f"{payment.payment_status.capitalize()}"
        )

        y -= 20

        if payment.payment_date:

            pdf.drawString(
                50,
                y,
                f"Payment Date: "
                f"{payment.payment_date.strftime('%d %B %Y, %I:%M %p')}"
            )

    else:

        pdf.drawString(
            50,
            y,
            "Payment information unavailable."
        )

    # ----------------------------------------------------------
    # Amount Summary
    # ----------------------------------------------------------

    y -= 45

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Amount Summary"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        f"Daily Rate: "
        f"Rs. {float(booking.daily_rate):,.2f}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Service Fee: "
        f"Rs. {float(booking.service_fee):,.2f}"
    )

    y -= 20

    pdf.drawString(
        50,
        y,
        f"Tax: "
        f"Rs. {float(booking.tax_amount):,.2f}"
    )

    y -= 30

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        50,
        y,
        f"Total Paid: "
        f"Rs. {float(booking.total_amount):,.2f}"
    )

    # ----------------------------------------------------------
    # Footer
    # ----------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        50,
        50,
        "Thank you for choosing UniRent Kerala."
    )

    pdf.drawRightString(
        width - 50,
        50,
        "Computer-generated receipt"
    )

    # ----------------------------------------------------------
    # Finish PDF
    # ----------------------------------------------------------

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    filename = (
        f"UniRent_Receipt_"
        f"{booking.booking_reference}.pdf"
    )

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )