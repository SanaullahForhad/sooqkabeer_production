import sqlite3
import sys
import os

def init_database():
    # Get the absolute path
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    # Remove existing database if exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database removed!")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    
    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT,
        name_ar TEXT,
        price REAL,
        visible INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity REAL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add users with different roles
    users = [
        ('admin', 'admin123', 'admin'),
        ('vendor1', 'vendor123', 'vendor'),
        ('vendor2', 'vendor123', 'vendor'),
        ('customer1', 'customer123', 'customer'),
        ('customer2', 'customer123', 'customer'),
        ('supermarket', 'super123', 'customer'),
        ('restaurant', 'rest123', 'customer')
    ]
    
    c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users)
    
    # Add more products
    products = [
        ('Tomatoes', 'طماطم', 0.900, 1),
        ('Potatoes', 'بطاطس', 0.750, 1),
        ('Onions', 'بصل', 0.650, 1),
        ('Carrots', 'جزر', 0.550, 1),
        ('Cucumbers', 'خيار', 0.450, 1),
        ('Bell Peppers', 'فلفل حلو', 0.950, 1),
        ('Lettuce', 'خس', 0.850, 1),
        ('Lemons', 'ليمون', 0.350, 1),
        ('Apples', 'تفاح', 1.250, 1),
        ('Bananas', 'موز', 0.750, 1),
        ('Oranges', 'برتقال', 0.850, 1),
        ('Grapes', 'عنب', 1.500, 1),
        ('Strawberries', 'فراولة', 2.000, 1),
        ('Milk 1L', 'حليب 1 لتر', 0.800, 1),
        ('Eggs (12)', 'بيض (12 حبة)', 1.200, 1),
        ('Chicken 1kg', 'دجاج 1 كجم', 2.500, 1),
        ('Beef 1kg', 'لحم بقري 1 كجم', 4.000, 1),
        ('Rice 5kg', 'أرز 5 كجم', 3.500, 1),
        ('Flour 2kg', 'دقيق 2 كجم', 1.200, 1),
        ('Sugar 2kg', 'سكر 2 كجم', 1.000, 1)
    ]
    
    c.executemany("INSERT INTO products (name_en, name_ar, price, visible) VALUES (?, ?, ?, ?)", products)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("=" * 50)
    print("DATABASE INITIALIZED SUCCESSFULLY!")
    print("=" * 50)
    print("\n🔐 LOGIN CREDENTIALS:")
    print("=" * 50)
    print("👑 ADMIN: admin / admin123")
    print("👨‍🍳 VENDOR 1: vendor1 / vendor123")
    print("👨‍🍳 VENDOR 2: vendor2 / vendor123")
    print("🛒 CUSTOMER 1: customer1 / customer123")
    print("🏪 SUPERMARKET: supermarket / super123")
    print("🍽️ RESTAURANT: restaurant / rest123")
    print("=" * 50)
    print(f"\n📊 Database created: {db_path}")
    print("✅ Total users: 7")
    print("✅ Total products: 20")
    print("=" * 50)

if __name__ == "__main__":
    init_database()
