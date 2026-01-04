import sqlite3
import os

# আপনার app.py যেভাবে পাথ চেনে
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

print(f"Checking database at: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ক্যাটাগরি টেবিল তৈরি
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories 
                     (id INTEGER PRIMARY KEY, name_ar TEXT NOT NULL, name_en TEXT)''')
    
    # ডিফল্ট ডাটা ইনসার্ট
    cursor.execute('INSERT OR IGNORE INTO categories (id, name_ar, name_en) VALUES (1, "General", "General")')
    
    # আপনার ভেন্ডর আইডি ঠিক করা
    cursor.execute('UPDATE vendors SET vendor_code = "HKO-001", status = "verified" WHERE id > 0')
    
    conn.commit()
    conn.close()
    print("✅ Success! Table created and Vendor ID updated.")
except Exception as e:
    print(f"❌ Error: {e}")

