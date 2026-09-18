
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='traveler')
    status = db.Column(db.String(20), nullable=False, default='active')
    profile_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    owner_profile = db.relationship(
        'Owner',
        backref='user',
        uselist=False,
        cascade='all, delete-orphan'
    )

    admin_profile = db.relationship(
        'Admin',
        backref='user',
        uselist=False,
        cascade='all, delete-orphan'
    )

    bookings = db.relationship(
        'Booking',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    reviews = db.relationship(
        'Review',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    complaints = db.relationship(
        'Complaint',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'status': self.status,
            'profile_image': self.profile_image,
            'created_at': (
                self.created_at.strftime('%Y-%m-%d %H:%M:%S')
                if self.created_at
                else None
            )
        }


class Owner(db.Model):
    __tablename__ = 'owners'

    owner_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    business_name = db.Column(db.String(150), nullable=True)
    district = db.Column(
        db.String(50),
        nullable=False,
        default='Ernakulam'
    )

    kyc_status = db.Column(
        db.String(20),
        nullable=False,
        default='verified'
    )

    bank_account = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    properties = db.relationship(
        'Property',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    vehicles = db.relationship(
        'Vehicle',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    bookings = db.relationship(
        'Booking',
        backref='owner',
        lazy='dynamic'
    )

    complaints = db.relationship(
        'Complaint',
        backref='owner',
        lazy='dynamic'
    )

    def to_dict(self):
        return {
            'owner_id': self.owner_id,
            'user_id': self.user_id,
            'full_name': (
                self.user.full_name
                if self.user
                else None
            ),
            'email': (
                self.user.email
                if self.user
                else None
            ),
            'business_name': self.business_name,
            'district': self.district,
            'kyc_status': self.kyc_status,
            'created_at': (
                self.created_at.strftime('%Y-%m-%d')
                if self.created_at
                else None
            )
        }


class Admin(db.Model):
    __tablename__ = 'admins'

    admin_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    admin_level = db.Column(
        db.String(50),
        nullable=False,
        default='Super Admin'
    )

    department = db.Column(
        db.String(100),
        nullable=False,
        default='Operations'
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Property(db.Model):
    __tablename__ = 'properties'

    property_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('owners.owner_id', ondelete='CASCADE'),
        nullable=False
    )

    property_name = db.Column(
        db.String(160),
        nullable=False
    )

    slug = db.Column(
        db.String(180),
        unique=True,
        nullable=False
    )

    property_type = db.Column(
        db.String(80),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    address = db.Column(
        db.String(255),
        nullable=False
    )

    district = db.Column(
        db.String(50),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    price_per_night = db.Column(
        db.Float,
        nullable=False
    )

    guest_capacity = db.Column(
        db.Integer,
        nullable=False,
        default=2
    )

    bedrooms = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    bathrooms = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    amenities = db.Column(
        db.Text,
        nullable=True
    )

    images = db.Column(
        db.Text,
        nullable=True
    )

    featured_image = db.Column(
        db.String(255),
        nullable=True
    )

    approval_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )

    rejection_reason = db.Column(
        db.Text,
        nullable=True
    )

    availability_status = db.Column(
        db.String(20),
        nullable=False,
        default='available'
    )

    featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationships
    bookings = db.relationship(
        'Booking',
        backref='property',
        lazy='dynamic'
    )

    reviews = db.relationship(
        'Review',
        backref='property',
        lazy='dynamic'
    )

    @property
    def amenities_list(self):
        if not self.amenities:
            return []

        try:
            return json.loads(self.amenities)
        except Exception:
            return [
                a.strip()
                for a in self.amenities.split(',')
                if a.strip()
            ]

    @property
    def images_list(self):
        if not self.images:
            return (
                [self.featured_image]
                if self.featured_image
                else []
            )

        try:
            return json.loads(self.images)
        except Exception:
            return [self.images]

    @property
    def average_rating(self):
        revs = self.reviews.all()

        if not revs:
            return 4.9

        return round(
            sum(r.rating for r in revs) / len(revs),
            1
        )

    @property
    def reviews_count(self):
        return self.reviews.count()

    def to_dict(self):
        return {
            'property_id': self.property_id,
            'owner_id': self.owner_id,

            'owner_name': (
                self.owner.user.full_name
                if self.owner and self.owner.user
                else 'UniRent Host'
            ),

            'property_name': self.property_name,
            'slug': self.slug,
            'property_type': self.property_type,
            'description': self.description,
            'address': self.address,
            'district': self.district,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'price_per_night': self.price_per_night,
            'guest_capacity': self.guest_capacity,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'amenities': self.amenities_list,
            'images': self.images_list,
            'featured_image': self.featured_image,
            'approval_status': self.approval_status,
            'availability_status': self.availability_status,
            'featured': self.featured,
            'rating': self.average_rating,
            'reviews_count': self.reviews_count
        }


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    vehicle_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('owners.owner_id', ondelete='CASCADE'),
        nullable=False
    )

    vehicle_name = db.Column(
        db.String(160),
        nullable=False
    )

    model = db.Column(
        db.String(100),
        nullable=False
    )

    vehicle_type = db.Column(
        db.String(20),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    price_per_day = db.Column(
        db.Float,
        nullable=False
    )

    # --------------------------------------------------
    # REFUNDABLE SECURITY / CAUTION DEPOSIT
    # Only applicable to vehicle rentals.
    # Default deposit = Rs. 2,000
    # --------------------------------------------------
    security_deposit = db.Column(
        db.Float,
        nullable=False,
        default=2000.0
    )

    district = db.Column(
        db.String(50),
        nullable=False
    )

    pickup_location = db.Column(
        db.String(255),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    delivery_available = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    specifications = db.Column(
        db.Text,
        nullable=True
    )

    images = db.Column(
        db.Text,
        nullable=True
    )

    featured_image = db.Column(
        db.String(255),
        nullable=True
    )

    approval_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )

    rejection_reason = db.Column(
        db.Text,
        nullable=True
    )

    availability_status = db.Column(
        db.String(20),
        nullable=False,
        default='available'
    )

    featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationships
    bookings = db.relationship(
        'Booking',
        backref='vehicle',
        lazy='dynamic'
    )

    reviews = db.relationship(
        'Review',
        backref='vehicle',
        lazy='dynamic'
    )

    @property
    def specs_dict(self):
        if not self.specifications:
            return {}

        try:
            return json.loads(self.specifications)
        except Exception:
            return {}

    @property
    def images_list(self):
        if not self.images:
            return (
                [self.featured_image]
                if self.featured_image
                else []
            )

        try:
            return json.loads(self.images)
        except Exception:
            return [self.images]

    @property
    def average_rating(self):
        revs = self.reviews.all()

        if not revs:
            return 4.8

        return round(
            sum(r.rating for r in revs) / len(revs),
            1
        )

    @property
    def reviews_count(self):
        return self.reviews.count()

    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'owner_id': self.owner_id,

            'owner_name': (
                self.owner.user.full_name
                if self.owner and self.owner.user
                else 'UniRent Host'
            ),

            'vehicle_name': self.vehicle_name,
            'model': self.model,
            'vehicle_type': self.vehicle_type,
            'description': self.description,
            'price_per_day': self.price_per_day,

            # NEW: Refundable vehicle deposit
            'security_deposit': self.security_deposit,

            'district': self.district,
            'pickup_location': self.pickup_location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'delivery_available': self.delivery_available,
            'specifications': self.specs_dict,
            'images': self.images_list,
            'featured_image': self.featured_image,
            'approval_status': self.approval_status,
            'availability_status': self.availability_status,
            'featured': self.featured,
            'rating': self.average_rating,
            'reviews_count': self.reviews_count
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    booking_reference = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey('owners.owner_id', ondelete='CASCADE'),
        nullable=False
    )

    listing_type = db.Column(
        db.String(20),
        nullable=False
    )

    property_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'properties.property_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'vehicles.vehicle_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    total_days = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    daily_rate = db.Column(
        db.Float,
        nullable=False
    )

    service_fee = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    tax_amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    # --------------------------------------------------
    # REFUNDABLE SECURITY / CAUTION DEPOSIT
    #
    # Property booking = 0
    # Vehicle booking = vehicle's security deposit
    # --------------------------------------------------
    security_deposit = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    total_amount = db.Column(
        db.Float,
        nullable=False
    )

    booking_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )

    special_requests = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationships
    payment = db.relationship(
        'Payment',
        backref='booking',
        uselist=False,
        cascade='all, delete-orphan'
    )

    review = db.relationship(
        'Review',
        backref='booking',
        uselist=False,
        cascade='all, delete-orphan'
    )

    complaints = db.relationship(
        'Complaint',
        backref='booking',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def listing_name(self):
        if self.listing_type == 'property' and self.property:
            return self.property.property_name

        elif self.listing_type == 'vehicle' and self.vehicle:
            return (
                f"{self.vehicle.vehicle_name} "
                f"({self.vehicle.model})"
            )

        return 'Listing'

    @property
    def listing_image(self):
        if self.listing_type == 'property' and self.property:
            return self.property.featured_image

        elif self.listing_type == 'vehicle' and self.vehicle:
            return self.vehicle.featured_image

        return '/static/images/hero_kerala_stay.jpg'

    def to_dict(self):
        return {
            'booking_id': self.booking_id,
            'booking_reference': self.booking_reference,
            'user_id': self.user_id,

            'traveler_name': (
                self.user.full_name
                if self.user
                else None
            ),

            'owner_id': self.owner_id,
            'listing_type': self.listing_type,
            'listing_name': self.listing_name,
            'listing_image': self.listing_image,

            'property_id': self.property_id,
            'vehicle_id': self.vehicle_id,

            'start_date': (
                self.start_date.strftime('%Y-%m-%d')
            ),

            'end_date': (
                self.end_date.strftime('%Y-%m-%d')
            ),

            'total_days': self.total_days,
            'daily_rate': self.daily_rate,
            'service_fee': self.service_fee,
            'tax_amount': self.tax_amount,

            # NEW
            'security_deposit': self.security_deposit,

            'total_amount': self.total_amount,
            'booking_status': self.booking_status,

            'payment_status': (
                self.payment.payment_status
                if self.payment
                else 'pending'
            ),

            'has_review': bool(self.review),

            'created_at': (
                self.created_at.strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            )
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'bookings.booking_id',
            ondelete='CASCADE'
        ),
        unique=True,
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_method = db.Column(
        db.String(50),
        nullable=False,
        default='card'
    )

    transaction_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    payment_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )

    gateway_response = db.Column(
        db.Text,
        nullable=True
    )

    payment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    @property
    def transaction_id(self):
        return self.transaction_reference

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'booking_id': self.booking_id,

            'booking_reference': (
                self.booking.booking_reference
                if self.booking
                else None
            ),

            'amount': self.amount,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_reference,
            'transaction_reference': self.transaction_reference,
            'payment_status': self.payment_status,

            'payment_date': (
                self.payment_date.strftime(
                    '%Y-%m-%d %H:%M:%S'
                )
            )
        }


class Review(db.Model):
    __tablename__ = 'reviews'

    review_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'bookings.booking_id',
            ondelete='CASCADE'
        ),
        unique=True,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'users.user_id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    listing_type = db.Column(
        db.String(20),
        nullable=False
    )

    property_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'properties.property_id',
            ondelete='CASCADE'
        ),
        nullable=True
    )

    vehicle_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'vehicles.vehicle_id',
            ondelete='CASCADE'
        ),
        nullable=True
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    review_title = db.Column(
        db.String(150),
        nullable=True
    )

    review_text = db.Column(
        db.Text,
        nullable=False
    )

    image_url = db.Column(
        db.String(255),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            'review_id': self.review_id,
            'booking_id': self.booking_id,

            'author_name': (
                self.user.full_name
                if self.user
                else 'Guest Traveler'
            ),

            'listing_type': self.listing_type,

            'property_name': (
                self.property.property_name
                if self.property
                else None
            ),

            'vehicle_name': (
                self.vehicle.vehicle_name
                if self.vehicle
                else None
            ),

            'rating': self.rating,
            'review_title': self.review_title,
            'review_text': self.review_text,
            'image_url': self.image_url,

            'created_at': (
                self.created_at.strftime(
                    '%b %d, %Y'
                )
            )
        }


class Complaint(db.Model):
    __tablename__ = 'complaints'

    complaint_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_reference = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'bookings.booking_id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'users.user_id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'owners.owner_id',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    category = db.Column(
        db.String(60),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    evidence_image = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default='open'
    )

    owner_response = db.Column(
        db.Text,
        nullable=True
    )

    admin_response = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    def to_dict(self):
        return {
            'complaint_id': self.complaint_id,
            'complaint_reference': self.complaint_reference,

            'booking_reference': (
                self.booking.booking_reference
                if self.booking
                else None
            ),

            'traveler_name': (
                self.user.full_name
                if self.user
                else None
            ),

            'owner_name': (
                self.owner.user.full_name
                if self.owner and self.owner.user
                else None
            ),

            'category': self.category,
            'description': self.description,
            'status': self.status,
            'owner_response': self.owner_response,
            'admin_response': self.admin_response,

            'created_at': (
                self.created_at.strftime(
                    '%Y-%m-%d %H:%M'
                )
            ),

            'resolved_at': (
                self.resolved_at.strftime(
                    '%Y-%m-%d %H:%M'
                )
                if self.resolved_at
                else None
            )
        }

