from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from datetime import datetime
from app.models import db, Property, Vehicle, Review, Booking, Payment, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Only show approved properties and vehicles
    featured_stays = Property.query.filter_by(approval_status='approved').order_by(Property.featured.desc(), Property.property_id.desc()).limit(6).all()
    popular_vehicles = Vehicle.query.filter_by(approval_status='approved').order_by(Vehicle.featured.desc(), Vehicle.vehicle_id.desc()).limit(6).all()
    recent_reviews = Review.query.order_by(Review.review_id.desc()).limit(4).all()
    
    # Counts for social proof
    stays_count = Property.query.filter_by(approval_status='approved').count()
    vehicles_count = Vehicle.query.filter_by(approval_status='approved').count()
    
    return render_template(
        'index.html',
        featured_stays=featured_stays,
        popular_vehicles=popular_vehicles,
        recent_reviews=recent_reviews,
        stays_count=stays_count,
        vehicles_count=vehicles_count
    )


@main_bp.route('/stays')
def stays():
    district = request.args.get('district', '').strip()
    property_type = request.args.get('type', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    guests = request.args.get('guests', type=int)
    sort_by = request.args.get('sort', 'newest').strip()
    search_q = request.args.get('q', '').strip()
    
    query = Property.query.filter_by(approval_status='approved')
    
    if district and district in ['Ernakulam', 'Thrissur']:
        query = query.filter(Property.district == district)
    if property_type:
        query = query.filter(Property.property_type.ilike(f"%{property_type}%"))
    if min_price is not None:
        query = query.filter(Property.price_per_night >= min_price)
    if max_price is not None:
        query = query.filter(Property.price_per_night <= max_price)
    if guests:
        query = query.filter(Property.guest_capacity >= guests)
    if search_q:
        query = query.filter(
            (Property.property_name.ilike(f"%{search_q}%")) |
            (Property.address.ilike(f"%{search_q}%")) |
            (Property.description.ilike(f"%{search_q}%"))
        )
        
    if sort_by == 'price_asc':
        query = query.order_by(Property.price_per_night.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Property.price_per_night.desc())
    elif sort_by == 'rating':
        query = query.order_by(Property.featured.desc(), Property.price_per_night.desc())
    else:
        query = query.order_by(Property.property_id.desc())
        
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


@main_bp.route('/stays/<int:property_id>')
def stay_details(property_id):
    prop = db.session.get(Property, property_id)
    if not prop or (prop.approval_status != 'approved' and session.get('user_role') not in ['admin', 'owner']):
        abort(404)
        
    similar_stays = Property.query.filter(
        Property.approval_status == 'approved',
        Property.property_id != prop.property_id,
        Property.district == prop.district
    ).limit(3).all()
    
    reviews = prop.reviews.order_by(Review.review_id.desc()).all()
    
    return render_template(
        'stay-details.html',
        property=prop,
        similar_stays=similar_stays,
        reviews=reviews
    )


@main_bp.route('/vehicles')
def vehicles():
    district = request.args.get('district', '').strip()
    v_type = request.args.get('type', '').strip().lower()
    delivery = request.args.get('delivery')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest').strip()
    search_q = request.args.get('q', '').strip()
    
    query = Vehicle.query.filter_by(approval_status='approved')
    
    if district and district in ['Ernakulam', 'Thrissur']:
        query = query.filter(Vehicle.district == district)
    if v_type and v_type in ['car', 'bike', 'scooter']:
        query = query.filter(Vehicle.vehicle_type == v_type)
    if delivery == '1':
        query = query.filter(Vehicle.delivery_available.is_(True))
    if min_price is not None:
        query = query.filter(Vehicle.price_per_day >= min_price)
    if max_price is not None:
        query = query.filter(Vehicle.price_per_day <= max_price)
    if search_q:
        query = query.filter(
            (Vehicle.vehicle_name.ilike(f"%{search_q}%")) |
            (Vehicle.model.ilike(f"%{search_q}%")) |
            (Vehicle.pickup_location.ilike(f"%{search_q}%"))
        )
        
    if sort_by == 'price_asc':
        query = query.order_by(Vehicle.price_per_day.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Vehicle.price_per_day.desc())
    else:
        query = query.order_by(Vehicle.vehicle_id.desc())
        
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


@main_bp.route('/vehicles/<int:vehicle_id>')
def vehicle_details(vehicle_id):
    veh = db.session.get(Vehicle, vehicle_id)
    if not veh or (veh.approval_status != 'approved' and session.get('user_role') not in ['admin', 'owner']):
        abort(404)
        
    similar_vehicles = Vehicle.query.filter(
        Vehicle.approval_status == 'approved',
        Vehicle.vehicle_id != veh.vehicle_id,
        Vehicle.vehicle_type == veh.vehicle_type
    ).limit(3).all()
    
    reviews = veh.reviews.order_by(Review.review_id.desc()).all()
    
    return render_template(
        'vehicle-details.html',
        vehicle=veh,
        similar_vehicles=similar_vehicles,
        reviews=reviews
    )


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for reaching out to UniRent. Our Kerala concierge team will contact you shortly.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')


@main_bp.route('/booking')
def booking():
    listing_type = request.args.get('type', 'property')
    item_id = request.args.get('id', type=int)
    
    item = None
    if listing_type == 'property':
        item = db.session.get(Property, item_id)
    elif listing_type == 'vehicle':
        item = db.session.get(Vehicle, item_id)
        
    if not item:
        flash('Please select a valid property or vehicle to book.', 'warning')
        return redirect(url_for('main.stays'))
        
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    
    return render_template(
        'booking.html',
        listing_type=listing_type,
        item=item,
        start_date=start_date,
        end_date=end_date
    )


@main_bp.route('/payment')
def payment():
    booking_id = request.args.get('booking_id', type=int)
    booking_ref = request.args.get('ref')
    
    booking_obj = None
    if booking_id:
        booking_obj = db.session.get(Booking, booking_id)
    elif booking_ref:
        booking_obj = Booking.query.filter_by(booking_reference=booking_ref).first()
        
    if not booking_obj:
        flash('Booking record not found.', 'warning')
        return redirect(url_for('main.index'))
        
    return render_template('payment.html', booking=booking_obj)


@main_bp.route('/confirmation')
def confirmation():
    booking_ref = request.args.get('ref')
    booking_obj = None
    if booking_ref:
        booking_obj = Booking.query.filter_by(booking_reference=booking_ref).first()
        
    if not booking_obj:
        flash('Confirmation details not found.', 'info')
        return redirect(url_for('main.index'))
        
    return render_template('confirmation.html', booking=booking_obj)
