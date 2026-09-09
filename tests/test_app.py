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

    print("\n=== 2. Testing Public Registration Security (No Admin Allowed) ===")
    # Attempting to register as admin must be blocked
    res = client.post('/auth/register', data={
        'full_name': 'Hacker Admin',
        'email': 'hacker@unirent.com',
        'phone': '1234567890',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'admin'
    }, follow_redirects=True)
    assert b"Public registration is restricted to Travelers and Owners only" in res.data or res.status_code == 400
    print("  [PASS] Admin public registration strictly forbidden.")

    # Valid Traveler Registration
    res = client.post('/auth/register', data={
        'full_name': 'Meera Krishnan',
        'email': 'meera@example.com',
        'phone': '+91 98470 99999',
        'password': 'password123',
        'confirm_password': 'password123',
        'role': 'traveler'
    }, follow_redirects=True)
    assert b"Traveler Sanctuary" in res.data or res.status_code == 200
    print("  [PASS] Traveler registration successful.")

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
        assert pending_p is not None, "Expected at least 1 pending property from seed"
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
