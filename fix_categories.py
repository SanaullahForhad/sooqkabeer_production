import sqlite3
import os

def fix_categories():
    # আপনার ডাটাবেস ফাইলের নাম নিশ্চিত করুন
    db_path = 'database.db' 
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📁 Creating categories table...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            description TEXT,
            parent_id INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ডিফল্ট ক্যাটাগরি যোগ করা
    default_cats = [
        ('Groceries', 'البقالة'),
        ('Electronics', 'إلكترونيات'),
        ('Clothing', 'ملابس')
    ]
    
    for en, ar in default_cats:
        cursor.execute("INSERT OR IGNORE INTO categories (name_en, name_ar) VALUES (?, ?)", (en, ar))
    
    # আপনার ভেন্ডর আইডি HKO-001 সেট করা
    cursor.execute('UPDATE vendors SET vendor_code = "HKO-001", status = "verified" WHERE id > 0')
    
    conn.commit()
    conn.close()
    print("✅ Success! Run python app.py now.")

if __name__ == "__main__":
    fix_categories()
