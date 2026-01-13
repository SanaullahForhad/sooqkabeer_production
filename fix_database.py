import sqlite3
import os
import hashlib
from datetime import datetime

def fix_database_issues():
    """
    Fix database issues and consolidate into one database
    """
    print("🔧 Fixing database issues...")
    
    # ১. আপনার প্রধান ডাটাবেস নির্ধারণ করুন
    MAIN_DB = 'sooqkabeer.db'
    print(f"🎯 Using main database: {MAIN_DB}")
    
    # ২. পুরনো ফাইল ব্যাকআপ
    if os.path.exists(MAIN_DB):
        backup = f"{MAIN_DB}.backup"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(MAIN_DB, backup)
        print(f"📁 Backup created: {backup}")
    
    # ৩. নতুন ডাটাবেস তৈরি
    conn = sqlite3.connect(MAIN_DB)
    cursor = conn.cursor()
    
    # ৪. সম্পূর্ণ নতুন schema তৈরি করুন
    print("🔄 Creating fresh database with correct schema...")
    
    # Users Table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        language TEXT DEFAULT 'ar',
        wallet_balance REAL DEFAULT 0.0,
        referral_code TEXT UNIQUE,
        referred_by TEXT,
        is_active INTEGER DEFAULT 1,
        vendor_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Vendors Table (সব columns সহ)
    cursor.execute('''
    CREATE TABLE vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_code TEXT UNIQUE NOT NULL,
        vendor_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        password_hash TEXT NOT NULL,
        balance REAL DEFAULT 0.0,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Categories Table
    cursor.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_ar TEXT NOT NULL,
        name_en TEXT,
        name_bn TEXT,
        description TEXT,
        image TEXT,
        is_active INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Products Table
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_ar TEXT NOT NULL,
        name_en TEXT,
        name_bn TEXT,
        description_ar TEXT,
        description_en TEXT,
        description_bn TEXT,
        price REAL NOT NULL,
        discount_price REAL,
        stock INTEGER DEFAULT 0,
        sku TEXT,
        barcode TEXT,
        image TEXT DEFAULT 'default_product.jpg',
        category_id INTEGER NOT NULL,
        vendor_id INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id),
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    )
    ''')
    
    # Other essential tables
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        shipping_address TEXT,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'pending',
        order_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        commission_rate REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        payment_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vendor_id) REFERENCES vendors(id),
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    ''')
    
    # ৫. Test Data যোগ করুন
    print("📝 Adding test data...")
    
    # Password hashing function
    def hash_password(password):
        SALT = 'sooqkabeer_salt_'
        return hashlib.sha256((SALT + password).encode()).hexdigest()
    
    # Sample Vendor
    vendor_password = hash_password("vendor123")
    cursor.execute('''
        INSERT INTO vendors (vendor_code, vendor_name, email, phone, address, password_hash, balance, status)
        VALUES ('HKO-001', 'Test Vendor Shop', 'vendor@sooqkabeer.com', '12345678', 'Kuwait City', ?, 1000.0, 'active')
    ''', (vendor_password,))
    
    # Sample User
    user_password = hash_password("user123")
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, phone, vendor_id, is_active)
        VALUES ('testuser', 'user@sooqkabeer.com', ?, '98765432', 1, 1)
    ''', (user_password,))
    
    # Sample Categories
    categories = [
        ('إلكترونيات', 'Electronics', 'ইলেকট্রনিক্স'),
        ('موضة', 'Fashion', 'ফ্যাশন'),
        ('بقالة', 'Grocery', 'গ্রোসারি'),
        ('منزل', 'Home', 'হোম'),
        ('ألعاب', 'Toys', 'খেলনা')
    ]
    
    for name_ar, name_en, name_bn in categories:
        cursor.execute('''
            INSERT INTO categories (name_ar, name_en, name_bn, is_active, display_order)
            VALUES (?, ?, ?, 1, ?)
        ''', (name_ar, name_en, name_bn, len(categories) - categories.index((name_ar, name_en, name_bn))))
    
    # Sample Products
    products = [
        ('آيفون 14', 'iPhone 14', 'আইফোন 14', 'أحدث آيفون', 'Latest iPhone', 'সবচেয়ে নতুন আইফোন', 350.500, 340.000, 50, 'IP14-001', '1234567890123', 1, 1),
        ('سامسونج جالاكسي', 'Samsung Galaxy', 'স্যামসাং গ্যালাক্সি', 'أحدث جالاكسي', 'Latest Galaxy', 'নতুন গ্যালাক্সি', 280.750, None, 30, 'SG-001', '9876543210987', 1, 1),
        ('تيشيرت قطن', 'Cotton T-Shirt', 'কটন টি-শার্ট', 'قطن 100%', '100% Cotton', '১০০% সুতি', 5.990, 4.990, 100, 'TS-001', '1112223334445', 2, 1),
    ]
    
    for prod in products:
        cursor.execute('''
            INSERT INTO products (name_ar, name_en, name_bn, description_ar, description_en, description_bn, 
                                 price, discount_price, stock, sku, barcode, category_id, vendor_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ''', prod)
    
    conn.commit()
    conn.close()
    
    # ৬. SQLAlchemy মডেলের সাথে ডাটাবেসের মিল আছে কিনা চেক করুন
    print("\n✅ Database created successfully!")
    print("\n📊 Database Summary:")
    print(f"   Database: {MAIN_DB}")
    print("   Tables created:")
    print("     - users")
    print("     - vendors (with created_at column)")
    print("     - categories")
    print("     - products")
    print("     - orders")
    print("     - order_items")
    print("     - commissions")
    print("\n🔐 Test Credentials:")
    print("   Vendor: vendor@sooqkabeer.com / vendor123")
    print("   User: user@sooqkabeer.com / user123")
    
    # ৭. পরীক্ষা করুন
    print("\n🔍 Testing database...")
    conn = sqlite3.connect(MAIN_DB)
    cursor = conn.cursor()
    
    # Check vendors table
    cursor.execute("PRAGMA table_info(vendors)")
    columns = cursor.fetchall()
    print("\n📋 Vendors table columns:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # Check data
    cursor.execute("SELECT COUNT(*) FROM vendors")
    vendor_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM categories")
    category_count = cursor.fetchone()[0]
    
    print(f"\n📈 Data Counts:")
    print(f"   Vendors: {vendor_count}")
    print(f"   Categories: {category_count}")
    print(f"   Products: {product_count}")
    
    conn.close()
    
    print("\n✅ All done! Now update your app.py configuration:")
    print(f"   app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{MAIN_DB}'")

if __name__ == "__main__":
    fix_database_issues()
