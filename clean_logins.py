#!/usr/bin/env python3
import re

def remove_login_functions(content):
    """Remove all login-related routes except one unified login"""
    lines = content.split('\n')
    new_lines = []
    i = 0
    skip = False
    login_to_keep = 'def login():'  # এই লগিন ফাংশনটি রাখতে চাই
    
    while i < len(lines):
        line = lines[i]
        
        # লগিন রুট খুঁজুন
        if '@app.route' in line and any(x in line.lower() for x in ['/login', '/vendor', '/admin']):
            if 'def login():' in lines[i+1] if i+1 < len(lines) else False:
                # এইটাই সেই একক লগিন যেটা আমরা রাখতে চাই
                print(f"Keeping unified login route at line {i+1}")
                new_lines.append(line)
                new_lines.append(lines[i+1])
                i += 2
                continue
            else:
                # অন্য কোনো লগিন রুট - ডিলেট করতে হবে
                print(f"Removing login route at line {i+1}: {line.strip()}")
                skip = True
                i += 1
                continue
        
        # যদি skip mode-এ থাকি
        if skip:
            # ফাংশনের শেষ খুঁজুন (খালি লাইন বা নতুন রুট)
            if i < len(lines) and (lines[i].strip() == '' or 
                                  (i+1 < len(lines) and '@app.route' in lines[i+1])):
                skip = False
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)

def keep_only_one_login(content):
    """Keep only one login function and remove all others"""
    # 1. শুধু 'def login():' ফাংশনটি রাখুন
    pattern = r'(@app\.route\([^)]*login[^)]*\)\s*\n.*def login\(.*?\).*?\n(?:    .*\n)*?\n)'
    
    # 2. সব লগিন ফাংশন খুঁজুন
    login_functions = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if login_functions:
        # প্রথম লগিন ফাংশনটি রাখুন (এটা unified login হবে)
        login_to_keep = login_functions[0]
        
        # 3. সব লগিন রুট রিমুভ করুন
        pattern_all = r'@app\.route\([^)]*(?:login|vendor|admin)[^)]*\)\s*\n.*def .*login\(.*?\).*?\n(?:    .*\n)*?\n'
        
        # শুধু unified login রাখুন, বাকিগুলো রিমুভ করুন
        def replace_func(match):
            if login_to_keep in match.group(0):
                return match.group(0)  # এইটা রাখুন
            return ''  # বাকিগুলো ডিলেট
        
        new_content = re.sub(pattern_all, replace_func, content, flags=re.DOTALL | re.IGNORECASE)
        return new_content
    
    return content

# মূল ফাইল পড়ুন
with open('app.py', 'r') as f:
    content = f.read()

print("="*50)
print("BEFORE CLEANUP - Login routes found:")
print("="*50)

# কি আছে দেখুন
import re
login_routes = re.findall(r'@app\.route\([^)]*login[^)]*\)', content, re.IGNORECASE)
for route in login_routes:
    print(f"  - {route}")

print("\n" + "="*50)
print("Starting cleanup...")
print("="*50)

# প্রথমে remove_login_functions ব্যবহার করুন
cleaned_content = remove_login_functions(content)

# তারপর keep_only_one_login ব্যবহার করুন
final_content = keep_only_one_login(cleaned_content)

# নতুন ফাইলে সেভ করুন
with open('app.py.cleaned', 'w') as f:
    f.write(final_content)

print("\n" + "="*50)
print("AFTER CLEANUP - Login routes found:")
print("="*50)

# কি আছে দেখুন
login_routes = re.findall(r'@app\.route\([^)]*login[^)]*\)', final_content, re.IGNORECASE)
for route in login_routes:
    print(f"  - {route}")

print("\n" + "="*50)
print("Cleanup complete!")
print("New file: app.py.cleaned")
print("To apply changes: mv app.py.cleaned app.py")
print("="*50)
