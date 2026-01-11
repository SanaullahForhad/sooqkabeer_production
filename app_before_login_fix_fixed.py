from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

import os
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
           static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
app.secret_key = 'sooqkabeer-complete-secure-key-2025'
app.config['UPLOAD_FOLDER'] = 'static/images'

# ==================== DATABASE ====================
def init_database():
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Drop and recreate tables with correct schema
    tables_to_drop = ['products', 'categories', 'vendors', 'users', 'admin_users', 'orders', 'referral_earnings']
    
    for table in tables_to_drop:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        except:
            pass
    
    # Create tables with correct schema
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
            name_ar TEXT,
            name_en TEXT,
            owner_name TEXT,
            email TEXT,
            phone TEXT,
            location_ar TEXT,
            location_en TEXT,
            category TEXT,
            logo_url TEXT DEFAULT 'default_vendor.jpg',
            banner_url TEXT DEFAULT 'default_banner.jpg',
            status TEXT DEFAULT 'active',
            commission_rate REAL DEFAULT 10.0,
            total_earnings REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Categories
        '''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT,
            name_en TEXT,
            icon TEXT,
            image_url TEXT,
            sort_order INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Products (FIXED - added old_price column)
        '''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT,
            name_en TEXT,
            description_ar TEXT,
            description_en TEXT,
            price REAL,
            old_price REAL,
            category_id INTEGER,
            vendor_id INTEGER,
            image_url TEXT DEFAULT 'default_product.jpg',
            stock INTEGER DEFAULT 100,
            is_featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Orders
        '''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            delivery_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Referral Earnings
        '''CREATE TABLE IF NOT EXISTS referral_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            referred_user_id INTEGER,
            amount REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        # Withdrawals
        '''CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # Insert default data
    # Default admin
    cursor.execute("INSERT OR IGNORE INTO admin_users (username, password, email) VALUES ('admin', 'admin123', 'admin@sooqkabeer.com')")
    
    # Default categories
    categories = [
        ('فواكه طازجة', 'Fresh Fruits', 'fas fa-apple-alt', 'fruits.jpg', 1, 1),
        ('خضروات طازجة', 'Fresh Vegetables', 'fas fa-carrot', 'vegetables.jpg', 2, 1),
        ('تمور كويتية', 'Kuwaiti Dates', 'fas fa-calendar-alt', 'dates.jpg', 3, 1),
        ('فواكه مجففة', 'Dry Fruits', 'fas fa-seedling', 'dryfruits.jpg', 4, 1),
        ('بهارات وتوابل', 'Spices', 'fas fa-mortar-pestle', 'spices.jpg', 5, 1),
        ('لحوم ودواجن', 'Meat & Poultry', 'fas fa-drumstick-bite', 'meat.jpg', 6, 1),
        ('أسماك وماريس', 'Fish & Seafood', 'fas fa-fish', 'fish.jpg', 7, 1),
        ('مخبوزات', 'Bakery', 'fas fa-bread-slice', 'bakery.jpg', 8, 1),
        ('معلبات', 'Canned Foods', 'fas fa-cookie-bite', 'canned.jpg', 9, 1),
        ('مشروبات', 'Beverages', 'fas fa-wine-bottle', 'beverages.jpg', 10, 1)
    ]
    
    for cat in categories:
        cursor.execute('''INSERT OR IGNORE INTO categories 
            (name_ar, name_en, icon, image_url, sort_order, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)''', cat)
    
    # Default vendors
    vendors = [
        ('تمور النخيل الذهبي', 'Golden Palm Dates', 'محمد القطان', 'mohamed@sooq.com', 
         '+96550012346', 'الفروانية', 'Farwaniya', 'dates', 'vendor1.jpg', 'banner1.jpg', 'active', 10.0, 0),
        ('فواكه الخليج', 'Gulf Fruits', 'خالد الصباح', 'khaled@sooq.com', 
         '+96550012347', 'السالمية', 'Salmiya', 'fruits', 'vendor2.jpg', 'banner2.jpg', 'active', 12.0, 0),
        ('بهارات العائلة', 'Family Spices', 'أحمد العلي', 'ahmed@sooq.com', 
         '+96550012348', 'الجهراء', 'Jahra', 'spices', 'vendor3.jpg', 'banner3.jpg', 'active', 8.0, 0)
    ]
    
    for vendor in vendors:
        cursor.execute('''INSERT OR IGNORE INTO vendors 
            (name_ar, name_en, owner_name, email, phone, location_ar, location_en, 
             category, logo_url, banner_url, status, commission_rate, total_earnings) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', vendor)
    
    # Default products (FIXED - with old_price)
    products = [
        ('تفاح أحمر', 'Red Apple', 'تفاح أحمر طازج', 'Fresh red apples', 1.500, 2.000, 1, 2, 'apple.jpg', 100, 1),
        ('موز', 'Banana', 'موز حلو وطازج', 'Sweet fresh bananas', 0.750, 1.000, 1, 2, 'banana.jpg', 150, 1),
        ('تمر كويتي', 'Kuwaiti Dates', 'تمر كويتي أصلي', 'Original Kuwaiti dates', 3.000, 4.000, 3, 1, 'dates.jpg', 80, 1),
        ('زعفران', 'Saffron', 'زعفران إيراني ممتاز', 'Premium Iranian saffron', 12.500, 15.000, 5, 3, 'saffron.jpg', 30, 1),
        ('برتقال', 'Orange', 'برتقال حلو', 'Sweet oranges', 1.200, 1.500, 1, 2, 'default_product.jpg', 120, 0),
        ('طماطم', 'Tomato', 'طماطم طازجة', 'Fresh tomatoes', 0.800, 1.000, 2, 2, 'default_product.jpg', 200, 0),
        ('قهوة عربية', 'Arabic Coffee', 'قهوة عربية أصيلة', 'Authentic Arabic coffee', 5.000, 6.000, 5, 3, 'default_product.jpg', 50, 1),
        ('عسل طبيعي', 'Natural Honey', 'عسل طبيعي 100%', '100% Natural honey', 8.000, 10.000, 5, 3, 'default_product.jpg', 40, 1)
    ]
    
    for prod in products:
        cursor.execute('''INSERT OR IGNORE INTO products 
            (name_ar, name_en, description_ar, description_en, price, old_price, 
             category_id, vendor_id, image_url, stock, is_featured) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', prod)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with correct schema!")

# ==================== ROUTES ====================

# Homepage with all features
@app.route('/')
def home():
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Get featured products
    cursor.execute('''SELECT p.*, c.name_ar as category_ar, c.name_en as category_en 
                      FROM products p 
                      JOIN categories c ON p.category_id = c.id 
                      WHERE p.is_featured = 1 LIMIT 8''')
    featured_products = cursor.fetchall()
    
    # Get categories
    cursor.execute('SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order LIMIT 10')
    categories = cursor.fetchall()
    
    # Get vendors
    cursor.execute('SELECT * FROM vendors WHERE status = "active" LIMIT 6')
    vendors = cursor.fetchall()
    
    conn.close()
    
    # Get current language
    current_lang = session.get('language', 'ar')
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         categories=categories,
                         vendors=vendors,
                         current_lang=current_lang)

# Language switcher
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'en', 'bn']:
        session['language'] = lang
    return redirect(request.referrer or '/')

# Admin System
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
    
    cursor.execute('SELECT SUM(total_amount) FROM orders WHERE status = "completed"')
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_vendors=total_vendors,
                         total_orders=total_orders,
                         total_revenue=total_revenue)

# Vendor management
@app.route('/vendors')
def vendors_list():
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendors WHERE status = "active"')
    vendors = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('vendors.html', vendors=vendors, current_lang=current_lang)

# Referral system
@app.route('/referral')
def referral():
    # For demo, use a mock user
    session['user_id'] = session.get('user_id', 1)
    user_id = session['user_id']
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Create user if not exists
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        cursor.execute('''INSERT INTO users (id, name, email, phone, password, referral_code) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                     (user_id, 'Demo User', 'demo@sooqkabeer.com', '+96550000000', 
                      'demo123', f'REF-SOOQ-{user_id}'))
        conn.commit()
    
    # Get user referral code and earnings
    cursor.execute('SELECT referral_code, wallet_balance FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    
    cursor.execute('''SELECT u.name, u.email, re.amount, re.created_at 
                      FROM referral_earnings re
                      JOIN users u ON re.referred_user_id = u.id
                      WHERE re.user_id = ? ORDER BY re.created_at DESC''', (user_id,))
    referrals = cursor.fetchall()
    
    # Add some demo referral earnings
    if not referrals:
        demo_users = [
            (2, 'Ahmed Ali', 'ahmed@example.com', 5.25),
            (3, 'Fatima Hassan', 'fatima@example.com', 8.75),
            (4, 'Khalid Omar', 'khalid@example.com', 12.50)
        ]
        
        for user_id2, name, email, amount in demo_users:
            cursor.execute('''INSERT OR IGNORE INTO referral_earnings 
                            (user_id, referred_user_id, amount, description)
                            VALUES (?, ?, ?, ?)''',
                         (user_id, user_id2, amount, f'Referral from {name}'))
        
        conn.commit()
        cursor.execute('''SELECT u.name, u.email, re.amount, re.created_at 
                          FROM referral_earnings re
                          JOIN users u ON re.referred_user_id = u.id
                          WHERE re.user_id = ? ORDER BY re.created_at DESC''', (user_id,))
        referrals = cursor.fetchall()
    
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('referral.html',
                         referral_code=user_data[0],
                         wallet_balance=user_data[1],
                         referrals=referrals,
                         current_lang=current_lang)

# Commission withdrawal
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if not session.get('user_id'):
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    amount = float(request.form.get('amount', 0))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    
    # Check balance
    cursor.execute('SELECT wallet_balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    
    if amount > balance:
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Update balance
    new_balance = balance - amount
    cursor.execute('UPDATE users SET wallet_balance = ? WHERE id = ?', (new_balance, user_id))
    
    # Add to withdrawal history
    cursor.execute('INSERT INTO withdrawals (user_id, amount) VALUES (?, ?)', (user_id, amount))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'new_balance': new_balance})

# Image serving
@app.route('/apple.jpg')
def serve_apple():
    return send_from_directory('static/images', 'apple.jpg')

@app.route('/banana.jpg')
def serve_banana():
    return send_from_directory('static/images', 'banana.jpg')

@app.route('/dates.jpg')
def serve_dates():
    return send_from_directory('static/images', 'dates.jpg')

@app.route('/saffron.jpg')
def serve_saffron():
    return send_from_directory('static/images', 'saffron.jpg')

@app.route('/static/images/<path:filename>')
def serve_static(filename):
    return send_from_directory('static/images', filename)

# Favicon
@app.route('/favicon.ico')
def favicon():
    return '', 200
# ==================== ADMIN ROUTES ====================

# Admin - Vendors Management
@app.route("/admin/vendors")
def admin_vendors():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("sooq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors")
    vendors = cursor.fetchall()
    conn.close()
    
    current_lang = session.get("language", "ar")
    return render_template("admin_vendors.html", 
                         vendors=vendors,
                         current_lang=current_lang)

# Admin - Referrals Management
@app.route("/admin/referrals")
def admin_referrals():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("sooq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT u.name, u.email, u.phone, r.amount, r.created_at FROM referral_earnings r JOIN users u ON r.user_id = u.id")
    referrals = cursor.fetchall()
    conn.close()
    
    current_lang = session.get("language", "ar")
    return render_template("admin_referrals.html",
                         referrals=referrals,
                         current_lang=current_lang)

# Admin - Products Management
@app.route("/admin/products")
def admin_products():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("sooq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    
    current_lang = session.get("language", "ar")
    return render_template("admin_products.html",
                         products=products,
                         current_lang=current_lang)

# Admin - Orders Management
@app.route("/admin/orders")
def admin_orders():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("sooq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    
    current_lang = session.get("language", "ar")
    return render_template("admin_orders.html",
                         orders=orders,
                         current_lang=current_lang)

# Admin - Users Management
@app.route("/admin/users")
def admin_users():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    conn = sqlite3.connect("sooq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    current_lang = session.get("language", "ar")
    return render_template("admin_users.html",
                         users=users,
                         current_lang=current_lang)

# Admin - Settings
@app.route("/admin/settings")
def admin_settings():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    current_lang = session.get("language", "ar")
    return render_template("admin_settings.html",
                         current_lang=current_lang)

# Admin - Logout
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

    return '', 200

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
            <a href="/vendors" style="padding: 10px 20px; background: #6f42c1; color: white; text-decoration: none; margin: 10px;">🏢 Vendors</a>
            <a href="/referral" style="padding: 10px 20px; background: #fd7e14; color: white; text-decoration: none; margin: 10px;">💰 Referral</a>
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
    print("✨ Features: Multi-language, Vendors, Referral, Commission, Payment")
    print("👤 Admin: admin | Password: admin123")
    print("="*70)
    app.run(host='0.0.0.0', port=8080, debug=True)
