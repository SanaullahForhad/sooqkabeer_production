import re

with open('app.py', 'r') as f:
    content = f.read()

# admin_dashboard ফাংশনের অগোছালো অংশটি রিপ্লেস করার জন্য
pattern = r"@app\.route\('/admin/dashboard'\)\ndef admin_dashboard\(\):[\s\S]*?return render_template\('admin/admin_dashboard\.html'[\s\S]*?\)"

new_function = """@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    total_products = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    try:
        comm_row = db.execute('SELECT SUM(commission_amount) FROM commissions').fetchone()
        total_commissions = comm_row[0] if comm_row and comm_row[0] is not None else 0.0
    except Exception as e:
        total_commissions = 0.0
    
    # Updated Clean Query
    recent_orders = db.execute('''
        SELECT id, user_id, total_price, status, created_at
        FROM orders
        ORDER BY created_at DESC LIMIT 5
    ''').fetchall()
    
    return render_template('admin/admin_dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_commissions=total_commissions,
                           recent_orders=recent_orders)"""

new_content = re.sub(pattern, new_function, content)

with open('app.py', 'w') as f:
    f.write(new_content)
print("#=== DASHBOARD CLEANED AND FIXED! ===#")
