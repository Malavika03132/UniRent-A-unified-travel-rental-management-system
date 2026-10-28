import json

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
    jsonify
)

from app.models import (
    db,
    User,
    Owner,
    Property,
    Vehicle,
    Booking,
    Payment,
    Review,
    Complaint
)

from app.routes.auth import login_required
from app.utils.validators import validate_full_name, validate_phone, validate_owner_fields


owner_bp = Blueprint('owner', __name__)


# ============================================================
# GET CURRENT OWNER
# ============================================================

def get_current_owner():

    user_id = session.get('user_id')

    owner = Owner.query.filter_by(
        user_id=user_id
    ).first()

    if not owner:

        # Auto-create owner profile if user has role owner
        user = db.session.get(
            User,
            user_id
        )

        if user and user.role == 'owner':

            owner = Owner(
                user_id=user_id,
                business_name=f"{user.full_name}'s Heritage Rentals",
                district='Ernakulam'
            )

            db.session.add(owner)
            db.session.commit()

    return owner


# ============================================================
# OWNER DASHBOARD
# ============================================================

@owner_bp.route('/dashboard')
@login_required('owner')
def dashboard():

    owner = get_current_owner()

    if not owner:

        flash(
            'Owner profile required.',
            'danger'
        )

        return redirect(
            url_for('auth.login')
        )

    properties = Property.query.filter_by(
        owner_id=owner.owner_id
    ).all()

    vehicles = Vehicle.query.filter_by(
        owner_id=owner.owner_id
    ).all()

    prop_ids = [
        p.property_id
        for p in properties
    ]

    veh_ids = [
        v.vehicle_id
        for v in vehicles
    ]

    # --------------------------------------------------------
    # BOOKINGS
    # --------------------------------------------------------

    bookings = Booking.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Booking.created_at.desc()
    ).all()

    active_bookings = [
        b for b in bookings
        if b.booking_status in [
            'active',
            'confirmed'
        ]
    ]

    total_revenue = sum(
        b.total_amount
        for b in bookings
        if b.booking_status in [
            'confirmed',
            'active',
            'completed'
        ]
    )

    # --------------------------------------------------------
    # COMPLAINTS
    # --------------------------------------------------------

    complaints = Complaint.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    open_complaints = [
        c for c in complaints
        if c.status in [
            'open',
            'under_review'
        ]
    ]

    # --------------------------------------------------------
    # REVIEWS
    # --------------------------------------------------------

    reviews = []

    if prop_ids or veh_ids:

        reviews = Review.query.filter(
            (Review.property_id.in_(prop_ids)) |
            (Review.vehicle_id.in_(veh_ids))
        ).order_by(
            Review.created_at.desc()
        ).limit(5).all()

    return render_template(
        'owner/dashboard.html',
        owner=owner,
        stats={
            'total_properties': len(properties),
            'total_vehicles': len(vehicles),
            'active_bookings': len(active_bookings),
            'total_revenue': total_revenue
        },
        properties=properties[:4],
        vehicles=vehicles[:4],
        recent_bookings=bookings[:5],
        reviews=reviews,
        open_complaints=open_complaints
    )


# ============================================================
# OWNER PROPERTIES
# ============================================================

@owner_bp.route('/properties')
@login_required('owner')
def properties():

    owner = get_current_owner()

    properties_list = Property.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Property.created_at.desc()
    ).all()

    return render_template(
        'owner/properties.html',
        properties=properties_list,
        owner=owner
    )


# ============================================================
# EDIT PROPERTY
# ============================================================

@owner_bp.route(
    '/properties/<int:property_id>/edit',
    methods=['POST']
)
@login_required('owner')
def edit_property(property_id):

    owner = get_current_owner()

    # Only the owner who owns this property can edit it.
    property_item = Property.query.filter_by(
        property_id=property_id,
        owner_id=owner.owner_id
    ).first_or_404()

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    property_name = request.form.get(
        'property_name',
        ''
    ).strip()

    property_type = request.form.get(
        'property_type',
        property_item.property_type
    )

    description = request.form.get(
        'description',
        ''
    ).strip()

    address = request.form.get(
        'address',
        ''
    ).strip()

    district = request.form.get(
        'district',
        property_item.district
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not property_name:

        flash(
            'Property name is required.',
            'danger'
        )

        return redirect(
            url_for('owner.properties')
        )

    if not description:

        flash(
            'Property description is required.',
            'danger'
        )

        return redirect(
            url_for('owner.properties')
        )

    if not address:

        flash(
            'Property address is required.',
            'danger'
        )

        return redirect(
            url_for('owner.properties')
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price = request.form.get(
        'price_per_night',
        type=float
    )

    if price is not None and price >= 0:

        property_item.price_per_night = price

    # --------------------------------------------------------
    # GUEST CAPACITY
    # --------------------------------------------------------

    guest_capacity = request.form.get(
        'guest_capacity',
        type=int
    )

    if guest_capacity is not None and guest_capacity > 0:

        property_item.guest_capacity = guest_capacity

    # --------------------------------------------------------
    # BEDROOMS
    # --------------------------------------------------------

    bedrooms = request.form.get(
        'bedrooms',
        type=int
    )

    if bedrooms is not None and bedrooms >= 0:

        property_item.bedrooms = bedrooms

    # --------------------------------------------------------
    # BATHROOMS
    # --------------------------------------------------------

    bathrooms = request.form.get(
        'bathrooms',
        type=int
    )

    if bathrooms is not None and bathrooms >= 0:

        property_item.bathrooms = bathrooms

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    latitude = request.form.get(
        'latitude',
        type=float
    )

    longitude = request.form.get(
        'longitude',
        type=float
    )

    if latitude is not None:
        property_item.latitude = latitude

    if longitude is not None:
        property_item.longitude = longitude

    # --------------------------------------------------------
    # UPDATE MAIN FIELDS
    # --------------------------------------------------------

    property_item.property_name = property_name

    property_item.property_type = property_type

    property_item.description = description

    property_item.address = address

    property_item.district = district

    # --------------------------------------------------------
    # AMENITIES
    # --------------------------------------------------------

    selected_amenities = request.form.getlist(
        'amenities'
    )

    property_item.amenities = json.dumps(
        selected_amenities
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image_url = request.form.get(
        'image_url',
        ''
    ).strip()

    if image_url:

        property_item.images = json.dumps(
            [image_url]
        )

        property_item.featured_image = image_url

    # --------------------------------------------------------
    # SAVE & RESUBMISSION
    # --------------------------------------------------------

    resubmit = request.form.get('resubmit') == '1' or property_item.approval_status == 'rejected'
    if resubmit:
        property_item.approval_status = 'pending'
        property_item.rejection_reason = None
        db.session.commit()
        flash(
            f"Property '{property_item.property_name}' was updated and resubmitted for Admin verification.",
            'success'
        )
    else:
        db.session.commit()
        flash(
            f"Property '{property_item.property_name}' was updated successfully.",
            'success'
        )

    return redirect(
        url_for('owner.properties')
    )


# ============================================================
# RESUBMIT PROPERTY
# ============================================================

@owner_bp.route(
    '/properties/<int:property_id>/resubmit',
    methods=['POST']
)
@login_required('owner')
def resubmit_property(property_id):

    owner = get_current_owner()

    property_item = Property.query.filter_by(
        property_id=property_id,
        owner_id=owner.owner_id
    ).first_or_404()

    property_item.approval_status = 'pending'
    property_item.rejection_reason = None
    db.session.commit()

    flash(
        f"Property '{property_item.property_name}' has been resubmitted for Admin verification.",
        'success'
    )

    return redirect(
        url_for('owner.properties')
    )


# ============================================================
# REMOVE PROPERTY
# ============================================================

@owner_bp.route(
    '/properties/<int:property_id>/remove',
    methods=['POST']
)
@login_required('owner')
def remove_property(property_id):

    owner = get_current_owner()

    property_item = Property.query.filter_by(
        property_id=property_id,
        owner_id=owner.owner_id
    ).first_or_404()

    # --------------------------------------------------------
    # We do NOT permanently delete the database record.
    #
    # This preserves existing bookings/reviews/history.
    # --------------------------------------------------------

    property_item.availability_status = 'inactive'

    db.session.commit()

    flash(
        f"Property '{property_item.property_name}' "
        f"has been removed from active listings.",
        'success'
    )

    return redirect(
        url_for('owner.properties')
    )


# ============================================================
# ADD PROPERTY
# ============================================================

@owner_bp.route(
    '/add-property',
    methods=['GET', 'POST']
)
@login_required('owner')
def add_property():

    owner = get_current_owner()

    if request.method == 'POST':

        name = request.form.get(
            'property_name',
            ''
        ).strip()

        prop_type = request.form.get(
            'property_type',
            'Heritage Villa'
        )

        description = request.form.get(
            'description',
            ''
        ).strip()

        address = request.form.get(
            'address',
            ''
        ).strip()

        district = request.form.get(
            'district',
            'Ernakulam'
        )

        lat = request.form.get(
            'latitude',
            type=float
        ) or 9.9312

        lng = request.form.get(
            'longitude',
            type=float
        ) or 76.2673

        price = request.form.get(
            'price_per_night',
            type=float
        ) or 4500.0

        guests = request.form.get(
            'guest_capacity',
            type=int
        ) or 4

        bedrooms = request.form.get(
            'bedrooms',
            type=int
        ) or 2

        bathrooms = request.form.get(
            'bathrooms',
            type=int
        ) or 2

        image_url = request.form.get(
            'image_url',
            ''
        ).strip() or (
            'https://images.unsplash.com/'
            'photo-1580587771525-78b9dba3b914'
            '?auto=format&fit=crop&w=1200&q=80'
        )

        selected_amenities = request.form.getlist(
            'amenities'
        )

        slug = (
            f"{name.lower().replace(' ', '-')}"
            f"-{int(datetime.utcnow().timestamp())}"
        )

        new_prop = Property(
            owner_id=owner.owner_id,
            property_name=name,
            slug=slug,
            property_type=prop_type,
            description=description,
            address=address,
            district=district,
            latitude=lat,
            longitude=lng,
            price_per_night=price,
            guest_capacity=guests,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            amenities=json.dumps(
                selected_amenities
            ),
            images=json.dumps(
                [image_url]
            ),
            featured_image=image_url,
            approval_status='pending',
            availability_status='available',
            featured=False
        )

        db.session.add(new_prop)

        db.session.commit()

        flash(
            f"Property '{name}' submitted! "
            f"Status: PENDING ADMIN APPROVAL. "
            f"An administrator will review it before publication.",
            'info'
        )

        return redirect(
            url_for('owner.properties')
        )

    return render_template(
        'owner/add_property.html',
        owner=owner
    )


# ============================================================
# OWNER VEHICLES
# ============================================================

@owner_bp.route('/vehicles')
@login_required('owner')
def vehicles():

    owner = get_current_owner()

    vehicles_list = Vehicle.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template(
        'owner/vehicles.html',
        vehicles=vehicles_list,
        owner=owner
    )


# ============================================================
# EDIT VEHICLE
# ============================================================

@owner_bp.route(
    '/vehicles/<int:vehicle_id>/edit',
    methods=['POST']
)
@login_required('owner')
def edit_vehicle(vehicle_id):

    owner = get_current_owner()

    # Only the owner who owns this vehicle can edit it.
    vehicle = Vehicle.query.filter_by(
        vehicle_id=vehicle_id,
        owner_id=owner.owner_id
    ).first_or_404()

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    vehicle_name = request.form.get(
        'vehicle_name',
        ''
    ).strip()

    model = request.form.get(
        'model',
        ''
    ).strip()

    vehicle_type = request.form.get(
        'vehicle_type',
        vehicle.vehicle_type
    ).lower()

    description = request.form.get(
        'description',
        ''
    ).strip()

    district = request.form.get(
        'district',
        vehicle.district
    )

    pickup_location = request.form.get(
        'pickup_location',
        ''
    ).strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not vehicle_name:

        flash(
            'Vehicle name is required.',
            'danger'
        )

        return redirect(
            url_for('owner.vehicles')
        )

    if not model:

        flash(
            'Vehicle model is required.',
            'danger'
        )

        return redirect(
            url_for('owner.vehicles')
        )

    if not description:

        flash(
            'Vehicle description is required.',
            'danger'
        )

        return redirect(
            url_for('owner.vehicles')
        )

    if not pickup_location:

        flash(
            'Pickup location is required.',
            'danger'
        )

        return redirect(
            url_for('owner.vehicles')
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price = request.form.get(
        'price_per_day',
        type=float
    )

    if price is not None and price >= 0:

        vehicle.price_per_day = price

    # --------------------------------------------------------
    # SECURITY DEPOSIT
    # --------------------------------------------------------

    security_deposit = request.form.get(
        'security_deposit',
        type=float
    )

    if security_deposit is not None and security_deposit >= 0:

        vehicle.security_deposit = security_deposit

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    latitude = request.form.get(
        'latitude',
        type=float
    )

    longitude = request.form.get(
        'longitude',
        type=float
    )

    if latitude is not None:
        vehicle.latitude = latitude

    if longitude is not None:
        vehicle.longitude = longitude

    # --------------------------------------------------------
    # DELIVERY
    # --------------------------------------------------------

    vehicle.delivery_available = bool(
        request.form.get(
            'delivery_available'
        )
    )

    # --------------------------------------------------------
    # UPDATE BASIC FIELDS
    # --------------------------------------------------------

    vehicle.vehicle_name = vehicle_name

    vehicle.model = model

    vehicle.vehicle_type = vehicle_type

    vehicle.description = description

    vehicle.district = district

    vehicle.pickup_location = pickup_location

    # --------------------------------------------------------
    # VEHICLE SPECIFICATIONS
    # --------------------------------------------------------

    specifications = {
        'transmission': request.form.get(
            'spec_transmission',
            'Manual'
        ),

        'fuel': request.form.get(
            'spec_fuel',
            'Petrol'
        ),

        'seats': request.form.get(
            'spec_seats',
            '5'
        ),

        'mileage': request.form.get(
            'spec_mileage',
            '18 kmpl'
        )
    }

    vehicle.specifications = json.dumps(
        specifications
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image_url = request.form.get(
        'image_url',
        ''
    ).strip()

    if image_url:

        vehicle.images = json.dumps(
            [image_url]
        )

        vehicle.featured_image = image_url

    # --------------------------------------------------------
    # SAVE & RESUBMISSION
    # --------------------------------------------------------

    resubmit = request.form.get('resubmit') == '1' or vehicle.approval_status == 'rejected'
    if resubmit:
        vehicle.approval_status = 'pending'
        vehicle.rejection_reason = None
        db.session.commit()
        flash(
            f"Vehicle '{vehicle.vehicle_name}' was updated and resubmitted for Admin verification.",
            'success'
        )
    else:
        db.session.commit()
        flash(
            f"Vehicle '{vehicle.vehicle_name}' was updated successfully.",
            'success'
        )

    return redirect(
        url_for('owner.vehicles')
    )


# ============================================================
# RESUBMIT VEHICLE
# ============================================================

@owner_bp.route(
    '/vehicles/<int:vehicle_id>/resubmit',
    methods=['POST']
)
@login_required('owner')
def resubmit_vehicle(vehicle_id):

    owner = get_current_owner()

    vehicle = Vehicle.query.filter_by(
        vehicle_id=vehicle_id,
        owner_id=owner.owner_id
    ).first_or_404()

    vehicle.approval_status = 'pending'
    vehicle.rejection_reason = None
    db.session.commit()

    flash(
        f"Vehicle '{vehicle.vehicle_name}' has been resubmitted for Admin verification.",
        'success'
    )

    return redirect(
        url_for('owner.vehicles')
    )


# ============================================================
# REMOVE VEHICLE
# ============================================================

@owner_bp.route(
    '/vehicles/<int:vehicle_id>/remove',
    methods=['POST']
)
@login_required('owner')
def remove_vehicle(vehicle_id):

    owner = get_current_owner()

    vehicle = Vehicle.query.filter_by(
        vehicle_id=vehicle_id,
        owner_id=owner.owner_id
    ).first_or_404()

    # --------------------------------------------------------
    # Soft removal.
    # Keeps booking/review history.
    # --------------------------------------------------------

    vehicle.availability_status = 'inactive'

    db.session.commit()

    flash(
        f"Vehicle '{vehicle.vehicle_name}' "
        f"has been removed from active listings.",
        'success'
    )

    return redirect(
        url_for('owner.vehicles')
    )


# ============================================================
# ADD VEHICLE
# ============================================================

@owner_bp.route(
    '/add-vehicle',
    methods=['GET', 'POST']
)
@login_required('owner')
def add_vehicle():

    owner = get_current_owner()

    if request.method == 'POST':

        name = request.form.get(
            'vehicle_name',
            ''
        ).strip()

        model = request.form.get(
            'model',
            ''
        ).strip()

        v_type = request.form.get(
            'vehicle_type',
            'car'
        ).lower()

        description = request.form.get(
            'description',
            ''
        ).strip()

        price = request.form.get(
            'price_per_day',
            type=float
        ) or 1500.0

        district = request.form.get(
            'district',
            'Ernakulam'
        )

        pickup = request.form.get(
            'pickup_location',
            ''
        ).strip()

        delivery = bool(
            request.form.get(
                'delivery_available'
            )
        )

        lat = request.form.get(
            'latitude',
            type=float
        ) or 9.9312

        lng = request.form.get(
            'longitude',
            type=float
        ) or 76.2673

        image_url = request.form.get(
            'image_url',
            ''
        ).strip() or (
            'https://images.unsplash.com/'
            'photo-1558981806-ec527fa84c39'
            '?auto=format&fit=crop&w=1200&q=80'
        )

        specs = {

            'transmission': request.form.get(
                'spec_transmission',
                'Manual'
            ),

            'fuel': request.form.get(
                'spec_fuel',
                'Petrol'
            ),

            'seats': request.form.get(
                'spec_seats',
                '5'
            ),

            'mileage': request.form.get(
                'spec_mileage',
                '18 kmpl'
            )
        }

        new_veh = Vehicle(
            owner_id=owner.owner_id,
            vehicle_name=name,
            model=model,
            vehicle_type=v_type,
            description=description,
            price_per_day=price,
            district=district,
            pickup_location=pickup,
            latitude=lat,
            longitude=lng,
            delivery_available=delivery,
            specifications=json.dumps(specs),
            images=json.dumps([image_url]),
            featured_image=image_url,
            approval_status='pending',
            availability_status='available',
            featured=False
        )

        db.session.add(new_veh)

        db.session.commit()

        flash(
            f"Vehicle '{name}' submitted! "
            f"Status: PENDING ADMIN APPROVAL.",
            'info'
        )

        return redirect(
            url_for('owner.vehicles')
        )

    return render_template(
        'owner/add_vehicle.html',
        owner=owner
    )


# ============================================================
# OWNER BOOKINGS
# ============================================================

@owner_bp.route('/bookings')
@login_required('owner')
def bookings():

    owner = get_current_owner()

    owner_bookings = Booking.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Booking.created_at.desc()
    ).all()

    return render_template(
        'owner/bookings.html',
        bookings=owner_bookings,
        owner=owner
    )


@owner_bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@login_required('owner')
def complete_booking(booking_id):
    owner = get_current_owner()
    booking = Booking.query.filter_by(
        booking_id=booking_id,
        owner_id=owner.owner_id
    ).first_or_404()

    booking.booking_status = 'completed'
    db.session.commit()
    flash(f"Booking {booking.booking_reference} marked as Completed / Checked Out.", 'success')
    return redirect(url_for('owner.bookings'))


# ============================================================
# OWNER PAYMENTS
# ============================================================

@owner_bp.route('/payments')
@login_required('owner')
def payments():

    owner = get_current_owner()

    bookings = Booking.query.filter_by(
        owner_id=owner.owner_id
    ).all()

    b_ids = [
        b.booking_id
        for b in bookings
    ]

    payments_list = (
        Payment.query.filter(
            Payment.booking_id.in_(b_ids)
        ).order_by(
            Payment.payment_date.desc()
        ).all()
        if b_ids
        else []
    )

    total_gross = sum(
        p.amount
        for p in payments_list
        if p.payment_status == 'successful'
    )

    platform_fee = total_gross * 0.10

    net_payout = total_gross - platform_fee

    return render_template(
        'owner/payments.html',
        payments=payments_list,
        owner=owner,
        total_gross=total_gross,
        platform_fee=platform_fee,
        net_payout=net_payout
    )


# ============================================================
# OWNER REVIEWS
# ============================================================

@owner_bp.route('/reviews')
@login_required('owner')
def reviews():

    owner = get_current_owner()

    props = Property.query.filter_by(
        owner_id=owner.owner_id
    ).all()

    vehs = Vehicle.query.filter_by(
        owner_id=owner.owner_id
    ).all()

    prop_ids = [
        p.property_id
        for p in props
    ]

    veh_ids = [
        v.vehicle_id
        for v in vehs
    ]

    reviews_list = []

    if prop_ids or veh_ids:

        reviews_list = Review.query.filter(
            (Review.property_id.in_(prop_ids)) |
            (Review.vehicle_id.in_(veh_ids))
        ).order_by(
            Review.created_at.desc()
        ).all()

    return render_template(
        'owner/reviews.html',
        reviews=reviews_list,
        owner=owner
    )


# ============================================================
# OWNER COMPLAINTS
# ============================================================

@owner_bp.route(
    '/complaints',
    methods=['GET', 'POST']
)
@login_required('owner')
def complaints():

    owner = get_current_owner()

    if request.method == 'POST':

        complaint_id = request.form.get(
            'complaint_id',
            type=int
        )

        response_text = request.form.get(
            'owner_response',
            ''
        ).strip()

        comp = db.session.get(
            Complaint,
            complaint_id
        )

        if comp and comp.owner_id == owner.owner_id:

            comp.owner_response = response_text

            comp.status = 'owner_responded'

            db.session.commit()

            flash(
                'Your response to the traveler complaint has been recorded.',
                'success'
            )

        return redirect(
            url_for('owner.complaints')
        )

    complaints_list = Complaint.query.filter_by(
        owner_id=owner.owner_id
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        'owner/complaints.html',
        complaints=complaints_list,
        owner=owner
    )


# ============================================================
# OWNER PROFILE
# ============================================================

@owner_bp.route(
    '/profile',
    methods=['GET', 'POST']
)
@login_required('owner')
def profile():

    owner = get_current_owner()

    user = owner.user

    if request.method == 'POST':

        new_full_name = request.form.get(
            'full_name',
            user.full_name
        ).strip()

        new_phone = request.form.get(
            'phone',
            user.phone
        ).strip()

        new_biz = request.form.get(
            'business_name',
            owner.business_name
        ).strip()

        new_dist = request.form.get(
            'district',
            owner.district
        )

        valid, err = validate_full_name(new_full_name)
        if not valid:
            flash(err, 'danger')
            return redirect(url_for('owner.profile'))

        valid, err, normalized_phone = validate_phone(new_phone)
        if not valid:
            flash(err, 'danger')
            return redirect(url_for('owner.profile'))

        valid, err, cleaned_biz, cleaned_dist = validate_owner_fields(new_biz, new_dist, new_full_name)
        if not valid:
            flash(err, 'danger')
            return redirect(url_for('owner.profile'))

        user.full_name = new_full_name
        user.phone = normalized_phone
        owner.business_name = cleaned_biz
        owner.district = cleaned_dist

        owner.bank_account = request.form.get(
            'bank_account',
            owner.bank_account
        ).strip()

        owner.bio = request.form.get(
            'bio',
            owner.bio
        ).strip()

        db.session.commit()

        session['user_name'] = user.full_name

        flash(
            'Owner profile successfully updated.',
            'success'
        )

        return redirect(
            url_for('owner.profile')
        )

    return render_template(
        'owner/profile.html',
        owner=owner,
        user=user
    )