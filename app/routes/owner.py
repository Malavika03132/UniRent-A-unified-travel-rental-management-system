import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, jsonify
from app.models import db, User, Owner, Property, Vehicle, Booking, Payment, Review, Complaint
from app.routes.auth import login_required

owner_bp = Blueprint('owner', __name__)

def get_current_owner():
    user_id = session.get('user_id')
    owner = Owner.query.filter_by(user_id=user_id).first()
    if not owner:
        # Auto-create owner profile if user has role owner
        user = db.session.get(User, user_id)
        if user and user.role == 'owner':
            owner = Owner(user_id=user_id, business_name=f"{user.full_name}'s Heritage Rentals", district='Ernakulam')
            db.session.add(owner)
            db.session.commit()
    return owner


@owner_bp.route('/dashboard')
@login_required('owner')
def dashboard():
    owner = get_current_owner()
    if not owner:
        flash('Owner profile required.', 'danger')
        return redirect(url_for('auth.login'))
        
    properties = Property.query.filter_by(owner_id=owner.owner_id).all()
    vehicles = Vehicle.query.filter_by(owner_id=owner.owner_id).all()
    
    prop_ids = [p.property_id for p in properties]
    veh_ids = [v.vehicle_id for v in vehicles]
    
    # Bookings for this owner
    bookings = Booking.query.filter_by(owner_id=owner.owner_id).order_by(Booking.created_at.desc()).all()
    active_bookings = [b for b in bookings if b.booking_status in ['active', 'confirmed']]
    
    total_revenue = sum(b.total_amount for b in bookings if b.booking_status in ['confirmed', 'active', 'completed'])
    
    # Complaints against owner's listings
    complaints = Complaint.query.filter_by(owner_id=owner.owner_id).order_by(Complaint.created_at.desc()).all()
    open_complaints = [c for c in complaints if c.status in ['open', 'under_review']]
    
    # Reviews
    reviews = []
    if prop_ids or veh_ids:
        reviews = Review.query.filter(
            (Review.property_id.in_(prop_ids)) | (Review.vehicle_id.in_(veh_ids))
        ).order_by(Review.created_at.desc()).limit(5).all()
        
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


@owner_bp.route('/properties')
@login_required('owner')
def properties():
    owner = get_current_owner()
    properties_list = Property.query.filter_by(owner_id=owner.owner_id).order_by(Property.created_at.desc()).all()
    return render_template('owner/properties.html', properties=properties_list, owner=owner)


@owner_bp.route('/add-property', methods=['GET', 'POST'])
@login_required('owner')
def add_property():
    owner = get_current_owner()
    if request.method == 'POST':
        name = request.form.get('property_name', '').strip()
        prop_type = request.form.get('property_type', 'Heritage Villa')
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        district = request.form.get('district', 'Ernakulam')
        lat = request.form.get('latitude', type=float) or 9.9312
        lng = request.form.get('longitude', type=float) or 76.2673
        price = request.form.get('price_per_night', type=float) or 4500.0
        guests = request.form.get('guest_capacity', type=int) or 4
        bedrooms = request.form.get('bedrooms', type=int) or 2
        bathrooms = request.form.get('bathrooms', type=int) or 2
        image_url = request.form.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80'
        
        # Amenities list
        selected_amenities = request.form.getlist('amenities')
        
        slug = f"{name.lower().replace(' ', '-')}-{int(datetime.utcnow().timestamp())}"
        
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
            amenities=json.dumps(selected_amenities),
            images=json.dumps([image_url]),
            featured_image=image_url,
            approval_status='pending',  # Enforces Admin Approval
            availability_status='available',
            featured=False
        )
        db.session.add(new_prop)
        db.session.commit()
        
        flash(f"Property '{name}' submitted! Status: PENDING ADMIN APPROVAL. An administrator will review it before publication.", 'info')
        return redirect(url_for('owner.properties'))
        
    return render_template('owner/add_property.html', owner=owner)


@owner_bp.route('/vehicles')
@login_required('owner')
def vehicles():
    owner = get_current_owner()
    vehicles_list = Vehicle.query.filter_by(owner_id=owner.owner_id).order_by(Vehicle.created_at.desc()).all()
    return render_template('owner/vehicles.html', vehicles=vehicles_list, owner=owner)


@owner_bp.route('/add-vehicle', methods=['GET', 'POST'])
@login_required('owner')
def add_vehicle():
    owner = get_current_owner()
    if request.method == 'POST':
        name = request.form.get('vehicle_name', '').strip()
        model = request.form.get('model', '').strip()
        v_type = request.form.get('vehicle_type', 'car').lower()
        description = request.form.get('description', '').strip()
        price = request.form.get('price_per_day', type=float) or 1500.0
        district = request.form.get('district', 'Ernakulam')
        pickup = request.form.get('pickup_location', '').strip()
        delivery = bool(request.form.get('delivery_available'))
        lat = request.form.get('latitude', type=float) or 9.9312
        lng = request.form.get('longitude', type=float) or 76.2673
        image_url = request.form.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=1200&q=80'
        
        specs = {
            'transmission': request.form.get('spec_transmission', 'Manual'),
            'fuel': request.form.get('spec_fuel', 'Petrol'),
            'seats': request.form.get('spec_seats', '5'),
            'mileage': request.form.get('spec_mileage', '18 kmpl')
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
            approval_status='pending',  # Enforces Admin Approval
            availability_status='available',
            featured=False
        )
        db.session.add(new_veh)
        db.session.commit()
        
        flash(f"Vehicle '{name}' submitted! Status: PENDING ADMIN APPROVAL.", 'info')
        return redirect(url_for('owner.vehicles'))
        
    return render_template('owner/add_vehicle.html', owner=owner)


@owner_bp.route('/bookings')
@login_required('owner')
def bookings():
    owner = get_current_owner()
    owner_bookings = Booking.query.filter_by(owner_id=owner.owner_id).order_by(Booking.created_at.desc()).all()
    return render_template('owner/bookings.html', bookings=owner_bookings, owner=owner)


@owner_bp.route('/payments')
@login_required('owner')
def payments():
    owner = get_current_owner()
    bookings = Booking.query.filter_by(owner_id=owner.owner_id).all()
    b_ids = [b.booking_id for b in bookings]
    payments_list = Payment.query.filter(Payment.booking_id.in_(b_ids)).order_by(Payment.payment_date.desc()).all() if b_ids else []
    
    total_gross = sum(p.amount for p in payments_list if p.payment_status == 'successful')
    platform_fee = total_gross * 0.10  # 10% platform fee
    net_payout = total_gross - platform_fee
    
    return render_template(
        'owner/payments.html',
        payments=payments_list,
        owner=owner,
        total_gross=total_gross,
        platform_fee=platform_fee,
        net_payout=net_payout
    )


@owner_bp.route('/reviews')
@login_required('owner')
def reviews():
    owner = get_current_owner()
    props = Property.query.filter_by(owner_id=owner.owner_id).all()
    vehs = Vehicle.query.filter_by(owner_id=owner.owner_id).all()
    
    prop_ids = [p.property_id for p in props]
    veh_ids = [v.vehicle_id for v in vehs]
    
    reviews_list = []
    if prop_ids or veh_ids:
        reviews_list = Review.query.filter(
            (Review.property_id.in_(prop_ids)) | (Review.vehicle_id.in_(veh_ids))
        ).order_by(Review.created_at.desc()).all()
        
    return render_template('owner/reviews.html', reviews=reviews_list, owner=owner)


@owner_bp.route('/complaints', methods=['GET', 'POST'])
@login_required('owner')
def complaints():
    owner = get_current_owner()
    
    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id', type=int)
        response_text = request.form.get('owner_response', '').strip()
        
        comp = db.session.get(Complaint, complaint_id)
        if comp and comp.owner_id == owner.owner_id:
            comp.owner_response = response_text
            comp.status = 'owner_responded'
            db.session.commit()
            flash('Your response to the traveler complaint has been recorded.', 'success')
        return redirect(url_for('owner.complaints'))
        
    complaints_list = Complaint.query.filter_by(owner_id=owner.owner_id).order_by(Complaint.created_at.desc()).all()
    return render_template('owner/complaints.html', complaints=complaints_list, owner=owner)


@owner_bp.route('/profile', methods=['GET', 'POST'])
@login_required('owner')
def profile():
    owner = get_current_owner()
    user = owner.user
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.phone = request.form.get('phone', user.phone).strip()
        owner.business_name = request.form.get('business_name', owner.business_name).strip()
        owner.district = request.form.get('district', owner.district)
        owner.bank_account = request.form.get('bank_account', owner.bank_account).strip()
        owner.bio = request.form.get('bio', owner.bio).strip()
        db.session.commit()
        session['user_name'] = user.full_name
        flash('Owner profile successfully updated.', 'success')
        return redirect(url_for('owner.profile'))
        
    return render_template('owner/profile.html', owner=owner, user=user)
