from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import db, User, Booking, Property, Vehicle, Review, Complaint, Payment
from app.routes.auth import login_required

traveler_bp = Blueprint('traveler', __name__)

@traveler_bp.route('/dashboard')
@login_required('traveler')
def dashboard():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)
    
    today = date.today()
    all_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    
    upcoming_bookings = [b for b in all_bookings if b.start_date > today and b.booking_status in ['confirmed', 'pending']]
    active_bookings = [b for b in all_bookings if b.start_date <= today <= b.end_date and b.booking_status == 'active']
    completed_bookings = [b for b in all_bookings if b.booking_status == 'completed']
    
    total_spent = sum(b.total_amount for b in all_bookings if b.booking_status in ['confirmed', 'active', 'completed'])
    
    # Recommended stays and vehicles
    recommended_stays = Property.query.filter_by(approval_status='approved', featured=True).limit(3).all()
    if not recommended_stays:
        recommended_stays = Property.query.filter_by(approval_status='approved').limit(3).all()
        
    recommended_vehicles = Vehicle.query.filter_by(approval_status='approved').limit(3).all()
    
    recent_reviews = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc()).limit(3).all()
    recent_complaints = Complaint.query.filter_by(user_id=user_id).order_by(Complaint.created_at.desc()).limit(3).all()
    
    next_upcoming = upcoming_bookings[0] if upcoming_bookings else None
    
    return render_template(
        'traveler/dashboard.html',
        user=user,
        stats={
            'upcoming': len(upcoming_bookings),
            'active': len(active_bookings),
            'completed': len(completed_bookings),
            'total_spent': total_spent
        },
        next_upcoming=next_upcoming,
        recent_bookings=all_bookings[:5],
        recommended_stays=recommended_stays,
        recommended_vehicles=recommended_vehicles,
        recent_reviews=recent_reviews,
        recent_complaints=recent_complaints
    )


@traveler_bp.route('/bookings')
@login_required('traveler')
def bookings():
    user_id = session.get('user_id')
    status_filter = request.args.get('status', 'all')
    
    query = Booking.query.filter_by(user_id=user_id)
    if status_filter != 'all':
        query = query.filter_by(booking_status=status_filter)
        
    bookings_list = query.order_by(Booking.created_at.desc()).all()
    
    return render_template(
        'traveler/bookings.html',
        bookings=bookings_list,
        current_status=status_filter
    )


@traveler_bp.route('/reviews', methods=['GET', 'POST'])
@login_required('traveler')
def reviews():
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        booking_id = request.form.get('booking_id', type=int)
        rating = request.form.get('rating', type=int)
        title = request.form.get('review_title', '').strip()
        review_text = request.form.get('review_text', '').strip()
        
        booking_obj = db.session.get(Booking, booking_id)
        if not booking_obj or booking_obj.user_id != user_id:
            flash('Booking not found or not authorized.', 'danger')
            return redirect(url_for('traveler.reviews'))
            
        existing_rev = Review.query.filter_by(booking_id=booking_id).first()
        if existing_rev:
            flash('You have already submitted a review for this booking.', 'info')
            return redirect(url_for('traveler.reviews'))
            
        new_review = Review(
            booking_id=booking_id,
            user_id=user_id,
            listing_type=booking_obj.listing_type,
            property_id=booking_obj.property_id,
            vehicle_id=booking_obj.vehicle_id,
            rating=rating or 5,
            review_title=title or 'Memorable Kerala Experience',
            review_text=review_text,
            image_url=None
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Thank you for sharing your review!', 'success')
        return redirect(url_for('traveler.reviews'))
        
    my_reviews = Review.query.filter_by(user_id=user_id).order_by(Review.created_at.desc()).all()
    # Bookings eligible for review (completed bookings with no review yet)
    eligible_bookings = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.booking_status == 'completed',
        ~Booking.booking_id.in_([r.booking_id for r in my_reviews])
    ).all()
    
    return render_template(
        'traveler/reviews.html',
        reviews=my_reviews,
        eligible_bookings=eligible_bookings
    )


@traveler_bp.route('/complaints', methods=['GET', 'POST'])
@login_required('traveler')
def complaints():
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        booking_id = request.form.get('booking_id', type=int)
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '').strip()
        
        booking_obj = db.session.get(Booking, booking_id)
        if not booking_obj or booking_obj.user_id != user_id:
            flash('Invalid booking selected.', 'danger')
            return redirect(url_for('traveler.complaints'))
            
        ref = f"CMP-{date.today().year}-{Booking.query.count() + 101}"
        new_complaint = Complaint(
            complaint_reference=ref,
            booking_id=booking_id,
            user_id=user_id,
            owner_id=booking_obj.owner_id,
            category=category,
            description=description,
            status='open'
        )
        db.session.add(new_complaint)
        db.session.commit()
        flash(f'Complaint ticket {ref} filed successfully. Our support & owner will review promptly.', 'success')
        return redirect(url_for('traveler.complaints'))
        
    my_complaints = Complaint.query.filter_by(user_id=user_id).order_by(Complaint.created_at.desc()).all()
    user_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    
    return render_template(
        'traveler/complaints.html',
        complaints=my_complaints,
        bookings=user_bookings
    )


@traveler_bp.route('/payments')
@login_required('traveler')
def payments():
    user_id = session.get('user_id')
    user_bookings = Booking.query.filter_by(user_id=user_id).all()
    booking_ids = [b.booking_id for b in user_bookings]
    
    payments_list = Payment.query.filter(Payment.booking_id.in_(booking_ids)).order_by(Payment.payment_date.desc()).all() if booking_ids else []
    
    return render_template(
        'traveler/payments.html',
        payments=payments_list
    )


@traveler_bp.route('/profile', methods=['GET', 'POST'])
@login_required('traveler')
def profile():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.phone = request.form.get('phone', user.phone).strip()
        db.session.commit()
        session['user_name'] = user.full_name
        flash('Your profile details have been updated.', 'success')
        return redirect(url_for('traveler.profile'))
        
    return render_template('traveler/profile.html', user=user)
