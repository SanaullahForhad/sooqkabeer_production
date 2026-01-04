#!/usr/bin/env python3

# app.py ফাইলে রাউট যোগ করি
app_file = 'app.py'

# ফাইল পড়ুন
with open(app_file, 'r') as f:
    lines = f.readlines()

# নতুন রাউটগুলো
new_routes = '''
# ভেন্ডর পেইজ
@app.route('/vendors')
def vendors_page():
    return render_template('vendors.html')

# কমিশন ডিস্ট্রিবিউশন পেইজ
@app.route('/admin/commission-distribution')
def commission_distribution():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin/commission_distribution.html')

# প্রোডাক্ট পেইজ
@app.route('/products')
def products_page():
    return "صفحة المنتجات قريباً..."  # পরে টেমপ্লেট যোগ করবেন

# রেজিস্ট্রেশন
@app.route('/register')
def register():
    return "صفحة التسجيل قريباً..."

# কন্টাক্ট
@app.route('/contact')
def contact():
    return "صفحة الاتصال قريباً..."

# এবাউট
@app.route('/about')
def about():
    return "صفحة من نحن قريباً..."
'''

# রাউট যোগ করার জায়গা খুঁজুন
for i, line in enumerate(lines):
    if '@app.route' in line and '/user/dashboard' in line:
        # এই লাইনের পরেই নতুন রাউট যোগ করুন
        lines.insert(i + 1, new_routes)
        break

# ফাইল লেখ
with open(app_file, 'w') as f:
    f.writelines(lines)

print("✅ নতুন রাউট যোগ করা হয়েছে")
print("📌 /vendors - ভেন্ডর তালিকা")
print("📌 /admin/commission-distribution - কমিশন ডিস্ট্রিবিউশন")
print("📌 /products - প্রোডাক্টস")
print("📌 /register - রেজিস্ট্রেশন")
print("📌 /contact - যোগাযোগ")
print("📌 /about - আমাদের সম্পর্কে")
