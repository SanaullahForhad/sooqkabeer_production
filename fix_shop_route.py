with open('app.py', 'r') as f:
    lines = f.readlines()

# লাইন 807 (0-based index 806) খুঁজে বের করুন
for i in range(len(lines)):
    if '@app.route(\'/shop\')' in lines[i] or 'def shop()' in lines[i]:
        # ভুল লাইন মুছে ফেলুন
        del lines[i:i+8]  # 8 লাইন মুছুন
        break

# সঠিকভাবে shop রুট যোগ করুন
new_route = '''# Shop route - redirects to products
@app.route('/shop')
def shop():
    return redirect(url_for('products'))

'''

# products ফাংশনের পরে যোগ করুন
for i in range(len(lines)):
    if 'def products(' in lines[i]:
        # products ফাংশনের শেষ খুঁজুন
        j = i
        while j < len(lines) and lines[j].strip() != '':
            j += 1
        # নতুন রুট যোগ করুন
        lines.insert(j, '\n' + new_route)
        break

with open('app.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed indentation and added shop route correctly")
