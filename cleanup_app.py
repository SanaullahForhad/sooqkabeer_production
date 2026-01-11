import re

# আপনার app ফাইল পড়ুন
with open('app_before_login_fix.py', 'r') as f:
    content = f.read()

# ১. সব কমেন্ট এবং প্রিন্ট স্টেটমেন্ট সরান (ঐচ্ছিক)
# content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
# content = re.sub(r'print\(.*\)', '', content)

# ২. ডুপ্লিকেট রাউটস চেক করুন
routes = re.findall(r"@app\.route\('([^']+)'\)", content)
print(f"মোট রাউটস: {len(routes)}")
print("প্রথম ১০টি রাউট:")
for route in routes[:10]:
    print(f"  - {route}")

# ৩. মডেলস খুঁজে বের করুন
models = re.findall(r'class (\w+)\(db\.Model\)', content)
print(f"\nমডেলস: {models}")

# ৪. ইম্পোর্টগুলো চেক করুন
imports = re.findall(r'from (\S+) import|import (\S+)', content)
print(f"\nইম্পোর্ট সংখ্যা: {len(imports)}")

# ৫. ফাইলটি সেভ করুন
with open('app_clean.py', 'w') as f:
    f.write(content)
    
print("\n✅ app_clean.py তৈরি হয়েছে")
