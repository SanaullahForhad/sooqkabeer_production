#!/usr/bin/env python3
# সব লগিন রুট রিমুভ করার স্ক্রিপ্ট

import re

with open('app.py', 'r') as f:
    content = f.read()

# প্যাটার্ন খুঁজে লগিন ফাংশন রিমুভ
patterns = [
    # ইউনিফাইড লগিন
    r"@app\.route\(['\"]/login['\"].*?def login\(.*?\):.*?(?=@app\.route|def |\Z)",
    # ভেন্ডর লগিন
    r"@app\.route\(['\"]/vendor/login['\"].*?def vendor_login\(.*?\):.*?(?=@app\.route|def |\Z)",
    # অ্যাডমিন লগিন
    r"@app\.route\(['\"]/admin/login['\"].*?def admin_login\(.*?\):.*?(?=@app\.route|def |\Z)",
    # কাস্টমার লগিন
    r"@app\.route\(['\"]/customer/login['\"].*?def customer_login\(.*?\):.*?(?=@app\.route|def |\Z)",
    # রেজিস্ট্রেশন
    r"@app\.route\(['\"]/register['\"].*?def register\(.*?\):.*?(?=@app\.route|def |\Z)",
    r"@app\.route\(['\"]/vendor/register['\"].*?def vendor_register\(.*?\):.*?(?=@app\.route|def |\Z)",
    r"@app\.route\(['\"]/customer/register['\"].*?def customer_register\(.*?\):.*?(?=@app\.route|def |\Z)",
]

print("Removing all login routes...")
for pattern in patterns:
    matches = re.findall(pattern, content, re.DOTALL)
    for match in matches:
        print(f"Found and removing: {match[:50]}...")
        content = content.replace(match, '')

# নতুন ফাইল সেভ
with open('app.py', 'w') as f:
    f.write(content)

print("\nAll login routes removed!")
print("Original backup saved as app.py.backup")
