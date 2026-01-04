#=== Database Path Fixer & Reset ===#
import sqlite3
import hashlib
import os

def reset_admin():
    # ডাটাবেস ফাইলের সঠিক লোকেশন খুঁজে বের করা
    possible_paths = ['database.db', 'instance/database.db', '../database.db']
    db_path = None
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
            
    if not db_path:
        print("#=== ERROR: database.db not found! ===#")
        return

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    salt = "sooqkabeer_salt_"
    password = "admin" # আপনার নতুন পাসওয়ার্ড
    hashed_pw = hashlib.sha256((salt + password).encode()).hexdigest()
    
    try:
        # পাসওয়ার্ড আপডেট এবং স্ট্যাটাস একটিভ করা
        cursor.execute("UPDATE users SET password = ?, role = 'admin' WHERE username = 'admin'", (hashed_pw,))
        if cursor.rowcount == 0:
            print("#=== ERROR: User 'admin' not found in database! ===#")
        else:
            db.commit()
            print(f"#=== SUCCESS: Password reset for 'admin' at {db_path} ===#")
    except sqlite3.OperationalError as e:
        print(f"#=== DB ERROR: {str(e)} ===#")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()

