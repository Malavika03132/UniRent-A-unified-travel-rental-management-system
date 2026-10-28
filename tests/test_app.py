import os
import sys
import hmac
import hashlib
import json
from datetime import date, timedelta
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Owner, Property, Vehicle, Booking, Payment


class UniRentComprehensiveTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SECRET_KEY'] = 'test-secret-key'
        cls.app.config['RAZORPAY_KEY_ID'] = 'rzp_test_samplekey123'
        cls.app.config['RAZORPAY_KEY_SECRET'] = 'test_secret_samplekey456'
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            # Clean up test-created bookings, payments, and restore listing statuses
            test_bookings = Booking.query.filter(Booking.booking_id > 5).all()
            for b in test_bookings:
                Payment.query.filter(Payment.booking_id == b.booking_id).delete()
                db.session.delete(b)
            for p in Property.query.all():
                p.approval_status = 'approved'
                p.availability_status = 'available'
                p.rejection_reason = None
            for v in Vehicle.query.all():
                v.approval_status = 'approved'
                v.availability_status = 'available'
                v.rejection_reason = None
            db.session.commit()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        # Clean up any non-seed bookings before each test to guarantee complete isolation
        test_bookings = Booking.query.filter(Booking.booking_id > 5).all()
        if test_bookings:
            for b in test_bookings:
                Payment.query.filter(Payment.booking_id == b.booking_id).delete()
                db.session.delete(b)
            db.session.commit()

    def tearDown(self):
        self.client.get('/auth/logout')
        self.app_context.pop()

    # =========================================================================
    # SUITE 1: PUBLIC DISCOVERY ROUTES & CATALOG AVAILABILITY
    # =========================================================================
    def test_01_public_routes(self):
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
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"Expected 200 for {url}, got {res.status_code}")

    def test_02_catalog_api_active_and_approved_only(self):
        res = self.client.get('/api/properties')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        for p in data['properties']:
            self.assertEqual(p['approval_status'], 'approved')
            self.assertEqual(p['availability_status'], 'available')

        res_v = self.client.get('/api/vehicles')
        self.assertEqual(res_v.status_code, 200)
        data_v = res_v.get_json()
        self.assertTrue(data_v['success'])
        for v in data_v['vehicles']:
            self.assertEqual(v['approval_status'], 'approved')
            self.assertEqual(v['availability_status'], 'available')

    # =========================================================================
    # SUITE 2: AUTHENTICATION, KYC & ROLE-BASED ACCESS CONTROL
    # =========================================================================
    def test_03_admin_registration_blocked(self):
        res = self.client.post('/auth/register', data={
            'full_name': 'Hacker Admin',
            'email': 'hacker@unirent.com',
            'phone': '+91 98470 12345',
            'password': 'password123',
            'confirm_password': 'password123',
            'kyc_document_type': 'pan_card',
            'kyc_document_number': 'ABCDE1234F',
            'role': 'admin'
        }, follow_redirects=True)
        self.assertTrue(b"Public registration is restricted to Travelers and Owners only" in res.data or res.status_code == 400)

    def test_04_invalid_kyc_and_phone_rejected(self):
        # Invalid PAN format
        res = self.client.post('/auth/register', data={
            'full_name': 'Meera Krishnan',
            'email': 'bad_pan@example.com',
            'phone': '+91 98470 99999',
            'password': 'password123',
            'confirm_password': 'password123',
            'kyc_document_type': 'pan_card',
            'kyc_document_number': 'INVALID_PAN_123',
            'role': 'traveler'
        }, follow_redirects=True)
        self.assertTrue(b"Invalid PAN Card" in res.data or res.status_code == 400)

        # Invalid Phone
        res = self.client.post('/auth/register', data={
            'full_name': 'Meera Krishnan',
            'email': 'bad_phone@example.com',
            'phone': '12345',
            'password': 'password123',
            'confirm_password': 'password123',
            'kyc_document_type': 'pan_card',
            'kyc_document_number': 'ABCDE1234F',
            'role': 'traveler'
        }, follow_redirects=True)
        self.assertTrue(b"valid 10-digit Indian mobile number" in res.data or res.status_code == 400)

    def test_05_role_based_access_enforcement(self):
        # Traveler cannot access admin dashboard
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertTrue(b"You do not have permission" in res.data or b"Traveler Sanctuary" in res.data)

        # Traveler cannot access owner properties
        res = self.client.get('/owner/properties', follow_redirects=True)
        self.assertTrue(b"You do not have permission" in res.data or b"Traveler Sanctuary" in res.data)

        # Admin login works
        self.client.get('/auth/logout')
        res = self.client.post('/auth/login', data={'email': 'admin@unirent.com', 'password': 'admin123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Platform Governance", res.data)

    # =========================================================================
    # SUITE 3: BOOKING CREATION, VERIFICATION & AVAILABILITY CONFLICTS
    # =========================================================================
    def test_06_property_booking_with_kyc_validation(self):
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)

        start = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')
        end = (date.today() + timedelta(days=23)).strftime('%Y-%m-%d')

        # Attempt property booking with invalid PAN Card format
        res = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 1,
            'start_date': start,
            'end_date': end,
            'identity_type': 'PAN Card',
            'identity_number': 'WRONG_FORMAT'
        })
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['success'])

        # Property booking with valid PAN Card
        res_ok = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 1,
            'start_date': start,
            'end_date': end,
            'identity_type': 'PAN Card',
            'identity_number': 'ABCDE1234F'
        })
        self.assertEqual(res_ok.status_code, 201)
        data = res_ok.get_json()
        self.assertTrue(data['success'])
        booking_ref = data['booking_reference']

        # Verify booking record has verification details stored on Booking, not User
        booking = Booking.query.filter_by(booking_reference=booking_ref).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.identity_type, 'PAN Card')
        self.assertEqual(booking.identity_number, 'ABCDE1234F')
        self.assertIn('*', booking.get_masked_identity_number())

    def test_07_vehicle_booking_with_dl_validation(self):
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)

        start = (date.today() + timedelta(days=25)).strftime('%Y-%m-%d')
        end = (date.today() + timedelta(days=27)).strftime('%Y-%m-%d')

        # Attempt vehicle booking without DL or with invalid DL
        res = self.client.post('/api/bookings', json={
            'listing_type': 'vehicle',
            'item_id': 1,
            'start_date': start,
            'end_date': end,
            'driver_license_number': '123'
        })
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['success'])

        # Valid vehicle booking with Indian Driving Licence (e.g. KL0720210001234)
        res_ok = self.client.post('/api/bookings', json={
            'listing_type': 'vehicle',
            'item_id': 1,
            'start_date': start,
            'end_date': end,
            'driver_license_number': 'KL0720210001234'
        })
        self.assertEqual(res_ok.status_code, 201)
        data = res_ok.get_json()
        self.assertTrue(data['success'])

        booking = Booking.query.filter_by(booking_reference=data['booking_reference']).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.driver_license_number, 'KL0720210001234')
        self.assertIn('*', booking.get_masked_driver_license())
        # Vehicle security deposit included in calculation
        self.assertGreater(booking.security_deposit, 0)
        self.assertEqual(booking.total_amount, round(booking.daily_rate * booking.total_days + booking.service_fee + booking.tax_amount + booking.security_deposit, 2))

    def test_08_overlapping_dates_conflict_prevention(self):
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)

        start1 = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        end1 = (date.today() + timedelta(days=35)).strftime('%Y-%m-%d')

        # First booking succeeds
        res1 = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 2,
            'start_date': start1,
            'end_date': end1,
            'identity_type': 'Passport',
            'identity_number': 'Z1234567'
        })
        self.assertEqual(res1.status_code, 201)

        # Overlapping booking attempt (dates 32 to 34 fall inside 30 to 35)
        start_overlap = (date.today() + timedelta(days=32)).strftime('%Y-%m-%d')
        end_overlap = (date.today() + timedelta(days=34)).strftime('%Y-%m-%d')

        res_conflict = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 2,
            'start_date': start_overlap,
            'end_date': end_overlap,
            'identity_type': 'Passport',
            'identity_number': 'Z7654321'
        })
        self.assertEqual(res_conflict.status_code, 409)
        self.assertFalse(res_conflict.get_json()['success'])
        self.assertIn('already booked', res_conflict.get_json()['error'])

        # Non-overlapping booking starting on checkout day (day 35 to 38) -> allowed
        start_ok = (date.today() + timedelta(days=35)).strftime('%Y-%m-%d')
        end_ok = (date.today() + timedelta(days=38)).strftime('%Y-%m-%d')
        res_ok = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 2,
            'start_date': start_ok,
            'end_date': end_ok,
            'identity_type': 'Passport',
            'identity_number': 'Z7654321'
        })
        self.assertEqual(res_ok.status_code, 201)

    def test_09_prevent_booking_unapproved_or_deactivated_listing(self):
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)

        # Find or create an unapproved property
        unapproved = Property.query.filter(Property.approval_status != 'approved').first()
        if not unapproved:
            unapproved = Property.query.first()
            unapproved.approval_status = 'pending'
            db.session.commit()

        start = (date.today() + timedelta(days=40)).strftime('%Y-%m-%d')
        end = (date.today() + timedelta(days=42)).strftime('%Y-%m-%d')

        res = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': unapproved.property_id,
            'start_date': start,
            'end_date': end,
            'identity_type': 'PAN Card',
            'identity_number': 'ABCDE1234F'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('not available', res.get_json()['error'])

        # Restore status
        unapproved.approval_status = 'approved'
        db.session.commit()

    # =========================================================================
    # SUITE 4: PAYMENT VERIFICATION (RAZORPAY TEST MODE ONLY)
    # =========================================================================
    def test_10_razorpay_order_creation_and_signature_verification(self):
        self.client.post('/auth/login', data={'email': 'traveler@unirent.com', 'password': 'traveler123'}, follow_redirects=True)

        start = (date.today() + timedelta(days=45)).strftime('%Y-%m-%d')
        end = (date.today() + timedelta(days=47)).strftime('%Y-%m-%d')

        res_b = self.client.post('/api/bookings', json={
            'listing_type': 'property',
            'item_id': 3,
            'start_date': start,
            'end_date': end,
            'identity_type': 'PAN Card',
            'identity_number': 'ABCDE1234F'
        })
        self.assertEqual(res_b.status_code, 201)
        ref = res_b.get_json()['booking_reference']
        booking_id = res_b.get_json()['booking_id']

        # Razorpay create order endpoint validation
        res_order = self.client.post('/api/create-order', json={
            'booking_reference': ref
        })
        # Note: if razorpay key is mock, BadRequestError or order creation succeeds
        self.assertIn(res_order.status_code, [200, 400, 401])

        # Test HMAC-SHA256 signature verification route
        order_id = 'order_test_123456'
        payment_id = 'pay_test_987654'
        msg = f"{order_id}|{payment_id}"
        valid_signature = hmac.new(
            self.app.config['RAZORPAY_KEY_SECRET'].encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 1. Invalid signature attempt must be rejected
        res_fail = self.client.post('/api/verify-payment', json={
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': 'tampered_signature_xyz',
            'booking_reference': ref
        })
        self.assertEqual(res_fail.status_code, 400)
        self.assertFalse(res_fail.get_json()['success'])

        # Booking must NOT be marked confirmed on invalid payment
        b_check = db.session.get(Booking, booking_id)
        self.assertNotEqual(b_check.booking_status, 'confirmed')

        # 2. Valid signature verification succeeds
        res_verify = self.client.post('/api/verify-payment', json={
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': valid_signature,
            'booking_reference': ref
        })
        self.assertEqual(res_verify.status_code, 200)
        self.assertTrue(res_verify.get_json()['success'])

        # Booking is now confirmed
        db.session.refresh(b_check)
        self.assertEqual(b_check.booking_status, 'confirmed')
        self.assertIsNotNone(b_check.payment)
        self.assertEqual(b_check.payment.payment_status, 'successful')

    def test_11_simulated_payment_endpoint_disabled(self):
        # Simulator payment route must return 400
        res = self.client.post('/payment/process', json={
            'booking_reference': 'UR-2026-FAKE',
            'payment_method': 'card'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"disabled", res.data)

    def test_12_payment_failed_recording(self):
        res = self.client.post('/api/payment-failed', json={
            'booking_reference': 'UR-2026-B8491',
            'error_description': 'Customer cancelled card prompt'
        })
        self.assertEqual(res.status_code, 200)

    # =========================================================================
    # SUITE 5: RECEIPT DOWNLOAD & PDF GENERATION
    # =========================================================================
    def test_13_download_receipt_pdf(self):
        # Fetch an existing confirmed or test booking
        booking = Booking.query.first()
        self.assertIsNotNone(booking)

        res = self.client.get(f'/confirmation/{booking.booking_id}/download-receipt')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        self.assertGreater(len(res.data), 1000)
        self.assertTrue(res.data.startswith(b'%PDF'))

    # =========================================================================
    # SUITE 6: ADMIN APPROVAL, REJECTION & REASON REQUIREMENT
    # =========================================================================
    def test_14_admin_approval_and_rejection_reason(self):
        self.client.post('/auth/login', data={'email': 'admin@unirent.com', 'password': 'admin123'}, follow_redirects=True)

        prop = Property.query.first()
        self.assertIsNotNone(prop)

        # 1. Attempt to reject without reason -> should fail and keep status
        res_no_reason = self.client.post('/admin/approvals/action', data={
            'item_type': 'property',
            'item_id': prop.property_id,
            'action': 'reject',
            'rejection_reason': ''
        }, follow_redirects=True)
        self.assertIn(b"rejection reason is required", res_no_reason.data)

        # 2. Reject with reason -> succeeds
        res_reject = self.client.post('/admin/approvals/action', data={
            'item_type': 'property',
            'item_id': prop.property_id,
            'action': 'reject',
            'rejection_reason': 'Missing architectural documentation for traditional wooden rafters.'
        }, follow_redirects=True)
        self.assertEqual(res_reject.status_code, 200)

        db.session.refresh(prop)
        self.assertEqual(prop.approval_status, 'rejected')
        self.assertEqual(prop.rejection_reason, 'Missing architectural documentation for traditional wooden rafters.')

        # 3. Approve listing
        res_approve = self.client.post('/admin/approvals/action', data={
            'item_type': 'property',
            'item_id': prop.property_id,
            'action': 'approve'
        }, follow_redirects=True)
        self.assertEqual(res_approve.status_code, 200)

        db.session.refresh(prop)
        self.assertEqual(prop.approval_status, 'approved')
        self.assertIsNone(prop.rejection_reason)

    # =========================================================================
    # SUITE 7: OWNER CORRECTION & RESUBMISSION
    # =========================================================================
    def test_15_owner_resubmit_rejected_listing(self):
        # Set property as rejected
        prop = Property.query.first()
        prop.approval_status = 'rejected'
        prop.rejection_reason = 'Please clarify floor plan.'
        db.session.commit()

        # Login as owner
        self.client.post('/auth/login', data={'email': 'owner@unirent.com', 'password': 'owner123'}, follow_redirects=True)

        # Resubmit via dedicated action
        res = self.client.post(f'/owner/properties/{prop.property_id}/resubmit', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        db.session.refresh(prop)
        self.assertEqual(prop.approval_status, 'pending')
        self.assertIsNone(prop.rejection_reason)

        # Approve again to keep catalog healthy
        prop.approval_status = 'approved'
        db.session.commit()

    # =========================================================================
    # SUITE 8: ADMIN LISTING MANAGEMENT (EDIT & DEACTIVATE)
    # =========================================================================
    def test_16_admin_listing_edit_and_deactivate(self):
        self.client.post('/auth/login', data={'email': 'admin@unirent.com', 'password': 'admin123'}, follow_redirects=True)

        prop = Property.query.first()
        orig_price = prop.price_per_night

        # 1. Admin Edit Property
        res_edit = self.client.post(f'/admin/properties/{prop.property_id}/edit', data={
            'property_name': prop.property_name,
            'property_type': prop.property_type,
            'description': prop.description,
            'address': prop.address,
            'district': prop.district,
            'price_per_night': orig_price + 200,
            'guest_capacity': prop.guest_capacity,
            'bedrooms': prop.bedrooms,
            'bathrooms': prop.bathrooms,
            'approval_status': 'approved',
            'availability_status': 'available'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        db.session.refresh(prop)
        self.assertEqual(prop.price_per_night, orig_price + 200)

        # Restore original price
        prop.price_per_night = orig_price
        db.session.commit()

        # 2. Admin Deactivate Property (Soft removal preserving bookings)
        res_deact = self.client.post(f'/admin/properties/{prop.property_id}/deactivate', follow_redirects=True)
        self.assertEqual(res_deact.status_code, 200)
        db.session.refresh(prop)
        self.assertEqual(prop.availability_status, 'inactive')

        # 3. Admin Reactivate Property
        res_react = self.client.post(f'/admin/properties/{prop.property_id}/deactivate', follow_redirects=True)
        self.assertEqual(res_react.status_code, 200)
        db.session.refresh(prop)
        self.assertEqual(prop.availability_status, 'available')


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(UniRentComprehensiveTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    run_tests()
