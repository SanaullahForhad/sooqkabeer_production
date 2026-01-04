import sqlite3

conn = sqlite3.connect('sooq.db')
cursor = conn.cursor()

# Ensure products table has required columns
try:
    cursor.execute("ALTER TABLE products ADD COLUMN image1 TEXT")
    print("✓ image1 column added")
except:
    print("image1 column already exists")

try:
    cursor.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'kg'")
    print("✓ unit column added")
except:
    print("unit column already exists")

# Add some sample products if empty
cursor.execute("SELECT COUNT(*) FROM products")
count = cursor.fetchone()[0]
print(f"Total products: {count}")

if count == 0:
    sample_products = [
        (1, 'تفاح أحمر', 'Red Apples', 'تفاح أحمر طازج من الكويت', 'Fresh red apples from Kuwait', 'fruits', 1.500, None, None, 'kg', 100, 'apple.jpg', None, None, None, 4.5, 23, 1, 0, 0, 0),
        (2, 'موز', 'Bananas', 'موز طازج', 'Fresh bananas', 'fruits', 0.750, 0.600, 20, 'kg', 150, 'banana.jpg', None, None, None, 4.2, 15, 0, 1, 0, 0),
        (3, 'تمور خلاص', 'Khalas Dates', 'تمور خلاص كويتية', 'Kuwaiti Khalas dates', 'dates', 3.000, 2.500, 17, 'kg', 80, 'dates.jpg', None, None, None, 4.8, 45, 1, 0, 1, 0),
        (4, 'زعفران', 'Saffron', 'زعفران إيراني', 'Iranian saffron', 'spices', 15.000, 12.000, 20, 'gm', 50, 'saffron.jpg', None, None, None, 4.7, 32, 0, 0, 0, 1)
    ]
    
    cursor.executemany('''INSERT INTO products (vendor_id, name_ar, name_en, description_ar, description_en, category, price, discount_price, discount_percent, unit, stock, image1, image2, image3, video_url, rating, total_reviews, is_featured, is_top_rated, is_b1g1, is_b2b) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_products)
    print("✓ Sample products added")

conn.commit()
conn.close()
print("Database fixed successfully!")
