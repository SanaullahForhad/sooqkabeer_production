#!/usr/bin/env python3
# লগিন রুট ডিলেট করার স্ক্রিপ্ট

import re

with open('app.py', 'r') as f:
    lines = f.readlines()

# নতুন ফাইল তৈরি
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # চেক করতে কোন ফাংশন ডিলেট করতে হবে
    if i+1 < len(lines):
        next_line = lines[i+1]
        
        # লগিন রুট ডিলেট
        if ('@app.route(\'/login\'' in line or 
            '@app.route("/login"' in line) and 'def login():' in next_line:
            print(f"Deleting unified login at line {i+1}")
            # ফাংশনের শেষ পর্যন্ত খুঁজে ডিলেট
            while i < len(lines) and not lines[i].strip().startswith('@app.route') and i > 0:
                # function end খুঁজে
                if lines[i].strip() == '' and 'def ' in lines[i-1]:
                    break
                i += 1
            continue
            
        # ভেন্ডর লগিন ডিলেট
        elif ('@app.route(\'/vendor/login\'' in line or 
              '@app.route("/vendor/login"' in line) and 'def vendor_login():' in next_line:
            print(f"Deleting vendor_login at line {i+1}")
            # 6 লাইন ডিলেট (এই ফাংশন ছোট)
            for _ in range(6):
                i += 1
            continue
            
        # অ্যাডমিন লগিন ডিলেট
        elif ('@app.route(\'/admin/login\'' in line or 
              '@app.route("/admin/login"' in line) and 'def admin_login():' in next_line:
            print(f"Deleting admin_login at line {i+1}")
            # 6 লাইন ডিলেট
            for _ in range(6):
                i += 1
            continue
    
    new_lines.append(line)
    i += 1

# নতুন ফাইল সেভ
with open('app.py.new', 'w') as f:
    f.writelines(new_lines)

print("Cleanup complete. New file: app.py.new")
print("To replace original: mv app.py.new app.py")
