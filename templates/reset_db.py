import sqlite3
import hashlib
import os

# ডাটাবেস পাথ
db_path = 'instance/sooqkabeer.db'

# পুরাতন ডাটাবেস ডিলিট করুন
if os.path.exists(db_path):
    os.remove(db_path)
    print("পুরাতন ডাটাবেস ডিলিট করা হয়েছে")

# নতুন ডাটাবেস তৈরি
os.makedirs('instance', exist_ok=True)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# টেবিল তৈরি
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# টেস্ট ইউজার যোগ করুন (পাসওয়ার্ড: 123456)
salt = 'sooqkabeer_salt_'
test_password = '123456'
hashed_pw = hashlib.sha256((salt + test_password).encode()).hexdigest()

cursor.execute('''
INSERT INTO users (username, email, password) 
VALUES (?, ?, ?)
''', ('admin', 'admin@sooqkabeer.com', hashed_pw))

conn.commit()
conn.close()
print("নতুন ডাটাবেস তৈরি হয়েছে!")
print("টেস্ট লগিন:")
print("ইমেইল: admin@sooqkabeer.com")
print("পাসওয়ার্ড: 123456")
