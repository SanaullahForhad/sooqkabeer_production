"""
SOOQ KABEER - COMPLETE E-COMMERCE PLATFORM
All features in one file: Referral, Vendor, Orders, Commission, Multi-language
Branding: Navy Blue (#0a192f) + Gold (#d4af37) + Glassmorphism
"""

# ============ CORE IMPORTS ============
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
import re
# ============ ARABIC SUPPORT ============
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    HAS_ARABIC_LIB = True
except ImportError:
    HAS_ARABIC_LIB = False
    print("#=== NOTICE: Running without Arabic reshaper library ===#")

# ============ BRANDING & UI COLORS ============
"""
BRANDING GUIDE:
- Background: #0a192f (Deep Navy)
- Primary Gold: #d4af37 (Kuwaiti Gold)
- Cards: rgba(255, 255, 255, 0.08) (Glassmorphism)
- Status Green: #28a745 (Stock/Freshness)
- Text White: #ffffff
- Text Gray: #b0b7c3
- Error Red: #dc3545
- Warning Orange: #ffc107
"""

# ============ CONFIGURATION CONSTANTS ============
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}
ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_ALL_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS).union(ALLOWED_DOC_EXTENSIONS)

REFERRAL_RATE = 0.05
MIN_WITHDRAWAL = 10
COMMISSION_RATE = 0.10
MIN_WITHDRAWAL_LIMIT = 5.0

SUPPORTED_LANGUAGES = ['ar', 'en']
DEFAULT_LANGUAGE = 'ar'

# ============ FILE DIRECTORY PLAN ============
"""
PATH LOGIC:
- Base: static/uploads/
- Products: static/uploads/products/
- Documents: static/uploads/documents/
- KYC: static/uploads/kyc/
- Banners: static/uploads/banners/
- Profile: static/uploads/profile/
"""
# ============ APP INITIALIZATION ============
app = Flask(__name__)
app.secret_key = 'sooqkabeer_secret_key_2024_production_2025'

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(basedir, 'sooqkabeer.db')

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure upload folders exist
UPLOAD_BASE = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_BASE'] = UPLOAD_BASE
os.makedirs(UPLOAD_BASE, exist_ok=True)
# ============ DATABASE CONFIGURATION ============
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = 'sooqkabeer.db'
DATABASE_PATH = os.path.join(basedir, DATABASE)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

print(f"📁 DATABASE PATH: {DATABASE_PATH}")

# ============ UPLOAD FOLDER CONFIGURATION ============
UPLOAD_BASE = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_BASE'] = UPLOAD_BASE

# Create all necessary upload directories
UPLOAD_DIRS = {
    'products': 'products',
    'products_images': 'products/images',
    'products_videos': 'products/videos',
    'documents': 'documents',
    'kyc': 'kyc',
    'kyc_civil': 'kyc/civil_id',
    'banners': 'banners',
    'profile': 'profile',
    'temp': 'temp'
}

# ============ BABEL CONFIGURATION ============
babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ar']

# ============ TEMPLATE CONFIGURATION ============
# Set template folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

print(f"📁 Template directory: {TEMPLATE_DIR}")
print(f"📁 Static directory: {STATIC_DIR}")

# Ensure directories exist
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Check if vendor templates exist
vendor_template_dir = os.path.join(TEMPLATE_DIR, 'vendor')
admin_template_dir = os.path.join(TEMPLATE_DIR, 'admin')
os.makedirs(vendor_template_dir, exist_ok=True)
os.makedirs(admin_template_dir, exist_ok=True)

print(f"✅ Vendor template directory: {os.path.exists(vendor_template_dir)}")
print(f"✅ Admin template directory: {os.path.exists(admin_template_dir)}")

# ============ TEMPLATE LOADING HELPER ============

def render_custom_template(template_name, **context):
    """Custom template renderer with fallback"""
    try:
        return render_template(template_name, **context)
    except TemplateNotFound:
        print(f"⚠️  Template not found: {template_name}")
        
        # Create fallback templates directory
        fallback_dir = os.path.join(TEMPLATE_DIR, 'fallback')
        os.makedirs(fallback_dir, exist_ok=True)
        
        # Check if it's a vendor template
        if template_name.startswith('vendor/'):
            fallback_path = os.path.join(fallback_dir, 'vendor_fallback.html')
            if not os.path.exists(fallback_path):
                create_vendor_fallback_template(fallback_path)
            return render_template('fallback/vendor_fallback.html', **context)
        
        # Check if it's an admin template
        elif template_name.startswith('admin/'):
            fallback_path = os.path.join(fallback_dir, 'admin_fallback.html')
            if not os.path.exists(fallback_path):
                create_admin_fallback_template(fallback_path)
            return render_template('fallback/admin_fallback.html', **context)
        
        # General fallback
        else:
            fallback_path = os.path.join(fallback_dir, 'general_fallback.html')
            if not os.path.exists(fallback_path):
                create_general_fallback_template(fallback_path)
            return render_template('fallback/general_fallback.html', **context)

def create_vendor_fallback_template(filepath):
    """Create vendor fallback template"""
    html_content = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SooqKabeer - Vendor Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Cairo', 'Tajawal', sans-serif;
            background-color: #0a192f;
            color: #ffffff;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #0a192f 0%, #1a2f4f 100%);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .logo h1 {
            color: #d4af37;
            font-size: 28px;
            font-weight: 700;
        }
        
        .welcome-card {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(212, 175, 55, 0.3);
            margin-bottom: 30px;
        }
        
        .welcome-title {
            color: #d4af37;
            font-size: 24px;
            margin-bottom: 15px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(212, 175, 55, 0.2);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            border-color: #d4af37;
        }
        
        .stat-title {
            color: #b0b7c3;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            color: #d4af37;
            font-size: 32px;
            font-weight: 700;
        }
        
        .mobile-menu {
            display: none;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .menu-btn {
            background: #d4af37;
            color: #0a192f;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        @media (max-width: 768px) {
            .mobile-menu {
                display: block;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .header {
                padding: 15px;
            }
            
            .logo h1 {
                font-size: 22px;
            }
        }
        
        .message-box {
            background: rgba(40, 167, 69, 0.15);
            border: 1px solid #28a745;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #d4af37 0%, #c19b2c 100%);
            color: #0a192f;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary:hover {
            opacity: 0.9;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&family=Tajawal:wght@300;400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <i class="fas fa-store" style="font-size: 32px; color: #d4af37;"></i>
                <h1>SooqKabeer Vendor Dashboard</h1>
            </div>
        </div>
        
        <div class="mobile-menu">
            <button class="menu-btn">
                <i class="fas fa-bars"></i>
                القائمة
            </button>
        </div>
        
        <div class="welcome-card">
            <h2 class="welcome-title">
                <i class="fas fa-user-tie"></i>
                مرحباً، {{ vendor.shop_name if vendor else "التاجر" }}
            </h2>
            <p>كود التاجر: <strong>{{ vendor.vendor_code if vendor else "N/A" }}</strong></p>
            <p>حالة الحساب: <strong>{{ vendor.status if vendor else "N/A" }}</strong></p>
        </div>
        
        <div class="message-box">
            <h3><i class="fas fa-info-circle"></i> ملاحظة</h3>
            <p>لوحة التحكم الأصلية غير متوفرة حالياً. يتم عرض النسخة البديلة.</p>
            <p>لتصميم لوحة تحكم كاملة، يرجى التأكد من وجود ملفات القوالب في مجلد templates/vendor/</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">المنتجات</div>
                <div class="stat-value">{{ stats.total_products if stats else 0 }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">الطلبات</div>
                <div class="stat-value">{{ stats.total_orders if stats else 0 }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">المبيعات</div>
                <div class="stat-value">{{ stats.total_sales if stats else 0 }} KD</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">الرصيد</div>
                <div class="stat-value">{{ stats.available_balance if stats else 0 }} KD</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="/vendor/products" class="btn-primary">
                <i class="fas fa-plus"></i>
                إضافة منتج جديد
            </a>
            
            <a href="/vendor/orders" class="btn-primary" style="margin-right: 15px;">
                <i class="fas fa-shopping-cart"></i>
                عرض الطلبات
            </a>
            
            <a href="/vendor/finance" class="btn-primary" style="margin-right: 15px;">
                <i class="fas fa-chart-line"></i>
                التقارير المالية
            </a>
        </div>
    </div>
    
    <script>
        // Mobile menu toggle
        document.querySelector('.menu-btn').addEventListener('click', function() {
            alert('القائمة الجانبية ستظهر هنا في النسخة الكاملة');
        });
        
        // Auto-refresh stats every 30 seconds
        setInterval(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_admin_fallback_template(filepath):
    """Create admin fallback template"""
    html_content = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SooqKabeer - Admin Panel</title>
    <style>
        /* Same styles as vendor but with admin colors */
        body {
            background: #0a192f;
            color: white;
            font-family: 'Cairo', sans-serif;
        }
    </style>
</head>
<body>
    <h1>لوحة تحكم المشرف - النسخة البديلة</h1>
    <p>يرجى إنشاء ملفات القوالب في مجلد templates/admin/</p>
</body>
</html>
'''
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_general_fallback_template(filepath):
    """Create general fallback template"""
    html_content = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SooqKabeer</title>
</head>
<body>
    <h1>مرحباً بك في SooqKabeer</h1>
    <p>يتم تحميل التطبيق...</p>
</body>
</html>
'''
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
# ============ CREATE UPLOAD DIRECTORIES ============
def create_upload_directories():
    """Create all necessary upload directories on startup"""
    for dir_name, dir_path in UPLOAD_DIRS.items():
        full_path = os.path.join(UPLOAD_BASE, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"✅ Created directory: {full_path}")

create_upload_directories()
# ============ HELPER FUNCTIONS ============

def allowed_file(filename, file_type='all'):
    """Check if file extension is allowed based on type"""
    if not filename:
        return False
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    elif file_type == 'document':
        return ext in ALLOWED_DOC_EXTENSIONS
    else:  # 'all'
        return ext in ALLOWED_ALL_EXTENSIONS

def save_uploaded_file(file, subfolder, custom_name=None):
    """
    Save uploaded file to specified subfolder
    Returns: relative_path or None
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Generate filename
    if custom_name:
        filename = secure_filename(custom_name)
    else:
        original_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        name_part = os.path.splitext(original_name)[0]
        ext = os.path.splitext(original_name)[1]
        filename = f"{name_part}_{timestamp}{ext}"
    
    # Create target directory
    target_dir = os.path.join(app.config['UPLOAD_BASE'], subfolder)
    os.makedirs(target_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(target_dir, filename)
    file.save(file_path)
    
    # Return relative path for database storage
    return f"uploads/{subfolder}/{filename}"

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Get database connection with app context"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
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
    SALT = 'sooqkabeer_salt_2025_'
    return hashlib.sha256((SALT + password).encode()).hexdigest()

def check_password(hashed_password, user_password):
    """Check password hash"""
    SALT = 'sooqkabeer_salt_2025_'
    new_hash = hashlib.sha256((SALT + user_password).encode()).hexdigest()
    return hashed_password == new_hash

def generate_referral_code(username):
    """Generate unique referral code"""
    code = hashlib.md5(f"{username}{random.random()}{time.time()}".encode()).hexdigest()[:8].upper()
    return f"REF{code}"

def fix_arabic(text):
    """Fix Arabic text for display"""
    if not text:
        return ""
    if HAS_ARABIC_LIB:
        try:
            reshaped = reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
    return text

def get_locale():
    """Get current locale for Babel"""
    return session.get('lang', app.config.get('BABEL_DEFAULT_LOCALE', 'en'))

babel.init_app(app, locale_selector=get_locale)

def generate_vendor_code():
    """Generate unique vendor code: HKO-XXXX"""
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT MAX(id) FROM vendors")
    result = cursor.fetchone()
    next_id = 1 if result[0] is None else result[0] + 1
    
    vendor_code = f"HKO-{next_id:04d}"
    db.close()
    return vendor_code

# ============ ROW WRAPPER CLASS ============
def get_db():
    db = sqlite3.connect('sooqkabeer.db')
    db.row_factory = sqlite3.Row
    return db

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

# ============ CONTEXT PROCESSORS ============
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
        'is_rtl': True if session.get('language') == 'ar' else False,
        'brand_colors': {
            'navy': '#0a192f',
            'gold': '#d4af37',
            'green': '#28a745',
            'red': '#dc3545',
            'orange': '#ffc107',
            'white': '#ffffff',
            'gray': '#b0b7c3'
        },
        'timestamp': int(time.time())  # Cache busting
    }

@app.before_request
def before_request():
    """Set language and RTL flag before each request"""
    if 'language' not in session:
        session['language'] = DEFAULT_LANGUAGE
    # Set RTL flag for Arabic
    request.is_rtl = True if session.get('language') == 'ar' else False
# ============ AUTHENTICATION DECORATORS ============

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
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

def vendor_required(f):
    """Require vendor role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor':
            flash('Access denied. Vendors only.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def vendor_login_required(f):
    """Require vendor login - specific to vendor routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor':
            flash("Vendor login required!", "warning")
            return redirect(url_for('vendor_login'))
        return f(*args, **kwargs)
    return decorated_function
# ============ DATABASE INITIALIZATION ============

def init_database():
    """Initialize database with all required tables"""
    print("📊 INITIALIZING DATABASE...")
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # ============ USERS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                full_name TEXT,
                profile_image TEXT,
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
                email_verified INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created: users table")

        # ============ VENDORS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
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
                civil_id_front TEXT,
                civil_id_back TEXT,
                commercial_license TEXT,
                vendor_code TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                kyc_status TEXT DEFAULT 'pending',
                agree_terms TEXT DEFAULT 'no',
                balance REAL DEFAULT 0,
                total_earnings REAL DEFAULT 0,
                profile_image TEXT,
                banner_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("✅ Created: vendors table")

        # ============ PRODUCTS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER NOT NULL,
                name_en TEXT NOT NULL,
                name_ar TEXT NOT NULL,
                description_en TEXT,
                description_ar TEXT,
                detailed_description TEXT,
                price REAL NOT NULL,
                b2b_price REAL,
                cost_price REAL,
                stock INTEGER NOT NULL DEFAULT 0,
                low_stock_alert INTEGER DEFAULT 10,
                unit TEXT DEFAULT 'piece',
                weight REAL,
                sku TEXT UNIQUE,
                product_code TEXT,
                category_id INTEGER,
                main_image TEXT,
                image_gallery TEXT,
                video_url TEXT,
                document_url TEXT,
                status TEXT DEFAULT 'active',
                visibility TEXT DEFAULT 'public',
                is_featured BOOLEAN DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                delivery_days INTEGER DEFAULT 3,
                allow_backorders BOOLEAN DEFAULT 0,
                views INTEGER DEFAULT 0,
                sales_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                total_reviews INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
            )
        ''')
        print("✅ Created: products table")

        # ============ CATEGORIES TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en TEXT NOT NULL,
                name_ar TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                image TEXT,
                parent_id INTEGER DEFAULT NULL,
                sort_order INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created: categories table")

        # ============ ORDERS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER,
                total_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                shipping_cost REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                shipping_address TEXT,
                billing_address TEXT,
                customer_notes TEXT,
                admin_notes TEXT,
                estimated_delivery DATE,
                delivered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        ''')
        print("✅ Created: orders table")

        # ============ ORDER ITEMS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                vendor_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        ''')
        print("✅ Created: order_items table")

        # ============ COMMISSIONS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER,
                order_id INTEGER,
                amount REAL NOT NULL,
                commission_rate REAL NOT NULL,
                type TEXT DEFAULT 'referral',
                status TEXT DEFAULT 'pending',
                description TEXT,
                notes TEXT,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        ''')
        print("✅ Created: commissions table")

        # ============ WITHDRAWALS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vendor_id INTEGER,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                account_details TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                rejected_reason TEXT,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (vendor_id) REFERENCES vendors(id)
            )
        ''')
        print("✅ Created: withdrawals table")

        # ============ SETTINGS TABLE ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_group TEXT DEFAULT 'general',
                data_type TEXT DEFAULT 'text',
                description TEXT,
                is_public INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created: settings table")

        # ============ INSERT DEFAULT SETTINGS ============
        default_settings = [
            ('site_name', 'SooqKabeer', 'general', 'Site Name'),
            ('site_description', 'Premium B2B Wholesale Marketplace', 'general', 'Site Description'),
            ('site_currency', 'KWD', 'general', 'Default Currency'),
            ('site_language', 'ar', 'general', 'Default Language'),
            ('commission_rate', '10', 'commission', 'Commission Percentage'),
            ('referral_rate', '5', 'referral', 'Referral Commission Rate'),
            ('vat_rate', '5', 'tax', 'VAT Percentage'),
            ('min_withdrawal', '10', 'withdrawal', 'Minimum Withdrawal Amount'),
            ('support_email', 'support@sooqkabeer.com', 'contact', 'Support Email'),
            ('support_phone', '+965 1234 5678', 'contact', 'Support Phone'),
            ('company_address', 'Kuwait City, Block 4, Street 12', 'contact', 'Company Address'),
            ('enable_registration', '1', 'registration', 'Enable User Registration'),
            ('enable_vendor_reg', '1', 'registration', 'Enable Vendor Registration'),
            ('default_theme', 'dark', 'appearance', 'Default Theme'),
            ('primary_color', '#0a192f', 'appearance', 'Primary Color'),
            ('secondary_color', '#d4af37', 'appearance', 'Secondary Color')
        ]

        for key, value, group, desc in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_group, description)
                VALUES (?, ?, ?, ?)
            ''', (key, value, group, desc))

        # ============ INSERT DEFAULT ADMIN USER ============
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password, full_name, role, is_active, email_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@sooqkabeer.com', admin_password, 'Administrator', 'admin', 1, 1))
            print("✅ Created: Default admin user (admin/admin123)")

        # ============ INSERT DEFAULT CATEGORIES ============
        default_categories = [
            ('Vegetables', 'خضروات', 'Fresh vegetables', 'vegetables'),
            ('Fruits', 'فواكه', 'Fresh fruits', 'fruits'),
            ('Dairy', 'ألبان', 'Dairy products', 'dairy'),
            ('Meat', 'لحوم', 'Fresh meat', 'meat'),
            ('Beverages', 'مشروبات', 'Drinks and beverages', 'beverages'),
            ('Snacks', 'وجبات خفيفة', 'Snacks and chips', 'snacks'),
            ('Spices', 'بهارات', 'Spices and herbs', 'spices'),
            ('Grains', 'حبوب', 'Grains and rice', 'grains')
        ]

        for name_en, name_ar, description, icon in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name_en, name_ar, description, icon, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (name_en, name_ar, description, icon, 'active'))

        db.commit()
        print("🎉 DATABASE INITIALIZATION COMPLETE!")
        print("="*50)

    except Exception as e:
        print(f"❌ DATABASE ERROR: {str(e)}")
        db.rollback()
    finally:
        db.close()
# ============ LANGUAGE & REGISTRATION ROUTES ============
@app.route('/set_language/<lang>')
@app.route('/change_site_lang/<lang>')
def set_language(lang):
    """টেমপ্লেট এবং বিটুবি সিস্টেমের সাথে ভাষার সামঞ্জস্য রাখা"""
    if lang in ['ar', 'en', 'bn']:
        session['lang'] = lang
    
    # ইউজার যে পেজে ছিল সেখানেই ফেরত পাঠাবে, নয়তো হোম পেজে
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    """Home page with featured products"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get featured products
        cursor.execute('''
            SELECT p.*, v.shop_name, v.vendor_code,
                   c.name_en as category_name, c.name_ar as category_name_ar
            FROM products p
            LEFT JOIN vendors v ON p.vendor_id = v.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.visibility = 'public'
            ORDER BY p.is_featured DESC, p.created_at DESC
            LIMIT 12
        ''')
        featured_products = [RowWrapper(row) for row in cursor.fetchall()]
        
        # Get categories
        cursor.execute('''
            SELECT * FROM categories
            WHERE status = 'active'
            ORDER BY sort_order, name_en
            LIMIT 8
        ''')
        categories = [RowWrapper(row) for row in cursor.fetchall()]
        
        # Get stats for display
        cursor.execute("SELECT COUNT(*) FROM products WHERE status='active'")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vendors WHERE status='verified'")
        total_vendors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status='completed'")
        total_orders = cursor.fetchone()[0]
        
        stats = {
            'products': total_products,
            'vendors': total_vendors,
            'orders': total_orders
        }
        
    except Exception as e:
        print(f"Home page error: {e}")
        featured_products = []
        categories = []
        stats = {'products': 0, 'vendors': 0, 'orders': 0}
    
    return render_template('index.html',
                         featured_products=featured_products,
                         categories=categories,
                         stats=stats,
                         lang=session.get('language', 'ar'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with vendor redirection"""
    # 1. Check if user wants to register as a vendor
    user_type = request.args.get('type', 'customer')
    if user_type == 'vendor':
        return redirect(url_for('vendor_register')) # Redirect to your 4-step form

    referral_code = request.args.get('ref', '') or request.form.get('referral_code', '')
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()
            agree_terms = request.form.get('agree_terms')
            
            # Validation
            if not all([username, email, password, confirm_password, agree_terms]):
                flash('Please fill all required fields', 'warning')
                return render_template('register.html', referral_code=referral_code)
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('register.html', referral_code=referral_code)
            
            if len(password) < 6:
                flash('Password must be at least 6 characters', 'warning')
                return render_template('register.html', referral_code=referral_code)
            
            db = get_db()
            cursor = db.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('Email already registered', 'danger')
                return render_template('register.html', referral_code=referral_code)
            
            # Check if username exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash('Username already taken', 'danger')
                return render_template('register.html', referral_code=referral_code)
            
            # Hash password
            hashed_password = hash_password(password)
            
            # Generate referral code for new user
            user_referral_code = generate_referral_code(username)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users
                (username, email, password, full_name, phone, referral_code, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (username, email, hashed_password, full_name, phone, user_referral_code))
            
            user_id = cursor.lastrowid
            
            # Process referral if provided
            if referral_code:
                process_referral_signup(user_id, referral_code)
            
            db.commit()
            
            # Auto login after registration
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            session['full_name'] = full_name or username
            session['role'] = 'customer'
            session['language'] = 'ar'
            
            flash('Registration successful! Welcome to SooqKabeer', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html', referral_code=referral_code)

# =============== AUTHENTICATION ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login system for all users"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'customer')  # customer, vendor, admin
        
        if not email or not password:
            flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'warning')
            return render_template('auth/login.html')
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # ============ CUSTOMER LOGIN ============
            if user_type == 'customer':
                cursor.execute('''
                    SELECT * FROM users
                    WHERE (email = ? OR username = ?)
                    AND role = 'customer'
                    AND is_active = 1
                ''', (email, email))
                user = cursor.fetchone()
                
                if user and check_password(user['password'], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP,
                            login_count = login_count + 1
                        WHERE id = ?
                    ''', (user['id'],))
                    db.commit()
                    
                    # Set session
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['role'] = 'customer'
                    session['full_name'] = user['full_name'] or user['username']
                    session['language'] = 'ar'
                    
                    flash(f'مرحباً بعودتك، {session["full_name"]}!', 'success')
                    return redirect(url_for('home'))
            
            # ============ VENDOR LOGIN ============
            elif user_type == 'vendor':
                # First check in vendors table
                cursor.execute('''
                    SELECT v.*, u.full_name, u.username
                    FROM vendors v
                    LEFT JOIN users u ON v.user_id = u.id
                    WHERE v.email = ? AND v.status IN ('verified', 'active')
                ''', (email,))
                vendor = cursor.fetchone()
                
                if vendor:
                    # Check password using the correct method
                    if check_password(vendor['password'], password):
                        # Update last login
                        cursor.execute('''
                            UPDATE vendors
                            SET updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (vendor['id'],))
                        
                        # Set session
                        session.clear()
                        session['user_id'] = vendor['id']
                        session['vendor_id'] = vendor['id']
                        session['username'] = vendor['email'].split('@')[0]
                        session['email'] = vendor['email']
                        session['full_name'] = vendor['name']
                        session['role'] = 'vendor'
                        session['vendor_code'] = vendor['vendor_code']
                        session['shop_name'] = vendor['shop_name']
                        session['vendor_status'] = vendor['status']
                        session['language'] = 'ar'
                        
                        db.commit()
                        
                        flash(f'مرحباً بعودتك، {vendor["shop_name"]}!', 'success')
                        
                        if vendor['status'] == 'pending':
                            return redirect(url_for('vendor_pending'))
                        else:
                            return redirect(url_for('vendor_dashboard'))
                
                # Also check in users table for vendor role
                cursor.execute('''
                    SELECT * FROM users
                    WHERE (email = ? OR username = ?)
                    AND role = 'vendor'
                    AND is_active = 1
                ''', (email, email))
                user = cursor.fetchone()
                
                if user and check_password(user['password'], password):
                    # Get vendor details
                    cursor.execute('SELECT * FROM vendors WHERE user_id = ?', (user['id'],))
                    vendor = cursor.fetchone()
                    
                    # Set session
                    session.clear()
                    session['user_id'] = user['id']
                    session['email'] = user['email']
                    session['role'] = 'vendor'
                    session['full_name'] = user['full_name'] or user['username']
                    session['language'] = 'ar'
                    
                    if vendor:
                        session['vendor_id'] = vendor['id']
                        session['vendor_code'] = vendor['vendor_code']
                        session['shop_name'] = vendor['shop_name']
                        session['vendor_status'] = vendor['status']
                    else:
                        session['vendor_code'] = 'HKO-001'
                        session['shop_name'] = user['full_name'] or 'My Shop'
                    
                    flash(f'مرحباً بعودتك، {session["shop_name"]}!', 'success')
                    return redirect(url_for('vendor_dashboard'))
            
            # ============ ADMIN LOGIN ============
            elif user_type == 'admin':
                cursor.execute('''
                    SELECT * FROM users
                    WHERE (email = ? OR username = ?)
                    AND role = 'admin'
                    AND is_active = 1
                ''', (email, email))
                admin = cursor.fetchone()
                
                if admin and check_password(admin['password'], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP,
                            login_count = login_count + 1
                        WHERE id = ?
                    ''', (admin['id'],))
                    db.commit()
                    
                    # Set session
                    session.clear()
                    session['user_id'] = admin['id']
                    session['username'] = admin['username']
                    session['email'] = admin['email']
                    session['role'] = 'admin'
                    session['full_name'] = admin['full_name'] or admin['username']
                    session['language'] = 'ar'
                    
                    flash(f'مرحباً بعودتك، المسؤول!', 'success')
                    return redirect(url_for('admin_dashboard'))
            
            # ============ DEFAULT FALLBACK ============
            # If no specific type or type not recognized, check all tables
            else:
                # Check users table first
                cursor.execute('''
                    SELECT * FROM users
                    WHERE (email = ? OR username = ?)
                    AND is_active = 1
                ''', (email, email))
                user = cursor.fetchone()
                
                if user and check_password(user['password'], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP,
                            login_count = login_count + 1
                        WHERE id = ?
                    ''', (user['id'],))
                    db.commit()
                    
                    # Set session
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['role'] = user['role']
                    session['full_name'] = user['full_name'] or user['username']
                    session['language'] = 'ar'
                    
                    # Set vendor session if user is vendor
                    if user['role'] == 'vendor':
                        cursor.execute('SELECT vendor_code FROM vendors WHERE user_id = ?', (user['id'],))
                        vendor = cursor.fetchone()
                        if vendor:
                            session['vendor_code'] = vendor['vendor_code']
                    
                    flash(f'مرحباً بعودتك، {session["full_name"]}!', 'success')
                    
                    # Redirect based on role
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    elif user['role'] == 'vendor':
                        return redirect(url_for('vendor_dashboard'))
                    else:
                        return redirect(url_for('home'))
                
                # Check vendors table
                cursor.execute('''
                    SELECT * FROM vendors
                    WHERE email = ? AND status IN ('verified', 'active', 'pending')
                ''', (email,))
                vendor = cursor.fetchone()
                
                if vendor and check_password(vendor['password'], password):
                    # Update last login
                    cursor.execute('''
                        UPDATE vendors
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (vendor['id'],))
                    
                    # Set session
                    session.clear()
                    session['user_id'] = vendor['id']
                    session['vendor_id'] = vendor['id']
                    session['username'] = vendor['email'].split('@')[0]
                    session['email'] = vendor['email']
                    session['full_name'] = vendor['name']
                    session['role'] = 'vendor'
                    session['vendor_code'] = vendor['vendor_code']
                    session['shop_name'] = vendor['shop_name']
                    session['vendor_status'] = vendor['status']
                    session['language'] = 'ar'
                    
                    db.commit()
                    
                    flash(f'مرحباً بعودتك، {vendor["shop_name"]}!', 'success')
                    
                    if vendor['status'] == 'pending':
                        return redirect(url_for('vendor_pending'))
                    else:
                        return redirect(url_for('vendor_dashboard'))
            
            # If we reach here, login failed
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
            
        except Exception as e:
            print(f"Login error: {e}")
            flash(f'خطأ في تسجيل الدخول: {str(e)}', 'danger')
    
    return render_template('auth/login.html')
@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    """Vendor login page"""
    # এখানে শুধু টেমপ্লেট রিটার্ন করুন, লগইন লজিক আলাদা
    return render_template('auth/login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    # এখানে শুধু টেমপ্লেট রিটার্ন করুন, লগইন লজিক আলাদা
    return render_template('admin/login.html')

@app.route('/logout')
def logout():
    """Logout user from all roles"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if email:
            db = get_db()
            cursor = db.cursor()
            
            # Check if email exists
            cursor.execute('''
                SELECT email, full_name FROM users
                WHERE email = ? AND is_active = 1
                UNION
                SELECT email, name as full_name FROM vendors
                WHERE email = ? AND status != 'suspended'
            ''', (email, email))
            
            user = cursor.fetchone()
            
            if user:
                # In production, send reset email here
                # For now, just show success message
                flash(f'تم إرسال رابط إعادة تعيين كلمة المرور إلى {email}', 'success')
            else:
                flash('البريد الإلكتروني غير مسجل في نظامنا', 'warning')
            
            return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html')

# ============ AUTH ROUTES (ADD TO YOUR APP.PY) ============

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    db = get_db()
    cursor = db.cursor()
    
    # Find user by reset token (you need to implement token storage)
    cursor.execute('''
        SELECT id, email FROM password_resets
        WHERE token = ? AND expires_at > CURRENT_TIMESTAMP
    ''', (token,))
    reset_data = cursor.fetchone()
    
    if not reset_data:
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('forgot_password'))
    
    user_id = reset_data['id']
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash('Please fill all fields', 'warning')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters', 'warning')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        hashed_password = hash_password(new_password)
        cursor.execute('''
            UPDATE users
            SET password = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (hashed_password, user_id))
        
        # Delete used token
        cursor.execute('DELETE FROM password_resets WHERE token = ?', (token,))
        
        db.commit()
        
        flash('Password reset successfully! Please login with your new password', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', token=token)

@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT user_id FROM email_verifications
        WHERE token = ? AND expires_at > CURRENT_TIMESTAMP
    ''', (token,))
    verify_data = cursor.fetchone()
    
    if verify_data:
        cursor.execute('''
            UPDATE users
            SET email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (verify_data['user_id'],))
        
        cursor.execute('DELETE FROM email_verifications WHERE token = ?', (token,))
        db.commit()
        
        flash('Email verified successfully!', 'success')
        return redirect(url_for('login'))
    else:
        flash('Invalid or expired verification token', 'danger')
        return redirect(url_for('login'))
# ========================= VENDOR ROUTES ===============

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    """Vendor registration page"""
    if request.method == 'POST':
        try:
            # ============ STEP 1: COLLECT FORM DATA ============
            # Personal Information
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            country_code = request.form.get('country_code', '+965')
            nationality = request.form.get('nationality', '').strip()

            # Business Information
            shop_name = request.form.get('shop_name', '').strip()
            business_name = request.form.get('business_name', shop_name)
            business_type = request.form.get('business_type', '').strip()
            cr_number = request.form.get('cr_number', '').strip()
            vat_number = request.form.get('vat_number', '').strip()

            # Address Information
            governorate = request.form.get('governorate', '').strip()
            block = request.form.get('block', '').strip()
            street = request.form.get('street', '').strip()
            building = request.form.get('building', '').strip()
            floor = request.form.get('floor', '').strip()
            unit = request.form.get('unit', '').strip()
            business_description = request.form.get('business_description', '').strip()

            # ============ STEP 2: VALIDATION ============
            # Check required fields
            required_fields = {
                'name': name,
                'email': email,
                'phone': phone,
                'shop_name': shop_name,
                'business_type': business_type
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                flash(f"Please fill in all required fields: {', '.join(missing_fields)}", "danger")
                return redirect(url_for('vendor_register'))
            
            # Email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                flash("Please enter a valid email address", "danger")
                return redirect(url_for('vendor_register'))
            
            # Phone validation
            if not re.match(r'^\+?[0-9\s\-\(\)]{8,}$', phone):
                flash("Please enter a valid phone number", "danger")
                return redirect(url_for('vendor_register'))
            
            # ============ STEP 3: GENERATE VENDOR CODE ============
            vendor_code = "HKO-" + str(random.randint(1000, 9999))
            
            # Check if vendor code already exists
            while True:
                cur = mysql.connection.cursor()
                cur.execute("SELECT id FROM vendors WHERE vendor_code = %s", (vendor_code,))
                if cur.fetchone():
                    vendor_code = "HKO-" + str(random.randint(1000, 9999))
                else:
                    break
                cur.close()
            
            # ============ STEP 4: SAVE TO DATABASE ============
            cur = mysql.connection.cursor()
            query = """
                INSERT INTO vendors
                (vendor_code, name, email, phone, country_code, nationality,
                 shop_name, business_name, business_type, cr_number, vat_number,
                 governorate, block, street, building, floor, unit, business_description,
                 status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
            """
            
            cur.execute(query, (
                vendor_code, name, email, phone, country_code, nationality,
                shop_name, business_name, business_type, cr_number, vat_number,
                governorate, block, street, building, floor, unit, business_description
            ))
            mysql.connection.commit()
            cur.close()
            
            # ============ STEP 5: STORE IN SESSION ============
            session['vendor_code'] = vendor_code
            session['business_name'] = business_name
            
            flash("Registration successful! Your vendor code is: " + vendor_code, "success")
            
            # ============ STEP 6: SEND EMAIL NOTIFICATION ============
            try:
                msg = Message('Vendor Registration - Sooq Kabeer',
                              sender='noreply@sooqkabeer.com',
                              recipients=[email])
                msg.body = f"""
                Dear {name},
                
                Thank you for registering as a vendor with Sooq Kabeer!
                
                Your Vendor Code: {vendor_code}
                Business Name: {business_name}
                Registration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                Our team will review your application and contact you within 24-48 hours.
                
                Best regards,
                Sooq Kabeer Team
                """
                mail.send(msg)
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            return redirect(url_for('vendor_thank_you'))
            
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return redirect(url_for('vendor_register'))

    # GET request - show registration form
    return render_template('vendor/register.html')


def vendor_thank_you():
    """Thank you page after vendor registration"""
    vendor_code = session.get('vendor_code')
    business_name = session.get('business_name')
    
    if not vendor_code:
        return redirect(url_for('vendor_register'))
    
    return render_template('vendor/thank_you.html',
                         vendor_code=vendor_code,
                         business_name=business_name)

@app.route('/vendor/welcome-pending')
def vendor_welcome_pending():
    """Vendor welcome page while pending approval"""
    if 'vendor_code' not in session:
        return redirect(url_for('vendor_register'))
    
    vendor_code = session.get('vendor_code')
    business_name = session.get('business_name')
    email = session.get('email')
    
    return render_template('vendor/welcome_pending.html',
                         vendor_code=vendor_code,
                         business_name=business_name,
                         email=email)


# Helper function for email sending
def send_vendor_registration_email(vendor_email,  business_name, vendor_code):
    """Send confirmation email to vendor"""
    subject = f"🎉 Welcome to SooqKabeer B2B Marketplace - Registration Received"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #0a192f 0%, #1a2c4f 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0;">SooqKabeer B2B Marketplace</h2>
                <p style="margin: 5px 0 0; opacity: 0.9;">Kuwait's Premier Wholesale Platform</p>
            </div>
            
            <div style="padding: 20px;">
                <h3>Dear {vendor_name},</h3>
                
                <p>Thank you for registering <strong>{business_name}</strong> on SooqKabeer B2B Marketplace!</p>
                
                <div style="background: #f8f9fa; border-left: 4px solid #d4af37; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #0a192f;">Your Registration Details:</h4>
                    <p><strong>Vendor Code:</strong> {vendor_code}</p>
                    <p><strong>Business Name:</strong> {business_name}</p>
                    <p><strong>Registration Status:</strong> <span style="color: #ff9500; font-weight: bold;">Pending Verification</span></p>
                </div>
                
                <p>✅ <strong>What happens next?</strong></p>
                <ol>
                    <li>Our team will review your application within <strong>3-5 business days</strong></li>
                    <li>We will verify your business documents</li>
                    <li>You will receive an email notification once approved</li>
                    <li>After approval, you can log in and start adding products</li>
                </ol>
                
                <p>📋 <strong>Required for approval:</strong></p>
                <ul>
                    <li>Valid Civil ID (Front & Back)</li>
                    <li>Valid Commercial License</li>
                    <li>Complete business information</li>
                </ul>
                
                <div style="background: #fff8e1; border: 1px solid #ffecb3; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;">
                        <strong>⚠️ Important:</strong> Please keep your vendor code <strong>{vendor_code}</strong> safe. 
                        You will need it for all future communications.
                    </p>
                </div>
                
                <p>If you have any questions, please contact our support team:</p>
                <ul>
                    <li>📧 Email: support@sooqkabeer.com</li>
                    <li>📞 Phone: +965 1234 5678</li>
                    <li>📍 Office Hours: 9:00 AM - 5:00 PM (Sunday - Thursday)</li>
                </ul>
                
                <p>Best regards,<br>
                <strong>SooqKabeer Team</strong><br>
                Kuwait's B2B Marketplace</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; margin-top: 20px;">
                <p style="margin: 0; font-size: 12px; color: #6c757d;">
                    © 2024 SooqKabeer B2B Marketplace. All rights reserved.<br>
                    This email was sent to {vendor_email}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Use your email sending function here
    # send_email(vendor_email, subject, body)
    print(f"Vendor confirmation email would be sent to: {vendor_email}")


def send_admin_notification_email( business_name, vendor_code, vendor_email, vendor_phone):
    """Send notification email to admin about new vendor registration"""
    subject = f"📋 New Vendor Registration: {business_name} ({vendor_code})"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h2 style="margin: 0;">📋 New Vendor Registration Alert</h2>
                <p style="margin: 5px 0 0; opacity: 0.9;">SooqKabeer Admin Panel</p>
            </div>
            
            <div style="padding: 20px;">
                <h3>New Vendor Registration Requires Review</h3>
                
                <div style="background: #f8f9fa; border: 1px solid #e3e6f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #0a192f;">Vendor Details:</h4>
                    <p><strong>Vendor Code:</strong> {vendor_code}</p>
                    <p><strong>Business Name:</strong> {business_name}</p>
                    <p><strong>Contact Person:</strong> {vendor_name}</p>
                    <p><strong>Email:</strong> {vendor_email}</p>
                    <p><strong>Phone:</strong> +965 {vendor_phone}</p>
                    <p><strong>Registration Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <p><strong>⚠️ Action Required:</strong></p>
                <ol>
                    <li>Review submitted documents in admin panel</li>
                    <li>Verify business information</li>
                    <li>Approve or reject within 3-5 business days</li>
                </ol>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{url_for('admin_vendor_review', _external=True)}" 
                       style="background: #0a192f; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                       👁️ Review Vendor Application
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Send to admin email
    # admin_email = "admin@sooqkabeer.com"
    # send_email(admin_email, subject, body)
    print(f"Admin notification email would be sent for vendor: {vendor_code}")

@app.route('/vendor/dashboard')
@vendor_required
def vendor_dashboard():
    """Vendor dashboard"""
    vendor_id = session.get('vendor_id')
    
    if not vendor_id:
        return redirect(url_for('vendor_login'))
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # ============ GET VENDOR DETAILS ============
        cursor.execute('SELECT * FROM vendors WHERE id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        
        if not vendor:
            flash('Vendor not found', 'danger')
            return redirect(url_for('vendor_login'))
        
        # ============ CALCULATE STATS ============
        # Total Products
        cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ?', (vendor_id,))
        total_products = cursor.fetchone()[0]
        
        # Active Products
        cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ? AND status = "active"', 
                      (vendor_id,))
        active_products = cursor.fetchone()[0]
        
        # Total Orders
        cursor.execute('''
            SELECT COUNT(DISTINCT o.id)
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE p.vendor_id = ?
        ''', (vendor_id,))
        total_orders = cursor.fetchone()[0]
        
        # Pending Orders
        cursor.execute('''
            SELECT COUNT(DISTINCT o.id)
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE p.vendor_id = ? AND o.status = 'pending'
        ''', (vendor_id,))
        pending_orders = cursor.fetchone()[0]
        
        # Total Sales
        cursor.execute('''
            SELECT SUM(oi.total_price)
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE p.vendor_id = ? AND oi.status = 'completed'
        ''', (vendor_id,))
        total_sales_result = cursor.fetchone()
        total_sales = total_sales_result[0] if total_sales_result[0] else 0
        
        # Available Balance
        available_balance = vendor['balance'] or 0
        
        # ============ RECENT ORDERS ============
        cursor.execute('''
            SELECT o.*, u.full_name as customer_name,
                   COUNT(oi.id) as items_count,
                   GROUP_CONCAT(p.name_en) as product_names
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            JOIN users u ON o.user_id = u.id
            WHERE p.vendor_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 5
        ''', (vendor_id,))
        recent_orders = cursor.fetchall()
        
        # ============ LOW STOCK PRODUCTS ============
        cursor.execute('''
            SELECT * FROM products
            WHERE vendor_id = ? AND stock <= low_stock_alert
            ORDER BY stock ASC
            LIMIT 5
        ''', (vendor_id,))
        low_stock = cursor.fetchall()
        
        # ============ TOP SELLING PRODUCTS ============
        cursor.execute('''
            SELECT p.*, SUM(oi.quantity) as total_sold
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            WHERE p.vendor_id = ?
            GROUP BY p.id
            ORDER BY total_sold DESC
            LIMIT 5
        ''', (vendor_id,))
        top_products = cursor.fetchall()
        
        stats = {
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_sales': round(total_sales, 3),
            'available_balance': round(available_balance, 3),
            'kyc_status': vendor['kyc_status']
        }
        
        # Try to render vendor dashboard template, fallback if not found
        try:
            return render_template('vendor/dashboard.html',
                                 vendor=vendor,
                                 stats=stats,
                                 recent_orders=recent_orders,
                                 low_stock=low_stock,
                                 top_products=top_products)
        except Exception as e:
            print(f"Template error: {e}")
            # Use fallback template
            return render_custom_template('vendor/dashboard.html',
                                        vendor=vendor,
                                        stats=stats,
                                        recent_orders=recent_orders,
                                        low_stock=low_stock,
                                        top_products=top_products)
        
    except Exception as e:
        print(f"Vendor dashboard error: {e}")
        flash('Error loading dashboard', 'danger')
        # Return fallback template
        return render_custom_template('vendor/dashboard.html',
                                    vendor={'shop_name': 'Unknown', 'vendor_code': 'N/A'},
                                    stats={})

# ============ VENDOR PRODUCT MANAGEMENT ============

@app.route('/vendor/products')
@vendor_required
def vendor_products():
    """Vendor products list"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT p.*, c.name_en as category_name, c.name_ar as category_name_ar
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.vendor_id = ?
    '''
    params = [vendor_id]
    
    if status != 'all':
        query += ' AND p.status = ?'
        params.append(status)
    
    if category != 'all' and category:
        query += ' AND p.category_id = ?'
        params.append(category)
    
    if search:
        query += ' AND (p.name_en LIKE ? OR p.name_ar LIKE ? OR p.sku LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])
    
    query += ' ORDER BY p.created_at DESC'
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    # Get categories for filter
    cursor.execute('SELECT id, name_en, name_ar FROM categories WHERE status = "active"')
    categories = cursor.fetchall()
    
    # Get stats
    cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ?', (vendor_id,))
    total_products = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ? AND status = "active"', 
                  (vendor_id,))
    active_products = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ? AND stock <= low_stock_alert', 
                  (vendor_id,))
    low_stock_count = cursor.fetchone()[0]
    
    stats = {
        'total': total_products,
        'active': active_products,
        'low_stock': low_stock_count
    }
    
    return render_template('vendor/products.html',
                         products=products,
                         categories=categories,
                         stats=stats,
                         current_status=status,
                         current_category=category,
                         search=search)

@app.route('/vendor/products/add', methods=['GET', 'POST'])
@vendor_required
def vendor_add_product():
    """Add new product"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        try:
            # ============ COLLECT FORM DATA ============
            # Basic Information
            name_en = request.form.get('name_en', '').strip()
            name_ar = request.form.get('name_ar', '').strip()
            description_en = request.form.get('description_en', '').strip()
            description_ar = request.form.get('description_ar', '').strip()
            detailed_description = request.form.get('detailed_description', '').strip()
            
            # Pricing
            price = float(request.form.get('price', 0))
            b2b_price = float(request.form.get('b2b_price', price))
            cost_price = float(request.form.get('cost_price', 0))
            
            # Inventory
            stock = int(request.form.get('stock', 0))
            low_stock_alert = int(request.form.get('low_stock_alert', 10))
            sku = request.form.get('sku', '').strip()
            product_code = request.form.get('product_code', '').strip()
            
            # Categorization
            category_id = request.form.get('category_id')
            unit = request.form.get('unit', 'piece')
            weight = float(request.form.get('weight', 0))
            
            # Settings
            status = request.form.get('status', 'active')
            visibility = request.form.get('visibility', 'public')
            is_featured = 1 if request.form.get('is_featured') else 0
            allow_backorders = 1 if request.form.get('allow_backorders') else 0
            shipping_cost = float(request.form.get('shipping_cost', 0))
            delivery_days = int(request.form.get('delivery_days', 3))
            
            # ============ HANDLE FILE UPLOADS ============
            # Main Image (required)
            main_image = request.files.get('main_image')
            main_image_path = save_uploaded_file(main_image, 'products/images', 
                                               f'{vendor_id}_{sku}_main')
            
            if not main_image_path:
                flash('Main image is required', 'danger')
                return redirect(url_for('vendor_add_product'))
            
            # Image Gallery (multiple)
            gallery_files = request.files.getlist('image_gallery[]')
            gallery_paths = []
            for i, gallery_file in enumerate(gallery_files):
                if gallery_file and gallery_file.filename:
                    gallery_path = save_uploaded_file(gallery_file, 'products/gallery',
                                                    f'{vendor_id}_{sku}_gallery_{i}')
                    if gallery_path:
                        gallery_paths.append(gallery_path)
            
            # Video (optional)
            video_file = request.files.get('video')
            video_path = save_uploaded_file(video_file, 'products/videos',
                                          f'{vendor_id}_{sku}_video')
            
            # Document (optional)
            document_file = request.files.get('document')
            document_path = save_uploaded_file(document_file, 'products/documents',
                                             f'{vendor_id}_{sku}_document')
            
            # ============ VALIDATION ============
            if not all([name_en, name_ar, price, category_id]):
                flash('Please fill all required fields', 'warning')
                return redirect(url_for('vendor_add_product'))
            
            if price <= 0:
                flash('Price must be greater than 0', 'warning')
                return redirect(url_for('vendor_add_product'))
            
            # Check SKU uniqueness
            if sku:
                cursor.execute("SELECT id FROM products WHERE sku = ? AND vendor_id != ?", 
                             (sku, vendor_id))
                if cursor.fetchone():
                    flash('SKU already exists', 'danger')
                    return redirect(url_for('vendor_add_product'))
            
            # ============ SAVE TO DATABASE ============
            cursor.execute('''
                INSERT INTO products (
                    vendor_id, name_en, name_ar, description_en, description_ar,
                    detailed_description, price, b2b_price, cost_price, stock,
                    low_stock_alert, unit, weight, sku, product_code, category_id,
                    main_image, image_gallery, video_url, document_url, status,
                    visibility, is_featured, shipping_cost, delivery_days,
                    allow_backorders, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor_id, name_en, name_ar, description_en, description_ar,
                detailed_description, price, b2b_price, cost_price, stock,
                low_stock_alert, unit, weight, sku, product_code, category_id,
                main_image_path, ','.join(gallery_paths) if gallery_paths else None,
                video_path, document_path, status, visibility, is_featured,
                shipping_cost, delivery_days, allow_backorders,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            db.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('vendor_products'))
            
        except ValueError as e:
            flash(f'Invalid number format: {str(e)}', 'danger')
        except Exception as e:
            print(f"Add product error: {e}")
            flash(f'Error adding product: {str(e)}', 'danger')
    
    # GET request - show form
    cursor.execute('SELECT id, name_en, name_ar FROM categories WHERE status = "active"')
    categories = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT unit FROM products WHERE unit IS NOT NULL')
    units = [row[0] for row in cursor.fetchall()]
    
    return render_template('vendor/add_product.html',
                         categories=categories,
                         units=units)

@app.route('/vendor/products/<int:product_id>/edit', methods=['GET', 'POST'])
@vendor_required
def vendor_edit_product(product_id):
    """Edit product"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Check product ownership
    cursor.execute('SELECT * FROM products WHERE id = ? AND vendor_id = ?', 
                  (product_id, vendor_id))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found or access denied', 'danger')
        return redirect(url_for('vendor_products'))
    
    if request.method == 'POST':
        try:
            # ============ COLLECT FORM DATA ============
            # Basic Information
            name_en = request.form.get('name_en', '').strip()
            name_ar = request.form.get('name_ar', '').strip()
            description_en = request.form.get('description_en', '').strip()
            description_ar = request.form.get('description_ar', '').strip()
            detailed_description = request.form.get('detailed_description', '').strip()
            
            # Pricing
            price = float(request.form.get('price', 0))
            b2b_price = float(request.form.get('b2b_price', price))
            cost_price = float(request.form.get('cost_price', 0))
            
            # Inventory
            stock = int(request.form.get('stock', 0))
            low_stock_alert = int(request.form.get('low_stock_alert', 10))
            sku = request.form.get('sku', '').strip()
            product_code = request.form.get('product_code', '').strip()
            
            # Categorization
            category_id = request.form.get('category_id')
            unit = request.form.get('unit', 'piece')
            weight = float(request.form.get('weight', 0))
            
            # Settings
            status = request.form.get('status', 'active')
            visibility = request.form.get('visibility', 'public')
            is_featured = 1 if request.form.get('is_featured') else 0
            allow_backorders = 1 if request.form.get('allow_backorders') else 0
            shipping_cost = float(request.form.get('shipping_cost', 0))
            delivery_days = int(request.form.get('delivery_days', 3))
            
            # ============ HANDLE FILE UPLOADS ============
            # Main Image (update if new)
            main_image = request.files.get('main_image')
            main_image_path = product['main_image']
            if main_image and main_image.filename:
                main_image_path = save_uploaded_file(main_image, 'products/images',
                                                   f'{vendor_id}_{sku}_main')
            
            # Image Gallery
            gallery_files = request.files.getlist('image_gallery[]')
            existing_gallery = product['image_gallery'].split(',') if product['image_gallery'] else []
            
            # Remove deleted images
            keep_gallery = request.form.getlist('keep_gallery[]')
            existing_gallery = [img for img in existing_gallery if img in keep_gallery]
            
            # Add new images
            for i, gallery_file in enumerate(gallery_files):
                if gallery_file and gallery_file.filename:
                    gallery_path = save_uploaded_file(gallery_file, 'products/gallery',
                                                    f'{vendor_id}_{sku}_gallery_{i}')
                    if gallery_path:
                        existing_gallery.append(gallery_path)
            
            # Video (update if new)
            video_file = request.files.get('video')
            video_path = product['video_url']
            if video_file and video_file.filename:
                video_path = save_uploaded_file(video_file, 'products/videos',
                                              f'{vendor_id}_{sku}_video')
            
            # Video Link (optional)
            video_link = request.form.get('video_link', '').strip()
            if video_link:
                video_path = video_link
            
            # Document (update if new)
            document_file = request.files.get('document')
            document_path = product['document_url']
            if document_file and document_file.filename:
                document_path = save_uploaded_file(document_file, 'products/documents',
                                                 f'{vendor_id}_{sku}_document')
            
            # ============ VALIDATION ============
            if not all([name_en, name_ar, price, category_id]):
                flash('Please fill all required fields', 'warning')
                return redirect(url_for('vendor_edit_product', product_id=product_id))
            
            if price <= 0:
                flash('Price must be greater than 0', 'warning')
                return redirect(url_for('vendor_edit_product', product_id=product_id))
            
            # Check SKU uniqueness
            if sku and sku != product['sku']:
                cursor.execute("SELECT id FROM products WHERE sku = ? AND vendor_id != ?", 
                             (sku, vendor_id))
                if cursor.fetchone():
                    flash('SKU already exists', 'danger')
                    return redirect(url_for('vendor_edit_product', product_id=product_id))
            
            # ============ UPDATE DATABASE ============
            cursor.execute('''
                UPDATE products SET
                    name_en = ?, name_ar = ?, description_en = ?, description_ar = ?,
                    detailed_description = ?, price = ?, b2b_price = ?, cost_price = ?,
                    stock = ?, low_stock_alert = ?, unit = ?, weight = ?, sku = ?,
                    product_code = ?, category_id = ?, main_image = ?, image_gallery = ?,
                    video_url = ?, document_url = ?, status = ?, visibility = ?,
                    is_featured = ?, shipping_cost = ?, delivery_days = ?,
                    allow_backorders = ?, updated_at = ?
                WHERE id = ? AND vendor_id = ?
            ''', (
                name_en, name_ar, description_en, description_ar,
                detailed_description, price, b2b_price, cost_price,
                stock, low_stock_alert, unit, weight, sku,
                product_code, category_id, main_image_path,
                ','.join(existing_gallery) if existing_gallery else None,
                video_path, document_path, status, visibility,
                is_featured, shipping_cost, delivery_days,
                allow_backorders, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                product_id, vendor_id
            ))
            
            db.commit()
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('vendor_products'))
            
        except ValueError as e:
            flash(f'Invalid number format: {str(e)}', 'danger')
        except Exception as e:
            print(f"Edit product error: {e}")
            flash(f'Error updating product: {str(e)}', 'danger')
    
    # GET request - show form with existing data
    cursor.execute('SELECT id, name_en, name_ar FROM categories WHERE status = "active"')
    categories = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT unit FROM products WHERE unit IS NOT NULL')
    units = [row[0] for row in cursor.fetchall()]
    
    # Parse gallery images
    gallery_images = []
    if product['image_gallery']:
        gallery_images = product['image_gallery'].split(',')
    
    return render_template('vendor/edit_product.html',
                         product=product,
                         categories=categories,
                         units=units,
                         gallery_images=gallery_images)

@app.route('/vendor/products/<int:product_id>/delete', methods=['POST'])
@vendor_required
def vendor_delete_product(product_id):
    """Delete product"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Check product ownership
    cursor.execute('SELECT id FROM products WHERE id = ? AND vendor_id = ?', 
                  (product_id, vendor_id))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    # Check if product has orders
    cursor.execute('''
        SELECT COUNT(*) FROM order_items
        WHERE product_id = ? AND status != 'cancelled'
    ''', (product_id,))
    order_count = cursor.fetchone()[0]
    
    if order_count > 0:
        # Soft delete - change status to deleted
        cursor.execute('''
            UPDATE products SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND vendor_id = ?
        ''', (product_id, vendor_id))
        message = 'Product marked as deleted (has existing orders)'
    else:
        # Hard delete
        cursor.execute('DELETE FROM products WHERE id = ? AND vendor_id = ?', 
                      (product_id, vendor_id))
        message = 'Product deleted successfully'
    
    db.commit()
    
    return jsonify({'success': True, 'message': message})

@app.route('/vendor/products/<int:product_id>/toggle', methods=['POST'])
@vendor_required
def vendor_toggle_product(product_id):
    """Toggle product status (active/inactive)"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Check product ownership
    cursor.execute('SELECT status FROM products WHERE id = ? AND vendor_id = ?', 
                  (product_id, vendor_id))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})
    
    # Toggle status
    new_status = 'inactive' if product['status'] == 'active' else 'active'
    
    cursor.execute('''
        UPDATE products SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND vendor_id = ?
    ''', (new_status, product_id, vendor_id))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Product {new_status}',
        'new_status': new_status
    })
# ============ VENDOR ORDER MANAGEMENT ============

@app.route('/vendor/orders')
@vendor_required
def vendor_orders_list():
    """Vendor orders list"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT DISTINCT o.*, u.full_name as customer_name, u.phone as customer_phone,
               COUNT(oi.id) as items_count, SUM(oi.quantity) as total_quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE p.vendor_id = ?
    '''
    params = [vendor_id]
    
    if status != 'all':
        query += ' AND o.status = ?'
        params.append(status)
    
    if date_from:
        query += ' AND DATE(o.created_at) >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND DATE(o.created_at) <= ?'
        params.append(date_to)
    
    if search:
        query += ' AND (o.order_number LIKE ? OR u.full_name LIKE ? OR u.phone LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term])
    
    query += ' GROUP BY o.id ORDER BY o.created_at DESC'
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    # Get stats
    cursor.execute('''
        SELECT
            COUNT(DISTINCT o.id) as total_orders,
            SUM(CASE WHEN o.status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
            SUM(CASE WHEN o.status = 'processing' THEN 1 ELSE 0 END) as processing_orders,
            SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
            SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
            SUM(oi.total_price) as total_sales
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE p.vendor_id = ?
    ''', (vendor_id,))
    
    stats_result = cursor.fetchone()
    stats = {
        'total': stats_result[0] or 0,
        'pending': stats_result[1] or 0,
        'processing': stats_result[2] or 0,
        'completed': stats_result[3] or 0,
        'cancelled': stats_result[4] or 0,
        'total_sales': round(stats_result[5] or 0, 3)
    }
    
    return render_template('vendor/orders_list.html',
                         orders=orders,
                         stats=stats,
                         current_status=status,
                         date_from=date_from,
                         date_to=date_to,
                         search=search)

@app.route('/vendor/orders/<int:order_id>')
@vendor_required
def vendor_order_detail(order_id):
    """Vendor order details"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get order with vendor validation
    cursor.execute('''
        SELECT o.*, u.full_name as customer_name, u.email as customer_email,
               u.phone as customer_phone, u.address as customer_address
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ? AND EXISTS (
            SELECT 1 FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = o.id AND p.vendor_id = ?
        )
    ''', (order_id, vendor_id))
    
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found or access denied', 'danger')
        return redirect(url_for('vendor_orders_list'))
    
    # Get order items for this vendor
    cursor.execute('''
        SELECT oi.*, p.name_en, p.name_ar, p.main_image, p.sku,
               p.price as original_price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ? AND p.vendor_id = ?
    ''', (order_id, vendor_id))
    
    items = cursor.fetchall()
    
    # Calculate vendor total
    vendor_total = sum(item['total_price'] for item in items)
    
    # Get order history
    cursor.execute('''
        SELECT * FROM order_history
        WHERE order_id = ?
        ORDER BY created_at DESC
    ''', (order_id,))
    
    history = cursor.fetchall()
    
    return render_template('vendor/order_detail.html',
                         order=order,
                         items=items,
                         vendor_total=vendor_total,
                         history=history)

@app.route('/vendor/orders/<int:order_id>/update-status', methods=['POST'])
@vendor_required
def vendor_update_order_status(order_id):
    """Update order status"""
    vendor_id = session.get('vendor_id')
    new_status = request.form.get('status', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status is required'})
    
    db = get_db()
    cursor = db.cursor()
    
    # Verify vendor has items in this order
    cursor.execute('''
        SELECT COUNT(*)
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ? AND p.vendor_id = ?
    ''', (order_id, vendor_id))
    
    vendor_item_count = cursor.fetchone()[0]
    
    if vendor_item_count == 0:
        return jsonify({'success': False, 'message': 'Order not found'})
    
    # Update order status
    cursor.execute('''
        UPDATE orders SET status = ?, admin_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_status, notes, order_id))
    
    # Record in history
    cursor.execute('''
        INSERT INTO order_history (order_id, status, notes, created_by, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (order_id, new_status, notes, f'vendor:{vendor_id}'))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Order status updated to {new_status}',
        'new_status': new_status
    })

# ============ VENDOR FINANCIAL MANAGEMENT ============

@app.route('/vendor/finance')
@vendor_required
def vendor_finance():
    """Vendor financial dashboard"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get vendor balance
    cursor.execute('SELECT balance, total_earnings FROM vendors WHERE id = ?', (vendor_id,))
    vendor = cursor.fetchone()
    
    if not vendor:
        flash('Vendor not found', 'danger')
        return redirect(url_for('vendor_dashboard'))
    
    # Get commission summary
    cursor.execute('''
        SELECT
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_commission,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_commission,
            SUM(CASE WHEN status = 'cancelled' THEN amount ELSE 0 END) as cancelled_commission,
            COUNT(*) as total_commissions
        FROM commissions
        WHERE vendor_id = ?
    ''', (vendor_id,))
    
    commission_stats = cursor.fetchone()
    
    # Get recent transactions
    cursor.execute('''
        SELECT c.*, o.order_number, u.full_name as customer_name
        FROM commissions c
        LEFT JOIN orders o ON c.order_id = o.id
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.vendor_id = ?
        ORDER BY c.created_at DESC
        LIMIT 10
    ''', (vendor_id,))
    
    recent_commissions = cursor.fetchall()
    
    # Get withdrawal summary
    cursor.execute('''
        SELECT
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_withdrawal,
            SUM(CASE WHEN status = 'approved' THEN amount ELSE 0 END) as approved_withdrawal,
            SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as completed_withdrawal,
            SUM(CASE WHEN status = 'rejected' THEN amount ELSE 0 END) as rejected_withdrawal,
            COUNT(*) as total_withdrawals
        FROM withdrawals
        WHERE vendor_id = ?
    ''', (vendor_id,))
    
    withdrawal_stats = cursor.fetchone()
    
    # Get recent withdrawals
    cursor.execute('''
        SELECT * FROM withdrawals
        WHERE vendor_id = ?
        ORDER BY requested_at DESC
        LIMIT 10
    ''', (vendor_id,))
    
    recent_withdrawals = cursor.fetchall()
    
    stats = {
        'balance': round(vendor['balance'] or 0, 3),
        'total_earnings': round(vendor['total_earnings'] or 0, 3),
        'pending_commission': round(commission_stats[0] or 0, 3),
        'paid_commission': round(commission_stats[1] or 0, 3),
        'pending_withdrawal': round(withdrawal_stats[0] or 0, 3),
        'available_for_withdrawal': round((vendor['balance'] or 0) - (withdrawal_stats[0] or 0), 3)
    }
    
    return render_template('vendor/finance.html',
                         stats=stats,
                         recent_commissions=recent_commissions,
                         recent_withdrawals=recent_withdrawals)

@app.route('/vendor/withdraw', methods=['GET', 'POST'])
@vendor_required
def vendor_withdraw_request():
    """Request withdrawal"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get vendor balance
    cursor.execute('SELECT balance FROM vendors WHERE id = ?', (vendor_id,))
    vendor = cursor.fetchone()
    
    if not vendor:
        flash('Vendor not found', 'danger')
        return redirect(url_for('vendor_dashboard'))
    
    available_balance = vendor['balance'] or 0
    
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            method = request.form.get('method', '').strip()
            account_details = request.form.get('account_details', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validation
            if amount < MIN_WITHDRAWAL_LIMIT:
                flash(f'Minimum withdrawal amount is {MIN_WITHDRAWAL_LIMIT} KWD', 'warning')
                return redirect(url_for('vendor_withdraw_request'))
            
            if amount > available_balance:
                flash('Insufficient balance', 'danger')
                return redirect(url_for('vendor_withdraw_request'))
            
            if not method:
                flash('Withdrawal method is required', 'warning')
                return redirect(url_for('vendor_withdraw_request'))
            
            # Check pending withdrawals
            cursor.execute('''
                SELECT SUM(amount) as pending_total
                FROM withdrawals
                WHERE vendor_id = ? AND status = 'pending'
            ''', (vendor_id,))
            
            pending_total = cursor.fetchone()[0] or 0
            
            if (available_balance - pending_total) < amount:
                flash('You have pending withdrawal requests', 'warning')
                return redirect(url_for('vendor_withdraw_request'))
            
            # Create withdrawal request
            cursor.execute('''
                INSERT INTO withdrawals (
                    vendor_id, amount, method, account_details, notes, status,
                    requested_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            ''', (vendor_id, amount, method, account_details, notes))
            
            # Update vendor balance (reserve the amount)
            cursor.execute('''
                UPDATE vendors SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (amount, vendor_id))
            
            db.commit()
            
            flash('Withdrawal request submitted successfully!', 'success')
            return redirect(url_for('vendor_finance'))
            
        except ValueError:
            flash('Invalid amount', 'danger')
        except Exception as e:
            print(f"Withdrawal request error: {e}")
            flash(f'Error submitting withdrawal request: {str(e)}', 'danger')
    
    # GET request - show form
    # Get pending withdrawals total
    cursor.execute('''
        SELECT SUM(amount) as pending_total
        FROM withdrawals
        WHERE vendor_id = ? AND status = 'pending'
    ''', (vendor_id,))
    
    pending_result = cursor.fetchone()
    pending_total = pending_result[0] or 0
    
    available_for_withdrawal = available_balance - pending_total
    if available_for_withdrawal < 0:
        available_for_withdrawal = 0
    
    return render_template('vendor/withdraw_request.html',
                         available_balance=round(available_balance, 3),
                         pending_total=round(pending_total, 3),
                         available_for_withdrawal=round(available_for_withdrawal, 3),
                         min_withdrawal=MIN_WITHDRAWAL_LIMIT)

@app.route('/vendor/transactions')
@vendor_required
def vendor_transactions():
    """Vendor transaction history"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    type_filter = request.args.get('type', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Get commissions (income)
    commissions_query = '''
        SELECT
            c.id, c.amount, c.commission_rate, c.type, c.status,
            c.description, c.notes, c.paid_at, c.created_at,
            o.order_number, u.full_name as customer_name,
            'commission' as transaction_type,
            'income' as flow
        FROM commissions c
        LEFT JOIN orders o ON c.order_id = o.id
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.vendor_id = ?
    '''
    commission_params = [vendor_id]
    
    # Get withdrawals (outgoing)
    withdrawals_query = '''
        SELECT
            w.id, w.amount, NULL as commission_rate, w.method as type, w.status,
            w.account_details as description, w.notes, w.processed_at as paid_at, 
            w.requested_at as created_at,
            NULL as order_number, NULL as customer_name,
            'withdrawal' as transaction_type,
            'outgoing' as flow
        FROM withdrawals w
        WHERE w.vendor_id = ?
    '''
    withdrawal_params = [vendor_id]
    
    # Apply filters
    if type_filter != 'all':
        if type_filter == 'commission':
            withdrawals_query += ' AND 1=0'  # Hide withdrawals
        elif type_filter == 'withdrawal':
            commissions_query += ' AND 1=0'  # Hide commissions
    
    if date_from:
        commissions_query += ' AND DATE(c.created_at) >= ?'
        commission_params.append(date_from)
        withdrawals_query += ' AND DATE(w.requested_at) >= ?'
        withdrawal_params.append(date_from)
    
    if date_to:
        commissions_query += ' AND DATE(c.created_at) <= ?'
        commission_params.append(date_to)
        withdrawals_query += ' AND DATE(w.requested_at) <= ?'
        withdrawal_params.append(date_to)
    
    # Combine queries
    query = f'''
        ({commissions_query})
        UNION ALL
        ({withdrawals_query})
        ORDER BY created_at DESC
    '''
    params = commission_params + withdrawal_params
    
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    
    # Calculate totals
    total_income = 0
    total_outgoing = 0
    
    for trans in transactions:
        if trans['flow'] == 'income':
            total_income += trans['amount']
        else:
            total_outgoing += trans['amount']
    
    stats = {
        'total_income': round(total_income, 3),
        'total_outgoing': round(total_outgoing, 3),
        'net_balance': round(total_income - total_outgoing, 3)
    }
    
    return render_template('vendor/transactions.html',
                         transactions=transactions,
                         stats=stats,
                         current_type=type_filter,
                         date_from=date_from,
                         date_to=date_to)
# ============ ADMIN ROUTES ============

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # ============ QUICK STATS ============
        # Total Users
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'")
        total_users = cursor.fetchone()[0]
        
        # Total Vendors
        cursor.execute("SELECT COUNT(*) FROM vendors")
        total_vendors = cursor.fetchone()[0]
        
        # Active Vendors
        cursor.execute("SELECT COUNT(*) FROM vendors WHERE status = 'verified'")
        active_vendors = cursor.fetchone()[0]
        
        # Pending Vendors
        cursor.execute("SELECT COUNT(*) FROM vendors WHERE status = 'pending'")
        pending_vendors = cursor.fetchone()[0]
        
        # Total Products
        cursor.execute("SELECT COUNT(*) FROM products WHERE status != 'deleted'")
        total_products = cursor.fetchone()[0]
        
        # Active Products
        cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
        active_products = cursor.fetchone()[0]
        
        # Total Orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        
        # Pending Orders
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        pending_orders = cursor.fetchone()[0]
        
        # Today's Orders
        cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')")
        today_orders = cursor.fetchone()[0]
        
        # Total Revenue
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'")
        total_revenue_result = cursor.fetchone()
        total_revenue = total_revenue_result[0] if total_revenue_result[0] else 0
        
        # Today's Revenue
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE DATE(created_at) = DATE('now') AND status = 'completed'")
        today_revenue_result = cursor.fetchone()
        today_revenue = today_revenue_result[0] if today_revenue_result[0] else 0
        
        stats = {
            'users': total_users,
            'vendors': total_vendors,
            'active_vendors': active_vendors,
            'pending_vendors': pending_vendors,
            'products': total_products,
            'active_products': active_products,
            'orders': total_orders,
            'pending_orders': pending_orders,
            'today_orders': today_orders,
            'revenue': round(total_revenue, 3),
            'today_revenue': round(today_revenue, 3)
        }
        
        # ============ RECENT DATA ============
        # Recent Orders
        cursor.execute('''
            SELECT o.*, u.full_name as customer_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 10
        ''')
        recent_orders = cursor.fetchall()
        
        # Recent Vendors
        cursor.execute('''
            SELECT v.*, u.full_name as user_name
            FROM vendors v
            LEFT JOIN users u ON v.user_id = u.id
            ORDER BY v.created_at DESC
            LIMIT 10
        ''')
        recent_vendors = cursor.fetchall()
        
        # Recent Users
        cursor.execute('''
            SELECT * FROM users
            WHERE role = 'customer'
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        recent_users = cursor.fetchall()
        
        # ============ CHART DATA (Last 7 days) ============
        cursor.execute('''
            SELECT
                DATE(created_at) as date,
                COUNT(*) as order_count,
                SUM(CASE WHEN status = 'completed' THEN total_price ELSE 0 END) as revenue
            FROM orders
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        chart_data = cursor.fetchall()
        
        # Format chart data
        dates = []
        orders_data = []
        revenue_data = []
        
        for row in chart_data:
            dates.append(row['date'])
            orders_data.append(row['order_count'])
            revenue_data.append(row['revenue'] or 0)
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_orders=recent_orders,
                             recent_vendors=recent_vendors,
                             recent_users=recent_users,
                             chart_dates=dates,
                             chart_orders=orders_data,
                             chart_revenue=revenue_data)
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading dashboard', 'danger')
        return render_template('admin/dashboard.html',
                             stats={},
                             recent_orders=[],
                             recent_vendors=[],
                             recent_users=[])

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    role = request.args.get('role', 'all')
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = 'SELECT * FROM users WHERE 1=1'
    params = []
    
    if role != 'all':
        query += ' AND role = ?'
        params.append(role)
    
    if status != 'all':
        if status == 'active':
            query += ' AND is_active = 1'
        elif status == 'inactive':
            query += ' AND is_active = 0'
    
    if search:
        query += ' AND (username LIKE ? OR email LIKE ? OR full_name LIKE ? OR phone LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'")
    total_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'vendor'")
    total_vendor_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    total_admins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()[0]
    
    stats = {
        'customers': total_customers,
        'vendors': total_vendor_users,
        'admins': total_admins,
        'active': active_users,
        'total': total_customers + total_vendor_users + total_admins
    }
    
    return render_template('admin/users.html',
                         users=users,
                         stats=stats,
                         current_role=role,
                         current_status=status,
                         search=search)

@app.route('/admin/users/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    """Admin user detail"""
    db = get_db()
    cursor = db.cursor()
    
    # Get user
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_users'))
    
    # Get user orders
    cursor.execute('''
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,))
    orders = cursor.fetchall()
    
    # Get user referrals
    cursor.execute('''
        SELECT u.*
        FROM users u
        WHERE u.referred_by = ?
        ORDER BY u.created_at DESC
    ''', (user['referral_code'],))
    referrals = cursor.fetchall()
    
    # Get user commissions
    cursor.execute('''
        SELECT c.*, o.order_number
        FROM commissions c
        LEFT JOIN orders o ON c.order_id = o.id
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
        LIMIT 10
    ''', (user_id,))
    commissions = cursor.fetchall()
    
    # Get vendor info if exists
    vendor = None
    if user['role'] == 'vendor':
        cursor.execute('SELECT * FROM vendors WHERE user_id = ?', (user_id,))
        vendor = cursor.fetchone()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         orders=orders,
                         referrals=referrals,
                         commissions=commissions,
                         vendor=vendor)

@app.route('/admin/users/<int:user_id>/update', methods=['POST'])
@admin_required
def admin_update_user(user_id):
    """Update user"""
    db = get_db()
    cursor = db.cursor()
    
    # Get form data
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    role = request.form.get('role', '').strip()
    is_active = 1 if request.form.get('is_active') else 0
    email_verified = 1 if request.form.get('email_verified') else 0
    
    # Update user
    cursor.execute('''
        UPDATE users SET
            full_name = ?, phone = ?, role = ?, is_active = ?, email_verified = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (full_name, phone, role, is_active, email_verified, user_id))
    
    # If changing to vendor role, create vendor record if not exists
    if role == 'vendor':
        cursor.execute('SELECT id FROM vendors WHERE user_id = ?', (user_id,))
        vendor_exists = cursor.fetchone()
        
        if not vendor_exists:
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                vendor_code = generate_vendor_code()
                cursor.execute('''
                    INSERT INTO vendors (
                    
                        user_id, name, email, password, phone, shop_name,
                        vendor_code, status, kyc_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 'pending', 
                             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, user['full_name'] or user['username'], 
                     user['email'], user['password'], user['phone'],
                     user['full_name'] or user['username'], vendor_code))
    
    db.commit()
    
    flash('User updated successfully', 'success')
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/admin/vendors')
@admin_required
def admin_vendors():
    """Admin vendors management"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    kyc_status = request.args.get('kyc_status', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT v.*, u.full_name as user_name, u.email as user_email
        FROM vendors v
        LEFT JOIN users u ON v.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if status != 'all':
        query += ' AND v.status = ?'
        params.append(status)
    
    if kyc_status != 'all':
        query += ' AND v.kyc_status = ?'
        params.append(kyc_status)
    
    if search:
        query += ' AND (v.shop_name LIKE ? OR v.business_name LIKE ? OR v.vendor_code LIKE ? OR v.email LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    query += ' ORDER BY v.created_at DESC'
    
    cursor.execute(query, params)
    vendors = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM vendors")
    total_vendors = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vendors WHERE status = 'verified'")
    verified_vendors = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vendors WHERE status = 'pending'")
    pending_vendors = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vendors WHERE kyc_status = 'verified'")
    kyc_verified = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(balance) FROM vendors")
    total_balance_result = cursor.fetchone()
    total_balance = total_balance_result[0] if total_balance_result[0] else 0
    
    stats = {
        'total': total_vendors,
        'verified': verified_vendors,
        'pending': pending_vendors,
        'kyc_verified': kyc_verified,
        'total_balance': round(total_balance, 3)
    }
    
    return render_template('admin/vendors.html',
                         vendors=vendors,
                         stats=stats,
                         current_status=status,
                         current_kyc_status=kyc_status,
                         search=search)

@app.route('/admin/vendors/<int:vendor_id>')
@admin_required
def admin_vendor_detail(vendor_id):
    """Admin vendor detail"""
    db = get_db()
    cursor = db.cursor()
    
    # Get vendor
    cursor.execute('''
        SELECT v.*, u.full_name as user_name, u.username, u.email as user_email
        FROM vendors v
        LEFT JOIN users u ON v.user_id = u.id
        WHERE v.id = ?
    ''', (vendor_id,))
    vendor = cursor.fetchone()
    
    if not vendor:
        flash('Vendor not found', 'danger')
        return redirect(url_for('admin_vendors'))
    
    # Get vendor products
    cursor.execute('''
        SELECT * FROM products
        WHERE vendor_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (vendor_id,))
    products = cursor.fetchall()
    
    # Get vendor orders
    cursor.execute('''
        SELECT DISTINCT o.*, u.full_name as customer_name
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE p.vendor_id = ?
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (vendor_id,))
    orders = cursor.fetchall()
    
    # Get vendor commissions
    cursor.execute('''
        SELECT c.*, o.order_number
        FROM commissions c
        LEFT JOIN orders o ON c.order_id = o.id
        WHERE c.vendor_id = ?
        ORDER BY c.created_at DESC
        LIMIT 10
    ''', (vendor_id,))
    commissions = cursor.fetchall()
    
    # Get vendor withdrawals
    cursor.execute('''
        SELECT * FROM withdrawals
        WHERE vendor_id = ?
        ORDER BY requested_at DESC
        LIMIT 10
    ''', (vendor_id,))
    withdrawals = cursor.fetchall()
    
    # Calculate totals
    cursor.execute('SELECT COUNT(*) FROM products WHERE vendor_id = ?', (vendor_id,))
    total_products = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(DISTINCT o.id)
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE p.vendor_id = ?
    ''', (vendor_id,))
    total_orders = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT SUM(oi.total_price)
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE p.vendor_id = ? AND oi.status = 'completed'
    ''', (vendor_id,))
    total_sales_result = cursor.fetchone()
    total_sales = total_sales_result[0] if total_sales_result[0] else 0
    
    stats = {
        'products': total_products,
        'orders': total_orders,
        'sales': round(total_sales, 3),
        'balance': round(vendor['balance'] or 0, 3),
        'earnings': round(vendor['total_earnings'] or 0, 3)
    }
    
    return render_template('admin/vendor_detail.html',
                         vendor=vendor,
                         products=products,
                         orders=orders,
                         commissions=commissions,
                         withdrawals=withdrawals,
                         stats=stats)

@app.route('/admin/vendors/<int:vendor_id>/update-status', methods=['POST'])
@admin_required
def admin_update_vendor_status(vendor_id):
    """Update vendor status"""
    status = request.form.get('status', '').strip()
    kyc_status = request.form.get('kyc_status', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not status:
        return jsonify({'success': False, 'message': 'Status is required'})
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current vendor
    cursor.execute('SELECT * FROM vendors WHERE id = ?', (vendor_id,))
    vendor = cursor.fetchone()
    
    if not vendor:
        return jsonify({'success': False, 'message': 'Vendor not found'})
    
    # Update vendor
    cursor.execute('''
        UPDATE vendors SET
            status = ?, kyc_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, kyc_status, vendor_id))
    
    # Update user role if vendor is verified
    if status == 'verified' and vendor['user_id']:
        cursor.execute('''
            UPDATE users SET role = 'vendor', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (vendor['user_id'],))
        
        # Send notification email (in production)
        try:
            send_vendor_approval_email(vendor['email'], vendor['shop_name'], status)
        except:
            pass
    
    # Record in audit log
    cursor.execute('''
        INSERT INTO vendor_audit_log (
            vendor_id, action, old_status, new_status, notes, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (vendor_id, 'status_update', vendor['status'], status, 
         notes, f'admin:{session["user_id"]}'))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Vendor status updated to {status}',
        'new_status': status,
        'new_kyc_status': kyc_status
    })

def send_vendor_approval_email(email, shop_name, status):
    """Send vendor approval email"""
    # This is a placeholder - implement email sending in production
    print(f"Would send email to {email} about vendor status {status} for {shop_name}")
    return True
# ============ ADMIN PRODUCT MANAGEMENT ============

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products management"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    vendor = request.args.get('vendor', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT p.*, v.shop_name, v.vendor_code,
               c.name_en as category_name, c.name_ar as category_name_ar
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.status != 'deleted'
    '''
    params = []
    
    if status != 'all':
        query += ' AND p.status = ?'
        params.append(status)
    
    if category != 'all' and category:
        query += ' AND p.category_id = ?'
        params.append(category)
    
    if vendor != 'all' and vendor:
        query += ' AND p.vendor_id = ?'
        params.append(vendor)
    
    if search:
        query += ' AND (p.name_en LIKE ? OR p.name_ar LIKE ? OR p.sku LIKE ? OR p.product_code LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    query += ' ORDER BY p.created_at DESC'
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    # Get filters data
    cursor.execute('SELECT id, name_en, name_ar FROM categories WHERE status = "active"')
    categories = cursor.fetchall()
    
    cursor.execute('SELECT id, shop_name, vendor_code FROM vendors WHERE status = "verified"')
    vendors = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM products WHERE status != 'deleted'")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
    active_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'inactive'")
    inactive_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= low_stock_alert")
    low_stock = cursor.fetchone()[0]
    
    stats = {
        'total': total_products,
        'active': active_products,
        'inactive': inactive_products,
        'low_stock': low_stock
    }
    
    return render_template('admin/products.html',
                         products=products,
                         categories=categories,
                         vendors=vendors,
                         stats=stats,
                         current_status=status,
                         current_category=category,
                         current_vendor=vendor,
                         search=search)

@app.route('/admin/products/<int:product_id>')
@admin_required
def admin_product_detail(product_id):
    """Admin product detail"""
    db = get_db()
    cursor = db.cursor()
    
    # Get product with related data
    cursor.execute('''
        SELECT p.*, v.shop_name, v.vendor_code, v.business_name,
               c.name_en as category_name, c.name_ar as category_name_ar
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
    
    # Get product orders
    cursor.execute('''
        SELECT o.*, u.full_name as customer_name, oi.quantity, oi.unit_price
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN users u ON o.user_id = u.id
        WHERE oi.product_id = ?
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (product_id,))
    orders = cursor.fetchall()
    
    # Parse gallery images
    gallery_images = []
    if product['image_gallery']:
        gallery_images = product['image_gallery'].split(',')
    
    return render_template('admin/product_detail.html',
                         product=product,
                         orders=orders,
                         gallery_images=gallery_images)

@app.route('/admin/products/<int:product_id>/update', methods=['POST'])
@admin_required
def admin_update_product(product_id):
    """Update product (admin)"""
    db = get_db()
    cursor = db.cursor()
    
    # Get form data
    status = request.form.get('status', '').strip()
    visibility = request.form.get('visibility', '').strip()
    is_featured = 1 if request.form.get('is_featured') else 0
    admin_notes = request.form.get('admin_notes', '').strip()
    
    # Update product
    cursor.execute('''
        UPDATE products SET
            status = ?, visibility = ?, is_featured = ?,
            admin_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, visibility, is_featured, admin_notes, product_id))
    
    db.commit()
    
    flash('Product updated successfully', 'success')
    return redirect(url_for('admin_product_detail', product_id=product_id))

# ============ ADMIN ORDER MANAGEMENT ============

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders management"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT o.*, u.full_name as customer_name, u.email as customer_email,
               COUNT(DISTINCT oi.id) as items_count,
               GROUP_CONCAT(DISTINCT v.shop_name) as vendor_names
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE 1=1
    '''
    params = []
    
    if status != 'all':
        query += ' AND o.status = ?'
        params.append(status)
    
    if date_from:
        query += ' AND DATE(o.created_at) >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND DATE(o.created_at) <= ?'
        params.append(date_to)
    
    if search:
        query += ' AND (o.order_number LIKE ? OR u.full_name LIKE ? OR u.email LIKE ? OR u.phone LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    query += ' GROUP BY o.id ORDER BY o.created_at DESC'
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    pending_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'processing'")
    processing_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
    completed_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'cancelled'")
    cancelled_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'")
    total_revenue_result = cursor.fetchone()
    total_revenue = total_revenue_result[0] if total_revenue_result[0] else 0
    
    # Today's stats
    cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')")
    today_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE DATE(created_at) = DATE('now') AND status = 'completed'")
    today_revenue_result = cursor.fetchone()
    today_revenue = today_revenue_result[0] if today_revenue_result[0] else 0
    
    stats = {
        'total': total_orders,
        'pending': pending_orders,
        'processing': processing_orders,
        'completed': completed_orders,
        'cancelled': cancelled_orders,
        'revenue': round(total_revenue, 3),
        'today_orders': today_orders,
        'today_revenue': round(today_revenue, 3)
    }
    
    return render_template('admin/orders.html',
                         orders=orders,
                         stats=stats,
                         current_status=status,
                         date_from=date_from,
                         date_to=date_to,
                         search=search)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin order detail"""
    db = get_db()
    cursor = db.cursor()
    
    # Get order
    cursor.execute('''
        SELECT o.*, u.full_name as customer_name, u.email as customer_email,
               u.phone as customer_phone, u.address as customer_address
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('admin_orders'))
    
    # Get order items
    cursor.execute('''
        SELECT oi.*, p.name_en, p.name_ar, p.main_image, p.sku,
               v.shop_name, v.vendor_code
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items = cursor.fetchall()
    
    # Get order history
    cursor.execute('''
        SELECT * FROM order_history
        WHERE order_id = ?
        ORDER BY created_at DESC
    ''', (order_id,))
    history = cursor.fetchall()
    
    # Get commissions for this order
    cursor.execute('''
        SELECT c.*, u.full_name as recipient_name, v.shop_name as vendor_name
        FROM commissions c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN vendors v ON c.vendor_id = v.id
        WHERE c.order_id = ?
        ORDER BY c.created_at
    ''', (order_id,))
    commissions = cursor.fetchall()
    
    return render_template('admin/order_detail.html',
                         order=order,
                         items=items,
                         history=history,
                         commissions=commissions)

@app.route('/admin/orders/<int:order_id>/update', methods=['POST'])
@admin_required
def admin_update_order(order_id):
    """Update order (admin)"""
    status = request.form.get('status', '').strip()
    payment_status = request.form.get('payment_status', '').strip()
    admin_notes = request.form.get('admin_notes', '').strip()
    estimated_delivery = request.form.get('estimated_delivery', '').strip()
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current order
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'})
    
    # Update order
    update_fields = []
    params = []
    
    if status:
        update_fields.append('status = ?')
        params.append(status)
    
    if payment_status:
        update_fields.append('payment_status = ?')
        params.append(payment_status)
    
    if admin_notes is not None:
        update_fields.append('admin_notes = ?')
        params.append(admin_notes)
    
    if estimated_delivery:
        update_fields.append('estimated_delivery = ?')
        params.append(estimated_delivery)
    
    update_fields.append('updated_at = CURRENT_TIMESTAMP')
    
    if update_fields:
        query = f'UPDATE orders SET {", ".join(update_fields)} WHERE id = ?'
        params.append(order_id)
        
        cursor.execute(query, params)
        
        # Record in history if status changed
        if status and status != order['status']:
            cursor.execute('''
                INSERT INTO order_history (order_id, status, notes, created_by, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (order_id, status, f'Status changed by admin', f'admin:{session["user_id"]}'))
            
            # Process commissions if order completed
            if status == 'completed' and order['status'] != 'completed':
                process_order_commissions(order_id)
        
        db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order updated successfully',
        'new_status': status or order['status']
    })

# ============ ADMIN COMMISSION MANAGEMENT ============

@app.route('/admin/commissions')
@admin_required
def admin_commissions():
    """Admin commissions management"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT c.*,
               u.full_name as user_name, u.email as user_email,
               v.shop_name as  v.vendor_code,
               o.order_number
        FROM commissions c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN vendors v ON c.vendor_id = v.id
        LEFT JOIN orders o ON c.order_id = o.id
        WHERE 1=1
    '''
    params = []
    
    if status != 'all':
        query += ' AND c.status = ?'
        params.append(status)
    
    if type_filter != 'all':
        query += ' AND c.type = ?'
        params.append(type_filter)
    
    if date_from:
        query += ' AND DATE(c.created_at) >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND DATE(c.created_at) <= ?'
        params.append(date_to)
    
    if search:
        query += ' AND (u.full_name LIKE ? OR u.email LIKE ? OR v.shop_name LIKE ? OR o.order_number LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    query += ' ORDER BY c.created_at DESC'
    
    cursor.execute(query, params)
    commissions = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM commissions")
    total_commissions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM commissions WHERE status = 'pending'")
    pending_commissions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM commissions WHERE status = 'paid'")
    paid_commissions = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM commissions")
    total_amount_result = cursor.fetchone()
    total_amount = total_amount_result[0] if total_amount_result[0] else 0
    
    cursor.execute("SELECT SUM(amount) FROM commissions WHERE status = 'pending'")
    pending_amount_result = cursor.fetchone()
    pending_amount = pending_amount_result[0] if pending_amount_result[0] else 0
    
    cursor.execute("SELECT SUM(amount) FROM commissions WHERE status = 'paid'")
    paid_amount_result = cursor.fetchone()
    paid_amount = paid_amount_result[0] if paid_amount_result[0] else 0
    
    stats = {
        'total': total_commissions,
        'pending': pending_commissions,
        'paid': paid_commissions,
        'total_amount': round(total_amount, 3),
        'pending_amount': round(pending_amount, 3),
        'paid_amount': round(paid_amount, 3)
    }
    
    return render_template('admin/commissions.html',
                         commissions=commissions,
                         stats=stats,
                         current_status=status,
                         current_type=type_filter,
                         date_from=date_from,
                         date_to=date_to,
                         search=search)

@app.route('/admin/commissions/<int:commission_id>/update', methods=['POST'])
@admin_required
def admin_update_commission(commission_id):
    """Update commission status"""
    status = request.form.get('status', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not status:
        return jsonify({'success': False, 'message': 'Status is required'})
    
    db = get_db()
    cursor = db.cursor()
    
    # Get current commission
    cursor.execute('SELECT * FROM commissions WHERE id = ?', (commission_id,))
    commission = cursor.fetchone()
    
    if not commission:
        return jsonify({'success': False, 'message': 'Commission not found'})
    
    # Update commission
    paid_at = 'CURRENT_TIMESTAMP' if status == 'paid' else 'NULL'
    
    cursor.execute(f'''
        UPDATE commissions SET
            status = ?, notes = ?, paid_at = {paid_at},
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, notes, commission_id))
    
    # If paying commission, update user/vendor balance
    if status == 'paid' and commission['status'] != 'paid':
        if commission['user_id']:
            # User commission
            cursor.execute('''
                UPDATE users
                SET wallet_balance = wallet_balance + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (commission['amount'], commission['user_id']))
        elif commission['vendor_id']:
            # Vendor commission
            cursor.execute('''
                UPDATE vendors
                SET balance = balance + ?, total_earnings = total_earnings + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (commission['amount'], commission['amount'], commission['vendor_id']))
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': f'Commission status updated to {status}',
        'new_status': status
    })
# ============ PUBLIC PRODUCT ROUTES ============

@app.route('/products')
def products():
    """Public products listing"""
    db = get_db()
    cursor = db.cursor()
    
    # Get filter parameters
    category = request.args.get('category', '')
    vendor = request.args.get('vendor', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build query
    query = '''
        SELECT p.*, v.shop_name, v.vendor_code,
               c.name_en as category_name, c.name_ar as category_name_ar
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.status = 'active' AND p.visibility = 'public'
        AND v.status = 'verified'
    '''
    params = []
    
    if category:
        query += ' AND p.category_id = ?'
        params.append(category)
    
    if vendor:
        query += ' AND p.vendor_id = ?'
        params.append(vendor)
    
    if search:
        query += ' AND (p.name_en LIKE ? OR p.name_ar LIKE ? OR p.description_en LIKE ? OR p.description_ar LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])
    
    if min_price:
        query += ' AND p.price >= ?'
        params.append(float(min_price))
    
    if max_price:
        query += ' AND p.price <= ?'
        params.append(float(max_price))
    
    # Sorting
    if sort == 'price_low':
        query += ' ORDER BY p.price ASC'
    elif sort == 'price_high':
        query += ' ORDER BY p.price DESC'
    elif sort == 'popular':
        query += ' ORDER BY p.sales_count DESC'
    elif sort == 'rating':
        query += ' ORDER BY p.rating DESC'
    else:  # newest
        query += ' ORDER BY p.created_at DESC'
    
    # Count total for pagination
    count_query = 'SELECT COUNT(*) FROM (' + query + ')'
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page
    
    # Apply pagination
    offset = (page - 1) * per_page
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    products_list = [RowWrapper(row) for row in cursor.fetchall()]
    
    # Get filters data
    cursor.execute('SELECT id, name_en, name_ar FROM categories WHERE status = "active"')
    categories = cursor.fetchall()
    
    cursor.execute('SELECT id, shop_name, vendor_code FROM vendors WHERE status = "verified"')
    vendors = cursor.fetchall()
    
    # Get featured categories
    cursor.execute('''
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.status = 'active'
        WHERE c.status = 'active'
        GROUP BY c.id
        ORDER BY c.sort_order, c.name_en
        LIMIT 8
    ''')
    featured_categories = cursor.fetchall()
    
    return render_template('products.html',
                         products=products_list,
                         categories=categories,
                         vendors=vendors,
                         featured_categories=featured_categories,
                         current_category=category,
                         current_vendor=vendor,
                         search=search,
                         sort=sort,
                         min_price=min_price,
                         max_price=max_price,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Public product detail page"""
    db = get_db()
    cursor = db.cursor()
    
    # Get product with related data
    cursor.execute('''
        SELECT p.*, v.shop_name, v.vendor_code, v.business_name,
               v.profile_image as vendor_logo,
               c.name_en as category_name, c.name_ar as category_name_ar
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ? AND p.status = 'active' AND p.visibility = 'public'
        AND v.status = 'verified'
    ''', (product_id,))
    product_row = cursor.fetchone()
    
    if not product_row:
        flash('Product not found or unavailable', 'warning')
        return redirect(url_for('products'))
    
    product = RowWrapper(product_row)
    
    # Increment views
    cursor.execute('''
        UPDATE products SET views = views + 1
        WHERE id = ?
    ''', (product_id,))
    
    # Get related products (same category)
    cursor.execute('''
        SELECT p.*, v.shop_name
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE p.category_id = ?
        AND p.id != ?
        AND p.status = 'active'
        AND p.visibility = 'public'
        AND v.status = 'verified'
        ORDER BY RANDOM()
        LIMIT 4
    ''', (product.category_id, product_id))
    related_products = [RowWrapper(row) for row in cursor.fetchall()]
    
    # Get product reviews
    cursor.execute('''
        SELECT r.*, u.full_name as reviewer_name
        FROM reviews r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE r.product_id = ? AND r.status = 'approved'
        ORDER BY r.created_at DESC
        LIMIT 10
    ''', (product_id,))
    reviews = cursor.fetchall()
    
    # Parse gallery images
    gallery_images = []
    if product.image_gallery:
        gallery_images = product.image_gallery.split(',')
    
    db.commit()
    
    return render_template('product_detail.html',
                         product=product,
                         related_products=related_products,
                         reviews=reviews,
                         gallery_images=gallery_images)

@app.route('/categories')
def categories():
    """Categories listing"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.status = 'active'
        WHERE c.status = 'active'
        GROUP BY c.id
        ORDER BY c.sort_order, c.name_en
    ''')
    categories_list = cursor.fetchall()
    
    return render_template('categories.html',
                         categories=categories_list)

# ============ CART & CHECKOUT SYSTEM ============

@app.route('/cart')
@login_required
def cart():
    """Shopping cart"""
    cart_items = session.get('cart', [])
    
    if not cart_items:
        return render_template('cart.html', cart_items=[], total=0)
    
    db = get_db()
    cursor = db.cursor()
    
    cart_products = []
    total = 0
    
    for item in cart_items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        
        cursor.execute('''
            SELECT p.*, v.shop_name, v.vendor_code
            FROM products p
            LEFT JOIN vendors v ON p.vendor_id = v.id
            WHERE p.id = ? AND p.status = 'active'
        ''', (product_id,))
        product = cursor.fetchone()
        
        if product:
            item_total = product['price'] * quantity
            total += item_total
            
            cart_products.append({
                'id': product['id'],
                'name_en': product['name_en'],
                'name_ar': product['name_ar'],
                'price': product['price'],
                'main_image': product['main_image'],
                'shop_name': product['shop_name'],
                'vendor_code': product['vendor_code'],
                'quantity': quantity,
                'item_total': item_total,
                'stock': product['stock'],
                'unit': product['unit']
            })
    
    return render_template('cart.html',
                         cart_items=cart_products,
                         total=round(total, 3))

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = int(request.form.get('quantity', 1))
    
    if quantity < 1:
        flash('Quantity must be at least 1', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    db = get_db()
    cursor = db.cursor()
    
    # Check product availability
    cursor.execute('''
        SELECT stock, status FROM products
        WHERE id = ? AND status = 'active'
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not available', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    
    if product['stock'] < quantity:
        flash(f'Only {product["stock"]} items available in stock', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Add to cart session
    cart = session.get('cart', [])
    
    # Check if product already in cart
    found = False
    for item in cart:
        if item['product_id'] == product_id:
            new_quantity = item['quantity'] + quantity
            if new_quantity > product['stock']:
                flash(f'Cannot add more than {product["stock"]} items', 'warning')
                return redirect(url_for('product_detail', product_id=product_id))
            item['quantity'] = new_quantity
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

@app.route('/update-cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    """Update cart quantity"""
    quantity = int(request.form.get('quantity', 0))
    
    cart = session.get('cart', [])
    
    if quantity <= 0:
        # Remove item
        cart = [item for item in cart if item['product_id'] != product_id]
    else:
        # Check stock
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if product and quantity > product['stock']:
            flash(f'Only {product["stock"]} items available', 'warning')
            return redirect(url_for('cart'))
        
        # Update quantity
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
    
    session['cart'] = cart
    session.modified = True
    
    flash('Cart updated', 'success')
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    
    session['cart'] = cart
    session.modified = True
    
    flash('Item removed from cart', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    cart_items = session.get('cart', [])
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get cart details with validation
    cart_products = []
    total = 0
    vendors = {}
    
    for item in cart_items:
        product_id = item['product_id']
        quantity = item['quantity']
        
        cursor.execute('''
            SELECT p.*, v.shop_name, v.vendor_id, v.vendor_code
            FROM products p
            LEFT JOIN vendors v ON p.vendor_id = v.id
            WHERE p.id = ? AND p.status = 'active' AND v.status = 'verified'
        ''', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash(f'Product ID {product_id} is no longer available', 'warning')
            return redirect(url_for('cart'))
        
        if product['stock'] < quantity:
            flash(f'Not enough stock for {product["name_en"]}', 'warning')
            return redirect(url_for('cart'))
        
        item_total = product['price'] * quantity
        total += item_total
        
        # Group by vendor
        vendor_id = product['vendor_id']
        if vendor_id not in vendors:
            vendors[vendor_id] = {
                'shop_name': product['shop_name'],
                'vendor_code': product['vendor_code'],
                'items': [],
                'subtotal': 0
            }
        
        vendors[vendor_id]['items'].append({
            'product_id': product_id,
            'name_en': product['name_en'],
            'name_ar': product['name_ar'],
            'price': product['price'],
            'quantity': quantity,
            'item_total': item_total
        })
        vendors[vendor_id]['subtotal'] += item_total
        
        cart_products.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total
        })
    
    if request.method == 'POST':
        try:
            # Get form data
            shipping_address = request.form.get('shipping_address', '').strip()
            billing_address = request.form.get('billing_address', '').strip()
            customer_notes = request.form.get('customer_notes', '').strip()
            payment_method = request.form.get('payment_method', 'cod')
            
            if not shipping_address:
                flash('Shipping address is required', 'warning')
                return render_template('checkout.html',
                                     cart_products=cart_products,
                                     total=total,
                                     vendors=vendors)
            
            # Generate order number
            order_number = f'SOQ-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
            
            # Create main order
            cursor.execute('''
                INSERT INTO orders (
                    order_number, user_id, total_price, subtotal, shipping_cost,
                    tax_amount, status, payment_method, payment_status,
                    shipping_address, billing_address, customer_notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 0, 'pending', ?, 'pending',
                         ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (order_number, session['user_id'], total, total,
                 payment_method, shipping_address, billing_address, customer_notes))
            
            order_id = cursor.lastrowid
            
            # Create order items
            for vendor_id, vendor_data in vendors.items():
                for item in vendor_data['items']:
                    cursor.execute('''
                        INSERT INTO order_items (
                            order_id, product_id, quantity, unit_price, total_price,
                            vendor_id, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                    ''', (order_id, item['product_id'], item['quantity'],
                         item['price'], item['item_total'], vendor_id))
                    
                    # Update product stock
                    cursor.execute('''
                        UPDATE products
                        SET stock = stock - ?, sales_count = sales_count + ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (item['quantity'], item['quantity'], item['product_id']))
            
            # Update user stats
            cursor.execute('''
                UPDATE users
                SET total_orders = total_orders + 1,
                    total_spent = total_spent + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (total, session['user_id']))
            
            db.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            # Send order confirmation (in production)
            try:
                send_order_confirmation_email(session['email'], order_number, total)
            except:
                pass
            
            flash(f'Order #{order_number} placed successfully!', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
            
        except Exception as e:
            db.rollback()
            print(f"Checkout error: {e}")
            flash(f'Error placing order: {str(e)}', 'danger')
    
    # GET request - show checkout form
    # Get user address if exists
    cursor.execute('SELECT address FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    default_address = user['address'] if user and user['address'] else ''
    
    return render_template('checkout.html',
                         cart_products=cart_products,
                         total=round(total, 3),
                         vendors=vendors,
                         default_address=default_address)

def send_order_confirmation_email(email, order_number, total):
    """Send order confirmation email"""
    # Placeholder for email sending
    print(f"Order confirmation sent to {email} for order #{order_number}")
    return True

@app.route('/orders')
@login_required
def orders():
    """User orders list"""
    user_id = session['user_id']
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT o.*, COUNT(oi.id) as items_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''', (user_id,))
    orders_list = cursor.fetchall()
    
    return render_template('orders.html', orders=orders_list)

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """User order detail"""
    user_id = session['user_id']
    
    db = get_db()
    cursor = db.cursor()
    
    # Verify order ownership
    cursor.execute('SELECT * FROM orders WHERE id = ? AND user_id = ?', (order_id, user_id))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    
    # Get order items
    cursor.execute('''
        SELECT oi.*, p.name_en, p.name_ar, p.main_image,
               v.shop_name, v.vendor_code
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items = cursor.fetchall()
    
    # Get order history
    cursor.execute('''
        SELECT * FROM order_history
        WHERE order_id = ?
        ORDER BY created_at DESC
    ''', (order_id,))
    history = cursor.fetchall()
    
    return render_template('order_detail.html',
                         order=order,
                         items=items,
                         history=history)
# ============ API ROUTES ============

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """API: Add product to cart"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity < 1:
            return jsonify({
                'success': False,
                'message': 'Invalid product ID or quantity'
            })
        
        db = get_db()
        cursor = db.cursor()
        
        # Check product availability
        cursor.execute('''
            SELECT stock, status FROM products
            WHERE id = ? AND status = 'active'
        ''', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not available'
            })
        
        if product['stock'] < quantity:
            return jsonify({
                'success': False,
                'message': f'Only {product["stock"]} items available'
            })
        
        # Add to cart session
        cart = session.get('cart', [])
        
        # Check if product already in cart
        found = False
        for item in cart:
            if item['product_id'] == product_id:
                new_quantity = item['quantity'] + quantity
                if new_quantity > product['stock']:
                    return jsonify({
                        'success': False,
                        'message': f'Cannot add more than {product["stock"]} items'
                    })
                item['quantity'] = new_quantity
                found = True
                break
        
        if not found:
            cart.append({
                'product_id': product_id,
                'quantity': quantity
            })
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/cart/update', methods=['POST'])
@login_required
def api_update_cart():
    """API: Update cart item"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 0))
        
        cart = session.get('cart', [])
        
        if quantity <= 0:
            # Remove item
            cart = [item for item in cart if item['product_id'] != product_id]
            message = 'Item removed from cart'
        else:
            # Check stock
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            
            if product and quantity > product['stock']:
                return jsonify({
                    'success': False,
                    'message': f'Only {product["stock"]} items available'
                })
            
            # Update quantity
            found = False
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] = quantity
                    found = True
                    break
            
            if not found:
                return jsonify({
                    'success': False,
                    'message': 'Product not in cart'
                })
            
            message = 'Cart updated'
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': message,
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(product_id):
    """API: Remove item from cart"""
    try:
        cart = session.get('cart', [])
        cart = [item for item in cart if item['product_id'] != product_id]
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/cart/count')
@login_required
def api_cart_count():
    """API: Get cart item count"""
    cart = session.get('cart', [])
    total_items = sum(item['quantity'] for item in cart)
    
    return jsonify({
        'success': True,
        'count': len(cart),
        'total_items': total_items
    })

@app.route('/api/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def api_add_to_wishlist(product_id):
    """API: Add product to wishlist"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if product exists
        cursor.execute('SELECT id FROM products WHERE id = ? AND status = "active"', (product_id,))
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Product not found'
            })
        
        # Check if already in wishlist
        cursor.execute('''
            SELECT id FROM wishlist
            WHERE user_id = ? AND product_id = ?
        ''', (session['user_id'], product_id))
        
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Already in wishlist'
            })
        
        # Add to wishlist
        cursor.execute('''
            INSERT INTO wishlist (user_id, product_id, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (session['user_id'], product_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added to wishlist'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/products/search')
def api_product_search():
    """API: Search products"""
    search = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if not search or len(search) < 2:
        return jsonify({'success': True, 'products': []})
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name_en, p.name_ar, p.price, p.main_image,
               v.shop_name, p.stock
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        WHERE (p.name_en LIKE ? OR p.name_ar LIKE ? OR p.sku LIKE ?)
        AND p.status = 'active' AND p.visibility = 'public'
        AND v.status = 'verified'
        LIMIT ?
    ''', (f'%{search}%', f'%{search}%', f'%{search}%', limit))
    
    products = []
    for row in cursor.fetchall():
        products.append({
            'id': row['id'],
            'name_en': row['name_en'],
            'name_ar': row['name_ar'],
            'price': row['price'],
            'image': row['main_image'],
            'shop_name': row['shop_name'],
            'stock': row['stock']
        })
    
    return jsonify({
        'success': True,
        'products': products
    })

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@login_required
def api_user_profile():
    """API: Get or update user profile"""
    if request.method == 'GET':
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, phone, address,
                   profile_image, wallet_balance, total_orders, total_spent,
                   created_at
            FROM users 
            WHERE id = ?
        ''', (session['user_id'],))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        user_data = dict(user)
        user_data.pop('password', None)  # Remove password
        
        return jsonify({
            'success': True,
            'user': user_data
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                })
            
            db = get_db()
            cursor = db.cursor()
            
            # Prepare update fields
            update_fields = []
            params = []
            
            allowed_fields = ['full_name', 'phone', 'address']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    params.append(data[field].strip())
            
            # Handle profile image upload
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename:
                    image_path = save_uploaded_file(file, 'profile', 
                                                   f'user_{session["user_id"]}')
                    if image_path:
                        update_fields.append('profile_image = ?')
                        params.append(image_path)
            
            if not update_fields:
                return jsonify({
                    'success': False,
                    'message': 'No valid fields to update'
                })
            
            # Update user
            params.append(session['user_id'])
            query = f'''
                UPDATE users SET {', '.join(update_fields)},
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            db.commit()
            
            # Update session
            if 'full_name' in data:
                session['full_name'] = data['full_name']
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            })

@app.route('/api/orders/track/<order_number>')
@login_required
def api_track_order(order_number):
    """API: Track order status"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT o.*,
               COUNT(oi.id) as items_count,
               GROUP_CONCAT(p.name_en) as product_names
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE o.order_number = ? AND o.user_id = ?
        GROUP BY o.id
    ''', (order_number, session['user_id']))
    
    order = cursor.fetchone()
    
    if not order:
        return jsonify({
            'success': False,
            'message': 'Order not found'
        })
    
    # Get order history
    cursor.execute('''
        SELECT status, notes, created_at
        FROM order_history
        WHERE order_id = ?
        ORDER BY created_at DESC
    ''', (order['id'],))
    
    history = cursor.fetchall()
    
    order_data = {
        'order_number': order['order_number'],
        'status': order['status'],
        'total': order['total_price'],
        'created_at': order['created_at'],
        'estimated_delivery': order['estimated_delivery'],
        'shipping_address': order['shipping_address'],
        'items_count': order['items_count'],
        'product_names': order['product_names'],
        'history': [dict(h) for h in history]
    }
    
    return jsonify({
        'success': True,
        'order': order_data
    })

@app.route('/api/vendor/products/stats')
@vendor_required
def api_vendor_product_stats():
    """API: Vendor product statistics"""
    vendor_id = session.get('vendor_id')
    
    db = get_db()
    cursor = db.cursor()
    
    # Product counts by status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM products
        WHERE vendor_id = ?
        GROUP BY status
    ''', (vendor_id,))
    
    status_counts = {}
    for row in cursor.fetchall():
        status_counts[row['status']] = row['count']
    
    # Low stock products
    cursor.execute('''
        SELECT COUNT(*) as low_stock_count
        FROM products
        WHERE vendor_id = ? AND stock <= low_stock_alert
    ''', (vendor_id,))
    
    low_stock = cursor.fetchone()['low_stock_count']
    
    # Top selling products
    cursor.execute('''
        SELECT p.id, p.name_en, p.name_ar,
               COALESCE(SUM(oi.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        WHERE p.vendor_id = ?
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5
    ''', (vendor_id,))
    
    top_products = cursor.fetchall()
    
    return jsonify({
        'success': True,
        'stats': {
            'status_counts': status_counts,
            'low_stock': low_stock,
            'top_products': [dict(p) for p in top_products]
        }
    })

@app.route('/api/admin/dashboard/stats')
@admin_required
def api_admin_dashboard_stats():
    """API: Admin dashboard statistics"""
    db = get_db()
    cursor = db.cursor()
    
    # Today's stats
    cursor.execute('''
        SELECT
            COUNT(*) as today_orders,
            SUM(CASE WHEN status = 'completed' THEN total_price ELSE 0 END) as today_revenue,
            COUNT(DISTINCT user_id) as today_customers
        FROM orders
        WHERE DATE(created_at) = DATE('now')
    ''')
    
    today_stats = cursor.fetchone()
    
    # Weekly stats
    cursor.execute('''
        SELECT
            DATE(created_at) as date,
            COUNT(*) as orders,
            SUM(CASE WHEN status = 'completed' THEN total_price ELSE 0 END) as revenue
        FROM orders
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''')
    
    weekly_data = cursor.fetchall()
    
    # Product stats
    cursor.execute('SELECT COUNT(*) as total_products FROM products')
    total_products = cursor.fetchone()['total_products']
    
    cursor.execute('SELECT COUNT(*) as low_stock FROM products WHERE stock <= low_stock_alert')
    low_stock = cursor.fetchone()['low_stock']
    
    # Vendor stats
    cursor.execute('SELECT COUNT(*) as total_vendors FROM vendors')
    total_vendors = cursor.fetchone()['total_vendors']
    
    cursor.execute('SELECT COUNT(*) as pending_vendors FROM vendors WHERE status = "pending"')
    pending_vendors = cursor.fetchone()['pending_vendors']
    
    # User stats
    cursor.execute('SELECT COUNT(*) as total_users FROM users')
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute('SELECT COUNT(*) as new_users_today FROM users WHERE DATE(created_at) = DATE("now")')
    new_users_today = cursor.fetchone()['new_users_today']
    
    stats = {
        'today': {
            'orders': today_stats['today_orders'] or 0,
            'revenue': round(today_stats['today_revenue'] or 0, 3),
            'customers': today_stats['today_customers'] or 0
        },
        'weekly': {
            'dates': [row['date'] for row in weekly_data],
            'orders': [row['orders'] for row in weekly_data],
            'revenue': [row['revenue'] or 0 for row in weekly_data]
        },
        'products': {
            'total': total_products,
            'low_stock': low_stock
        },
        'vendors': {
            'total': total_vendors,
            'pending': pending_vendors
        },
        'users': {
            'total': total_users,
            'new_today': new_users_today
        }
    }
    
    return jsonify({
        'success': True,
        'stats': stats
    })
# ============ REFERRAL SYSTEM FUNCTIONS ============

def process_referral_signup(new_user_id, referral_code):
    """Process referral when new user signs up"""
    if not referral_code:
        return False
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Find referrer
        cursor.execute("SELECT id FROM users WHERE referral_code = ?", (referral_code,))
        referrer = cursor.fetchone()
        
        if not referrer:
            return False
        
        referrer_id = referrer['id']
        
        # 1. Add to referrals table
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, level, commission_rate)
            VALUES (?, ?, 1, ?)
        ''', (referrer_id, new_user_id, REFERRAL_RATE))
        
        # 2. Update referrer's counts
        cursor.execute('''
            UPDATE users
            SET direct_referrals = direct_referrals + 1
            WHERE id = ?
        ''', (referrer_id,))
        
        # 3. Update new user's referred_by field
        cursor.execute("UPDATE users SET referred_by = ? WHERE id = ?",
                      (referral_code, new_user_id))
        
        # 4. Add signup bonus (Optional: 5.0 KD)
        signup_bonus = 5.0
        add_commission(referrer_id, signup_bonus, 'signup_bonus',
                      referred_user_id=new_user_id,
                      description=f"Signup bonus for new referral")
        
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
            SET indirect_referrals = indirect_referrals + 1
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
                SET indirect_referrals = indirect_referrals + 1
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
    
    # Update user wallet for referral commissions
    if commission_type == 'referral':
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
    
    # Commission stats
    cursor.execute('''
        SELECT
            SUM(amount) as total_earned,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_amount,
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_amount
        FROM commissions
        WHERE user_id = ? AND type = 'referral'
    ''', (user_id,))
    
    commission_stats = cursor.fetchone()
    
    return {
        'referrals': dict(main_stats) if main_stats else {},
        'commissions': dict(commission_stats) if commission_stats else {},
        'referral_rate': REFERRAL_RATE
    }

# ============ UTILITY FUNCTIONS ============

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = random.randint(1000, 9999)
    return f'SOQ-{timestamp}-{random_part}'

def calculate_order_totals(order_id):
    """Calculate order totals including taxes and shipping"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            SUM(oi.total_price) as subtotal,
            COUNT(oi.id) as items_count
        FROM order_items oi
        WHERE oi.order_id = ?
    ''', (order_id,))
    
    result = cursor.fetchone()
    subtotal = result['subtotal'] or 0
    
    # Calculate tax (5% VAT)
    tax_rate = 0.05  # 5% VAT
    tax_amount = subtotal * tax_rate
    
    # Shipping cost (free over 50 KD)
    shipping_cost = 0 if subtotal >= 50 else 5.0
    
    total = subtotal + tax_amount + shipping_cost
    
    return {
        'subtotal': round(subtotal, 3),
        'tax_amount': round(tax_amount, 3),
        'shipping_cost': shipping_cost,
        'total': round(total, 3),
        'items_count': result['items_count']
    }

def check_stock_availability(product_id, quantity):
    """Check if product has sufficient stock"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT stock, allow_backorders
        FROM products
        WHERE id = ? AND status = 'active'
    ''', (product_id,))
    
    product = cursor.fetchone()
    
    if not product:
        return False, 'Product not found'
    
    if product['allow_backorders']:
        return True, 'Available (backorder allowed)'
    
    if product['stock'] >= quantity:
        return True, 'Available'
    else:
        return False, f'Only {product["stock"]} items in stock'

def send_notification(user_id, title, message, notification_type='info'):
    """Send notification to user"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO notifications (
            user_id, title, message, type, is_read, created_at
        ) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
    ''', (user_id, title, message, notification_type))
    
    db.commit()
    return True

def get_user_notifications(user_id, limit=10):
    """Get user notifications"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    return cursor.fetchall()

def mark_notification_read(notification_id):
    """Mark notification as read"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        UPDATE notifications
        SET is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (notification_id,))
    
    db.commit()
    return True

# ============ SCHEDULED TASKS ============

def check_expired_carts():
    """Remove expired cart items (older than 7 days)"""
    # This would be called by a scheduler in production
    pass

def send_stock_alerts():
    """Send low stock alerts to vendors"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT p.*, v.email, v.shop_name
        FROM products p
        JOIN vendors v ON p.vendor_id = v.id
        WHERE p.stock <= p.low_stock_alert
        AND p.status = 'active'
        AND v.status = 'verified'
    ''')
    
    low_stock_products = cursor.fetchall()
    
    for product in low_stock_products:
        # Send email alert (implement in production)
        print(f"Low stock alert for {product['name_en']} in {product['shop_name']}")
    
    return len(low_stock_products)

def process_pending_withdrawals():
    """Process pending withdrawals (auto-approve after 24 hours)"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT w.*, v.email, v.shop_name
        FROM withdrawals w
        JOIN vendors v ON w.vendor_id = v.id
        WHERE w.status = 'pending'
        AND w.requested_at <= DATETIME('now', '-1 day')
    ''')
    
    pending_withdrawals = cursor.fetchall()
    
    for withdrawal in pending_withdrawals:
        # Auto-approve and mark as processing
        cursor.execute('''
            UPDATE withdrawals
            SET status = 'processing',
                processed_at = CURRENT_TIMESTAMP,
                notes = CONCAT(notes, ' - Auto-approved after 24 hours')
            WHERE id = ?
        ''', (withdrawal['id'],))
        
        # Send notification
        send_notification(
            withdrawal['vendor_id'],
            'Withdrawal Processing',
            f'Your withdrawal of {withdrawal["amount"]} KD is being processed.',
            'success'
        )
    
    db.commit()
    return len(pending_withdrawals)
# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found_error(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    db = get_db()
    db.rollback()  # Rollback any database transaction
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """403 error handler"""
    return render_template('errors/403.html'), 403

# ============ COMMAND LINE COMMANDS ============

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database"""
    init_database()
    print('✅ Database initialized successfully!')

@app.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin_command(username, email, password):
    """Create admin user"""
    db = get_db_connection()
    cursor = db.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = ? AND role = 'admin'", (username,))
    if cursor.fetchone():
        print(f'⚠️  Admin user {username} already exists!')
        db.close()
        return
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create admin user
    cursor.execute('''
        INSERT INTO users (username, email, password, full_name, role, is_active, email_verified)
        VALUES (?, ?, ?, ?, 'admin', 1, 1)
    ''', (username, email, hashed_password, username))
    
    db.commit()
    db.close()
    
    print(f'✅ Admin user {username} created successfully!')
    print(f'📧 Email: {email}')
    print(f'🔑 Password: {password}')

@app.cli.command('reset-password')
@click.argument('email')
@click.argument('new_password')
def reset_password_command(email, new_password):
    """Reset user password"""
    db = get_db_connection()
    cursor = db.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f'❌ User with email {email} not found!')
        db.close()
        return
    
    # Hash new password
    hashed_password = hash_password(new_password)
    
    # Update password
    cursor.execute('''
        UPDATE users
        SET password = ?, updated_at = CURRENT_TIMESTAMP
        WHERE email = ?
    ''', (hashed_password, email))
    
    db.commit()
    db.close()
    
    print(f'✅ Password reset successfully for {email}!')

@app.cli.command('vendor-stats')
def vendor_stats_command():
    """Display vendor statistics"""
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT
            COUNT(*) as total_vendors,
            SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified_vendors,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_vendors,
            SUM(CASE WHEN status = 'suspended' THEN 1 ELSE 0 END) as suspended_vendors,
            SUM(balance) as total_balance,
            SUM(total_earnings) as total_earnings
        FROM vendors
    ''')
    
    stats = cursor.fetchone()
    
    print("="*50)
    print("📊 VENDOR STATISTICS")
    print("="*50)
    print(f"Total Vendors: {stats['total_vendors']}")
    print(f"Verified Vendors: {stats['verified_vendors']}")
    print(f"Pending Vendors: {stats['pending_vendors']}")
    print(f"Suspended Vendors: {stats['suspended_vendors']}")
    print(f"Total Balance: {stats['total_balance'] or 0:.3f} KD")
    print(f"Total Earnings: {stats['total_earnings'] or 0:.3f} KD")
    print("="*50)
    
    db.close()

@app.cli.command('cleanup-temp-files')
def cleanup_temp_files_command():
    """Cleanup temporary files"""
    import shutil
    import os
    
    temp_dir = os.path.join(app.config['UPLOAD_BASE'], 'temp')
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        print(f"✅ Cleaned up temporary files in {temp_dir}")
    else:
        print("ℹ️  No temporary directory found")

@app.cli.command('list-routes')
def list_routes_command():
    """List all available routes"""
    print("="*60)
    print("🌐 AVAILABLE ROUTES")
    print("="*60)
    
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        routes.append((rule.endpoint, methods, str(rule)))
    
    routes.sort(key=lambda x: x[0])
    
    for endpoint, methods, rule in routes:
        print(f"{endpoint:30} {methods:15} {rule}")
    
    print("="*60)
    print(f"Total routes: {len(routes)}")

# ============ HEALTH CHECK ============

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1')
        
        # Test file system
        upload_dirs = ['products/images', 'products/videos', 'documents', 'kyc/civil_id', 'banners', 'profile']
        for dir_name in upload_dirs:
            dir_path = os.path.join(UPLOAD_BASE, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'filesystem': 'ok',
            'upload_dirs': upload_dirs
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/version')
def version_info():
    """Version information"""
    return jsonify({
        'name': 'SooqKabeer',
        'version': '2.0.0',
        'description': 'Complete E-commerce Platform',
        'features': [
            'Multi-vendor marketplace',
            'Arabic/English support',
            'Referral system with MLM',
            'Commission tracking',
            'Order management',
            'File upload system',
            'Admin dashboard',
            'Vendor dashboard',
            'User profiles'
        ],
        'branding': {
            'primary_color': '#0a192f',
            'secondary_color': '#d4af37',
            'accent_color': '#28a745'
        }
    })

# ============ DATABASE REPAIR FUNCTION ============

def repair_database():
    """Repair database by adding missing columns"""
    print("🔧 REPAIRING DATABASE...")
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print("❌ Products table not found!")
            return
        
        # Add missing columns to products table
        missing_columns = [
            ('visibility', 'TEXT DEFAULT "public"'),
            ('video_url', 'TEXT'),
            ('document_url', 'TEXT'),
            ('b2b_price', 'REAL'),
            ('cost_price', 'REAL'),
            ('low_stock_alert', 'INTEGER DEFAULT 10'),
            ('weight', 'REAL'),
            ('product_code', 'TEXT'),
            ('shipping_cost', 'REAL DEFAULT 0'),
            ('delivery_days', 'INTEGER DEFAULT 3'),
            ('allow_backorders', 'BOOLEAN DEFAULT 0'),
            ('rating', 'REAL DEFAULT 0'),
            ('total_reviews', 'INTEGER DEFAULT 0'),
            ('admin_notes', 'TEXT')
        ]
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(products)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        added_count = 0
        for col_name, col_type in missing_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                    added_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to add {col_name}: {e}")
        
        # Add missing columns to vendors table
        vendor_columns = [
            ('video_link', 'TEXT'),
            ('banner_image', 'TEXT'),
            ('total_earnings', 'REAL DEFAULT 0'),
            ('kyc_status', 'TEXT DEFAULT "pending"')
        ]
        
        cursor.execute("PRAGMA table_info(vendors)")
        existing_vendor_columns = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in vendor_columns:
            if col_name not in existing_vendor_columns:
                try:
                    cursor.execute(f"ALTER TABLE vendors ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added vendor column: {col_name}")
                    added_count += 1
                except Exception as e:
                    print(f"⚠️  Failed to add vendor column {col_name}: {e}")
        
        db.commit()
        print(f"🎉 Database repair complete! Added {added_count} columns.")
        
    except Exception as e:
        print(f"❌ Database repair failed: {e}")
        db.rollback()
    finally:
        db.close()

# ============ DATABASE FIX COMMAND ============

@app.cli.command('fix-db')
def fix_database_command():
    """Fix database structure"""
    repair_database()

# ============ DEBUG TEMPLATE PATHS ============

@app.route('/debug/templates')
def debug_templates():
    """Debug template paths"""
    import os
    
    template_paths = []
    
    # Check all template locations
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), 'templates')
                template_paths.append(rel_path)
    
    # Check vendor templates specifically
    vendor_templates = []
    vendor_path = os.path.join('templates', 'vendor')
    if os.path.exists(vendor_path):
        for f in os.listdir(vendor_path):
            if f.endswith('.html'):
                vendor_templates.append(f)
    
    return jsonify({
        'base_dir': os.path.dirname(os.path.abspath(__file__)),
        'template_dir': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
        'vendor_dir': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'vendor'),
        'vendor_exists': os.path.exists(vendor_path),
        'all_templates': template_paths,
        'vendor_templates': vendor_templates,
        'vendor_dashboard_exists': 'vendor/dashboard.html' in template_paths,
        'vendor_base_exists': 'vendor/base.html' in template_paths
    })

# ============ LOGIN TEST UTILITIES ============

@app.cli.command('test-login')
@click.argument('email')
@click.argument('password')
def test_login_command(email, password):
    """Test login with any user"""
    db = get_db_connection()
    cursor = db.cursor()
    
    print(f"🔍 Testing login for: {email}")
    print("="*50)
    
    # Check in users table
    cursor.execute('''
        SELECT id, email, password, role, is_active
        FROM users WHERE email = ?
    ''', (email,))
    user = cursor.fetchone()
    
    if user:
        print(f"✅ Found in users table:")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Role: {user['role']}")
        print(f"   Password hash: {user['password'][:30]}...")
        
        # Test password
        if check_password(user['password'], password):
            print(f"🔑 Password: CORRECT")
        else:
            print(f"🔑 Password: INCORRECT")
            print(f"   Try using: 'admin123' for admin users")
    
    # Check in vendors table
    cursor.execute('''
        SELECT id, email, password, status, vendor_code
        FROM vendors WHERE email = ?
    ''', (email,))
    vendor = cursor.fetchone()
    
    if vendor:
        print(f"\n✅ Found in vendors table:")
        print(f"   ID: {vendor['id']}")
        print(f"   Email: {vendor['email']}")
        print(f"   Status: {vendor['status']}")
        print(f"   Vendor Code: {vendor['vendor_code']}")
        print(f"   Password hash: {vendor['password'][:30]}...")
        
        # Test password
        if check_password(vendor['password'], password):
            print(f"🔑 Password: CORRECT")
        else:
            print(f"🔑 Password: INCORRECT")
    
    if not user and not vendor:
        print(f"❌ User not found in database")
    
    db.close()
    print("="*50)

@app.cli.command('fix-admin-password')
@click.argument('email')
def fix_admin_password_command(email):
    """Fix admin password to default 'admin123'"""
    db = get_db_connection()
    cursor = db.cursor()
    
    # Hash the default password
    hashed_password = hash_password('admin123')
    
    # Update password in users table
    cursor.execute('''
        UPDATE users
        SET password = ?, updated_at = CURRENT_TIMESTAMP
        WHERE email = ?
    ''', (hashed_password, email))
    
    # Also update in vendors table if exists
    cursor.execute('''
        UPDATE vendors
        SET password = ?, updated_at = CURRENT_TIMESTAMP
        WHERE email = ?
    ''', (hashed_password, email))
    
    db.commit()
    db.close()
    
    print(f"✅ Password reset to 'admin123' for {email}")
    print(f"🔑 New hash: {hashed_password[:30]}...")
# ============ MAIN EXECUTION ============

if __name__ == '__main__':
    print("="*60)
    print("🚀 SOOQ KABEER - COMPLETE E-COMMERCE PLATFORM")
    print("="*60)
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"📁 Uploads: {UPLOAD_BASE}")
    print(f"🎨 Branding: Navy (#0a192f) + Gold (#d4af37)")
    print(f"🌐 Languages: Arabic, English")
    print("="*60)
    
    # Check and repair database first
    repair_database()
    
    # Initialize database (will skip existing tables)
    init_database()
    
    # Check for required directories
    create_upload_directories()
    
    print("✅ Database checked and repaired")
    print("✅ Upload directories created")
    print("="*60)
    print("✅ Database initialized")
    print("✅ Upload directories created")
    print("="*60)
    print("🔑 Default Admin: admin / admin123")
    print("💰 Commission Rate: 10%")
    print("🤝 Referral Rate: 5%")
    print("💵 Min Withdrawal: 10 KD")
    print("="*60)
    print("🌐 Server starting on: http://localhost:8000")
    print("📱 API Documentation: http://localhost:8000/version")
    print("🩺 Health Check: http://localhost:8000/health")
    print("="*60)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        threaded=True
    )
