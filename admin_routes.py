# ==================== ADMIN ROUTES ====================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_db()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_revenue = conn.execute('SELECT SUM(total_price) FROM orders WHERE status="completed"').fetchone()[0] or 0
    
    return render_template('admin_dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         total_revenue=total_revenue)

@app.route('/admin/products')
def admin_products():
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if 'admin' not in session:
        return redirect('/admin/login')
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        stock = request.form['stock']
        
        conn = get_db()
        conn.execute('INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)',
                    (name, price, category, stock))
        conn.commit()
        flash('Product added successfully', 'success')
        return redirect('/admin/products')
    
    return render_template('admin_add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_product(id):
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        stock = request.form['stock']
        
        conn.execute('UPDATE products SET name=?, price=?, category=?, stock=? WHERE id=?',
                    (name, price, category, stock, id))
        conn.commit()
        flash('Product updated successfully', 'success')
        return redirect('/admin/products')
    
    product = conn.execute('SELECT * FROM products WHERE id=?', (id,)).fetchone()
    return render_template('admin_edit_product.html', product=product)

@app.route('/admin/products/delete/<int:id>')
def admin_delete_product(id):
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id=?', (id,))
    conn.commit()
    flash('Product deleted successfully', 'success')
    return redirect('/admin/products')

@app.route('/admin/orders')
def admin_orders():
    if 'admin' not in session:
        return redirect('/admin/login')
    
    conn = get_db()
    orders = conn.execute('''
        SELECT orders.*, users.username, products.name 
        FROM orders 
        JOIN users ON orders.user_id = users.id 
        JOIN products ON orders.product_id = products.id 
        ORDER BY orders.order_date DESC
    ''').fetchall()
    
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/orders/update_status/<int:id>', methods=['POST'])
def update_order_status(id):
    if 'admin' not in session:
        return redirect('/admin/login')
    
    status = request.form['status']
    conn = get_db()
    conn.execute('UPDATE orders SET status=? WHERE id=?', (status, id))
    conn.commit()
    flash('Order status updated', 'success')
    return redirect('/admin/orders')
