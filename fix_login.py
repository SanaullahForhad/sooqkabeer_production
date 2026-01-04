import sqlite3
import hashlib

# সল্ট যোগ করুন
SALT = 'sooqkabeer_salt_'

# ডাটাবেস connect
conn = sqlite3.connect('instance/sooqkabeer.db')
cursor = conn.cursor()

# ১. Admin ইউজারের পাসওয়ার্ড আপডেট করুন
admin_email = 'admin@sooqkabeer.com'
new_password = 'admin123'

# নতুন হ্যাশ তৈরি করুন
hashed_password = hashlib.sha256((SALT + new_password).encode()).hexdigest()

# ডাটাবেস আপডেট
cursor.execute("UPDATE users SET password = ? WHERE email = ?", 
               (hashed_password, admin_email))

conn.commit()
conn.close()

print("✅ Admin password updated successfully!")
print(f"New hash: {hashed_password}")
print("You can now login with:")
print(f"Email: {admin_email}")
print(f"Password: {new_password}")
