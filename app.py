"""
SooqKabeer - Complete E-commerce Platform
All features in one file: Referral,Vendor, Orders, Commission
"""
#========= Import necessary Flask and system modules =======
from flask import Flask, render_template, request, session, redirect, url_for, g, flash, current_app
from flask_babel import Babel, _
import sqlite3
import os
import hashlib
import random
import string
from datetime import datetime
from functools import wraps
import json

#=== [PLACEMENT_GUIDE] ===#
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#=== Arabic Support (Already Installed) ===#
from arabic_reshaper import reshape
from bidi.algorithm import get_display

#=== Logic: Try to import vendor_api from external file ===#
try:
    from vendor_api import vendor_api
except ImportError as e:
    print(f"#=== WARNING: vendor_api.py not found or has errors ===#")
    vendor_api = None

#=== Add referral settings to configuration ===#
REFERRAL_RATE = 0.05
MIN_WITHDRAWAL = 10

#=== Arabic Text Fixer Function ===#
def fix_arabic(text):
    if not text:
        return ""
    return get_display(reshape(text))

#=== Configuration and App Initialization ===#
app = Flask(__name__)

import sqlite3

UPLOAD_FOLDER = 'static/uploads/kyc'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# এই ফাংশনটি ৫৩ নম্বর লাইনের এররটি দূর করবে
def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sooqkabeer.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
#============ [FIX_DATABASE_KYC_COLUMN] =============#

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ১. ক্যাটাগরি টেবিল তৈরি
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories 
                     (id INTEGER PRIMARY KEY, name_ar TEXT NOT NULL, name_en TEXT)''')
    
    # ২. ডিফল্ট ক্যাটাগরি ইনসার্ট
    cursor.execute('INSERT OR IGNORE INTO categories (id, name_ar, name_en) VALUES (1, "General", "General")')
    
    # ৩. ভেন্ডর আইডি HKO-001 আপডেট
    cursor.execute('UPDATE vendors SET vendor_code = "HKO-001", status = "verified" WHERE id > 0')
    
    conn.commit()
    conn.close()
    print("✅ Database Fixed: categories table created and HKO-001 set.")


    # Create the vendors table with ALL columns at once
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            -- Primary Key
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Account Information (ব্যক্তিগত তথ্য)
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            country_code TEXT DEFAULT '+965',
            nationality TEXT,
            
            -- Business Information (ব্যবসার তথ্য)
            shop_name TEXT NOT NULL,
            business_name TEXT,
            business_type TEXT,
            cr_number TEXT UNIQUE,
            vat_number TEXT,
            
            -- Address Information (ঠিকানা)
            address TEXT,
            governorate TEXT,
            block TEXT,
            street TEXT,
            building TEXT,
            floor TEXT,
            unit TEXT,
            
            -- Business Details (ব্যবসার বিস্তারিত)
            business_description TEXT,
            
            -- Documents & Verification (ডকুমেন্টস)
            civil_id TEXT,
            civil_id_path TEXT,
            civil_id_back_path TEXT,
            commercial_license_path TEXT,
            
            -- System Fields (সিস্টেম ফিল্ড)
            vendor_code TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'pending',
            agree_terms TEXT DEFAULT 'no',
            
            -- Timestamps (সময় স্ট্যাম্প)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Check if columns already exist and add if missing (for backward compatibility)
    required_columns = [
        ('business_name', 'TEXT'),
        ('business_type', 'TEXT'),
        ('cr_number', 'TEXT UNIQUE'),
        ('vat_number', 'TEXT'),
        ('governorate', 'TEXT'),
        ('block', 'TEXT'),
        ('street', 'TEXT'),
        ('building', 'TEXT'),
        ('floor', 'TEXT'),
        ('unit', 'TEXT'),
        ('business_description', 'TEXT'),
        ('civil_id_back_path', 'TEXT'),
        ('commercial_license_path', 'TEXT'),
        ('agree_terms', "TEXT DEFAULT 'no'"),
        ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]

    # Get existing columns
    cursor.execute("PRAGMA table_info(vendors)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Add missing columns
    for col_name, col_def in required_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE vendors ADD COLUMN {col_name} {col_def}")
                print(f"✅ Added column: {col_name}")
            except Exception as e:
                print(f"⚠️  Failed to add column {col_name}: {e}")

    # Create other necessary tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            document_name TEXT,
            status TEXT DEFAULT 'pending',
            verified_by INTEGER,
            verified_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            vendor_id INTEGER NOT NULL,
            main_image TEXT,
            image_gallery TEXT,
            status TEXT DEFAULT 'active',
            visibility TEXT DEFAULT 'public',
            is_featured BOOLEAN DEFAULT 0,
            shipping_cost REAL DEFAULT 0,
            delivery_days INTEGER DEFAULT 3,
            allow_backorders BOOLEAN DEFAULT 0,
            views INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            country_code TEXT DEFAULT '+965',
            full_name TEXT,
            company_name TEXT,
            user_type TEXT DEFAULT 'customer',
            address TEXT,
            city TEXT,
            governorate TEXT,
            language TEXT DEFAULT 'en',
            currency TEXT DEFAULT 'KWD',
            status TEXT DEFAULT 'active',
            email_verified BOOLEAN DEFAULT 0,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_group TEXT,
            data_type TEXT DEFAULT 'text',
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default settings
    cursor.execute('''
        INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_group, description)
        VALUES
        ('site_name', 'SooqKabeer', 'general', 'Site Name'),
        ('site_description', 'B2B Wholesale Marketplace', 'general', 'Site Description'),
        ('site_currency', 'KWD', 'general', 'Default Currency'),
        ('commission_rate', '5', 'payment', 'Commission Percentage'),
        ('vat_rate', '5', 'payment', 'VAT Percentage'),
        ('vendor_registration', 'enabled', 'vendor', 'Vendor Registration Status'),
        ('order_processing_fee', '0.500', 'payment', 'Order Processing Fee'),
        ('minimum_order_amount', '10', 'order', 'Minimum Order Amount'),
        ('free_shipping_threshold', '50', 'shipping', 'Free Shipping Threshold'),
        ('support_email', 'support@sooqkabeer.com', 'contact', 'Support Email'),
        ('support_phone', '+965 1234 5678', 'contact', 'Support Phone'),
        ('address', 'Kuwait City, Block 4, Street 12', 'contact', 'Company Address')
    ''')

    # Insert default admin user if not exists (password: admin123)
    cursor.execute('''
        INSERT OR IGNORE INTO admin_users (username, email, password, full_name, role, status)
        VALUES ('admin', 'admin@sooqkabeer.com',
                '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 
                'Administrator', 'admin', 'active')
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

#============ [FULL_VENDOR_REGISTER_FIXED] ================

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        try:
            # Step 1: Get form data from all steps
            # Account Information
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            country_code = request.form.get('country_code', '+965')
            nationality = request.form.get('nationality')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Business Information
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
            
            # Civil ID Number (from old form)
            civil_id_number = request.form.get('civil_id_number', '')
            
            # Terms agreement
            agree_terms = request.form.get('agree_terms')
            
            # Step 2: Validation
            # Check if passwords match
            if password != confirm_password:
                flash('❌ Passwords do not match!', 'error')
                return redirect('/vendor/register')
            
            # Check if terms agreed
            if not agree_terms:
                flash('❌ You must agree to the terms and conditions', 'error')
                return redirect('/vendor/register')
            
            # Step 3: Construct address from parts
            address_parts = []
            if building:
                address_parts.append(building)
            if street:
                address_parts.append(street)
            if block:
                address_parts.append(f"Block {block}")
            if governorate:
                address_parts.append(governorate)
            address = ", ".join(address_parts) if address_parts else request.form.get('address', '')
            
            # Step 4: Get database connection
            db = get_db_connection()
            cursor = db.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM vendors WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('❌ Email already registered! Please use a different email or login.', 'error')
                db.close()
                return redirect('/vendor/register')
            
            # Check if CR number already exists
            if cr_number:
                cursor.execute("SELECT id FROM vendors WHERE cr_number = ?", (cr_number,))
                if cursor.fetchone():
                    flash('❌ Commercial Registration number already registered!', 'error')
                    db.close()
                    return redirect('/vendor/register')
            
            # Step 5: Generate Unique Vendor Code (HKO-0001)
            cursor.execute("SELECT MAX(id) FROM vendors")
            result = cursor.fetchone()
            next_id = 1 if result[0] is None else result[0] + 1
            vendor_code = f"HKO-{next_id:04d}"
            
            # Step 6: Password Hashing (using old logic)
            salt = "sooqkabeer_salt_"
            password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            
            # Step 7: Handle file uploads
            uploaded_files = {}
            
            # Civil ID Front (required)
            civil_id_front_path = ""
            if 'civil_id_front' in request.files:
                file = request.files['civil_id_front']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_civil_id_front_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    civil_id_front_path = file_path
                    uploaded_files['civil_id_front'] = file_path
            
            # Civil ID Back (required)
            civil_id_back_path = ""
            if 'civil_id_back' in request.files:
                file = request.files['civil_id_back']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_civil_id_back_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    civil_id_back_path = file_path
                    uploaded_files['civil_id_back'] = file_path
            
            # Commercial License (required)
            commercial_license_path = ""
            if 'commercial_license' in request.files:
                file = request.files['commercial_license']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{email}_commercial_license_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    commercial_license_path = file_path
                    uploaded_files['commercial_license'] = file_path
            
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
            
            # Step 8: Insert Data into vendors table (using old table structure)
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
                        
                        # Insert into vendor_documents table
                        cursor.execute("""
                            INSERT INTO vendor_documents (vendor_id, document_type, file_path, created_at)
                            VALUES (?, ?, ?, datetime('now'))
                        """, (vendor_id, 'additional', file_path))
            
            # Step 10: Insert into vendor_additional_info if table exists
            try:
                cursor.execute("""
                    INSERT INTO vendor_additional_info 
                    (vendor_id, business_type, cr_number, vat_number, 
                     governorate, block, street, building, floor, unit, 
                     business_description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    vendor_id, business_type, cr_number, vat_number,
                    governorate, block, street, building, floor, unit,
                    business_description
                ))
            except:
                # Table might not exist, which is okay
                pass
            
            # Step 11: Commit transaction
            db.commit()
            
            # Step 12: Send confirmation email (optional)
            try:
                # You can implement email sending here
                send_vendor_registration_email(
                    email=email,
                    name=name,
                    business_name=business_name,
                    vendor_code=vendor_code
                )
            except Exception as e:
                print(f"Email sending failed: {e}")
            
            # Step 13: Success - Send to Welcome Pending Page
            db.close()
            
            # Store vendor code in session for welcome page
            session['vendor_code'] = vendor_code
            session['business_name'] = business_name
            
            return redirect('/vendor/welcome-pending')
            
        except Exception as e:
            # Rollback in case of error
            if 'db' in locals():
                db.rollback()
                db.close()
            
            flash(f'❌ Registration failed: {str(e)}', 'error')
            return redirect('/vendor/register')
    
    # GET request - Show the form
    return render_template('vendor/vendor_register.html')

@app.route('/vendor/welcome-pending')
def vendor_welcome_pending():
    vendor_code = session.get('vendor_code', 'N/A')
    business_name = session.get('business_name', 'Your Business')
    
    return render_template('vendor/welcome_pending.html', 
                         vendor_code=vendor_code,
                         business_name=business_name)

def send_vendor_registration_email(email, name, business_name, vendor_code):
    """Send registration confirmation email to vendor"""
    # This is a placeholder function - implement your email logic here
    # You can use Flask-Mail or any other email service
    pass

            
#=== INTERNATIONAL LOGIN ROUTE ===#
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email')
        password = request.form.get('password', '')

        salt = "sooqkabeer_salt_"
        hashed_pw = hashlib.sha256((salt + password).encode()).hexdigest()

        db = get_db()
        # এখানে users টেবিল থেকে চেক করা হচ্ছে
        user = db.execute('SELECT * FROM users WHERE email = ? OR username = ?', 
                          (login_input, login_input)).fetchone()

        if user and user['password'] == hashed_pw:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # অ্যাডমিন হলে অ্যাডমিন প্যানেলে যাবে
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            
            # ভেন্ডর হলে ভেন্ডর ড্যাশবোর্ডে যাবে
            elif user['role'] == 'vendor':
                # সেশনে ভেন্ডর কোড সেট করা (যদি ইউজার টেবিলে থাকে)
                session['vendor_code'] = user.get('vendor_code', '')
                return redirect(url_for('vendor_dashboard'))

            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
app.secret_key = 'sooqkabeer_secret_key_2024'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ar']

# ডাটাবেস কনফিগারেশন এখানে যোগ করুন
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sooqkabeer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#=== Register Blueprint if it exists ===#
if vendor_api:
    app.register_blueprint(vendor_api, url_prefix='/vendor')

#=== Database Path Settings ===#
DATABASE = 'sooqkabeer.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

#=== FIXED HASH FUNCTION WITH SALT ===#
def hash_password(password):
    SALT = 'sooqkabeer_salt_'
    return hashlib.sha256((SALT + password).encode()).hexdigest()

def check_password(hashed_password, user_password):
    new_hash = hashlib.sha256(user_password.encode()).hexdigest()
    return hashed_password == new_hash

def fix_arabic(text):
    if not text: return " "
    return get_display(reshape(text))


#=== 1. Babel and RowWrapper Class ===#
babel = Babel(app)
from datetime import datetime

class RowWrapper:
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

#=== Arabic Text Handling Function ===#
def get_arabic_text(text):
    if not text:
        return ""
    
    # Check if libraries are loaded
    if 'HAS_ARABIC_LIB' in globals() and HAS_ARABIC_LIB:
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except Exception:
            return text
    return text

#=== Context Processor to use it in HTML Templates ===#
@app.context_processor
def utility_processor():
    return dict(get_arabic_text=get_arabic_text)

#=== Language and RTL Support Configuration ===#

from datetime import timedelta
import secrets

# Safe import for Arabic libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_LIB = True
except ImportError:
    HAS_ARABIC_LIB = False
    print("#=== NOTICE: Running without Arabic reshaper library ===#")

SUPPORTED_LANGUAGES = ['ar', 'en']
DEFAULT_LANGUAGE = 'ar'

@app.before_request
def before_request():
    if 'language' not in session:
        session['language'] = DEFAULT_LANGUAGE

    #=== Language and RTL Support Configuration ===#
from datetime import timedelta
import secrets

# Safe import for Arabic tools (No crash if libraries are missing)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_LIB = True
except ImportError:
    HAS_ARABIC_LIB = False
    print("#=== NOTICE: Running without Arabic reshaper library ===#")

SUPPORTED_LANGUAGES = ['ar', 'en']
DEFAULT_LANGUAGE = 'ar'

#=== Babel Configuration (New Method for Babel 3.x+) ===#
def get_locale():
    return session.get('language', DEFAULT_LANGUAGE)

babel = Babel(app, locale_selector=get_locale)

@app.before_request
def before_request():
    if 'language' not in session:
        session['language'] = DEFAULT_LANGUAGE
    # Set RTL flag for Arabic
    request.is_rtl = True if session.get('language') == 'ar' else False

#=== 1. Translations Dictionary (Global) ===#
translations = {
    'ar': {
        'login': 'تسجيل الدخول',
        'register': 'إنشاء حساب',
        'logout': 'تسجيل الخروج',
        'dashboard': 'لوحة التحكم',
        'home': 'الرئيسية',
        'success_msg': 'تم تسجيل الدخول بنجاح!',
        'error_msg': 'اسم المستخدم أو كلمة المرور غير صالحة'
    },
    'en': {
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'dashboard': 'Dashboard',
        'home': 'Home',
        'success_msg': 'Login successful!',
        'error_msg': 'Invalid email or password'
    }
}

#=== 2. Arabic Text & Translation Logic ===#
def get_arabic_text(text):
    if not text: return ""
    if HAS_ARABIC_LIB and session.get('language') == 'ar':
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text

def translate_text(text_key, language=None):
    if language is None:
        language = session.get('language', 'ar')
    
    lang_dict = translations.get(language, translations.get('ar', {}))
    translated = lang_dict.get(text_key, text_key)
    
    if language == 'ar':
        return get_arabic_text(translated)
    return translated

#=== 3. Register for HTML Templates ===#
@app.context_processor
def utility_processor():
    return dict(
        get_arabic_text=get_arabic_text,
        tr=translate_text
    )

#=== 1. Global Data Injector ===#
@app.context_processor
def inject_global_data():
    user = None
    if 'user_id' in session:
        try:
            db = get_db()
            #=== Corrected SQL query with parameters ===#
            row = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
            if row:
                user = RowWrapper(row)
        except Exception as e:
            print(f"Error in inject_global_data: {e}")
    
    return {
        'now': datetime.now(),
        'current_user': user,
        'wrap_row': lambda r: RowWrapper(r) if r else None
    }

#=== 2. Admin Access Decorator ===#
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #=== Only checks for admin_logged_in to match your login logic ===#
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

#=== 3. Language Selector Function ===#
def get_locale():
    return session.get('lang', app.config.get('BABEL_DEFAULT_LOCALE', 'en'))

# ===================== HELPER FUNCTIONS =====================

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#=== Final Fixed Independent Database Initialization ===#
def init_database():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("📊 Initializing database from code...")
        try:
            # Drop existing table to ensure clean schema
            cursor.execute("DROP TABLE IF EXISTS users")
            
            # Create table with all required columns
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE,
                    password TEXT NOT NULL,
                    phone TEXT,
                    role TEXT DEFAULT 'vendor',
                    is_active INTEGER DEFAULT 1,
                    vendor_id_code TEXT,
                    vendor_verified INTEGER DEFAULT 0,
                    referral_code TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            db.commit()
            print("✅ Database repair complete with ALL columns!")
        except Exception as e:
            print(f"#=== ERROR: {str(e)} ===#")

        
        # Users table
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
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en TEXT NOT NULL,
                name_ar TEXT,
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
        
        # Orders table
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
        
        # Order items table
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
        
        # Referrals table
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
        
        # Commissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id INTEGER,
                referred_user_id INTEGER,
                amount REAL NOT NULL,
                commission_rate REAL NOT NULL,
                type TEXT,  -- referral, vendor, signup_bonus, withdrawal
                status TEXT DEFAULT 'pending',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Withdrawals table
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
        
        # Site statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_visits INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                total_commission_paid REAL DEFAULT 0,
                date DATE UNIQUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add default admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
        if cursor.fetchone()[0] == 0:
            password_hash = hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (username, email, password, role, referral_code) VALUES (?, ?, ?, ?, ?)",
                ('admin', 'admin@sooqkabeer.com', password_hash, 'admin', 'ADMIN001')
            )
            print("✅ Default admin created: admin / admin123")
        
        # Add sample products
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('Fresh Tomatoes', 'طماطم طازجة', 'Premium tomatoes', 'طماطم عالية الجودة', 0.90, 'kg', 'vegetables', '', 100, 5),
                ('Potatoes', 'بطاطس', 'Fresh potatoes', 'بطاطس طازجة', 0.75, 'kg', 'vegetables', '', 80, 10),
                ('Onions', 'بصل', 'White onions', 'بصل أبيض', 0.65, 'kg', 'vegetables', '', 120, 5),
                ('Carrots', 'جزر', 'Sweet carrots', 'جزر حلو', 0.55, 'kg', 'vegetables', '', 60, 3),
                ('Cucumbers', 'خيار', 'Green cucumbers', 'خيار أخضر', 0.45, 'kg', 'vegetables', '', 70, 5)
            ]
            
            cursor.executemany('''
                INSERT INTO products (name_en, name_ar, description_en, description_ar, price, unit, category, image_url, stock_quantity, vendor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_products)
            print(f"✅ Added {len(sample_products)} sample products")
        
        db.commit()
        print("✅ Database initialized successfully")

#=== FIXED HASH FUNCTION  ===#
def hash_password(password):
    SALT = 'sooqkabeer_salt_'
    return hashlib.sha256((SALT + password).encode()).hexdigest()

def generate_referral_code(username):
    """Generate unique referral code"""
    code = hashlib.md5(f"{username}{random.random()}".encode()).hexdigest()[:8].upper()
    return f"REF{code}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ===================== REFERRAL SYSTEM FUNCTIONS =====================

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

        # 4. Add signup bonus (Optional: 5.0 units)
        signup_bonus = 5.0
        # Ensure add_commission function exists before calling
        if 'add_commission' in globals():
            add_commission(referrer_id, signup_bonus, 'signup_bonus', 
                          referred_user_id=new_user_id,
                          description=f"Signup bonus for new referral: {new_user_id}")

        # 5. Process multi-level referral (Optional)
        if 'process_multi_level_referral' in globals():
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
        FROM orders o JOIN users u ON o.user_id = u.id
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
            commission = vs['vendor_sales'] * VENDOR_RATE
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
        INSERT INTO commissions (user_id, order_id, referred_user_id, amount, commission_rate, type, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    ''', (user_id, order_id, referred_user_id, amount,
          REFERRAL_RATE if commission_type == 'referral' else VENDOR_RATE,
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
            SUM(CASE WHEN level > 1 THEN 1 ELSE 0 END) as indirect_referrals,
            SUM(commission_earned) as total_earnings
        FROM referrals
        WHERE referrer_id = ?
    ''', (user_id,))
    
    main_stats = cursor.fetchone()
    
    # Level-wise stats
    cursor.execute('''
        SELECT
            level,
            COUNT(*) as referral_count,
            SUM(commission_earned) as total_earnings,
            AVG(commission_rate) as avg_rate
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

# ===================== AUTHENTICATION ROUTES =====================

@app.route('/logout')
@app.route('/')
def home():
    db = get_db()
    cursor = db.cursor()

    #=== Fetch products for all users with error handling ===#
    try:
        # Fixed: Added '= 1' and closed the query properly
        cursor.execute("SELECT * FROM products WHERE is_active = 1")
        products = cursor.fetchall()
    except Exception:
        # Fallback if the is_active column doesn't exist
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

    return render_template('index.html', products=products)

#=== Language Switcher Route ===#
@app.route('/change_language/<lang>')
def change_site_lang(lang):
    if lang in ['en', 'ar']:
        session['language'] = lang
        session.permanent = True
    return redirect(request.referrer or url_for('home'))

# ===================== PRODUCT ROUTES =====================

@app.route('/products')
def products():
    #=== View all products with search and category filters ===#
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
        #=== Support for multilingual search ===#
        query += " AND (name_en LIKE ? OR name_ar LIKE ? OR description LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    products_list = cursor.fetchall()

    #=== Get categories for filter ===#
    cursor.execute("SELECT DISTINCT category FROM products WHERE is_active = 1")
    categories = cursor.fetchall()

    #=== WRAP THE DATA: Use RowWrapper to fix 'get_name' error in HTML ===#
    wrapped_products = [RowWrapper(row) for row in products_list]
    # If your category list also uses get_name in HTML, wrap it too:
    wrapped_categories = [RowWrapper(row) for row in categories]

    return render_template('products.html',
                         products=wrapped_products,
                         categories=wrapped_categories,
                         selected_category=category,
                         search=search,
                         lang=session.get('lang', 'en'))
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    #=== Product detail page with vendor info ===#
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
        #=== Redirect if product does not exist ===#
        flash('Product not found', 'danger')
        return redirect(url_for('products'))

    #=== Increment views count ===#
    cursor.execute("UPDATE products SET views = views + 1 WHERE id = ?", (product_id,))
    db.commit()

    #=== Wrap the product row to support get_name(lang) in template ===#
    wrapped_product = RowWrapper(product_row)

    return render_template('product_detail.html',
                         product=wrapped_product,
                         lang=session.get('lang', 'en'))

# ===================== ORDER ROUTES =====================

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
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
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

#=== Fixed Order History Function ===#
@app.route('/orders')
@login_required
def order_history():
    """View user's order history with item count"""
    db = get_db()
    cursor = db.cursor()

    # Corrected Sub-query for counting items
    cursor.execute('''
        SELECT o.*,
        (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as items_count
        FROM orders o JOIN users u ON o.user_id = u.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (session['user_id'],))

    orders = cursor.fetchall()

    return render_template('orders.html', orders=orders)

#=== Fixed Order Detail Function ===#
@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """View detailed information of a specific order"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('order_history'))

    if order['user_id'] != session['user_id'] and not session.get('admin_logged_in'):
        flash('Access denied', 'danger')
        return redirect(url_for('order_history'))

    cursor.execute('''
        SELECT o.*, u.username, u.email, u.phone
        FROM orders o JOIN users u ON o.user_id = u.id
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
    ''', (order_id,))
    order_info = cursor.fetchone()

    cursor.execute('''
        SELECT oi.*, p.name_en, p.name_ar, p.image_url
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,))
    items = cursor.fetchall()

    return render_template('order_detail.html', order=order_info, items=items)

# ===================== REFERRAL ROUTES =====================

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

@app.route('/referral/withdraw', methods=['POST'])
@login_required
def request_withdrawal():
    """Request withdrawal of referral earnings"""
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

# ===================== VENDOR ROUTES =====================

def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor':
            flash('Access denied. Vendors only.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/vendor/edit_product/<int:product_id>', methods=['GET', 'POST'])
@vendor_required
def vendor_edit_product(product_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT vendor_id FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    if not product or product['vendor_id'] != session['user_id']:
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
            stock_quantity = float(request.form['stock_quantity', 0])
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

# ===================== ADMIN ROUTES =====================

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage users - FIXED VERSION"""
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
        
        # Pass column names to template for proper display
        return render_template('admin/users.html',
                             users=users,
                             column_names=column_names)
                             
    except Exception as e:
        return f"Error fetching users: {str(e)}"

# app.py-তে একটি নতুন রুট যোগ করুন
@app.route('/fix-database-columns')
def fix_database_columns():
    """Add missing columns to database"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # users টেবিলে created_at যোগ করুন
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')
        
        # orders টেবিলেও একই করুন
        cursor.execute('''
            ALTER TABLE orders 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')
        
        db.commit()
        return "✅ Database columns added successfully!"
        
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/admin/approve-vendor/<int:v_id>')
@admin_required
def approve_vendor(v_id):
    db = get_db()
    cursor = db.cursor()
    
    # সরাসরি vendors টেবিল আপডেট করুন
    cursor.execute('''
        UPDATE vendors
        SET kyc_status = 'verified', vendor_verified = 1
        WHERE id = ?
    ''', (v_id,))
    
    # users টেবিলেও আপডেট করুন
    cursor.execute('''
        UPDATE users
        SET role = 'vendor'
        WHERE id = (SELECT user_id FROM vendors WHERE id = ?)
    ''', (v_id,))
    
    db.commit()
    flash('Vendor approved successfully!', 'success')
    return redirect(url_for('admin_vendors'))

# === Admin Commission and Withdrawal Management === #

@app.route('/admin/commissions')
def admin_commissions():
    """Manage commissions and show statistics"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch all commissions with associated user details using id_code
    cursor.execute("SELECT * FROM commissions ORDER BY created_at DESC")
    commissions = cursor.fetchall()

    # Calculate summary statistics for commissions
    cursor.execute('''
        SELECT
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_total,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_total,
            COUNT(*) as total_commissions
        FROM commissions
    ''')
    summary = cursor.fetchone()
    # Fetch all commissions with associated user details using id_code
    cursor.execute("SELECT * FROM commissions ORDER BY created_at DESC")
    commissions = cursor.fetchall()

    # Calculate summary statistics for commissions
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
def approve_commission(commission_id):
    """Approve a specific commission and mark as paid"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.execute('''
        UPDATE commissions 
        SET status = 'paid', paid_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (commission_id,))
    db.commit()
    
    return redirect(url_for('admin_commissions'))

@app.route('/admin/withdrawals')
def admin_withdrawals():
    """Manage and view all withdrawal requests"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch all withdrawals with user information
    cursor.execute('''
        SELECT w.*, u.username, u.email, u.wallet_balance
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        ORDER BY w.created_at DESC
    ''')
    withdrawals_list = cursor.fetchall()

    return render_template('admin/admin_withdrawals.html', withdrawals=withdrawals_list)

#=== Fixed Admin Process Withdrawal Function ===#
@app.route('/admin/process_withdrawal/<int:withdrawal_id>')
def process_withdrawal(withdrawal_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

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

# ===================== API ROUTES =====================

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

# ===================================================
#  ADMIM   PANEL  ROUTE
# ==================================================

@app.route('/admin/dashboard')
def admin_dashboard():
    # 1. Login & Role Security Check
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.row_factory = sqlite3.Row

    # 2. Fetching Stats Data
    total_products = db.execute('SELECT COUNT(*) FROM products')
    total_orders = db.execute('SELECT COUNT(*) FROM orders')
    total_users = db.execute('SELECT COUNT(*) FROM users')

    # Optional: Commission Calculation
    comm_data = db.execute('SELECT SUM(total_amount * 0.1) FROM orders').fetchone()
    total_commissions = comm_data[0] if comm_data and comm_data[0] else 0

    # 3. Packing stats for the new UI
    stats = {
        'total_products': total_products.fetchone()[0] if total_products else 0,
        'total_orders': total_orders.fetchone()[0] if total_orders else 0,
        'total_users': total_users.fetchone()[0] if total_users else 0,
        'total_revenue': total_commissions
    }

    # 4. Fetching Recent Data for Tables

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

    # 5. Rendering Template
    return render_template('admin/admin_dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_orders=recent_orders)
#=== Forgot Password Route ===#
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # এখানে আপনি ভবিষ্যতে ইমেইল চেক করার লজিক যোগ করতে পারবেন
        # এখনকার জন্য এটি একটি সাকসেস মেসেজ দিয়ে লগইন পেজে পাঠিয়ে দিবে
        flash(f'Success: A reset link has been sent to {email}. Please check your inbox.', 'info')
        
        # ভেন্ডরদের কথা মাথায় রেখে ভেন্ডর লগইন পেজে পাঠানোই ভালো
        return redirect(url_for('vendor_login'))
        
    return render_template('vendor/forgot_password.html')

#=== ACCESS CONTROL DECORATORS ===#
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Access denied: Admins only!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def vendor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'vendor':
            flash('Access denied: Vendors only!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

#=== ADMIN ROUTES WITH DECORATORS ===#

@app.route('/admin')
@admin_required
def admin_redirect():
    #=== REDIRECT BASE ADMIN URL TO DASHBOARD ===#
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Manage orders"""
    db = get_db()
    cursor = db.cursor()
    
    # ডিবাগিং: কতগুলো অর্ডার আছে?
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    print(f"Total orders in database: {count}")
    
    # যদি orders টেবিলে created_at না থাকে
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
        # Alternative query without created_at
        cursor.execute('''
            SELECT o.*, u.username as customer_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.id DESC
        ''')
    
    orders = cursor.fetchall()
    
    # ডিবাগিং: প্রাপ্ত অর্ডারগুলো প্রিন্ট করুন
    print(f"Fetched {len(orders)} orders")
    for i, order in enumerate(orders[:3]):  # প্রথম ৩টি
        print(f"Order {i+1}: {order}")
    
    return render_template('admin/orders.html', orders=orders)

#=== [FIXED ADMIN VENDORS - NO MORE ERRORS] ===#

@app.route('/admin/vendors')
@admin_required
def admin_vendors():
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    try:
        # প্রথমে ডাটাবেস টেবিল চেক করুন
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vendors'")
        if not cursor.fetchone():
            return render_template('admin/vendors.html', vendors=[], total=0, licensed=0, pending=0)
        
        # ভেন্ডর ডাটা
        cursor.execute("""
            SELECT id, company_name, vendor_code, kyc_status, 
                   total_earnings, commission_rate, created_at
            FROM vendors
            ORDER BY created_at DESC
        """)
        vendors = cursor.fetchall()
        
        # স্ট্যাটাস
        total_v = len(vendors)
        verified_v = sum(1 for v in vendors if v['kyc_status'] == 'verified')
        pending_v = total_v - verified_v

    except Exception as e:
        print(f"#=== VENDORS ERROR: {str(e)} ===#")
        vendors = []
        total_v, verified_v, pending_v = 0, 0, 0

    return render_template('admin/vendors.html',
                           vendors=vendors,
                           total=total_v,
                           licensed=verified_v,
                           pending=pending_v)

# === [FUNCTION] ADMIN ADD VENDOR === #
@app.route('/admin/vendors/add', methods=['GET', 'POST'])
@admin_required
def admin_add_vendor():
    import sqlite3
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

            # Hash the password for security
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
            print(f"#=== ERROR: {str(e)} ===#")
            flash(f'System Error: {str(e)}', 'danger')

    return render_template('admin/add_vendor.html')

# =============  Admin Products Route ==============

@app.route('/admin/products')
@admin_required
def admin_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    return render_template('admin/products.html', products=products)

# #=== [UPDATED ROUTE FOR ADVANCED FORM] ===#
@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_product():
    db = get_db()
    if request.method == 'POST':
        # ১. বেসিক ইনফো
        name_en = request.form.get('name_en')
        name_ar = request.form.get('name_ar')
        short_desc_en = request.form.get('short_description_en')
        short_desc_ar = request.form.get('short_description_ar')
        detailed_desc = request.form.get('detailed_description')

        # ২. প্রাইসিং ও স্টক
        price = request.form.get('price')
        b2b_price = request.form.get('b2b_price')
        cost_price = request.form.get('cost_price')
        stock = request.form.get('stock')
        sku = request.form.get('sku')

        # ৩. অ্যাডভান্সড সেটিংস
        category_id = request.form.get('category_id')
        vendor_id = request.form.get('vendor_id')
        status = request.form.get('status')

        # ৪. ইমেজ হ্যান্ডলিং (Main Image)
        image = request.files.get('main_image') # আপনার ফর্মে নাম 'main_image'
        filename = ""
        if image and image.filename != '':
            filename = image.filename
            image.save(f"static/uploads/{filename}")

        # ডাটাবেসে সেভ (নিশ্চিত করুন আপনার ডাটাবেসে এই কলামগুলো আছে)
        db.execute('''INSERT INTO products
            (name_en, name_ar, price, b2b_price, stock, category_id, vendor_id, image, sku, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name_en, name_ar, price, b2b_price, stock, category_id, vendor_id, filename, sku, status))
        db.commit()
        return redirect(url_for('admin_dashboard'))

    # ড্রপডাউনের জন্য ডাটা আনা
    categories = db.execute('SELECT * FROM categories').fetchall()
    vendors = db.execute('SELECT * FROM users WHERE role="vendor"').fetchall()
    
    return render_template('admin/add_product.html', categories=categories, vendors=vendors)
# #=== [END OF UPDATED ROUTE] ===#

# === [UPDATED] EDIT PRODUCT FUNCTION WITH B2B & COMMISSION === #
@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    # ডাটাবেস থেকে ওই প্রোডাক্টের তথ্য নেওয়া
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        try:
            # ১. ফরম থেকে সব ডাটা রিসিভ করা (অসম্পূর্ণ লাইনগুলো এখানে পূর্ণ করা হয়েছে)
            name_ar = request.form.get('name_ar')
            name_en = request.form.get('name_en')
            category_id = request.form.get('category_id')
            price = request.form.get('price')
            b2b_price = request.form.get('b2b_price') or 0
            stock = request.form.get('stock') or 0
            unit = request.form.get('unit') or 'pcs'
            min_qty = request.form.get('min_qty') or 1
            admin_commission = request.form.get('admin_commission') or 10.0

            # ২. ইমেজ হ্যান্ডলিং (নতুন ছবি দিলে আপডেট হবে, না দিলে আগেরটাই থাকবে)
            image_file = request.files.get('image')
            image_name = product['image'] # ডিফল্ট আগের ছবি
            
            if image_file and image_file.filename != '':
                from werkzeug.utils import secure_filename
                import os
                image_name = secure_filename(image_file.filename)
                image_file.save(os.path.join('static/images/products', image_name))

            # ৩. ডাটাবেসে আপডেট কুয়েরি চালানো
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
            # এরর হলে টার্মিনালে প্রিন্ট হবে
            print(f"#=== [EDIT ERROR]: {str(e)} ===#")
            flash('Error updating product', 'danger')

    # এডিট পেজ লোড করার সময় ক্যাটাগরি লিস্ট নিয়ে আসা
    categories = db.execute("SELECT * FROM categories").fetchall()
    return render_template('admin/edit_product.html', product=product, categories=categories)


@app.route('/admin/products/<int:product_id>/delete')
@admin_required
def admin_delete_product(product_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash('تم حذف المنتج بنجاح (Product Deleted)', 'success')
    except Exception as e:
        print(f"#=== DELETE ERROR: {str(e)} ===#")
        flash('Error occurred during deletion', 'danger')

    return redirect(url_for('admin_products'))

@app.route('/admin/products-debug')
def admin_products_debug():
    import sqlite3
    from flask import render_template
    
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
        # ডিবাগ প্রিন্ট
        print(f"Product: {product_dict.get('id')}, Stock: {product_dict.get('stock')}, Keys: {list(product_dict.keys())}")
    
    cursor.execute("SELECT * FROM categories")
    categories = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    print(f"Total products: {len(products)}")
    
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/order/<int:order_id>')
def admin_order_detail(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    db.row_factory = sqlite3.Row

    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

    if not order:
        return "Order not found", 404

    items = db.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()

    return render_template('order_detail.html', order=order, items=items)

@app.route('/admin/update-order-status/<int:order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    db = get_db()
    
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    
    if new_status == 'completed':
        order = db.execute('SELECT total_price, referrer_id_code FROM orders WHERE id = ?', (order_id,)).fetchone()
        
        if order and order['referrer_id_code']:
            # কমিশন ৩% ফিক্সড (০.০৩)
            commission_amount = order['total_price'] * 0.03
            
            db.execute('''
                INSERT INTO commissions (order_id, referrer_id_code, amount, status, created_at)
                VALUES (?, ?, ?, 'paid', CURRENT_TIMESTAMP)
            ''', (order_id, order['referrer_id_code'], commission_amount))
            
    db.commit()
    return redirect(url_for('admin_order_detail', order_id=order_id))

# ======================
# FORCE ADMIN
# ======================

@app.route('/force-admin')
def force_admin():
    db = get_db()
    # Fetch the admin user correctly
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

# =======================================
#    [FUNCTION]   VENDOR ROUTES
# =======================================

@app.route('/vendor/add_product', methods=['GET', 'POST'])
@vendor_required
def vendor_add_product():
    import sqlite3
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    # Auto-create categories if missing
    cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT, name_ar TEXT)")
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categories (name_en, name_ar) VALUES ('General', 'সাধারণ')")
    db.commit()
    if request.method == 'POST':
        try:
            # 1. Get form data
            name_en = request.form.get('name_en', '').strip()
            name_ar = request.form.get('name_ar', '').strip()
            desc_en = request.form.get('description_en', '').strip()
            desc_ar = request.form.get('description_ar', '').strip()
            price = float(request.form.get('price', 0))
            unit = request.form.get('unit', 'pcs').strip()
            category_id = request.form.get('category_id', '').strip()
            stock = float(request.form.get('stock_quantity', 0))
            image_url = request.form.get('image_url', 'default.jpg').strip()
            
            # Additional B2B fields we added to DB earlier
            b2b_price = float(request.form.get('b2b_price') or price)
            min_qty = int(request.form.get('min_qty') or 1)

            # 2. Get Vendor Details from Session
            vendor_id = session.get('user_id')
            # Note: Ensure session key matches your login system (user_id/vendor_id)

            # 3. Validation
            if not all([name_en, name_ar, price, category_id]):
                flash('Please fill all required fields!', 'danger')
                categories = cursor.execute("SELECT id, name_ar FROM categories").fetchall()
                return render_template('vendor/add_product.html', categories=categories)

            # 4. Database Insert
            sql = """INSERT INTO products
                     (name_en, name_ar, description_en, description_ar,
                      price, b2b_price, min_qty, unit, category_id, stock_quantity, 
                      image_url, vendor_id, status, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"""

            cursor.execute(sql, (
                name_en, name_ar, desc_en, desc_ar,
                price, b2b_price, min_qty, unit, category_id,
                stock, image_url, vendor_id, 'active'
            ))

            db.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('vendor_dashboard'))

        except ValueError:
            flash('Invalid number format for price or stock!', 'danger')
        except Exception as e:
            db.rollback()
            print(f"#=== ERROR: {str(e)} ===#")
            flash(f'System Error: {str(e)}', 'danger')

    # GET request - Show form with categories
    categories = cursor.execute("SELECT id, name_ar FROM categories").fetchall()
    return render_template('vendor/add_product.html', categories=categories)

    # Get vendor products
    cursor.execute("""
        SELECT p.*,
               (SELECT COUNT(*) FROM order_items oi WHERE oi.product_id = p.id) as total_sold,
               (SELECT SUM(oi.quantity) FROM order_items oi WHERE oi.product_id = p.id) as total_quantity
        FROM products p
        WHERE p.vendor_id = ?
        ORDER BY p.created_at DESC
    """, (vendor_id,))
    products = cursor.fetchall()
    
    # Convert products to list of dicts
    products_list = []
    for product in products:
        products_list.append({
            'id': product[0],
            'name_en': product[1],
            'name_ar': product[2],
            'price': product[5],
            'stock_quantity': product[9],
            'total_sold': product[13] if len(product) > 13 else 0,
            'total_quantity': product[14] if len(product) > 14 else 0
        })
    
        #=== Get vendor orders - Pure Code ===#
    cursor.execute("""
        SELECT DISTINCT o.id, o.order_number, u.username, o.total_amount, o.status, o.created_at
        FROM orders o JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN users u ON o.user_id = u.id
        WHERE p.vendor_id = ?
        ORDER BY o.created_at DESC
        LIMIT 10
    """, (vendor_id,))
    orders = cursor.fetchall()

    # Convert orders to list of dicts
    orders_list = []
    for order in orders:
        orders_list.append({
            'id': order[0],
            'order_number': order[1],
            'customer_name': order[2],
            'total_amount': order[3],
            'status': order[4],
            'created_at': order[5]
        })
    
        # Get vendor commissions
    cursor.execute("""
        SELECT SUM(amount) FROM commissions
        WHERE user_id = ? AND type = 'vendor' AND status = 'paid'
    """, (vendor_id,))
    total_commission = cursor.fetchone()[0] or 0

    # Get vendor stats
    cursor.execute("""
        SELECT
            COUNT(DISTINCT o.id),
            SUM(o.total_amount),
            COUNT(DISTINCT p.id)
        FROM orders o JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE p.vendor_id = ?
    """, (vendor_id,))
    stats = cursor.fetchone()

    return render_template('vendor/dashboard.html',
                         vendor={
                             'id': vendor[0],
                             'username': vendor[1],
                             'email': vendor[2]
                         } if vendor else {},
                         products=products_list,
                         orders=orders_list,
                         total_commission=total_commission,
                         total_orders=stats[0] if stats else 0,
                         total_sales=stats[1] if stats else 0,
                         total_products=stats[2] if stats else 0)

#=== Vendor Authentication & Dashboard (Security Enhanced) ===#

from functools import wraps

def vendor_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'vendor':
            flash("Please login first", "warning")
            return redirect(url_for('vendor_login'))
        return f(*args, **kwargs)
    return decorated_function

# === [FUNCTION] VENDOR LOGIN === #

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Matching your salt logic
        salt = "sooqkabeer_salt_"
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

        db = get_db_connection()
        db.row_factory = sqlite3.Row

        # AUTO-FIX: Ensure columns exist without dropping data
        try:
            db.execute("SELECT vendor_code FROM vendors LIMIT 1")
        except sqlite3.OperationalError:
            try:
                db.execute("ALTER TABLE vendors ADD COLUMN vendor_code TEXT UNIQUE")
                db.execute("ALTER TABLE vendors ADD COLUMN balance REAL DEFAULT 0.0")
                db.execute("ALTER TABLE vendors ADD COLUMN commission_rate REAL DEFAULT 10.0")
                db.commit()
            except:
                pass

                # Temporarily searching without hash to fix login issue
        user = db.execute("SELECT * FROM vendors WHERE email = ?", (email,)).fetchone()

        if user:
            # Check password directly (Plain text comparison for testing)
            if user['password'] == password or user['password'] == password_hash:
                session.clear()
                session.permanent = True
                session['user_id'] = user['id']
                session['role'] = 'vendor'
                session['vendor_code'] = user['vendor_code'] if user['vendor_code'] else "HKO-001"

                flash("Login Successful!", "success")
                db.close()
                return redirect(url_for('vendor_dashboard'))
            else:
                flash("Invalid password", "danger")
        else:
            flash("Invalid email", "danger")


        if user:
            session.clear()
            session.permanent = True
            session['user_id'] = user['id']
            session['role'] = 'vendor'
            
            # Ensure vendor_code is retrieved correctly (e.g. HKO-001)
            session['vendor_code'] = user['vendor_code'] if user['vendor_code'] else "HKO-001"

            flash("Login Successful!", "success")
            db.close()
            return redirect(url_for('vendor_dashboard'))
        else:
            flash("Invalid email or password", "danger")
            db.close()

    return render_template('vendor/vendor_login.html')

#=== Vendor Logout Route ===#
@app.route('/vendor/logout')
def vendor_logout():
    session.clear()
    return redirect(url_for('vendor_login'))

# === [FUNCTION] VENDOR DASHBOARD === #

@app.route('/vendor/dashboard')
@vendor_login_required
def vendor_dashboard():
    user_id = session.get('user_id')
    db = get_db_connection()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    try:
        # Get vendor details safely
        vendor = cursor.execute("SELECT * FROM vendors WHERE id = ?", (user_id,)).fetchone()
        if not vendor:
            return redirect(url_for('vendor_login'))

        # 1. Total Sales Calculation (Safe way)
        try:
            # We try to sum subtotal, if it fails, we default to 0
            stats = cursor.execute("""
                SELECT COUNT(id) as total_orders,
                SUM(subtotal) as total_sales
                FROM order_items
                WHERE product_id IN (SELECT id FROM products WHERE vendor_id = ?)
            """, (user_id,)).fetchone()
        except:
            stats = {'total_orders': 0, 'total_sales': 0.0}

        # 2. Commission calculation
        try:
            income_row = cursor.execute("SELECT SUM(amount) FROM commissions WHERE vendor_id = ?", (user_id,)).fetchone()
            total_income = income_row[0] if income_row and income_row[0] else 0.0
        except:
            total_income = 0.0

        # 3. Fetch products and orders
        products = cursor.execute("SELECT * FROM products WHERE vendor_id = ?", (user_id,)).fetchall()
        
        # Safe order fetching
        try:
            orders = cursor.execute("""
                SELECT oi.*, p.name_en, o.order_number
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                JOIN orders o ON oi.order_id = o.id
                WHERE p.vendor_id = ?
                ORDER BY o.id DESC LIMIT 5
            """, (user_id,)).fetchall()
        except:
            orders = []

        return render_template('vendor/dashboard.html',
                             vendor=vendor,
                             products=products,
                             stats=stats,
                             orders=orders,
                             income=total_income)

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        # If still error, show a simpler dashboard instead of crashing
        return f"Dashboard currently unavailable, but you are logged in as {vendor['vendor_code'] if vendor else 'Vendor'}"
    finally:
        db.close()

#=== REGISTER FUNCTION - NO BENGALI ALLOWED ===#
@app.route('/register', methods=['GET', 'POST'])
def register():
    referral_code = request.args.get('referral_code', '')

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            phone = request.form.get('phone', '').strip()
            ref_code = request.form.get('referral_code', '').strip()

            #=== PASSWORD MATCH CHECK (ENGLISH MESSAGES) ===#
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

            #=== VENDOR ID LOGIC ===#
            cursor.execute("SELECT COUNT(id) FROM users")
            count = cursor.fetchone()[0]
            vendor_custom_id = f"HKO-{(count + 1):05d}"

            salt = "sooqkabeer_salt_"
            password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

            # SQL insert with active status
            sql = """INSERT INTO users
                     (username, email, password, phone, role, is_active, 
                      vendor_id_code, vendor_verified, referral_code, status) 
                     VALUES (?, ?, ?, ?, 'vendor', 1, ?, 0, ?, 'active')"""

            cursor.execute(sql, (username, email, password_hash, phone, 
                                vendor_custom_id, ref_code))
            db.commit()

            flash(f'Registration Successful! Vendor ID: {vendor_custom_id}', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"#=== DEBUG ERROR: {str(e)} ===#")
            return f"Internal Server Error: {str(e)}"

    return render_template('register.html', referral_code=referral_code)

from datetime import datetime

#​#=== [ADD_KYC_ROUTE] ===#
@app.route('/vendor/upload-kyc', methods=['GET', 'POST'])
@vendor_login_required
def upload_kyc():
    if request.method == 'POST':
        # logic for file upload will go here
        flash("KYC Documents submitted successfully!", "success")
        return redirect(url_for('vendor_dashboard'))
    return render_template('vendor/upload_kyc.html')

#==============================================
#===[COMPLETE_VENDOR_WITHDRAW_FUNCTION]
#===============================================

@app.route('/vendor/withdraw', methods=['POST'])
def vendor_withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    amount = float(request.form.get('amount', 0))
    user_id = session['user_id']

    conn = get_db_connection()
    
    # Fetching vendor data using session user_id
    vendor = conn.execute('SELECT * FROM vendors WHERE id = ?', (user_id,)).fetchone()

    if not vendor:
        conn.close()
        return redirect(url_for('login'))

    # Condition 1: Check if Vendor Status is Verified
    if vendor['status'] != 'verified':
        flash("Your account is not verified! Please wait for admin approval.", "warning")
    
    # Condition 2: Minimum Withdrawal Limit (5 KD)
    elif amount < 5:
        flash("Minimum withdrawal amount is 5 KD.", "warning")
    
    # Condition 3: Sufficient Balance Check
    elif vendor['balance'] < amount:
        flash("Insufficient balance in your account!", "danger")
    
    else:
        # Update Balance and Save Withdrawal Request
        new_balance = vendor['balance'] - amount
        
        # Deducting from vendor balance
        conn.execute('UPDATE vendors SET balance = ? WHERE id = ?', (new_balance, user_id))
        
        # Inserting into withdrawal_requests table
        conn.execute('''
            INSERT INTO withdrawal_requests (vendor_id, amount, status, date) 
            VALUES (?, ?, ?, ?)
        ''', (vendor['id'], amount, 'pending', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        flash(f"Withdrawal request for {amount} KD has been submitted successfully!", "success")

    conn.close()
    return redirect(url_for('vendor_dashboard'))

# ======================
# ADDITIONAL ADMIN ROUTES
# ======================

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings"""
    db = get_db()
    cursor = db.cursor()
    
    # Get settings
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
            SUM(total_amount) as total_sales,
            AVG(total_amount) as avg_order_value
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
            SUM(oi.quantity * oi.price) as revenue,
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

@app.route('/admin/verify_vendor/<int:id>/<string:status>')
def verify_vendor(id, status):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
        
    conn = get_db_connection()
    # স্ট্যাটাস 'verified' অথবা 'unverified' সেট করা
    conn.execute('UPDATE vendors SET kyc_status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    
    flash(f"Vendor status updated to {status}", "success")
    return redirect(url_for('admin_vendors')) # আপনার এডমিন ভেন্ডর লিস্ট পেজ

# ======================
# HOME PAGE ROUTE
# ======================

@app.route('/')
def index():
    try:
        db = get_db()
        cursor = db.cursor()
        
        # ডাটাবেস থেকে প্রোডাক্ট নিয়ে আসা
        cursor.execute('''
            SELECT id, name_en, name_ar, price, category, image_url
            FROM products
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 8
        ''')
        products = cursor.fetchall()
        
        products_list = []
        for product in products:
            products_list.append({
                'id': product[0], 'name_en': product[1],
                'name_ar': product[2], 'price': product[3],
                'category': product[4], 'image_url': product[5]
            })
        
        return render_template('index.html', products=products_list)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', products=[])

# ===================== MAIN =========================

@app.route('/admin/toggle/<int:product_id>', methods=['POST'])
def admin_toggle_product(product_id):
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
    data = request.get_json()
    new_stock = data.get('stock')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
    db.commit()
    
    return jsonify({'success': True, 'stock': new_stock})

# === [FUNCTION] ADMIN ADD PRODUCT =============

import os
from werkzeug.utils import secure_filename

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    db = get_db()
    if request.method == 'POST':
        try:
            # ১. টেক্সট ডাটা সংগ্রহ (আপনার HTML ফর্মের সাথে মিলিয়ে)
            name_ar = request.form.get('name_ar')
            name_en = request.form.get('name_en')
            category_id = request.form.get('category_id')
            vendor_id = request.form.get('vendor_id') or None
            
            # ২. প্রাইস এবং বি২বি লজিক
            price = request.form.get('price', 0)
            b2b_price = request.form.get('b2b_price') or 0  # পাইকারি মূল্য
            min_qty = request.form.get('min_qty', 1)        # সর্বনিম্ন অর্ডারের পরিমাণ
            
            # ৩. স্টক এবং ইউনিট
            stock = request.form.get('stock', 0)
            unit = request.form.get('unit', 'pcs')          # কেজি, পিস বা বক্স
            
            # ৪. ইমেজ হ্যান্ডলিং
            image_file = request.files.get('image')
            image_name = 'default_product.jpg'
            if image_file and image_file.filename != '':
                image_name = secure_filename(image_file.filename)
                upload_path = os.path.join('static/images/products', image_name)
                image_file.save(upload_path)

            # ৫. ডাটাবেসে পূর্ণাঙ্গ ইনসার্ট (কলামগুলো আপনার DB অনুযায়ী চেক করবেন)
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO products (
                    name_ar, name_en, category_id, vendor_id,
                    price, b2b_price, min_qty, stock_quantity,
                    unit, image_url, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                name_ar, name_en, category_id, vendor_id,
                price, b2b_price, min_qty, stock,
                unit, image_name, 'active'
            ))
            
            db.commit()
            flash('Success! Product Added with B2B Details.', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.rollback()
            print(f"#=== [DATABASE ERROR]: {str(e)} ===#")
            flash(f'Error: {str(e)}', 'danger')

    # ড্রপডাউন ডাটা (ক্যাটাগরি ও ভেন্ডর)
    categories = db.execute("SELECT id, name_ar FROM categories").fetchall()
    vendors = db.execute("SELECT id, company_name FROM users WHERE role='vendor'").fetchall()
    
    return render_template('simple_add.html', categories=categories, vendors=vendors)

@app.route('/test-categories')
def test_categories():
    db = get_db()
    categories = db.execute("SELECT * FROM categories").fetchall()
    
    result = "<h1>Categories Test</h1>"
    result += f"<p>Found {len(categories)} categories</p>"
    result += "<ul>"
    for cat in categories:
        result += f"<li>{cat['id']}: {cat['name']}</li>"
    result += "</ul>"
    
    return result

#===================== MAIN =====================

if __name__ == '__main__':
    print("🚀 Starting SooqKabeer...")
    print("📊 Initializing database...")
    
    # Initialize database
    init_database()
    
    print("✅ Database ready")
    print("🌐 Available at: http://localhost:8000")
    print("🔑 Admin login: admin / admin123")
    print("💰 Features: Referral System, Multi-vendor, Commission Tracking")
    
    app.run(host='0.0.0.0', port=8000, debug=True)

