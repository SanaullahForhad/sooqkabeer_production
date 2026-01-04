from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sooqkabeer-complete-secure-key-2025'
app.config['UPLOAD_FOLDER'] = 'static/images'

# ==================== DATABASE ====================
def init_database():
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Create tables if not exist (basic structure)
    tables = [
        # Users/Customers
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            referral_code TEXT UNIQUE,
            referred_by TEXT,
            wallet_balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Admin Users
        '''CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Vendors
        '''CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            vendor_code TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT "pending",
            license_number TEXT,
            license_expiry DATE,
            commission_rate REAL DEFAULT 10.0,
            total_earnings REAL DEFAULT 0,
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Categories
        '''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT,
            image TEXT,
            product_count INTEGER DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Products
        '''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            stock INTEGER DEFAULT 0,
            description TEXT,
            image TEXT,
            vendor_id INTEGER,
            is_featured BOOLEAN DEFAULT 0,
            bulk_price REAL,
            min_quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Orders
        '''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT "pending",
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',

        # Referral Earnings
        '''CREATE TABLE IF NOT EXISTS referral_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            referral_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
        except Exception as e:
            print(f"Error creating table: {e}")
    
    # Insert default admin if not exists
    cursor.execute("INSERT OR IGNORE INTO admin_users (username, password, email) VALUES ('admin', 'admin123', 'admin@sooqkabeer.com')")
    
    # Insert default categories if not exists
    default_categories = [
        ('خضار طازجة', 'Fresh Vegetables', 'vegetables.jpg'),
        ('بقالة', 'Groceries', 'fruits.jpg'),
        ('طلبات بالجملة', 'Bulk Orders', 'dryfruits.jpg'),
        ('طلب مجدول', 'Scheduled Orders', 'meat.jpg'),
        ('عروض اليوم', "Today's Offers", 'spices.jpg')
    ]
    
    for cat_ar, cat_en, img in default_categories:
        cursor.execute('''INSERT OR IGNORE INTO categories (name, name_en, image) 
                         VALUES (?, ?, ?)''', (cat_ar, cat_en, img))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with correct schema!")

# ==================== ROUTES ====================

# Homepage - HP-01 to HP-05
@app.route('/')
def index():
    # Set default language to Arabic
    if 'language' not in session:
        session['language'] = 'ar'
    
    current_lang = session.get('language', 'ar')
    
    # Connect to database
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Get all categories (HP-03)
    cursor.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY display_order, id')
    categories = cursor.fetchall()
    
    # Get featured products (HP-05)
    cursor.execute('SELECT * FROM products WHERE is_featured = 1 LIMIT 8')
    featured_products = cursor.fetchall()
    
    # Get top vendors
    cursor.execute('SELECT * FROM vendors WHERE status = "approved" ORDER BY total_earnings DESC LIMIT 4')
    top_vendors = cursor.fetchall()
    
    # Get B2B wholesale products (HP-04)
    cursor.execute('SELECT * FROM products WHERE bulk_price IS NOT NULL LIMIT 4')
    b2b_products = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html',
                         current_lang=current_lang,
                         categories=categories,
                         featured_products=featured_products,
                         top_vendors=top_vendors,
                         b2b_products=b2b_products)

# Language switcher
@app.route('/language/<lang>')
def switch_language(lang):
    if lang in ['ar', 'en', 'bn']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()

    # Get stats
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM vendors')
    total_vendors = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()[0]

    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_vendors=total_vendors,
                         total_orders=total_orders,
                         current_lang=current_lang)

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# Test route
@app.route('/test')
def test():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body style="padding: 40px; text-align: center; font-family: Arial;">
        <h1 style="color: green;">✅ SooqKabeer Test Page</h1>
        <p>All systems are working perfectly!</p>
        <div style="margin: 30px;">
            <a href="/" style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none; margin: 10px;">🏠 Home</a>
            <a href="/admin/login" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; margin: 10px;">👨‍💼 Admin</a>
        </div>
    </body>
    </html>
    '''

# ==================== MAIN ====================
if __name__ == '__main__':
    init_database()
    print("="*70)
    print("🇰🇼 SooqKabeer Kuwait - Complete Marketplace Platform")
    print("="*70)
    print("🌐 Website: http://127.0.0.1:8080")
    print("🔐 Admin: http://127.0.0.1:8080/admin/login")
    print("📱 Network: http://10.84.179.168:8080")
    print("="*70)
    print("✨ Features: B2B Wholesale, Scheduled Orders, Multi-language")
    print("👤 Admin: admin | Password: admin123")
    print("="*70)
    app.run(host='0.0.0.0', port=8080, debug=True)
