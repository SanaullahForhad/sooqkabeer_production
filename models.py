"""
Database Models for SooqKabeer Kuwait
Filename: models.py
Standardized with proper relationships and password hashing
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(db.Model):
    """User/Customer Model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text)
    language = db.Column(db.String(10), default='ar')
    wallet_balance = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)

    # Relationships
    orders = db.relationship('Order', back_populates='user')
    vendor = db.relationship('Vendor', back_populates='user_profile', uselist=False)
    withdrawals = db.relationship('Withdrawal', back_populates='user')
    referrals_made = db.relationship('Referral', foreign_keys='Referral.referrer_id', back_populates='referrer')
    referrals_received = db.relationship('Referral', foreign_keys='Referral.referred_id', back_populates='referred')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()

    def generate_referral_code(self):
        """Generate unique referral code"""
        prefix = "SK"
        random_part = secrets.token_hex(3).upper()
        return f"{prefix}{random_part}"

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class AdminUser(db.Model):
    """Admin User Model"""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    """Product Category Model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    name_bn = db.Column(db.String(100))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', back_populates='category')

    def get_name(self, lang='ar'):
        """Get category name in selected language"""
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'bn' and self.name_bn:
            return self.name_bn
        return self.name_ar

class Product(db.Model):
    """Product Model"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    name_bn = db.Column(db.String(200))
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    description_bn = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100))
    barcode = db.Column(db.String(100))
    image = db.Column(db.String(200), default='default_product.jpg')
    status = db.Column(db.String(20), default='active')
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', back_populates='products')
    vendor = db.relationship('Vendor', back_populates='products')
    order_items = db.relationship('OrderItem', back_populates='product')

    def get_name(self, lang='ar'):
        """Get product name in selected language"""
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'bn' and self.name_bn:
            return self.name_bn
        return self.name_ar

    def get_description(self, lang='ar'):
        """Get description in selected language"""
        if lang == 'en' and self.description_en:
            return self.description_en
        elif lang == 'bn' and self.description_bn:
            return self.description_bn
        return self.description_ar

class Vendor(db.Model):
    """Vendor Model"""
    __tablename__ = 'vendors'

    id = db.Column(db.Integer, primary_key=True)
    vendor_code = db.Column(db.String(20), unique=True, nullable=False)
    vendor_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    password_hash = db.Column(db.String(256), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', back_populates='vendor')
    commissions = db.relationship('Commission', back_populates='vendor')
    user_profile = db.relationship('User', back_populates='vendor', uselist=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.vendor_code:
            self.vendor_code = self.generate_vendor_code()

    def generate_vendor_code(self):
        """Generate sequential vendor code"""
        # Get the last vendor code in HKO-XXX format
        last_vendor = Vendor.query.order_by(Vendor.id.desc()).first()
        if last_vendor and last_vendor.vendor_code.startswith('HKO-'):
            try:
                last_num = int(last_vendor.vendor_code.split('-')[1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        return f"HKO-{next_num:03d}"

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Vendor {self.vendor_code}: {self.vendor_name}>'

class Order(db.Model):
    """Order Model"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text)
    payment_method = db.Column(db.String(50))  # bank, stc_pay, knet, cash
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    order_status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order')
    commissions = db.relationship('Commission', back_populates='order')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()

    def generate_order_number(self):
        """Generate unique order number"""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_part = secrets.token_hex(3).upper()
        return f"SK{date_str}{random_part}"

class OrderItem(db.Model):
    """Order Items Model"""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

class Commission(db.Model):
    """Commission Tracking Model"""
    __tablename__ = 'commissions'

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid
    payment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    vendor = db.relationship('Vendor', back_populates='commissions')
    order = db.relationship('Order', back_populates='commissions')

class Referral(db.Model):
    """Referral Tracking Model"""
    __tablename__ = 'referrals'

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    commission_earned = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id], back_populates='referrals_made')
    referred = db.relationship('User', foreign_keys=[referred_id], back_populates='referrals_received')

class Withdrawal(db.Model):
    """Withdrawal Request Model"""
    __tablename__ = 'withdrawals'

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)  # 1% fee
    net_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    account_details = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', back_populates='withdrawals')
