import sqlite3
import os
import hashlib

def recreate_database():
    # ১. আপনার আসল ডাটাবেস নাম
    db_path = 'database.db'
    
    # ব্যাকআপ নেওয়া (যদি আগের ফাইল থাকে)
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        if os.path.exists(backup_path): os.remove(backup_path)
        os.rename(db_path, backup_path)
        print(f"📁 Old database backed up to: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Creating fresh database with all required columns...")
    
    # ২. Vendors Table তৈরি
    cursor.execute('''
        CREATE TABLE vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            shop_name TEXT,
            vendor_code TEXT NOT NULL UNIQUE,
            kyc_status TEXT DEFAULT 'pending',
            balance REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ৩. আপনার HKO-001 আইডিটি সরাসরি ইনসার্ট করা
    # পাসওয়ার্ড: 12345678 (সল্ট সহ হ্যাশ করা)
    salt = "sooqkabeer_salt_"
    raw_pass = "12345678"
    hashed_pass = hashlib.sha256((salt + raw_pass).encode()).hexdigest()

    cursor.execute('''
        INSERT INTO vendors (name, email, password, shop_name, vendor_code, kyc_status)
        VALUES ('Fahad', 'chanaullahfahad@gmail.com', ?, 'My Shop', 'HKO-001', 'approved')
    ''', (hashed_pass,))
    
    # ৪. Orders এবং Order Items টেবিল (ড্যাশবোর্ড এর জন্য)
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        vendor_id INTEGER,
        total_amount REAL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        subtotal REAL DEFAULT 0.0,
        quantity INTEGER DEFAULT 1)''')

    conn.commit()
    conn.close()
    print(f"✅ Fresh database '{db_path}' created successfully!")
    print("🔑 Login with: chanaullahfahad@gmail.com / 12345678")

if __name__ == "__main__":
    recreate_database()

