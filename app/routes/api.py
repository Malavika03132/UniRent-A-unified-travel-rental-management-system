from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.models import db, User, Owner, Property, Vehicle, Booking, Payment, Review, Complaint

api_bp = Blueprint('api', __name__)

@api_bp.route('/properties', methods=['GET'])
def get_properties():
    district = request.args.get('district')
    p_type = request.args.get('type')
    max_price = request.args.get('max_price', type=float)
    
    query = Property.query.filter_by(approval_status='approved')
    if district:
        query = query.filter_by(district=district)
    if p_type:
        query = query.filter(Property.property_type.ilike(f"%{p_type}%"))
    if max_price:
        query = query.filter(Property.price_per_night <= max_price)
        
    items = query.all()
    return jsonify({
        'success': True,
        'count': len(items),
        'properties': [p.to_dict() for p in items]
    })


@api_bp.route('/properties/<int:property_id>', methods=['GET'])
def get_property(property_id):
    p = db.session.get(Property, property_id)
    if not p:
        return jsonify({'success': False, 'error': 'Property not found'}), 404
    return jsonify({'success': True, 'property': p.to_dict()})


@api_bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    district = request.args.get('district')
    v_type = request.args.get('type')
    
    query = Vehicle.query.filter_by(approval_status='approved')
    if district:
        query = query.filter_by(district=district)
    if v_type:
        query = query.filter_by(vehicle_type=v_type)
        
    items = query.all()
    return jsonify({
        'success': True,
        'count': len(items),
        'vehicles': [v.to_dict() for v in items]
    })


@api_bp.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        return jsonify({'success': False, 'error': 'Vehicle not found'}), 404
    return jsonify({'success': True, 'vehicle': v.to_dict()})


@api_bp.route('/bookings', methods=['POST'])
def create_booking():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Please log in to make a booking'
        }), 401

    data = request.get_json() or request.form

    listing_type = data.get('listing_type', 'property')
    item_id = int(data.get('item_id', 0))
    start_str = data.get('start_date')
    end_str = data.get('end_date')
    special_requests = data.get('special_requests', '')

    # --------------------------------------------------
    # VALIDATE DATES
    # --------------------------------------------------

    try:
        start_date = datetime.strptime(
            start_str,
            '%Y-%m-%d'
        ).date()

        end_date = datetime.strptime(
            end_str,
            '%Y-%m-%d'
        ).date()

        if end_date <= start_date:
            return jsonify({
                'success': False,
                'error': 'Check-out/return date must be after check-in date'
            }), 400

        days = (end_date - start_date).days

    except Exception:
        return jsonify({
            'success': False,
            'error': 'Invalid dates provided'
        }), 400

    # --------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------

    owner_id = None
    rate = 0.0

    property_id = None
    vehicle_id = None

    # Security deposit is ONLY for vehicles
    security_deposit = 0.0

    # --------------------------------------------------
    # PROPERTY
    # --------------------------------------------------

    if listing_type == 'property':

        prop = db.session.get(Property, item_id)

        if not prop:
            return jsonify({
                'success': False,
                'error': 'Property not found'
            }), 404

        owner_id = prop.owner_id
        rate = float(prop.price_per_night)
        property_id = prop.property_id

        # No security deposit for properties
        security_deposit = 0.0

    # --------------------------------------------------
    # VEHICLE
    # --------------------------------------------------

    elif listing_type == 'vehicle':

        veh = db.session.get(Vehicle, item_id)

        if not veh:
            return jsonify({
                'success': False,
                'error': 'Vehicle not found'
            }), 404

        owner_id = veh.owner_id
        rate = float(veh.price_per_day)
        vehicle_id = veh.vehicle_id

        # Get vehicle-specific security deposit
        # Default = ₹2,000
        security_deposit = float(
            veh.security_deposit or 2000.0
        )

    else:

        return jsonify({
            'success': False,
            'error': 'Invalid listing type'
        }), 400

    # --------------------------------------------------
    # CALCULATE AMOUNTS
    # --------------------------------------------------

    # Rental amount
    subtotal = rate * days

    # 5% service fee
    service_fee = round(
        subtotal * 0.05,
        2
    )

    # 12% tax
    tax = round(
        subtotal * 0.12,
        2
    )

    # Final total
    #
    # Property:
    # subtotal + service fee + tax
    #
    # Vehicle:
    # subtotal + service fee + tax + security deposit

    total_amount = round(
        subtotal
        + service_fee
        + tax
        + security_deposit,
        2
    )

    # --------------------------------------------------
    # BOOKING REFERENCE
    # --------------------------------------------------

    ref = (
        f"UR-{datetime.utcnow().year}-"
        f"B{int(datetime.utcnow().timestamp()) % 100000:05d}"
    )

    # --------------------------------------------------
    # CREATE BOOKING
    # --------------------------------------------------

    booking = Booking(
        booking_reference=ref,

        user_id=user_id,
        owner_id=owner_id,

        listing_type=listing_type,

        property_id=property_id,
        vehicle_id=vehicle_id,

        start_date=start_date,
        end_date=end_date,

        total_days=days,
        daily_rate=rate,

        service_fee=service_fee,
        tax_amount=tax,

        # Security deposit
        # 0 for property
        # Vehicle-specific amount for vehicle
        security_deposit=security_deposit,

        total_amount=total_amount,

        booking_status='pending',

        special_requests=special_requests
    )

    db.session.add(booking)
    db.session.commit()

    # --------------------------------------------------
    # RESPONSE
    # --------------------------------------------------

    return jsonify({
        'success': True,

        'message': (
            'Booking created successfully. '
            'Please proceed to payment.'
        ),

        'booking_reference': ref,

        'booking_id': booking.booking_id,

        'listing_type': listing_type,

        'days': days,

        'daily_rate': rate,

        'subtotal': round(
            subtotal,
            2
        ),

        'service_fee': service_fee,

        'tax': tax,

        'security_deposit': security_deposit,

        'total_amount': total_amount,

        'redirect_url': (
            f"/payment?"
            f"booking_id={booking.booking_id}"
            f"&ref={ref}"
        )
    }), 201

@api_bp.route('/reviews', methods=['POST'])
def add_review():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Login required'}), 401
        
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    rating = int(data.get('rating', 5))
    title = data.get('review_title', '')
    text = data.get('review_text', '')
    
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.user_id != user_id:
        return jsonify({'success': False, 'error': 'Invalid booking'}), 403
        
    existing = Review.query.filter_by(booking_id=booking_id).first()
    if existing:
        return jsonify({'success': False, 'error': 'Review already submitted'}), 400
        
    rev = Review(
        booking_id=booking_id,
        user_id=user_id,
        listing_type=booking.listing_type,
        property_id=booking.property_id,
        vehicle_id=booking.vehicle_id,
        rating=rating,
        review_title=title,
        review_text=text
    )
    db.session.add(rev)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review published!', 'review': rev.to_dict()})
