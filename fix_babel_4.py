import sys

with open('app.py', 'r') as f:
    lines = f.readlines()

# লাইন 228 (0-indexed 227) - ডেকোরেটর লাইন
if len(lines) > 227 and '@babel.localeselector' in lines[227]:
    # ডেকোরেটর লাইনটি মুছুন
    lines[227] = ''
    
    # get_locale ফাংশন খুঁজুন
    for i in range(228, len(lines)):
        if 'def get_locale' in lines[i]:
            func_start = i
            break
    
    # ফাংশনের শেষ খুঁজুন (indentation ভাঙ্গা পর্যন্ত)
    for j in range(func_start + 1, len(lines)):
        if lines[j].strip() == '' or (not lines[j].startswith('    ') and not lines[j].startswith('\t')):
            func_end = j
            break
    
    # babel.init_app কল যোগ করুন ফাংশনের পর
    lines.insert(func_end, '\n# Initialize Babel with locale selector\n')
    lines.insert(func_end + 1, 'babel.init_app(app, locale_selector=get_locale)\n')
    break

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Flask-Babel 4.x এর জন্য কোড আপডেট করা হয়েছে")
