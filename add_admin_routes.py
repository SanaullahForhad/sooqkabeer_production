import re

# Read original file
with open('app.py', 'r') as f:
    content = f.read()

# Find where to insert admin routes (before test() function)
# Look for the test() function
test_func_pos = content.find('def test():')

if test_func_pos != -1:
    # Find the line before test() function
    # Go backwards to find the previous @app.route or function
    lines = content[:test_func_pos].split('\n')
    insert_pos = 0
    
    # Find the last empty line before test() to insert
    for i in range(len(lines)-1, 0, -1):
        if lines[i].strip() == '':
            insert_pos = i
            break
    
    # Admin routes code
    admin_routes = '''

# ==================== ADMIN ROUTES ====================

# Admin - Vendors Management
@app.route('/admin/vendors')
def admin_vendors():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vendors')
    vendors = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_vendors.html', 
                         vendors=vendors,
                         current_lang=current_lang)

# Admin - Referrals Management
@app.route('/admin/referrals')
def admin_referrals():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT u.name, u.email, u.phone, r.amount, r.created_at FROM referral_earnings r JOIN users u ON r.user_id = u.id')
    referrals = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_referrals.html',
                         referrals=referrals,
                         current_lang=current_lang)

# Admin - Products Management
@app.route('/admin/products')
def admin_products():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_products.html',
                         products=products,
                         current_lang=current_lang)

# Admin - Orders Management
@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders')
    orders = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_orders.html',
                         orders=orders,
                         current_lang=current_lang)

# Admin - Users Management
@app.route('/admin/users')
def admin_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('sooq.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_users.html',
                         users=users,
                         current_lang=current_lang)

# Admin - Settings
@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    current_lang = session.get('language', 'ar')
    return render_template('admin_settings.html',
                         current_lang=current_lang)

# Admin - Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

'''
    
    # Insert admin routes
    new_lines = lines[:insert_pos] + [admin_routes] + lines[insert_pos:]
    new_content = '\n'.join(new_lines)
    
    # Write to new file
    with open('app_new.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Admin routes added successfully!")
    print("New file: app_new.py")
else:
    print("Error: Could not find test() function")
