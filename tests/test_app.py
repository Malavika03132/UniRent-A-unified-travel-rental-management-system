import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.models import db, User, Property, Vehicle, Booking

def run_tests():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    print("=== 1. Testing Public Routes ===")
    public_urls = [
        '/',
        '/stays',
        '/stays/1',
        '/vehicles',
        '/vehicles/1',
        '/about',
        '/how-it-works',
        '/contact',
        '/auth/login',
        '/auth/register'
    ]
    for url in public_urls:
        res = client.get(url)
        assert res.status_code == 200, f"Expected 200 for {url}, got {res.status_code}"
        print(f"  [PASS] GET {url} -> 200 OK")

    print("\n=== 2. Testing Registration Security & Validations ===")
    # 2.1 Attempting to register as admin must be blocked
    res = client.post('/auth/register', data={
        'full_name': 'Hacker Admin',
        'email': 'hacker@unirent.com',
        'phone': '+91 98470 12345',
        'password': 'password123',
        'confirm_password': 'password123',
        'kyc_document_type': 'pan_card',
        'kyc_document_number': 'ABCDE1234F',
        'role': 'admin'
    }, follow_redirects=True)
    assert b"Public registration is restricted to Travelers and Owners only" in res.data or res.status_code == 400
    print("  [PASS] Admin public registration strictly forbidden.")

    # 2.2 Validation: Invalid PAN Card format
    res = client.post('/auth/register', data={
        'full_name': 'Meera Krishnan',
        'email': 'meera_bad_pan@example.com',
        'phone': '+91 98470 99999',
        'password': 'password123',
        'confirm_password': 'password123',
        'kyc_document_type': 'pan_card',
        'kyc_document_number': 'INVALID_PAN_123',
        'role': 'traveler'
    }, follow_redirects=True)
    assert b"Invalid PAN Card" in res.data or res.status_code == 400
    print("  [PASS] Invalid PAN Card rejected by KYC validator.")

    # 2.3 Validation: Invalid Indian Phone Number
    res = client.post('/auth/register', data={
        'full_name': 'Meera Krishnan',
        'email': 'meera_bad_phone@example.com',
        'phone': '12345',
        'password': 'password123',
        'confirm_password': 'password123',
        'kyc_document_type': 'pan_card',
        'kyc_document_number': 'ABCDE1234F',
        'role': 'traveler'
    }, follow_redirects=True)
    assert b"valid 10-digit Indian mobile number" in res.data or res.status_code == 400
    print("  [PASS] Invalid phone number rejected by validator.")

    # 2.4 Validation: Password mismatch
    res = client.post('/auth/register', data={
        'full_name': 'Meera Krishnan',
        'email': 'meera_mismatch@example.com',
        'phone': '+91 98470 99999',
        'password': 'password123',
        'confirm_password': 'different_password',
        'kyc_document_type': 'pan_card',
        'kyc_document_number': 'ABCDE1234F',
        'role': 'traveler'
    }, follow_redirects=True)
    assert b"Passwords do not match" in res.data or res.status_code == 400
    print("  [PASS] Password mismatch rejected by validator.")

    # Cleanup any previous test registration emails
    with app.app_context():
        test_emails = ['meera_test@example.com', 'venu_test@example.com', 'meera_bad_pan@example.com', 'meera_bad_phone@example.com', 'meera_mismatch@example.com']
        users_to_del = User.query.filter(User.email.in_(test_emails)).all()
        for u in users_to_del:
            db.session.delete(u)
        db.session.commit()

    # 2.5 Valid Traveler Registration with Verified PAN Card
    res = client.post('/auth/register', data={
        'full_name': 'Meera Krishnan',
        'email': 'meera_test@example.com',
        'phone': '+91 98470 99999',
        'password': 'password123',
        'confirm_password': 'password123',
        'kyc_document_type': 'pan_card',
        'kyc_document_number': 'abcde1234f',  # Test auto-uppercasing
        'role': 'traveler'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Traveler Sanctuary" in res.data
    with app.app_context():
        u = User.query.filter_by(email='meera_test@example.com').first()
        assert u is not None
        assert u.kyc_document_type == 'pan_card'
        assert u.kyc_document_number == 'ABCDE1234F'
        assert u.kyc_status == 'verified'
    print("  [PASS] Valid Traveler registration with PAN Card KYC succeeded.")

    # 2.6 Valid Owner Registration with Verified Passport & Business Info
    client.get('/auth/logout')
    res = client.post('/auth/register', data={
        'full_name': 'Venugopal Varma',
        'email': 'venu_test@example.com',
        'phone': '+91 94470 88888',
        'password': 'password123',
        'confirm_password': 'password123',
        'kyc_document_type': 'passport',
        'kyc_document_number': 'Z1234567',
        'business_name': 'Varma Heritage Palaces & Rides',
        'district': 'Thrissur',
        'role': 'owner'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Host Business Portal" in res.data
    with app.app_context():
        u_owner = User.query.filter_by(email='venu_test@example.com').first()
        assert u_owner is not None
        assert u_owner.kyc_document_type == 'passport'
        assert u_owner.kyc_document_number == 'Z1234567'
        assert u_owner.owner_profile is not None
        assert u_owner.owner_profile.business_name == 'Varma Heritage Palaces & Rides'
        assert u_owner.owner_profile.district == 'Thrissur'
    print("  [PASS] Valid Owner registration with Passport KYC and Business Info succeeded.")

    print("\n=== 3. Testing Role-Based Dashboards & Access Controls ===")
    
    # Traveler Login
    client.get('/auth/logout')
    res = client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Traveler Sanctuary" in res.data
    print("  [PASS] Traveler login -> redirects to Traveler Dashboard.")

    # Traveler accessing Traveler routes
    res = client.get('/traveler/bookings')
    assert res.status_code == 200
    print("  [PASS] GET /traveler/bookings -> 200 OK")

    # Traveler trying to access Admin dashboard -> should be redirected/forbidden
    res = client.get('/admin/dashboard', follow_redirects=True)
    assert b"You do not have permission" in res.data or b"Traveler Sanctuary" in res.data
    print("  [PASS] Traveler blocked from Admin portal.")

    # Owner Login
    client.get('/auth/logout')
    res = client.post('/auth/login', data={'email': 'owner@unirent.com', 'password': 'owner123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Host Business Portal" in res.data
    print("  [PASS] Owner login -> redirects to Owner Dashboard.")

    res = client.get('/owner/properties')
    assert res.status_code == 200
    print("  [PASS] GET /owner/properties -> 200 OK")

    # Admin Login
    client.get('/auth/logout')
    res = client.post('/auth/login', data={'email': 'admin@unirent.com', 'password': 'admin123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Platform Governance" in res.data
    print("  [PASS] Admin login -> redirects to Admin Dashboard.")

    # Admin Approvals
    res = client.get('/admin/approvals')
    assert res.status_code == 200
    assert b"Listing Verification Center" in res.data
    print("  [PASS] GET /admin/approvals -> 200 OK")

    print("\n=== 4. Testing Admin Listing Approval Workflow ===")
    with app.app_context():
        pending_p = Property.query.filter_by(approval_status='pending').first()
        if not pending_p:
            pending_p = Property.query.first()
            if pending_p:
                pending_p.approval_status = 'pending'
                db.session.commit()
        assert pending_p is not None, "Expected at least 1 property for approval testing"
        pending_id = pending_p.property_id
        pending_name = pending_p.property_name

    res = client.post('/admin/approvals/action', data={
        'item_type': 'property',
        'item_id': pending_id,
        'action': 'approve'
    }, follow_redirects=True)
    assert res.status_code == 200
    with app.app_context():
        approved_p = db.session.get(Property, pending_id)
        assert approved_p.approval_status == 'approved', f"Expected approved status, got {approved_p.approval_status}"
    print(f"  [PASS] Admin approved property '{pending_name}' successfully.")

    print("\n=== 5. Testing REST API Endpoints ===")
    res = client.get('/api/properties')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True and data['count'] > 0
    print(f"  [PASS] GET /api/properties returned {data['count']} properties.")

    res = client.get('/api/vehicles')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True and data['count'] > 0
    print(f"  [PASS] GET /api/vehicles returned {data['count']} vehicles.")

    print("\n=== ALL 5 VERIFICATION SUITES PASSED FLAWLESSLY! ===")

if __name__ == '__main__':
    run_tests()
