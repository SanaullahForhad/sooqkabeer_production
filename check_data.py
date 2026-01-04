import os
import sqlite3

print("🔍 আপনার কম্পিউটারে ডাটাবেস ফাইল খোঁজা হচ্ছে...\n")

# সম্ভাব্য ফাইল লোকেশন
possible_paths = [
    'sooqkabeer.db',
    'instance/sooqkabeer.db',
    'database.db',
    'data.db',
    'app.db',
    'test.db',
    'sqlite.db',
    'user.db',
    'users.db',
    'flask.db',
    'project.db'
]

found_files = []

for path in possible_paths:
    if os.path.exists(path):
        found_files.append(path)
        size = os.path.getsize(path)
        print(f"✅ পেয়েছি: {path} ({size} bytes)")
        
        # ডাটাবেস ওপেন করার চেষ্টা
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # সব টেবিলের নাম দেখি
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"   টেবিলগুলো: {[t[0] for t in tables]}")
            
            # users টেবিল চেক
            table_names = [t[0] for t in tables]
            if 'users' in table_names:
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                print(f"   users টেবিলে {count}টি রেকর্ড")
                
                # কিছু ডাটা দেখি
                cursor.execute("SELECT * FROM users LIMIT 3")
                users = cursor.fetchall()
                for user in users:
                    print(f"   - {user}")
            else:
                print("   ❌ users টেবিল নেই")
            
            conn.close()
        except Exception as e:
            print(f"   ❌ খুলতে সমস্যা: {e}")

if not found_files:
    print("❌ কোনো .db ফাইল পাওয়া যায়নি!")
    
    # সব SQLite ফাইল সার্চ
    print("\n🔎 সম্পূর্ণ সার্চ চালাচ্ছি...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                full_path = os.path.join(root, file)
                print(f"✅ পাওয়া গেছে: {full_path}")
                found_files.append(full_path)

if found_files:
    print(f"\n🎯 মোট {len(found_files)}টি ডাটাবেস ফাইল পাওয়া গেছে")
    print("আপনার ডাটা এখনো আছে!")
else:
    print("\n⚠️ কোনো ডাটাবেস ফাইল নেই। নতুন করে তৈরি করতে হবে।")
