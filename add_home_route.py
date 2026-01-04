#!/usr/bin/env python3

import os

# app.py ফাইলের পাথ
app_file = 'app.py'

# প্রথমে backup নিন
os.system(f'cp {app_file} {app_file}.backup')

# app.py পড়ুন
with open(app_file, 'r') as f:
    content = f.read()

# হোম রাউট আছে কিনা চেক
if '@app.route("/")' not in content:
    print("হোম রাউট যোগ করা হচ্ছে...")
    
    # render_template ইম্পোর্ট আছে কিনা চেক
    if 'from flask import' in content:
        # render_template যোগ করুন যদি না থাকে
        if 'render_template' not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from flask import'):
                    lines[i] = line.replace('from flask import', 'from flask import render_template,')
                    content = '\n'.join(lines)
                    break
    
    # হোম রাউট যোগ করুন
    route_to_add = '''

# হোমপেজ রাউট
@app.route('/')
def home():
    return render_template('index.html')
'''
    
    # রাউট যোগ করার উপযুক্ত স্থান খুঁজুন
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '@app.route' in line and i > 10:  # প্রথম few রাউটের পর
            lines.insert(i, route_to_add)
            content = '\n'.join(lines)
            print(f"হোম রাউট লাইন {i}-এ যোগ করা হয়েছে")
            break
    
    # ফাইলে লেখ
    with open(app_file, 'w') as f:
        f.write(content)
    
    print("✅ হোম রাউট যোগ করা হয়েছে")
else:
    print("✅ হোম রাউট ইতিমধ্যেই আছে")

print("\napp.py চেক করুন এবং সার্ভার রিস্টার্ট করুন")
