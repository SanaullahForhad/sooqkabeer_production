"""
Database Models for SooqKabeer Kuwait
Filename: models.py
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import secrets

db = SQLAlchemy()

class User(db.Model):
    """User/Customer Model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    language = db.Column(db.String(10), default='ar')  # ar, en, bn
    wallet_balance = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    vendor = db.relationship('Vendor', backref='user', uselist=False, lazy=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        prefix = "SK"
        random_part = secrets.token_hex(3).upper()
        return f"{prefix}{random_part}"
    
    def check_password(self, password):
        """Check password (simplified - in production use proper hashing)"""
        return self.password == hashlib.sha256(password.encode()).hexdigest()
    
    def set_password(self, password):
        """Set password hash"""
        self.password = hashlib.sha256(password.encode()).hexdigest()

class AdminUser(db.Model):
    """Admin User Model"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def check_password(self, password):
        """Check admin password"""
        return self.password == hashlib.sha256(password.encode()).hexdigest()

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
    products = db.relationship('Product', backref='category', lazy=True)
    
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
    image = db.Column(db.String(200), default='default_product.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    """Vendor/Supplier Model"""
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    company_name = db.Column(db.String(200), nullable=False)
    vendor_code = db.Column(db.String(20), unique=True, nullable=False, default="")  # HKO-001 format
    license_number = db.Column(db.String(100))
    license_expiry = db.Column(db.Date)
    kyc_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    commission_rate = db.Column(db.Float, default=10.0)  # 10% default
    total_earnings = db.Column(db.Float, default=0.0)
    pending_balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='vendor', lazy=True)
    
    def generate_vendor_code(self):
        """Generate vendor code in HKO-001 format"""
        import random
        prefix = "HKO"
        number = str(self.id).zfill(3)
        return f"{prefix}-{number}"

class Order(db.Model):
    """Order Model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shipping_address = db.Column(db.Text)
    payment_method = db.Column(db.String(50))  # bank, stc_pay, knet, cash
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    order_status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def generate_order_number(self):
        """Generate unique order number"""
        import secrets
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_part = secrets.token_hex(3).upper()
        return f"SK{date_str}{random_part}"

class OrderItem(db.Model):
    """Order Items Model"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='order_items', lazy=True)

class Commission(db.Model):
    """Commission Tracking Model"""
    __tablename__ = 'commissions'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    commission_rate = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid
    payment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Referral(db.Model):
    """Referral Tracking Model"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    commission_earned = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='referrals_made', lazy=True)
    referred = db.relationship('User', foreign_keys=[referred_id], backref='referrals_received', lazy=True)

class Withdrawal(db.Model):
    """Withdrawal Request Model"""
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.Integer, primary_key=True)
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
    
    # Relationship
    user = db.relationship('User', backref='withdrawals', lazy=True)

# Add after Vendor class __init__ method

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.vendor_code:
            # Generate vendor code
            import random
            self.vendor_code = f"HKO-{random.randint(1, 999):03d}"


# Add vendor code generation logic after Vendor class
def generate_vendor_code_sequence():
    """Generate sequential vendor codes"""
    from models import Vendor, db
    last_vendor = Vendor.query.order_by(Vendor.id.desc()).first()
    if last_vendor and last_vendor.vendor_code and last_vendor.vendor_code.startswith('HKO-'):
        try:
            last_number = int(last_vendor.vendor_code.split('-')[1])
            next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1
    return f"HKO-{next_number:03d}"
