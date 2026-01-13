# ========== SOOQ KABEER - COMPLETE E-COMMERCE PLATFORM ==========
# All features in one file: Referral, Vendor, Orders, Commission
# ================================================================

# ========== IMPORTS ==========
from flask import Flask, render_template, request, session, redirect, url_for, g, flash, current_app, jsonify
from flask_babel import Babel, _
import sqlite3
import os
import hashlib
import random
import string
from datetime import datetime
from functools import wraps
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import time
import click

# ========== ARABIC SUPPORT ==========
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    HAS_ARABIC_LIB = True
except ImportError:
    HAS_ARABIC_LIB = False
    print("#=== NOTICE: Running without Arabic reshaper library ===#")

# ========== CONFIGURATION CONSTANTS ==========
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
REFERRAL_RATE = 0.05
MIN_WITHDRAWAL = 10
COMMISSION_RATE = 0.10
MIN_WITHDRAWAL_LIMIT = 5.0
DATABASE = 'sooqkabeer.db'
UPLOAD_FOLDER = 'static/uploads/kyc'
SUPPORTED_LANGUAGES = ['ar', 'en']
DEFAULT_LANGUAGE = 'ar'

# ========== APP INITIALIZATION ==========
app = Flask(__name__)
app.secret_key = 'sooqkabeer_secret_key_2024'
# ========== DATABASE CONFIGURATION ==========
basedir = os.path.abspath(os.path.dirname(__file__))
MAIN_DB = 'sooqkabeer.db'  # Single database name
DATABASE_PATH = os.path.join(basedir, MAIN_DB)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"📁 Using database: {DATABASE_PATH}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ar']

# ========== BABEL CONFIGURATION ==========
babel = Babel(app)
from models import db
db.init_app(app)
# ========== HELPER FUNCTIONS ==========
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Create database connection"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sooqkabeer.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Get database connection with app context"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    """Hash password with salt"""
    SALT = 'sooqkabeer_salt_'
    return hashlib.sha256((SALT + password).encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Check password hash"""
    SALT = 'sooqkabeer_salt_'
    new_hash = hashlib.sha256((SALT + user_password).encode()).hexdigest()
    return hashed_password == new_hash

def generate_referral_code(username):
    """Generate unique referral code"""
    code = hashlib.md5(f"{username}{random.random()}".encode()).hexdigest()[:8].upper()
    return f"REF{code}"

def fix_arabic(text):
    """Fix Arabic text for display"""
    if not text:
        return ""
    if HAS_ARABIC_LIB:
        try:
            return get_display(reshape(text))
        except Exception:
            return text
    return text

def get_locale():
    """Get current locale for Babel"""
    return session.get('lang', app.config.get('BABEL_DEFAULT_LOCALE', 'en'))

babel = Babel(app, locale_selector=get_locale)

def create_upload_folder():
    """Create upload folder if not exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# cache busting
@app.context_processor
def inject_cache_buster():
    import time
    return {'timestamp': int(time.time())}

# ========== TEMPLATE FILTERS ==========
@app.template_filter('datetime')
def format_datetime(value, format="%d %b %Y, %I:%M %p"):
    """Format datetime for templates"""
    if value is None:
        return ""
    
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                value = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    
    if isinstance(value, datetime):
        return value.strftime(format)
    
    return str(value)

@app.template_filter('date_only')
def format_date_only(value):
    """Format date only"""
    return format_datetime(value, "%d %B %Y")

# ========== CONTEXT PROCESSORS ==========
@app.context_processor
def inject_timestamp():
    """Inject timestamp to prevent browser cache issues"""
    return {'timestamp': int(time.time())}

# ========== CLASSES ==========
class RowWrapper:
    """Wrapper for database rows to support multilingual names"""
    def __init__(self, row):
        self.row = dict(row) if row else {}

    def __getattr__(self, name):
        return self.row.get(name)

    def get_name(self, lang='en'):
        col = f'name_{lang}'
        return self.row.get(col) or self.row.get('name_en') or self.row.get('name', '')

    def get_description(self, lang='en'):
        col = f'description_{lang}'
        return self.row.get(col) or self.row.get('description_en') or self.row.get('description', '')

# ========== CLI COMMANDS ==========
@app.cli.command("product-help")
def product_help():
    """Show help for product CLI commands"""
    print("\n" + "="*60)
    print("SOOQ KABEER - PRODUCT CLI COMMANDS".center(60))
    print("="*60)
    
    print("\n📦 Available Commands:")
    print("  flask add-product         - Interactive product creation")
    print("  flask quick-add           - Quick product add with parameters")
    print("  flask import-products     - Import products from CSV")
    print("  flask list-products       - List all products")
    print("  flask product-help        - Show this help")
    
    print("\n🚀 Examples:")
    print("  flask add-product")
    print("  flask quick-add --name \"iPhone 14\" --price 350.500 --vendor HKO-001")
    print("  flask import-products --file products.csv --vendor HKO-001")
    print("  flask list-products --vendor HKO-001 --limit 50")
    
    print("\n📄 CSV Format for Import:")
    print("  name_en,name_ar,description_en,description_ar,price,category_id,sku,stock")
    print("  Example: iPhone 14,آيفون 14,Latest iPhone,أحدث آيفون,350.500,1,IP14-001,50")

@app.cli.command("add-product")
def add_product_cli():
    """Add product from terminal - Interactive CLI"""
    try:
        # Late import to avoid circular import
        from models import Product, Category, Vendor
        from datetime import datetime
        
        print("\n" + "="*60)
        print("SOOQ KABEER - TERMINAL PRODUCT MANAGER".center(60))
        print("="*60)
        
        # Simple authentication
        vendor_code = input("\nEnter Vendor Code (e.g., HKO-001): ")
        
        # Check vendor
        vendor = Vendor.query.filter_by(vendor_code=vendor_code).first()
        if not vendor:
            print(f"✗ Vendor {vendor_code} not found!")
            return
        
        print(f"✓ Authenticated as: {vendor.vendor_name}")
        
        # Show categories
        categories = Category.query.all()
        if categories:
            print("\n📂 Available Categories:")
            for cat in categories:
                print(f"  {cat.id}. {cat.name_en} / {cat.name_ar}")
        
        # Get category ID
        try:
            category_id = int(input("\nEnter Category ID: "))
            category = Category.query.get(category_id)
            if not category:
                print("✗ Invalid Category ID!")
                return
        except ValueError:
            print("✗ Please enter a valid number!")
            return
        
        # Get product details
        print("\n📝 Product Details:")
        name_en = input("Product Name (English): ")
        name_ar = input("Product Name (Arabic): ")
        description_en = input("Description (English): ")
        description_ar = input("Description (Arabic): ")
        
        try:
            price = float(input("Price (KWD): "))
            stock = int(input("Stock Quantity: "))
        except ValueError:
            print("✗ Invalid price or stock!")
            return
        
        sku = input("SKU (optional): ")
        barcode = input("Barcode (optional): ")
        
        # Create product
        product = Product(
            name_en=name_en,
            name_ar=name_ar,
            description_en=description_en,
            description_ar=description_ar,
            price=price,
            category_id=category_id,
            vendor_id=vendor.id,
            sku=sku or '',
            barcode=barcode or '',
            stock=stock,
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(product)
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ PRODUCT CREATED SUCCESSFULLY!".center(60))
        print("="*60)
        print(f"\n📋 Product Details:")
        print(f"  ID: {product.id}")
        print(f"  Name: {product.name_en}")
        print(f"  Price: {product.price:.3f} KWD")
        print(f"  Stock: {product.stock}")
        print(f"  SKU: {product.sku or 'Not set'}")
        print(f"  Vendor: {vendor.vendor_name}")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {str(e)}")

@app.cli.command("quick-add")
@click.option('--name', required=True, help='Product name (English)')
@click.option('--price', required=True, type=float, help='Product price')
@click.option('--vendor', required=True, help='Vendor code')
@click.option('--category', default=1, help='Category ID')
@click.option('--stock', default=10, help='Stock quantity')
@click.option('--sku', help='SKU')
def quick_add(name, price, vendor, category, stock, sku):
    """Quickly add a product with minimal input"""
    try:
        from models import Product, Vendor
        from datetime import datetime
        
        vendor_obj = Vendor.query.filter_by(vendor_code=vendor).first()
        if not vendor_obj:
            print(f"✗ Vendor {vendor} not found!")
            return
        
        product = Product(
            name_en=name,
            name_ar=name,
            description_en=f"Added via CLI - {name}",
            description_ar=f"تمت الإضافة عبر CLI - {name}",
            price=price,
            category_id=category,
            vendor_id=vendor_obj.id,
            sku=sku or '',
            stock=stock,
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(product)
        db.session.commit()
        
        print(f"✅ Product added successfully!")
        print(f"  ID: {product.id}")
        print(f"  Name: {product.name_en}")
        print(f"  Price: {product.price:.3f} KWD")
        print(f"  Vendor: {vendor_obj.vendor_name}")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {str(e)}")

@app.cli.command("list-products")
@click.option('--vendor', help='Filter by vendor code')
@click.option('--category', help='Filter by category ID')
@click.option('--limit', default=20, help='Number of products to show')
def list_products(vendor, category, limit):
    """List products in terminal"""
    try:
        from models import Product, Vendor
        
        query = Product.query
        
        if vendor:
            vendor_obj = Vendor.query.filter_by(vendor_code=vendor).first()
            if vendor_obj:
                query = query.filter_by(vendor_id=vendor_obj.id)
        
        if category:
            query = query.filter_by(category_id=category)
        
        products = query.order_by(Product.created_at.desc()).limit(limit).all()
        
        if not products:
            print("No products found!")
            return
        
        print("\n" + "="*85)
        print(f"{'ID':<6} {'Name':<30} {'Price':<10} {'Stock':<8} {'Vendor':<15} {'Status':<10}")
        print("="*85)
        
        for p in products:
            vendor_name = Vendor.query.get(p.vendor_id).vendor_code if p.vendor_id else 'N/A'
            name_display = p.name_en[:27] + '...' if len(p.name_en) > 27 else p.name_en
            
            status_icon = '✅' if p.status == 'active' else '⏸️'
            
            print(f"{p.id:<6} {name_display:<30} {p.price:<10.3f} {p.stock:<8} {vendor_name:<15} {status_icon} {p.status:<10}")
        
        print(f"\n📊 Total products: {len(products)}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")

@app.cli.command("import-products")
@click.option('--file', type=click.Path(exists=True), help='CSV file path')
@click.option('--vendor', help='Vendor code')
def import_products(file, vendor):
    """Import products from CSV file"""
    try:
        import csv
        import os
        from models import Product, Vendor
        from datetime import datetime
        
        if not file:
            file = input("Enter CSV file path: ")
        
        if not vendor:
            vendor = input("Enter Vendor Code: ")
        
        if not os.path.exists(file):
            print(f"✗ File not found: {file}")
            return
        
        vendor_obj = Vendor.query.filter_by(vendor_code=vendor).first()
        if not vendor_obj:
            print(f"✗ Vendor not found: {vendor}")
            return
        
        with open(file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"📥 Found {len(rows)} products in CSV")
        
        success_count = 0
        error_count = 0
        
        for i, row in enumerate(rows, 1):
            try:
                product = Product(
                    name_en=row.get('name_en', ''),
                    name_ar=row.get('name_ar', ''),
                    description_en=row.get('description_en', ''),
                    description_ar=row.get('description_ar', ''),
                    price=float(row.get('price', 0)),
                    category_id=int(row.get('category_id', 1)),
                    vendor_id=vendor_obj.id,
                    sku=row.get('sku', ''),
                    stock=int(row.get('stock', 0)),
                    status='active',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(product)
                print(f"✅ [{i}] Added: {product.name_en}")
                success_count += 1
                
                if i % 10 == 0:
                    db.session.commit()
                    
            except Exception as e:
                error_count += 1
                print(f"✗ [{i}] Error: {str(e)}")
                continue
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY".center(60))
        print("="*60)
        print(f"✅ Successfully imported: {success_count} products")
        if error_count > 0:
            print(f"⚠ Failed to import: {error_count} products")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {str(e)}")

@app.cli.command("setup-vendor")
@click.option('--code', required=True, help='Vendor code (e.g., HKO-001)')
@click.option('--name', required=True, help='Vendor name')
@click.option('--email', required=True, help='Vendor email')
@click.option('--password', required=True, help='Vendor password (Minimum 8 characters)')
def setup_vendor(code, name, email, password):
    """Setup a new vendor for testing"""
    # Import inside the function to avoid NameError and circular imports
    from models import Vendor, db
    
    try:
        # 1. Validation: Check password length
        if len(password) < 8:
            print(f"✗ Error: Password must be at least 8 characters long!")
            return

        # 2. Check if vendor already exists
        existing = Vendor.query.filter_by(vendor_code=code).first()
        if existing:
            print(f"⚠ Vendor {code} already exists!")
            return
        
        # 3. Create new vendor
        # Note: We pass 'password' directly because the Vendor model 
        # has a @password.setter that handles hashing automatically.
        vendor = Vendor(
            vendor_code=code,
            vendor_name=name,
            email=email,
            password=password,
            phone='',
            address='',
            balance=0.0,
            status='active'
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        print(f"✅ Vendor created successfully!")
        print(f"  Code: {vendor.vendor_code}")
        print(f"  Name: {vendor.vendor_name}")
        print(f"  Email: {vendor.email}")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {str(e)}")

#=== Context Processors ===#
@app.context_processor
def utility_processor():
    return dict(
        get_arabic_text=fix_arabic,
        now=datetime.now(),
        wrap_row=lambda r: RowWrapper(r) if r else None
    )

@app.before_request
def before_request():
    """Set language and RTL flag before each request"""
    if 'language' not in session:
        session['language'] = DEFAULT_LANGUAGE
    # Set RTL flag for Arabic
    request.is_rtl = True if session.get('language') == 'ar' else False
#============ DATABASE INITIALIZATION =============#

def init_database():
    """Initialize database with all required tables"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("📊 Initializing database from code...")
        
        try:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT,
                    role TEXT DEFAULT 'customer',
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    wallet_balance REAL DEFAULT 0,
                    total_commission REAL DEFAULT 0,
                    direct_referrals INTEGER DEFAULT 0,
                    indirect_referrals INTEGER DEFAULT 0,
                    total_orders INTEGER DEFAULT 0,
                    total_spent REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')

            # Create vendors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT,
                    country_code TEXT DEFAULT '+965',
                    nationality TEXT,
                    shop_name TEXT NOT NULL,
                    business_name TEXT,
                    business_type TEXT,
                    cr_number TEXT UNIQUE,
                    vat_number TEXT,
                    address TEXT,
                    governorate TEXT,
                    block TEXT,
                    street TEXT,
                    building TEXT,
                    floor TEXT,
                    unit TEXT,
                    business_description TEXT,
                    civil_id TEXT,
                    civil_id_path TEXT,
                    civil_id_back_path TEXT,
                    commercial_license_path TEXT,
                    vendor_code TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'pending',
                    agree_terms TEXT DEFAULT 'no',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_en TEXT NOT NULL,
                    name_ar TEXT NOT NULL,
                    description_en TEXT,
                    description_ar TEXT,
                    price REAL NOT NULL,
                    unit TEXT DEFAULT 'kg',
                    category TEXT,
                    image_url TEXT,
                    stock_quantity REAL DEFAULT 0,
                    vendor_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    views INTEGER DEFAULT 0,
                    total_sales INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vendor_id) REFERENCES users (id)
                )
            ''')

            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    shipping_address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Create order_items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Create referrals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    level INTEGER DEFAULT 1,
                    commission_rate REAL DEFAULT 0.05,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(referrer_id, referred_id),
                    FOREIGN KEY (referrer_id) REFERENCES users (id),
                    FOREIGN KEY (referred_id) REFERENCES users (id)
                )
            ''')

            # Create commissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_id INTEGER,
                    referred_user_id INTEGER,
                    amount REAL NOT NULL,
                    commission_rate REAL NOT NULL,
                    type TEXT,
                    status TEXT DEFAULT 'pending',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')

            # Create withdrawals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    method TEXT,
                    account_details TEXT,
                    status TEXT DEFAULT 'pending',
                    transaction_id TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Create categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_en TEXT NOT NULL,
                    name_ar TEXT NOT NULL,
                    description TEXT,
                    parent_id INTEGER DEFAULT NULL,
                    icon TEXT,
                    image TEXT,
                    sort_order INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create admin_users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT DEFAULT 'admin',
                    permissions TEXT,
                    last_login TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert default admin user (password: admin123)
            cursor.execute('''
                INSERT OR IGNORE INTO admin_users (username, email, password, full_name, role, status)
                VALUES ('admin', 'admin@sooqkabeer.com',
                        '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
                        'Administrator', 'admin', 'active')
            ''')

            # Insert default categories
            cursor.execute('''
                INSERT OR IGNORE INTO categories (id, name_ar, name_en)
                VALUES (1, "General", "General")
            ''')

            db.commit()
            print("✅ Database initialized successfully!")

        except Exception as e:
            print(f"Database initialization error: {str(e)}")
#============ AUTHENTICATION DECORATORS =============#
#=====================================================
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))

        if session.get('role') != 'vendor':
            flash('Access denied. Vendor account required.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied: Admins only!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

from functools import wraps

def vendor_login_required(f):
    """Require vendor login - specific to vendor routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor':
            flash("Vendor login required!", "warning")
            return redirect(url_for('vendor_login'))
        return f(*args, **kwargs)
    return decorated_function

#=== Context Processor for Global User Data ===#
@app.context_processor
def inject_global_data():
    """Inject global data into all templates"""
    user = None
    if 'user_id' in session:
        try:
            db = get_db()
            row = db.execute("SELECT * FROM users WHERE id = ?", 
                           (session['user_id'],)).fetchone()
            if row:
                user = RowWrapper(row)
        except Exception as e:
            print(f"Error in inject_global_data: {e}")
    
    return {
        'now': datetime.now(),
        'current_user': user,
        'is_rtl': True if session.get('language') == 'ar' else False
    }
#============ REFERRAL & COMMISSION FUNCTIONS =============#

def process_referral_signup(new_user_id, referral_code):
    """Process referral when new user signs up with bonus and MLM support"""
    if not referral_code:
        return False

    db = get_db()
    cursor = db.cursor()

    # Find referrer
    cursor.execute("SELECT id FROM users WHERE referral_code = ?", (referral_code,))
    referrer = cursor.fetchone()

    if not referrer:
        return False

    referrer_id = referrer['id']

    try:
        # 1. Add to referrals table
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, level, commission_rate)
            VALUES (?, ?, 1, ?)
        ''', (referrer_id, new_user_id, REFERRAL_RATE))

        # 2. Update referrer's counts
        cursor.execute('''
            UPDATE users
            SET direct_referrals = direct_referrals + 1,
                total_referrals = total_referrals + 1
            WHERE id = ?
        ''', (referrer_id,))

        # 3. Update new user's referred_by field
        cursor.execute("UPDATE users SET referred_by = ? WHERE id = ?",
                      (referral_code, new_user_id))

        # 4. Add signup bonus
        signup_bonus = 5.0
        add_commission(referrer_id, signup_bonus, 'signup_bonus',
                      referred_user_id=new_user_id,
                      description=f"Signup bonus for new referral: {new_user_id}")

        # 5. Process multi-level referral
        process_multi_level_referral(new_user_id, referrer_id)

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Referral error: {e}")
        return False

def process_multi_level_referral(new_user_id, direct_referrer_id):
    """Process multi-level referral network"""
    db = get_db()
    cursor = db.cursor()

    # Level 2 (indirect)
    cursor.execute('''
        SELECT referrer_id FROM referrals
        WHERE referred_id = ? AND level = 1
    ''', (direct_referrer_id,))

    level2_referrer = cursor.fetchone()
    if level2_referrer:
        level2_rate = REFERRAL_RATE * 0.5  # 2.5%
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, level, commission_rate)
            VALUES (?, ?, 2, ?)
        ''', (level2_referrer['referrer_id'], new_user_id, level2_rate))

        # Update indirect referrals count
        cursor.execute('''
            UPDATE users
            SET indirect_referrals = indirect_referrals + 1,
                total_referrals = total_referrals + 1
            WHERE id = ?
        ''', (level2_referrer['referrer_id'],))

        # Level 3
        cursor.execute('''
            SELECT referrer_id FROM referrals
            WHERE referred_id = ? AND level = 1
        ''', (level2_referrer['referrer_id'],))

        level3_referrer = cursor.fetchone()
        if level3_referrer:
            level3_rate = REFERRAL_RATE * 0.25  # 1.25%
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id, level, commission_rate)
                VALUES (?, ?, 3, ?)
            ''', (level3_referrer['referrer_id'], new_user_id, level3_rate))

            cursor.execute('''
                UPDATE users
                SET indirect_referrals = indirect_referrals + 1,
                    total_referrals = total_referrals + 1
                WHERE id = ?
            ''', (level3_referrer['referrer_id'],))

def process_order_commissions(order_id):
    """Process all commissions for an order"""
    db = get_db()
    cursor = db.cursor()

    # Get order details
    cursor.execute('''
        SELECT o.id, o.user_id, o.total_price, u.referred_by
        FROM orders o 
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,))

    order = cursor.fetchone()
    if not order:
        return

    buyer_id = order['user_id']
    total_price = order['total_price']

    # 1. Vendor commissions
    cursor.execute('''
        SELECT p.vendor_id, SUM(oi.total_price) as vendor_sales
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
        GROUP BY p.vendor_id
    ''', (order_id,))

    vendor_sales = cursor.fetchall()
    for vs in vendor_sales:
        if vs['vendor_id']:
            commission = vs['vendor_sales'] * COMMISSION_RATE
            add_commission(vs['vendor_id'], commission, 'vendor', order_id,
                          f"Vendor commission from order #{order_id}")

    # 2. Referral commissions
    cursor.execute('''
        SELECT r.referrer_id, r.level, r.commission_rate
        FROM referrals r
        WHERE r.referred_id = ?
        ORDER BY r.level
    ''', (buyer_id,))

    referrals = cursor.fetchall()
    for ref in referrals:
        commission = total_price * ref['commission_rate']
        if commission > 0:
            add_commission(ref['referrer_id'], commission, 'referral', order_id,
                          f"Level {ref['level']} referral commission from order #{order_id}",
                          referred_user_id=buyer_id)

    db.commit()

def add_commission(user_id, amount, commission_type, order_id=None, description="", referred_user_id=None):
    """Add commission record"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        INSERT INTO commissions (user_id, order_id, referred_user_id, amount, 
                               commission_rate, type, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (user_id, order_id, referred_user_id, amount,
          REFERRAL_RATE if commission_type == 'referral' else COMMISSION_RATE,
          commission_type, description))

    # Update user wallet
    cursor.execute('''
        UPDATE users
        SET wallet_balance = wallet_balance + ?,
            total_commission = total_commission + ?
        WHERE id = ?
    ''', (amount, amount, user_id))

    return True

def get_referral_stats(user_id):
    """Get referral statistics for user"""
    db = get_db()
    cursor = db.cursor()

    # Main stats
    cursor.execute('''
        SELECT
            COUNT(*) as total_referrals,
            SUM(CASE WHEN level = 1 THEN 1 ELSE 0 END) as direct_referrals,
            SUM(CASE WHEN level > 1 THEN 1 ELSE 0 END) as indirect_referrals
        FROM referrals
        WHERE referrer_id = ?
    ''', (user_id,))

    main_stats = cursor.fetchone()

    # Level-wise stats
    cursor.execute('''
        SELECT
            level,
            COUNT(*) as referral_count
        FROM referrals
        WHERE referrer_id = ?
        GROUP BY level
        ORDER BY level
    ''', (user_id,))

    level_stats = cursor.fetchall()

    # Monthly earnings
    cursor.execute('''
        SELECT
            strftime('%Y-%m', created_at) as month,
            SUM(amount) as monthly_income,
            COUNT(*) as transaction_count
        FROM commissions
        WHERE user_id = ? AND type = 'referral' AND status = 'completed'
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month DESC
        LIMIT 6
    ''', (user_id,))

    monthly_stats = cursor.fetchall()

    return {
        'main': dict(main_stats) if main_stats else {},
        'level': [dict(level) for level in level_stats],
        'monthly': [dict(month) for month in monthly_stats]
    }
#============ MAIN ROUTES =============#

@app.route('/')
def home():
    """Home page"""
    db = get_db()
    cursor = db.cursor()

    # Fetch active products
    try:
        cursor.execute("SELECT * FROM products WHERE is_active = 1 LIMIT 8")
        products = cursor.fetchall()
    except Exception:
        cursor.execute("SELECT * FROM products LIMIT 8")
        products = cursor.fetchall()

    # Wrap products for template
    wrapped_products = [RowWrapper(row) for row in products]
    
    return render_template('index.html',
                         products=wrapped_products,
                         lang=session.get('language', 'en'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        login_input = request.form.get('email')
        password = request.form.get('password', '')

        # Hash password with salt
        salt = "sooqkabeer_salt_"
        hashed_pw = hashlib.sha256((salt + password).encode()).hexdigest()

        db = get_db()
        
        # Check in users table
        user = db.execute('SELECT * FROM users WHERE email = ? OR username = ?',
                         (login_input, login_input)).fetchone()

        if user and user['password'] == hashed_pw:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'vendor':
                return redirect(url_for('vendor_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid username/email or password', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    referral_code = request.args.get('referral_code', '')

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            phone = request.form.get('phone', '').strip()
            ref_code = request.form.get('referral_code', '').strip()

            # Password match check
            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return render_template('register.html', referral_code=referral_code)

            db = get_db()
            cursor = db.cursor()

            # Check for existing email
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('Email already registered!', 'danger')
                return render_template('register.html', referral_code=referral_code)

            # Generate vendor ID
            cursor.execute("SELECT COUNT(id) FROM users")
            count = cursor.fetchone()[0]
            vendor_custom_id = f"HKO-{(count + 1):05d}"

            # Hash password
            password_hash = hash_password(password)

            # Insert user
            sql = """INSERT INTO users
                     (username, email, password, phone, role, is_active,
                      vendor_id_code, vendor_verified, referral_code, status)
                     VALUES (?, ?, ?, ?, 'customer', 1, ?, 0, ?, 'active')"""

            cursor.execute(sql, (username, email, password_hash, phone,
                                vendor_custom_id, ref_code))
            
            user_id = cursor.lastrowid
            
            # Generate referral code for new user
            user_ref_code = generate_referral_code(username)
            cursor.execute("UPDATE users SET referral_code = ? WHERE id = ?",
                         (user_ref_code, user_id))
            
            # Process referral if provided
            if ref_code:
                process_referral_signup(user_id, ref_code)

            db.commit()

            flash(f'Registration Successful!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')

    return render_template('register.html', referral_code=referral_code)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/change_language/<lang>')
def change_site_lang(lang):
    """Change site language"""
    if lang in ['en', 'ar']:
        session['language'] = lang
        session.permanent = True
    return redirect(request.referrer or url_for('home'))

@app.route('/products')
def products():
    """View all products"""
    db = get_db()
    cursor = db.cursor()

    category = request.args.get('category', '')
    search = request.args.get('search', '')

    query = "SELECT * FROM products WHERE is_active = 1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (name_en LIKE ? OR name_ar LIKE ? OR description LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    products_list = cursor.fetchall()

    # Get categories for filter
    cursor.execute("SELECT id FROM products LIMIT 1")
    categories = cursor.fetchall()

    # Wrap data for template
    wrapped_products = [RowWrapper(row) for row in products_list]
    wrapped_categories = [RowWrapper(row) for row in categories]

    return render_template('products.html',
                         products=wrapped_products,
                         categories=wrapped_categories,
                         selected_category=category,
                         search=search,
                         lang=session.get('lang', 'en'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT p.*, u.username as vendor_name
        FROM products p
        LEFT JOIN users u ON p.vendor_id = u.id
        WHERE p.id = ?
    ''', (product_id,))

    product_row = cursor.fetchone()

    if not product_row:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))

    # Increment views count
    cursor.execute("UPDATE products SET views = views + 1 WHERE id = ?", (product_id,))
    db.commit()

    wrapped_product = RowWrapper(product_row)

    return render_template('product_detail.html',
                         product=wrapped_product,
                         lang=session.get('lang', 'en'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password"""
    if request.method == 'POST':
        email = request.form.get('email')
        flash(f'Success: A reset link has been sent to {email}. Please check your inbox.', 'info')
        return redirect(url_for('login'))

    return render_template('vendor/forgot_password.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    from models import Vendor, db
    """Vendor login using SQLAlchemy Models"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        try:
            # Query vendor by email
            vendor = Vendor.query.filter_by(email=email).first()

            if vendor:
                from werkzeug.security import check_password_hash
                
                # Use password_hash as confirmed by previous DB error
                stored_pw = vendor.password_hash if hasattr(vendor, 'password_hash') else vendor.password
                
                if stored_pw and check_password_hash(stored_pw, password):
                    # Update last login
                    vendor.last_login = db.func.now()
                    db.session.commit()

                    # Initialize Session
                    session.clear()
                    session['user_id'] = vendor.id
                    session['role'] = 'vendor'
                    # Use vendor_name instead of business_name as per DB schema
                    session['vendor_name'] = vendor.vendor_name if hasattr(vendor, 'vendor_name') else "Vendor"
                    session['email'] = vendor.email
                    
                    if not vendor.vendor_code:
                        vendor.vendor_code = f"HKO-{vendor.id:03d}"
                        db.session.commit()
                    
                    session['vendor_code'] = vendor.vendor_code

                    flash('Login successful!', 'success')
                    return redirect(url_for('vendor_dashboard'))
                else:
                    flash('Invalid password', 'danger')
            else:
                flash('Email address not found', 'danger')
                
        except Exception as e:
            print(f"Login Error: {str(e)}")
            flash(f'System Error: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('vendor/vendor_login.html')

#============ VENDOR ROUTES =========================
#===================================================

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    """Vendor registration"""
    if request.method == 'POST':
        try:
            # Step 1: Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            country_code = request.form.get('country_code', '+965')
            nationality = request.form.get('nationality')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            business_name = request.form.get('business_name') or request.form.get('shop_name')
            business_type = request.form.get('business_type')
            cr_number = request.form.get('cr_number')
            vat_number = request.form.get('vat_number')
            governorate = request.form.get('governorate')
            block = request.form.get('block')
            street = request.form.get('street')
            building = request.form.get('building')
            floor = request.form.get('floor')
            unit = request.form.get('unit')
            business_description = request.form.get('business_description')
            
            civil_id_number = request.form.get('civil_id_number', '')
            agree_terms = request.form.get('agree_terms')

            # Step 2: Validation
            if password != confirm_password:
                flash('❌ Passwords do not match!', 'error')
                return redirect('/vendor/register')

            if not agree_terms:
                flash('❌ You must agree to the terms and conditions', 'error')
                return redirect('/vendor/register')

            # Step 3: Construct address
            address_parts = []
            if building: address_parts.append(building)
            if street: address_parts.append(street)
            if block: address_parts.append(f"Block {block}")
            if governorate: address_parts.append(governorate)
            address = ", ".join(address_parts) if address_parts else ""

            # Step 4: Database connection
            db = get_db_connection()
            cursor = db.cursor()

            # Check if email exists
            cursor.execute("SELECT id FROM vendors WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('❌ Email already registered!', 'error')
                db.close()
                return redirect('/vendor/register')

            # Check if CR number exists
            if cr_number:
                cursor.execute("SELECT id FROM vendors WHERE cr_number = ?", (cr_number,))
                if cursor.fetchone():
                    flash('❌ Commercial Registration number already registered!', 'error')
                    db.close()
                    return redirect('/vendor/register')

            # Step 5: Generate Vendor Code
            cursor.execute("SELECT MAX(id) FROM vendors")
            result = cursor.fetchone()
            next_id = 1 if result[0] is None else result[0] + 1
            vendor_code = f"HKO-{next_id:04d}"

            # Step 6: Password Hashing
            salt = "sooqkabeer_salt_"
            password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

            # Step 7: Handle file uploads
            civil_id_front_path = ""
            if 'civil_id_front' in request.files:
                file = request.files['civil_id_front']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_civil_id_front_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    civil_id_front_path = file_path

            civil_id_back_path = ""
            if 'civil_id_back' in request.files:
                file = request.files['civil_id_back']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_civil_id_back_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    civil_id_back_path = file_path

            commercial_license_path = ""
            if 'commercial_license' in request.files:
                file = request.files['commercial_license']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_commercial_license_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    commercial_license_path = file_path

            # Check required files
            if not civil_id_front_path:
                flash('❌ Civil ID Front is required!', 'error')
                db.close()
                return redirect('/vendor/register')

            if not civil_id_back_path:
                flash('❌ Civil ID Back is required!', 'error')
                db.close()
                return redirect('/vendor/register')

            if not commercial_license_path:
                flash('❌ Commercial License is required!', 'error')
                db.close()
                return redirect('/vendor/register')

            # Step 8: Insert into database
            cursor.execute("""
                INSERT INTO vendors (
                    name, email, password, shop_name, address,
                    civil_id, civil_id_path, vendor_code, status,
                    phone, country_code, nationality, business_type,
                    cr_number, vat_number, governorate, block, street,
                    building, floor, unit, business_description,
                    civil_id_back_path, commercial_license_path,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                name, email, password_hash, business_name, address,
                civil_id_number, civil_id_front_path, vendor_code, 'pending',
                phone, country_code, nationality, business_type,
                cr_number, vat_number, governorate, block, street,
                building, floor, unit, business_description,
                civil_id_back_path, commercial_license_path
            ))

            vendor_id = cursor.lastrowid

            # Step 9: Handle additional documents
            if 'additional_docs[]' in request.files:
                files = request.files.getlist('additional_docs[]')
                for i, file in enumerate(files):
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(f"{email}_additional_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)

                        cursor.execute("""
                            INSERT INTO vendor_documents (vendor_id, document_type, file_path, created_at)
                            VALUES (?, ?, ?, datetime('now'))
                        """, (vendor_id, 'additional', file_path))

            # Step 10: Commit transaction
            db.commit()

            # Step 11: Store in session for welcome page
            session['vendor_code'] = vendor_code
            session['business_name'] = business_name

            db.close()
            return redirect('/vendor/welcome-pending')

        except Exception as e:
            if 'db' in locals():
                db.rollback()
                db.close()
            flash(f'❌ Registration failed: {str(e)}', 'error')
            return redirect('/vendor/register')

    # GET request - Show the form
    return render_template('vendor/vendor_register.html')

@app.route('/vendor/welcome-pending')
def vendor_welcome_pending():
    """Welcome page after vendor registration"""
    vendor_code = session.get('vendor_code', 'N/A')
    business_name = session.get('business_name', 'Your Business')

    return render_template('vendor/welcome_pending.html',
                         vendor_code=vendor_code,
                         business_name=business_name)

@app.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    from datetime import datetime
    user_id = session.get('user_id')
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    try:
        # Get vendor ID for HKO-001
        user = cursor.execute("SELECT vendor_id FROM users WHERE id = ?", (user_id,)).fetchone()
        v_id = user['vendor_id'] if user and user['vendor_id'] else user_id

        # Get vendor profile
        vendor = cursor.execute("SELECT * FROM vendors WHERE id = ?", (v_id,)).fetchone()
        balance = vendor['balance'] if vendor else 0.0

        # Fetch stats directly into a dictionary to match dashboard.html
        o_row = cursor.execute("""
            SELECT
                COUNT(DISTINCT o.id) as total_orders,
                SUM(oi.price * oi.quantity) as total_sales
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE p.vendor_id = ?
        """, (v_id,)).fetchone()

        stats = {
            'total_orders': o_row['total_orders'] if o_row['total_orders'] else 0,
            'total_sales': o_row['total_sales'] if o_row['total_sales'] else 0.0
        }

        # Fetch products and orders list
        products = cursor.execute("SELECT * FROM products WHERE vendor_id = ?", (v_id,)).fetchall()
        orders = cursor.execute("""
            SELECT o.* FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE p.vendor_id = ?
            GROUP BY o.id ORDER BY o.created_at DESC LIMIT 5
        """, (v_id,)).fetchall()

        db.close()
        
        return render_template('vendor/dashboard.html',
                               vendor=vendor,
                               products=products,
                               stats=stats,
                               balance=balance,
                               orders=orders,
                               now=datetime.now())

    except Exception as e:
        if db: db.close()
        print(f"Error: {str(e)}")
        return f"Database Error: {str(e)}"

@app.route('/vendor/products')
@vendor_required
def vendor_products():
    """View vendor products - WITH DEBUG"""
    print(f"DEBUG: Session data: {dict(session)}")  # Debug line
    
    try:
        db = get_db_connection()
        db.row_factory = sqlite3.Row
        
        vendor_id = session.get('user_id')
        print(f"DEBUG: Vendor ID from session: {vendor_id}")  # Debug line
        
        if not vendor_id:
            flash('Please login first', 'warning')
            return redirect(url_for('vendor_login'))
        
        # Get vendor info
        vendor = db.execute(
            "SELECT * FROM vendors WHERE id = ?",
            (vendor_id,)
        ).fetchone()
        
        if not vendor:
            flash('Vendor not found', 'danger')
            return redirect(url_for('vendor_login'))
        
        print(f"DEBUG: Found vendor: {vendor['business_name']}")  # Debug line
        
        # Get products
        products = db.execute("""
            SELECT * FROM products
            WHERE id > 0 OR vendor_id = ?
            ORDER BY created_at DESC
        """, (vendor_id,)).fetchall()
        
        print(f"DEBUG: Found {len(products)} products")  # Debug line
        
        return render_template('vendor/products_list.html',
                             vendor=vendor,
                             products=products)
        
    except Exception as e:
        print(f"ERROR in vendor_products: {str(e)}")  # Debug line
        flash(f'Error loading products: {str(e)}', 'danger')
        return redirect(url_for('vendor_dashboard'))
    finally:
        db.close()

@app.route('/debug/session')
def debug_session():
    """Debug session data"""
    return jsonify({
        'session_data': dict(session),
        'user_id': session.get('user_id'),
        'role': session.get('role'),
        'vendor_name': session.get('vendor_name')
    })

@app.route('/debug/products')
@vendor_required
def debug_products():
    """Debug products route"""
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    
    vendor_id = session.get('user_id')
    products = db.execute(
        "SELECT id, name_en, status FROM products WHERE id > 0 OR vendor_id = ?", 
        (vendor_id,)
    ).fetchall()
    
    db.close()
    
    return jsonify({
        'vendor_id': vendor_id,
        'product_count': len(products),
        'products': [dict(p) for p in products]
    })

@app.route('/vendor/add-product', methods=['GET', 'POST'])
@login_required
def vendor_add_product():
    if request.method == 'GET':
        return render_template('vendor/add_product.html')

    db = get_db_connection()
    try:
        # ১. সব ডাটা রিসিভ করা (আপনার অরিজিনাল লজিক)
        name_en = request.form.get('name_en', '').strip()
        name_ar = request.form.get('name_ar', '').strip()
        desc_en = request.form.get('description_en', '').strip()
        desc_ar = request.form.get('description_ar', '').strip()
        price = float(request.form.get('retail_price', 0))
        cost_price = float(request.form.get('cost_price', 0))
        b2b_price = float(request.form.get('b2b_price', price))
        stock = int(request.form.get('stock_quantity', 0))
        sku = request.form.get('sku') or f"HKO-{int(time.time())}"
        vendor_id = session.get('user_id')

        # ২. ফাইল হ্যান্ডলিং
        main_image = request.files.get('main_image')
        video_file = request.files.get('video_file')
        
        image_path = save_file(main_image, 'products') if main_image else ""
        video_path = save_file(video_file, 'videos') if video_file else ""
        video_type = 'file' if video_path else 'none'

        # ৩. ডাটাবেস ইনসার্ট (নতুন কলামসহ)
        cursor = db.cursor()
        sql = """INSERT INTO products
                 (name_en, name_ar, description_en, description_ar, sku, 
                  price, b2b_price, cost_price, stock_quantity, 
                  image_url, video_url, video_type, vendor_id, status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')"""
        
        cursor.execute(sql, (
            name_en, name_ar, desc_en, desc_ar, sku,
            price, b2b_price, cost_price, stock,
            image_path, video_path, video_type, vendor_id
        ))
        
        db.commit()
        flash('Success! Product added and waiting for review.', 'success')
        return redirect(url_for('vendor_dashboard'))

    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        flash(f'System Error: {str(e)}', 'danger')
        return render_template('vendor/add_product.html')
    finally:
        db.close()

@app.route('/vendor/edit_product/<int:product_id>', methods=['GET', 'POST'])
@vendor_required
def vendor_edit_product(product_id):
    """Edit product (vendor)"""
    db = get_db_connection()
    cursor = db.cursor()

    # Check product ownership
    cursor.execute("SELECT vendor_id FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if not product or product['vendor_id'] != session.get('user_id'):
        flash('Access denied or product not found', 'danger')
        return redirect(url_for('vendor_dashboard'))

    if request.method == 'POST':
        try:
            name_en = request.form['name_en']
            name_ar = request.form.get('name_ar', '')
            description_en = request.form['description_en']
            description_ar = request.form.get('description_ar', '')
            price = float(request.form['price'])
            unit = request.form['unit']
            category = request.form['category']
            stock_quantity = float(request.form.get('stock_quantity', 0))
            image_url = request.form.get('image_url', '')
            is_active = 1 if request.form.get('is_active') else 0

            cursor.execute('''
                UPDATE products
                SET name_en = ?, name_ar = ?, description_en = ?, description_ar = ?,
                    price = ?, unit = ?, category = ?, stock_quantity = ?,
                    image_url = ?, is_active = ?
                WHERE id = ? AND vendor_id = ?
            ''', (name_en, name_ar, description_en, description_ar,
                  price, unit, category, stock_quantity,
                  image_url, is_active, product_id, session['user_id']))

            db.commit()
            flash('Product updated successfully', 'success')
            return redirect(url_for('vendor_dashboard'))

        except Exception as e:
            db.rollback()
            flash(f'Failed to update product: {str(e)}', 'danger')

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product_data = cursor.fetchone()

    return render_template('vendor_edit_product.html', product=product_data)

#======== VENDOR PROFILE ROUT =========

@app.route('/vendor/create-profile', methods=['GET'])
@login_required
def vendor_profile_setup():
    """Show vendor profile setup form"""
    user_id = session.get('user_id')
    
    # Get database connection
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    
    vendor_data = None
    try:
        # First get vendor_id from users table
        user = db.execute("SELECT vendor_id FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user['vendor_id']:
            # If user has vendor_id, get vendor info
            vendor = db.execute(
                "SELECT vendor_name, phone, address FROM vendors WHERE id = ?", 
                (user['vendor_id'],)
            ).fetchone()
            
            if vendor:
                vendor_data = {
                    'shop_name_en': vendor['vendor_name'],
                    'phone': vendor['phone'],
                    'location': vendor['address']
                }
    except Exception as e:
        print(f"Error fetching vendor data: {e}")
    finally:
        db.close()

    return render_template('vendor/vendor_profile_setup.html', vendor_data=vendor_data)


@app.route('/vendor/create-profile', methods=['POST'])
@login_required
def vendor_create_profile():
    """Create or update vendor profile"""
    if request.method == 'POST':
        shop_name_en = request.form.get('shop_name_en')
        phone = request.form.get('phone')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Password validation
        if password and password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('vendor_profile_setup'))
        
        db = get_db_connection()
        db.row_factory = sqlite3.Row
        user_id = session.get('user_id')
        
        try:
            # Get user email
            user_email = db.execute(
                "SELECT email FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            email = user_email['email'] if user_email else ''
            
            # Check existing vendor link
            user = db.execute(
                "SELECT vendor_id FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            current_vendor_id = user['vendor_id'] if user else None
            
            if current_vendor_id:
                # Update existing vendor
                update_query = """
                    UPDATE vendors
                    SET vendor_name = ?, phone = ?, address = ?, status = 'approved'
                    WHERE id = ?
                """
                db.execute(update_query, (shop_name_en, phone, location, current_vendor_id))
                
                # Update password if provided
                if password:
                    password_hash = hash_password(password)
                    db.execute(
                        "UPDATE vendors SET password_hash = ? WHERE id = ?",
                        (password_hash, current_vendor_id)
                    )
                
                vendor = db.execute(
                    "SELECT vendor_code FROM vendors WHERE id = ?", 
                    (current_vendor_id,)
                ).fetchone()
                vendor_code = vendor['vendor_code'] if vendor else "HKO-001"
                
                flash('Profile updated successfully!', 'success')
            else:
                # Generate next HKO vendor code
                last_vendor = db.execute(
                    "SELECT vendor_code FROM vendors WHERE vendor_code LIKE 'HKO-%' ORDER BY id DESC LIMIT 1"
                ).fetchone()
                
                if last_vendor:
                    try:
                        last_num = int(last_vendor['vendor_code'].split('-')[1])
                        next_num = last_num + 1
                    except:
                        next_num = 1
                else:
                    next_num = 1
                
                vendor_code = f"HKO-{next_num:03d}"
                
                # Hash password
                password_hash = hash_password(password) if password else hash_password("vendor123")
                
                # Insert new vendor
                insert_query = """
                    INSERT INTO vendors (vendor_code, vendor_name, email, phone, address, password_hash, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'approved')
                """
                cursor = db.execute(
                    insert_query,
                    (vendor_code, shop_name_en, email, phone, location, password_hash)
                )
                
                current_vendor_id = cursor.lastrowid
                
                # Update user with vendor_id
                db.execute(
                    "UPDATE users SET vendor_id = ? WHERE id = ?", 
                    (current_vendor_id, user_id)
                )
                
                flash('Vendor profile created successfully!', 'success')
            
            db.commit()
            
            # Set vendor session
            session['vendor_id'] = current_vendor_id
            session['vendor_code'] = vendor_code
            
            return redirect(url_for('vendor_dashboard'))
            
        except Exception as e:
            db.rollback()
            print(f"Error creating vendor profile: {e}")
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('vendor_profile_setup'))
        finally:
            db.close()
    
    return redirect(url_for('vendor_profile_setup'))

@app.route('/vendor/orders')
@vendor_required
def vendor_orders():
    user_id = session.get('user_id')
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    
    # Base query
    query = """
        SELECT
            oi.*,
            p.name_en as product_name,
            p.name_ar as product_name_ar,
            o.order_number,
            o.status as order_status,
            o.total_amount,
            o.customer_name,
            o.customer_phone,
            o.created_at as order_date
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE p.vendor_id = ?
    """
    
    params = [user_id]
    
    # Apply status filter
    if status_filter != 'all':
        query += " AND o.status = ?"
        params.append(status_filter)
    
    # Order by
    query += " ORDER BY o.created_at DESC"
    
    orders = db.execute(query, params).fetchall()
    
    # Get stats
    stats_query = """
        SELECT
            COUNT(*) as total_orders,
            SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
            SUM(CASE WHEN o.status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
            SUM(oi.quantity * oi.price) as total_revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE p.vendor_id = ?
    """
    stats = db.execute(stats_query, (user_id,)).fetchone()
    
    db.close()
    
    return render_template('vendor/orders.html',
                         orders=orders,
                         stats=stats,
                         status_filter=status_filter)

@app.route('/vendor/orders/<int:order_id>/update', methods=['POST'])
@vendor_required
def update_order_status(order_id):
    """Update order status (vendor) with security check"""
    status = request.form.get('status')
    vendor_id = session.get('user_id')
    db = get_db_connection()
    
    # Verify if this order actually belongs to the logged-in vendor
    check = db.execute("""
        SELECT 1 FROM order_items
        WHERE order_id = ? AND vendor_id = ?
    """, (order_id, vendor_id)).fetchone()

    if check:
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        db.commit()
        flash('Order status updated successfully!', 'success')
    else:
        flash('Unauthorized action!', 'danger')
        
    db.close()
    return redirect(url_for('vendor_orders'))

@app.route('/vendor/earnings')
@vendor_required
def vendor_earnings():
    user_id = session.get('user_id')
    db = get_db_connection()
    db.row_factory = sqlite3.Row

    # Calculate total earnings and pending balance using subqueries
    earnings_query = """
        SELECT
            (SELECT IFNULL(SUM(amount), 0.0) FROM commissions 
             WHERE id > 0 OR vendor_id = ? AND status = 'completed') as total_earned,
            (SELECT IFNULL(SUM(amount), 0.0) FROM commissions 
             WHERE id > 0 OR vendor_id = ? AND status = 'pending') as pending_balance
    """
    
    earnings = db.execute(earnings_query, (user_id, user_id)).fetchone()

    # Fetch complete commission history for the table
    history = db.execute("""
        SELECT * FROM commissions
        WHERE id > 0 OR vendor_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    
    db.close()
    return render_template('vendor/earnings.html', earnings=earnings, history=history)

# Vendor Wallet Route
@app.route('/vendor/wallet', methods=['GET', 'POST'])
def vendor_wallet():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
    
    # Check if user is vendor
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user or not user.is_vendor:
        flash('Access denied. Vendor account required.', 'danger')
        return redirect(url_for('index'))
    
    # Get vendor's current balance
    balance = user.balance
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
            method = request.form.get('method')
            details = request.form.get('details')
            
            # Validate amount
            if amount <= 0:
                flash('Please enter a valid amount', 'danger')
            elif amount > balance:
                flash('Insufficient balance', 'danger')
            elif amount < 5.000:
                flash('Minimum withdrawal amount is KWD 5.000', 'danger')
            elif not method:
                flash('Please select a payment method', 'danger')
            elif not details:
                flash('Please provide account details', 'danger')
            else:
                # Create withdrawal record
                withdrawal = Withdrawal(
                    vendor_id=user_id,
                    amount=amount,
                    method=method,
                    account_details=details,
                    status='pending'
                )
                
                # Update vendor balance (temporarily hold the amount)
                user.balance -= amount
                
                db.session.add(withdrawal)
                db.session.commit()
                
                flash(f'Withdrawal request of KWD {amount:.3f} submitted successfully!', 'success')
                return redirect(url_for('vendor_wallet'))
                
        except ValueError:
            flash('Please enter a valid amount', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('vendor/wallet.html', balance=balance)

@app.route('/vendor/withdraw', methods=['GET', 'POST'])
@vendor_required
def vendor_withdraw():
    """Vendor withdrawal"""
    vendor_id = session['user_id']

    if request.method == 'POST':
        amount = float(request.form['amount'])

        # Validation
        if amount < MIN_WITHDRAWAL_LIMIT:
            flash(f'Minimum withdrawal: {MIN_WITHDRAWAL_LIMIT} KWD', 'warning')
            return render_template('vendor/withdraw.html')

        db = get_db_connection()
        balance = db.execute(
            'SELECT available_balance FROM vendor_balances WHERE id > 0 OR vendor_id = ?',
            (vendor_id,)
        ).fetchone()

        if balance and balance['available_balance'] >= amount:
            # Create withdrawal request
            withdrawal_id = db.execute(
                'INSERT INTO withdrawals (vendor_id, amount, status) VALUES (?, ?, ?)',
                (vendor_id, amount, 'pending')
            ).lastrowid

            # Deduct from balance
            db.execute(
                'UPDATE vendor_balances SET available_balance = available_balance - ?, '
                'pending_withdrawals = pending_withdrawals + ?, last_updated = CURRENT_TIMESTAMP '
                'WHERE id > 0 OR vendor_id = ?',
                (amount, amount, vendor_id)
            )

            db.commit()
            db.close()
            flash(f'Withdrawal request {amount} KWD submitted! (ID: #{withdrawal_id})', 'success')
            return redirect(url_for('vendor_dashboard'))

        flash('Insufficient balance!', 'danger')
        db.close()

    # Show withdrawal form
    db = get_db_connection()
    balance = db.execute('SELECT * FROM vendor_balances WHERE id > 0 OR vendor_id = ?', (vendor_id,)).fetchone()
    db.close()

    return render_template('vendor/withdraw.html', balance=balance)

@app.route('/vendor/financials')
@vendor_required
def vendor_financials():
    """Vendor financials"""
    vendor_id = session['user_id']
    db = get_db_connection()

    # Get balance summary
    balance = db.execute('SELECT * FROM vendor_balances WHERE id > 0 OR vendor_id = ?', (vendor_id,)).fetchone()

    # Recent transactions
    transactions = db.execute("""
        SELECT * FROM financial_transactions
        WHERE id > 0 OR vendor_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (vendor_id,)).fetchall()

    # Pending withdrawals
    withdrawals = db.execute("""
        SELECT * FROM withdrawals
        WHERE id > 0 OR vendor_id = ? AND status = 'pending'
        ORDER BY requested_at DESC
    """, (vendor_id,)).fetchall()

    db.close()
    return render_template('vendor/financials.html',
                         balance=balance,
                         transactions=transactions,
                         withdrawals=withdrawals)

@app.route('/vendor/upload-kyc', methods=['GET', 'POST'])
@vendor_required
def upload_kyc():
    """Upload KYC documents and update vendor status"""
    if request.method == 'POST':
        # In a real scenario, you would handle file saving here
        # Example: file = request.files['kyc_document']
        
        db = get_db_connection()
        vendor_id = session.get('user_id')
        
        # Update vendor status to 'pending_verification' if you have that column
        try:
            db.execute("UPDATE vendors SET status = 'pending' WHERE id = ?", (vendor_id,))
            db.commit()
            flash("KYC Documents submitted successfully! Waiting for admin approval.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error submitting KYC: {str(e)}", "danger")
        finally:
            db.close()
            
        return redirect(url_for('vendor_dashboard'))
        
    return render_template('vendor/upload_kyc.html')

@app.route('/vendor/logout')
def vendor_logout():
    """Vendor logout"""
    session.clear()
    return redirect(url_for('vendor_login'))

#============ ADMIN ROUTES =============#

@app.route('/admin')
@admin_required
def admin_redirect():
    """Redirect admin to dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Security check
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.row_factory = sqlite3.Row

    # Fetching stats
    total_products = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    # Commission calculation
    comm_data = db.execute('SELECT SUM(total_price * 0.1) FROM orders').fetchone()
    total_commissions = comm_data[0] if comm_data and comm_data[0] else 0

    # Packing stats
    stats = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_commissions
    }

    # Recent data
    recent_users = db.execute('''
        SELECT id, username, email, role, status FROM users
        ORDER BY id DESC LIMIT 5
    ''').fetchall()

    recent_orders = db.execute("""
        SELECT o.*, u.username as customer_name
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 5
    """).fetchall()

    return render_template('admin/admin_dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_orders=recent_orders)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage users"""
    db = get_db()
    cursor = db.cursor()

    try:
        # Dynamic column selection
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]

        # Select all available columns
        select_columns = ', '.join(column_names)

        # Determine order by column
        order_column = 'created_at' if 'created_at' in column_names else 'id'

        query = f'''
            SELECT {select_columns}
            FROM users
            ORDER BY {order_column} DESC
        '''

        cursor.execute(query)
        users = cursor.fetchall()

        return render_template('admin/users.html',
                             users=users,
                             column_names=column_names)

    except Exception as e:
        return f"Error fetching users: {str(e)}"

@app.route('/admin/vendors')
@admin_required
def admin_vendors():
    """Manage vendors"""
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    try:
        # Check if vendors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendors'")
        if not cursor.fetchone():
            return render_template('admin/vendors.html', vendors=[], total=0, licensed=0, pending=0)

        # Get vendor data
        cursor.execute("""
            SELECT id, company_name, vendor_code, kyc_status,
                   total_earnings, commission_rate, created_at
            FROM vendors
            ORDER BY created_at DESC
        """)
        vendors = cursor.fetchall()

        # Stats
        total_v = len(vendors)
        verified_v = sum(1 for v in vendors if v['kyc_status'] == 'verified')
        pending_v = total_v - verified_v

    except Exception as e:
        print(f"VENDORS ERROR: {str(e)}")
        vendors = []
        total_v, verified_v, pending_v = 0, 0, 0

    return render_template('admin/vendors.html',
                           vendors=vendors,
                           total=total_v,
                           licensed=verified_v,
                           pending=pending_v)

@app.route('/admin/approve-vendor/<int:v_id>')
@admin_required
def approve_vendor(v_id):
    """Approve vendor"""
    db = get_db()
    cursor = db.cursor()

    # Update vendors table
    cursor.execute('''
        UPDATE vendors
        SET kyc_status = 'verified', vendor_verified = 1
        WHERE id = ?
    ''', (v_id,))

    # Update users table
    cursor.execute('''
        UPDATE users
        SET role = 'vendor'
        WHERE id = (SELECT user_id FROM vendors WHERE id = ?)
    ''', (v_id,))

    db.commit()
    flash('Vendor approved successfully!', 'success')
    return redirect(url_for('admin_vendors'))

@app.route('/admin/vendors/add', methods=['GET', 'POST'])
@admin_required
def admin_add_vendor():
    """Add vendor (admin)"""
    from werkzeug.security import generate_password_hash

    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            phone = request.form.get('phone', '').strip()
            status = request.form.get('status', 'active')

            if not all([username, password]):
                flash('Username and Password are required!', 'danger')
                return render_template('admin/add_vendor.html')

            # Hash password
            hashed_pw = generate_password_hash(password)

            cursor.execute('''
                INSERT INTO users (username, email, password, phone, role, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, hashed_pw, phone, 'vendor', status))

            db.commit()
            flash('Vendor added successfully!', 'success')
            return redirect(url_for('admin_vendors'))

        except sqlite3.IntegrityError:
            db.rollback()
            flash('Username or Email already exists!', 'danger')
        except Exception as e:
            db.rollback()
            print(f"ERROR: {str(e)}")
            flash(f'System Error: {str(e)}', 'danger')

    return render_template('admin/add_vendor.html')

@app.route('/admin/products')
@admin_required
def admin_products():
    """Manage products (admin)"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add product (admin)"""
    db = get_db()
    if request.method == 'POST':
        # Get form data
        name_en = request.form.get('name_en')
        name_ar = request.form.get('name_ar')
        short_desc_en = request.form.get('short_description_en')
        short_desc_ar = request.form.get('short_description_ar')
        detailed_desc = request.form.get('detailed_description')
        
        price = request.form.get('price')
        b2b_price = request.form.get('b2b_price')
        cost_price = request.form.get('cost_price')
        stock = request.form.get('stock')
        sku = request.form.get('sku')
        
        category_id = request.form.get('category_id')
        vendor_id = request.form.get('vendor_id')
        status = request.form.get('status')

        # Image handling
        image = request.files.get('main_image')
        filename = ""
        if image and image.filename != '':
            filename = image.filename
            image.save(f"static/uploads/{filename}")

        # Save to database
        db.execute('''INSERT INTO products
            (name_en, name_ar, price, b2b_price, stock, category_id, vendor_id, image, sku, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name_en, name_ar, price, b2b_price, stock, category_id, vendor_id, filename, sku, status))
        db.commit()
        return redirect(url_for('admin_dashboard'))

    # Get data for dropdowns
    categories = db.execute('SELECT * FROM categories').fetchall()
    vendors = db.execute('SELECT * FROM users WHERE role="vendor"').fetchall()

    return render_template('admin/add_product.html', categories=categories, vendors=vendors)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product (admin)"""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        try:
            # Get form data
            name_ar = request.form.get('name_ar')
            name_en = request.form.get('name_en')
            category_id = request.form.get('category_id')
            price = request.form.get('price')
            b2b_price = request.form.get('b2b_price') or 0
            stock = request.form.get('stock') or 0
            unit = request.form.get('unit') or 'pcs'
            min_qty = request.form.get('min_qty') or 1
            admin_commission = request.form.get('admin_commission') or 10.0

            # Image handling
            image_file = request.files.get('image')
            image_name = product['image']

            if image_file and image_file.filename != '':
                from werkzeug.utils import secure_filename
                import os
                image_name = secure_filename(image_file.filename)
                image_file.save(os.path.join('static/images/products', image_name))

            # Update database
            db.execute("""
                UPDATE products SET
                name_ar=?, name_en=?, category_id=?, price=?, b2b_price=?,
                stock=?, unit=?, min_qty=?, admin_commission=?, image=?
                WHERE id=?
            """, (name_ar, name_en, category_id, price, b2b_price,
                  stock, unit, min_qty, admin_commission, image_name, product_id))

            db.commit()
            flash('تم التحديث بنجاح (Product Updated!)', 'success')
            return redirect(url_for('admin_products'))

        except Exception as e:
            print(f"EDIT ERROR: {str(e)}")
            flash('Error updating product', 'danger')

    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/products/<int:product_id>/delete')
@admin_required
def admin_delete_product(product_id):
    """Delete product (admin)"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash('تم حذف المنتج بنجاح (Product Deleted)', 'success')
    except Exception as e:
        print(f"DELETE ERROR: {str(e)}")
        flash('Error occurred during deletion', 'danger')

    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Manage orders (admin)"""
    db = get_db()
    cursor = db.cursor()

    # Check if created_at exists
    cursor.execute("PRAGMA table_info(orders)")
    order_columns = [col[1] for col in cursor.fetchall()]

    if 'created_at' in order_columns:
        cursor.execute('''
            SELECT o.*, u.username as customer_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        ''')
    else:
        cursor.execute('''
            SELECT o.*, u.username as customer_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.id DESC
        ''')

    orders = cursor.fetchall()

    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Order details (admin)"""
    db = get_db()
    db.row_factory = sqlite3.Row

    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

    if not order:
        return "Order not found", 404

    items = db.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()

    return render_template('order_detail.html', order=order, items=items)

@app.route('/admin/update-order-status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    """Update order status (admin)"""
    new_status = request.form.get('status')
    db = get_db()

    db.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))

    if new_status == 'completed':
        order = db.execute('SELECT total_price, referrer_id_code FROM orders WHERE id = ?', (order_id,)).fetchone()

        if order and order['referrer_id_code']:
            commission_amount = order['total_price'] * 0.03

            db.execute('''
                INSERT INTO commissions (order_id, referrer_id_code, amount, status, created_at)
                VALUES (?, ?, ?, 'paid', CURRENT_TIMESTAMP)
            ''', (order_id, order['referrer_id_code'], commission_amount))

    db.commit()
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/commissions')
@admin_required
def admin_commissions():
    """Manage commissions (admin)"""
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch all commissions
    cursor.execute("SELECT * FROM commissions ORDER BY created_at DESC")
    commissions = cursor.fetchall()

    # Calculate summary
    cursor.execute('''
        SELECT
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_total,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_total,
            COUNT(*) as total_commissions
        FROM commissions
    ''')
    summary = cursor.fetchone()

    return render_template('admin/admin_commissions.html', commissions=commissions, summary=summary)

@app.route('/admin/approve_commission/<int:commission_id>')
@admin_required
def approve_commission(commission_id):
    """Approve commission (admin)"""
    db = get_db()
    db.execute('''
        UPDATE commissions
        SET status = 'paid', paid_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (commission_id,))
    db.commit()

    return redirect(url_for('admin_commissions'))

@app.route('/admin/withdrawals')
@admin_required
def admin_withdrawals():
    """Manage withdrawals (admin)"""
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch all withdrawals
    cursor.execute('''
        SELECT w.*, u.username, u.email, u.wallet_balance
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        ORDER BY w.created_at DESC
    ''')
    withdrawals_list = cursor.fetchall()

    return render_template('admin/admin_withdrawals.html', withdrawals=withdrawals_list)

@app.route('/admin/process_withdrawal/<int:withdrawal_id>')
@admin_required
def process_withdrawal(withdrawal_id):
    """Process withdrawal (admin)"""
    db = get_db()
    cursor = db.cursor()

    try:
        withdrawal = db.execute(
            'SELECT user_id, amount FROM withdrawals WHERE id = ?',
            (withdrawal_id,)
        ).fetchone()

        if withdrawal:
            cursor.execute('''
                UPDATE withdrawals
                SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (withdrawal_id,))

            cursor.execute('''
                UPDATE users
                SET wallet_balance = wallet_balance - ?
                WHERE id = ?
            ''', (withdrawal['amount'], withdrawal['user_id']))

            db.commit()

    except Exception as e:
        db.rollback()

    return redirect(url_for('admin_withdrawals'))

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM settings")
    settings = cursor.fetchall()

    settings_dict = {}
    for setting in settings:
        settings_dict[setting[1]] = setting[2]

    return render_template('admin/admin_settings.html', settings=settings_dict)

@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Admin messages"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT m.*, u.username, u.email
        FROM messages m
        LEFT JOIN users u ON m.user_id = u.id
        ORDER BY m.created_at DESC
        LIMIT 50
    """)
    messages = cursor.fetchall()

    return render_template('admin/admin_messages.html', messages=messages)

@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Admin reports"""
    db = get_db()
    cursor = db.cursor()

    # Sales report
    cursor.execute("""
        SELECT
            DATE(created_at) as date,
            COUNT(*) as order_count,
            SUM(total_price) as total_sales,
            AVG(total_price) as avg_order_value
        FROM orders
        WHERE created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)
    sales_report = cursor.fetchall()

    # Product report
    cursor.execute("""
        SELECT
            p.name_en,
            p.category,
            COUNT(oi.id) as units_sold,
            SUM(oi.quantity * oi.unit_price) as revenue,
            p.stock_quantity
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.id
        ORDER BY revenue DESC
        LIMIT 20
    """)
    product_report = cursor.fetchall()

    return render_template('admin/admin_reports.html',
                         sales_report=sales_report,
                         product_report=product_report)

@app.route('/force-admin')
def force_admin():
    """Force admin login (for testing)"""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE role = 'admin'").fetchone()

    if user:
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = 'admin'
        session['admin_logged_in'] = True
        session['language'] = 'ar'
        return redirect(url_for('admin_dashboard'))
    else:
        return "No admin user found in database. Please create an admin first."

#============ ORDER & CART SYSTEM =============#

@app.route('/cart')
@login_required
def cart():
    """View shopping cart"""
    cart_items = session.get('cart', [])

    db = get_db()
    cursor = db.cursor()

    cart_details = []
    total = 0

    for item in cart_items:
        cursor.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],))
        product = cursor.fetchone()

        if product:
            item_total = item['quantity'] * product['price']
            total += item_total

            cart_details.append({
                'product': dict(product),
                'quantity': item['quantity'],
                'item_total': item_total
            })

    return render_template('cart.html', cart_items=cart_details, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = float(request.form.get('quantity', 1))

    # Check stock
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT stock_quantity FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if not product or product['stock_quantity'] < quantity:
        flash('Insufficient stock', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

    # Add to cart
    cart = session.get('cart', [])

    # Check if product already in cart
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'product_id': product_id,
            'quantity': quantity
        })

    session['cart'] = cart
    session.modified = True

    flash('Product added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    """Update cart item quantity"""
    quantity = float(request.form.get('quantity', 0))

    cart = session.get('cart', [])

    if quantity <= 0:
        # Remove item
        cart = [item for item in cart if item['product_id'] != product_id]
    else:
        # Update quantity
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break

    session['cart'] = cart
    session.modified = True

    flash('Cart updated', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    if request.method == 'POST':
        shipping_address = request.form['shipping_address']
        notes = request.form.get('notes', '')

        db = get_db()
        cursor = db.cursor()

        # Calculate total from cart
        cart_items = session.get('cart', [])
        if not cart_items:
            flash('Cart is empty', 'danger')
            return redirect(url_for('cart'))

        total_price = 0
        order_items = []

        for item in cart_items:
            cursor.execute("SELECT id, price, stock_quantity FROM products WHERE id = ?",
                         (item['product_id'],))
            product = cursor.fetchone()

            if not product:
                continue

            if product['stock_quantity'] < item['quantity']:
                flash(f"Insufficient stock for product ID: {product['id']}", 'danger')
                return redirect(url_for('cart'))

            item_total = item['quantity'] * product['price']
            total_price += item_total

            order_items.append({
                'product_id': product['id'],
                'quantity': item['quantity'],
                'unit_price': product['price'],
                'total_price': item_total
            })

        # Create order
        cursor.execute('''
            INSERT INTO orders (user_id, total_price, shipping_address, notes, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (session['user_id'], total_price, shipping_address, notes))

        order_id = cursor.lastrowid

        # Add order items
        for item in order_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'],
                  item['unit_price'], item['total_price']))

            # Update product stock
            cursor.execute('''
                UPDATE products
                SET stock_quantity = stock_quantity - ?,
                    total_sales = total_sales + 1
                WHERE id = ?
            ''', (item['quantity'], item['product_id']))

        # Update user stats
        cursor.execute('''
            UPDATE users
            SET total_orders = total_orders + 1,
                total_spent = total_spent + ?
            WHERE id = ?
        ''', (total_price, session['user_id']))

        # Process commissions
        process_order_commissions(order_id)

        db.commit()

        # Clear cart
        session.pop('cart', None)

        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_history'))

    return render_template('checkout.html')

@app.route('/orders')
@login_required
def order_history():
    """View user's order history"""
    db = get_db()
    cursor = db.cursor()

    # Get orders with item count
    cursor.execute('''
        SELECT o.*,
        (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as items_count
        FROM orders o
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (session['user_id'],))

    orders = cursor.fetchall()

    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """View detailed information of a specific order"""
    db = get_db()
    cursor = db.cursor()

    # Check order ownership
    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('order_history'))

    if order['user_id'] != session['user_id'] and not session.get('admin_logged_in'):
        flash('Access denied', 'danger')
        return redirect(url_for('order_history'))

    # Get order info
    cursor.execute('''
        SELECT o.*, u.username, u.email, u.phone
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,))
    order_info = cursor.fetchone()

    # Get order items
    cursor.execute('''
        SELECT oi.*, p.name_en, p.name_ar, p.image_url
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items = cursor.fetchall()

    return render_template('order_detail.html', order=order_info, items=items)

#============ REFERRAL DASHBOARD =============#

@app.route('/referral')
@login_required
def referral_dashboard():
    """Complete referral dashboard with stats and history"""
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.cursor()

    # Get current user details
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    current_user = cursor.fetchone()

    # Get referral stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_refs,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_refs,
            SUM(total_spent) as total_sales,
            SUM(total_commission) as total_earned
        FROM users
        WHERE referred_by = ?
    """, (current_user['referral_code'],))

    stats_data = cursor.fetchone()
    referral_stats = {
        'total_referrals': stats_data[0] if stats_data[0] else 0,
        'active_referrals': stats_data[1] if stats_data[1] else 0,
        'total_referred_sales': stats_data[2] if stats_data[2] else 0,
        'total_earned': stats_data[3] if stats_data[3] else 0,
        'available_balance': current_user['wallet_balance']
    }

    # Get referrals list
    cursor.execute("""
        SELECT username, email, created_at, is_active, total_orders, total_spent
        FROM users
        WHERE referred_by = ?
        ORDER BY created_at DESC
    """, (current_user['referral_code'],))
    referrals = cursor.fetchall()

    # Get commission history
    cursor.execute("""
        SELECT c.*, u.username as referred_user_name
        FROM commissions c
        LEFT JOIN users u ON c.referred_user_id = u.id
        WHERE c.user_id = ? AND c.type = 'referral'
        ORDER BY c.created_at DESC
        LIMIT 15
    """, (user_id,))
    commissions = cursor.fetchall()

    referral_url = f"{request.host_url}register?ref={current_user['referral_code']}"

    return render_template('referral_dashboard.html',
                         user=current_user,
                         referral_stats=referral_stats,
                         referrals=referrals,
                         commissions=commissions,
                         referral_url=referral_url,
                         referral_rate=REFERRAL_RATE,
                         min_withdrawal=MIN_WITHDRAWAL)

@app.route('/referral/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw_earnings():
    """Withdraw referral earnings"""
    if request.method == 'POST':
        amount = float(request.form['amount'])
        method = request.form['method']
        account = request.form['account']

        if amount < MIN_WITHDRAWAL:
            flash(f'Minimum withdrawal amount is ${MIN_WITHDRAWAL}', 'danger')
            return redirect(url_for('withdraw_earnings'))

        db = get_db()
        cursor = db.cursor()

        # Check balance
        cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

        if amount > user['wallet_balance']:
            flash('Insufficient balance', 'danger')
            return redirect(url_for('withdraw_earnings'))

        try:
            # Create withdrawal record
            cursor.execute('''
                INSERT INTO withdrawals (user_id, amount, method, account_details, status)
                VALUES (?, ?, ?, ?, 'pending')
            ''', (session['user_id'], amount, method, account))

            # Update wallet balance
            cursor.execute('''
                UPDATE users
                SET wallet_balance = wallet_balance - ?
                WHERE id = ?
            ''', (amount, session['user_id']))

            db.commit()

            flash('Withdrawal request submitted successfully', 'success')
            return redirect(url_for('referral_dashboard'))

        except Exception as e:
            db.rollback()
            flash(f'Withdrawal failed: {str(e)}', 'danger')

    # Get balance info
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    return render_template('withdraw.html',
                         balance=user['wallet_balance'] if user else 0,
                         min_withdrawal=MIN_WITHDRAWAL)

@app.route('/referral/withdraw', methods=['POST'])
@login_required
def request_withdrawal():
    """Request withdrawal of referral earnings (API)"""
    user_id = session.get('user_id')
    amount = request.json.get('amount')
    method = request.json.get('method')
    account_details = request.json.get('account_details')

    if not all([amount, method, account_details]):
        return jsonify({'success': False, 'error': 'All fields are required'})

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'})

    db = get_db()
    cursor = db.cursor()

    # Check user balance
    cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or user['wallet_balance'] < amount:
        return jsonify({'success': False, 'error': 'Insufficient balance'})

    if amount < MIN_WITHDRAWAL:
        return jsonify({'success': False, 'error': f'Minimum withdrawal is {MIN_WITHDRAWAL} KD'})

    try:
        # Create withdrawal request
        cursor.execute("""
            INSERT INTO withdrawals (user_id, amount, method, account_details, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (user_id, amount, method, account_details))

        # Deduct from wallet
        cursor.execute("""
            UPDATE users
            SET wallet_balance = wallet_balance - ?
            WHERE id = ?
        """, (amount, user_id))

        db.commit()
        return jsonify({'success': True, 'message': 'Withdrawal request submitted'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)})

#============ API ROUTES =============#

@app.route('/api/user_stats')
@login_required
def api_user_stats():
    """API: Get user statistics"""
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT
            total_orders,
            total_spent,
            wallet_balance,
            total_commission,
            direct_referrals,
            indirect_referrals,
            total_referrals
        FROM users
        WHERE id = ?
    ''', (user_id,))

    stats = cursor.fetchone()

    return jsonify(dict(stats) if stats else {})

@app.route('/api/referral_stats')
@login_required
def api_referral_stats():
    """API: Get referral statistics"""
    user_id = session['user_id']
    stats = get_referral_stats(user_id)

    return jsonify(stats)

@app.route('/api/withdraw', methods=['POST'])
@login_required
def api_withdraw():
    """API: Request withdrawal"""
    data = request.json
    amount = float(data.get('amount', 0))
    method = data.get('method', '')
    account = data.get('account', '')

    if amount < MIN_WITHDRAWAL:
        return jsonify({
            'success': False,
            'message': f'Minimum withdrawal amount is ${MIN_WITHDRAWAL}'
        })

    db = get_db()
    cursor = db.cursor()

    # Check balance
    cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    if amount > user['wallet_balance']:
        return jsonify({
            'success': False,
            'message': 'Insufficient balance'
        })

    try:
        # Create withdrawal
        cursor.execute('''
            INSERT INTO withdrawals (user_id, amount, method, account_details, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (session['user_id'], amount, method, account))

        # Update balance
        cursor.execute('''
            UPDATE users
            SET wallet_balance = wallet_balance - ?
            WHERE id = ?
        ''', (amount, session['user_id']))

        db.commit()

        return jsonify({
            'success': True,
            'message': 'Withdrawal request submitted'
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/admin/toggle/<int:product_id>', methods=['POST'])
def admin_toggle_product(product_id):
    """Toggle product visibility (admin)"""
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    row = cursor.execute("SELECT visible FROM products WHERE id = ?", (product_id,)).fetchone()

    if row:
        new_status = 0 if row['visible'] else 1
        cursor.execute("UPDATE products SET visible = ? WHERE id = ?", (new_status, product_id))
        db.commit()
        return jsonify({'success': True, 'visible': new_status})

    return jsonify({'success': False}), 404

@app.route('/admin/update-stock/<int:product_id>', methods=['POST'])
def admin_update_stock(product_id):
    """Update product stock (admin)"""
    data = request.get_json()
    new_stock = data.get('stock')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
    db.commit()

    return jsonify({'success': True, 'stock': new_stock})

#============ UTILITY ROUTES =============#

@app.route('/fix-database-columns')
def fix_database_columns():
    """Add missing columns to database"""
    db = get_db()
    cursor = db.cursor()

    try:
        # Add created_at to users table
        cursor.execute('''
            ALTER TABLE users
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')

        # Add created_at to orders table
        cursor.execute('''
            ALTER TABLE orders
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')

        db.commit()
        return "✅ Database columns added successfully!"

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/test-categories')
def test_categories():
    """Test categories"""
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()

    result = "<h1>Categories Test</h1>"
    result += f"<p>Found {len(categories)} categories</p>"
    result += "<ul>"
    for cat in categories:
        result += f"<li>{cat['id']}: {cat['name']}</li>"
    result += "</ul>"

    return result

@app.route('/admin/products-debug')
def admin_products_debug():
    """Debug products"""
    import sqlite3
    conn = sqlite3.connect('sooqkabeer.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *,
               stock_quantity AS stock,
               visible AS is_active
        FROM products
        ORDER BY id DESC
    """)

    products = []
    for row in cursor.fetchall():
        product_dict = dict(row)
        products.append(product_dict)

    cursor.execute("SELECT * FROM categories")
    categories = [dict(row) for row in cursor.fetchall()]

    conn.close()

    print(f"Total products: {len(products)}")

    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/verify_vendor/<int:id>/<string:status>')
@admin_required
def verify_vendor(id, status):
    """Verify vendor"""
    conn = get_db_connection()
    conn.execute('UPDATE vendors SET kyc_status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()

    flash(f"Vendor status updated to {status}", "success")
    return redirect(url_for('admin_vendors'))

@app.route('/debug/vendor-orders')
def debug_vendor_orders():
    user_id = session.get('user_id', 1) # আপনার আইডি ১ তাই ১ ধরেছি
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    
    try:
        # ভেন্ডর চেক
        vendor = db.execute("SELECT * FROM vendors WHERE id = ?", (user_id,)).fetchone()
        
        # প্রোডাক্ট চেক
        products = db.execute("SELECT id, name_en, vendor_id FROM products WHERE vendor_id = ?", (user_id,)).fetchall()
        
        # অর্ডার চেক (status এর বদলে order_status ব্যবহার করা হয়েছে)
        orders = db.execute("""
            SELECT oi.*, p.name_en, o.order_number, o.order_status 
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE p.vendor_id = ?
        """, (user_id,)).fetchall()
        
        db.close()
        
        return {
            'vendor': dict(vendor) if vendor else None,
            'products_count': len(products),
            'products': [dict(p) for p in products],
            'orders_count': len(orders),
            'orders': [dict(o) for o in orders]
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/test/force-order')
def force_order():
    db = get_db_connection()
    try:
        cursor = db.cursor()
        # ১. সরাসরি একটি অর্ডার তৈরি (মিনিমাম কলাম দিয়ে)
        cursor.execute("""
            INSERT INTO orders (order_number, total_amount, order_status, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (f'ORD-HKO-101', 500.0, 'pending'))
        
        order_id = cursor.lastrowid
        
        # ২. সরাসরি ভেন্ডর ১ এর প্রোডাক্ট ১ এর সাথে লিঙ্ক করা
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (order_id, 1, 1, 500.0))
        
        db.commit()
        db.close()
        return "✅ Success! Order forced for HKO-001. Now refresh /debug/vendor-orders"
    except Exception as e:
        return f"❌ Error: {str(e)}"

#============ MAIN EXECUTION =============#

from cli import *

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000)
    # Initialize database
    init_database()

    print("✅ Database ready")
    print("🌐 Available at: http://localhost:8000")
    print("🔑 Admin login: admin / admin123")
    print("💰 Features: Referral System, Multi-vendor, Commission Tracking")

    app.run(host='0.0.0.0', port=8000, debug=True)
import cli

def init_db():
    import sqlite3
    conn = sqlite3.connect('sooqkabeer.db')
    cursor = conn.cursor()
    
    # Create the vendors table with HKO-001 requirements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            country_code TEXT DEFAULT '+965',
            nationality TEXT,
            shop_name TEXT NOT NULL,
            business_name TEXT,
            business_type TEXT,
            cr_number TEXT UNIQUE,
            vat_number TEXT,
            address TEXT,
            governorate TEXT,
            block TEXT,
            street TEXT,
            building TEXT,
            floor TEXT,
            unit TEXT,
            business_description TEXT,
            civil_id TEXT,
            civil_id_path TEXT,
            civil_id_back_path TEXT,
            commercial_license_path TEXT,
            vendor_code TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'pending',
            agree_terms TEXT DEFAULT 'no',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            vendor_id INTEGER NOT NULL,
            main_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database Reset and Initialized Successfully!")

