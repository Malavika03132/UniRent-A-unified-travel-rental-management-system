from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import db, User, Owner, Admin, Property, Vehicle, Booking, Payment, Review, Complaint
from app.routes.auth import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required('admin')
def dashboard():
    total_travelers = User.query.filter_by(role='traveler').count()
    total_owners = User.query.filter_by(role='owner').count()
    total_properties = Property.query.count()
    total_vehicles = Vehicle.query.count()
    total_bookings = Booking.query.count()
    
    payments = Payment.query.filter_by(payment_status='successful').all()
    total_revenue = sum(p.amount for p in payments)
    
    pending_props = Property.query.filter_by(approval_status='pending').count()
    pending_vehs = Vehicle.query.filter_by(approval_status='pending').count()
    pending_approvals = pending_props + pending_vehs
    
    open_complaints = Complaint.query.filter(Complaint.status.in_(['open', 'under_review', 'owner_responded'])).count()
    
    # Recent activity feeds
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_registrations = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_complaints_list = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    
    # Pending approval items
    pending_properties_list = Property.query.filter_by(approval_status='pending').limit(3).all()
    pending_vehicles_list = Vehicle.query.filter_by(approval_status='pending').limit(3).all()
    
    return render_template(
        'admin/dashboard.html',
        stats={
            'travelers': total_travelers,
            'owners': total_owners,
            'properties': total_properties,
            'vehicles': total_vehicles,
            'bookings': total_bookings,
            'revenue': total_revenue,
            'pending_approvals': pending_approvals,
            'open_complaints': open_complaints
        },
        recent_bookings=recent_bookings,
        recent_registrations=recent_registrations,
        recent_complaints=recent_complaints_list,
        pending_properties=pending_properties_list,
        pending_vehicles=pending_vehicles_list
    )


@admin_bp.route('/approvals')
@login_required('admin')
def approvals():
    status_filter = request.args.get('status', 'pending')
    tab = request.args.get('tab', 'all')  # all, properties, vehicles
    
    prop_query = Property.query
    veh_query = Vehicle.query
    
    if status_filter != 'all':
        prop_query = prop_query.filter_by(approval_status=status_filter)
        veh_query = veh_query.filter_by(approval_status=status_filter)
        
    properties_list = prop_query.order_by(Property.created_at.desc()).all()
    vehicles_list = veh_query.order_by(Vehicle.created_at.desc()).all()
    
    pending_count = (
        Property.query.filter_by(approval_status='pending').count() +
        Vehicle.query.filter_by(approval_status='pending').count()
    )
    
    return render_template(
        'admin/approvals.html',
        properties=properties_list,
        vehicles=vehicles_list,
        current_status=status_filter,
        current_tab=tab,
        pending_count=pending_count
    )


@admin_bp.route('/approvals/action', methods=['POST'])
@login_required('admin')
def approval_action():
    item_type = request.form.get('item_type')  # property or vehicle
    item_id = request.form.get('item_id', type=int)
    action = request.form.get('action')  # approve or reject
    reason = request.form.get('rejection_reason', '').strip()
    
    if item_type == 'property':
        item = db.session.get(Property, item_id)
    else:
        item = db.session.get(Vehicle, item_id)
        
    if not item:
        flash('Listing not found.', 'danger')
        return redirect(url_for('admin.approvals'))
        
    if action == 'approve':
        item.approval_status = 'approved'
        item.rejection_reason = None
        flash(f"Listing '{item.property_name if item_type == 'property' else item.vehicle_name}' has been APPROVED and is now live on UniRent!", 'success')
    elif action == 'reject':
        item.approval_status = 'rejected'
        item.rejection_reason = reason or 'Listing details did not meet UniRent heritage quality or safety standards.'
        flash(f"Listing '{item.property_name if item_type == 'property' else item.vehicle_name}' was REJECTED. Reason has been noted.", 'warning')
        
    db.session.commit()
    return redirect(url_for('admin.approvals'))


@admin_bp.route('/travelers')
@login_required('admin')
def travelers():
    travelers_list = User.query.filter_by(role='traveler').order_by(User.created_at.desc()).all()
    return render_template('admin/travelers.html', travelers=travelers_list)


@admin_bp.route('/owners')
@login_required('admin')
def owners():
    owners_list = Owner.query.order_by(Owner.created_at.desc()).all()
    return render_template('admin/owners.html', owners=owners_list)


@admin_bp.route('/properties')
@login_required('admin')
def properties():
    props = Property.query.order_by(Property.created_at.desc()).all()
    return render_template('admin/properties.html', properties=props)


@admin_bp.route('/vehicles')
@login_required('admin')
def vehicles():
    vehs = Vehicle.query.order_by(Vehicle.created_at.desc()).all()
    return render_template('admin/vehicles.html', vehicles=vehs)


@admin_bp.route('/bookings')
@login_required('admin')
def bookings():
    bookings_list = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings_list)


@admin_bp.route('/payments')
@login_required('admin')
def payments():
    payments_list = Payment.query.order_by(Payment.payment_date.desc()).all()
    total_vol = sum(p.amount for p in payments_list if p.payment_status == 'successful')
    return render_template('admin/payments.html', payments=payments_list, total_volume=total_vol)


@admin_bp.route('/complaints', methods=['GET', 'POST'])
@login_required('admin')
def complaints():
    if request.method == 'POST':
        comp_id = request.form.get('complaint_id', type=int)
        admin_action = request.form.get('action')  # resolve, reject, review
        admin_note = request.form.get('admin_response', '').strip()
        
        comp = db.session.get(Complaint, comp_id)
        if comp:
            comp.admin_response = admin_note
            if admin_action == 'resolve':
                comp.status = 'resolved'
                comp.resolved_at = datetime.utcnow()
                flash(f"Complaint {comp.complaint_reference} marked as RESOLVED.", 'success')
            elif admin_action == 'reject':
                comp.status = 'rejected'
                flash(f"Complaint {comp.complaint_reference} marked as REJECTED.", 'warning')
            elif admin_action == 'review':
                comp.status = 'under_review'
                flash(f"Complaint {comp.complaint_reference} placed under active investigation.", 'info')
            db.session.commit()
        return redirect(url_for('admin.complaints'))
        
    complaints_list = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin/complaints.html', complaints=complaints_list)


@admin_bp.route('/reports')
@login_required('admin')
def reports():
    total_bookings = Booking.query.count()
    completed_bookings = Booking.query.filter_by(booking_status='completed').count()
    
    ernakulam_props = Property.query.filter_by(district='Ernakulam', approval_status='approved').count()
    thrissur_props = Property.query.filter_by(district='Thrissur', approval_status='approved').count()
    
    ernakulam_vehs = Vehicle.query.filter_by(district='Ernakulam', approval_status='approved').count()
    thrissur_vehs = Vehicle.query.filter_by(district='Thrissur', approval_status='approved').count()
    
    cars_count = Vehicle.query.filter_by(vehicle_type='car', approval_status='approved').count()
    bikes_count = Vehicle.query.filter_by(vehicle_type='bike', approval_status='approved').count()
    scooters_count = Vehicle.query.filter_by(vehicle_type='scooter', approval_status='approved').count()
    
    return render_template(
        'admin/reports.html',
        stats={
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'ernakulam_props': ernakulam_props,
            'thrissur_props': thrissur_props,
            'ernakulam_vehs': ernakulam_vehs,
            'thrissur_vehs': thrissur_vehs,
            'cars_count': cars_count,
            'bikes_count': bikes_count,
            'scooters_count': scooters_count
        }
    )
