import re

with open('app.py', 'r') as f:
    content = f.read()

# Admin table code to be inserted
admin_code = '''
    # Admin Users
    cursor.execute("""CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Default admin user
    cursor.execute("""INSERT OR IGNORE INTO admin_users (username, password, email) 
    VALUES ('admin', 'admin123', 'admin@sooqkabeer.com')""")
'''

# Find the users table creation and insert admin code after it
if 'CREATE TABLE IF NOT EXISTS users' in content:
    new_content = re.sub(
        r'(cursor\.execute\("""CREATE TABLE IF NOT EXISTS users[\s\S]*?"""\))',
        r'\1' + admin_code,
        content
    )
    with open('app.py', 'w') as f:
        f.write(new_content)
    print("✅ সফলভাবে Admin টেবিলের কোড app.py-তে যোগ করা হয়েছে!")
else:
    print("❌ 'users' টেবিল খুঁজে পাওয়া যায়নি। দয়া করে আপনার app.py চেক করুন।")

