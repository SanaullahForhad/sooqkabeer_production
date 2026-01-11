from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db():
    db = sqlite3.connect('database.db')
    return db

@app.route('/vendor/dashboard')
def vendor_dashboard():
    return "Vendor Dashboard - Welcome HKO-001"

@app.route('/vendor/add_product', methods=['GET', 'POST'])
def vendor_add_product():
    import sqlite3
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # ডাটাবেস এরর ফিক্স - টেবিল না থাকলে তৈরি করবে
    cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT, name_ar TEXT)")
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categories (name_en, name_ar) VALUES ('General', 'সাধারণ')")
    db.commit()

    if request.method == 'POST':
        try:
            # আপনার সেই অরিজিনাল লজিকগুলো এখানে ফিরিয়ে আনা হয়েছে
            name_en = request.form.get('name_en', '').strip()
            name_ar = request.form.get('name_ar', '').strip()
            desc_en = request.form.get('description_en', '').strip()
            desc_ar = request.form.get('description_ar', '').strip()
            price = float(request.form.get('price', 0))
            unit = request.form.get('unit', 'pcs').strip()
            category_id = request.form.get('category_id', '').strip()
            stock = float(request.form.get('stock_quantity', 0))
            image_url = request.form.get('image_url', 'default.jpg').strip()
            
            b2b_price = float(request.form.get('b2b_price') or price)
            min_qty = int(request.form.get('min_qty') or 1)
            vendor_id = session.get('user_id')

            if not all([name_en, name_ar, price, category_id]):
                flash('Please fill all required fields!', 'danger')
                categories = cursor.execute("SELECT id, name_ar FROM categories").fetchall()
                return render_template('vendor/add_product.html', categories=categories)

            sql = """INSERT INTO products 
                     (name_en, name_ar, description_en, description_ar, 
                      price, b2b_price, min_qty, unit, category_id, stock_quantity, 
                      image_url, vendor_id, status, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"""
            
            cursor.execute(sql, (name_en, name_ar, desc_en, desc_ar, price, b2b_price, min_qty, unit, category_id, stock, image_url, vendor_id, 'active'))
            db.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('vendor_dashboard'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'danger')

    # GET Request: ক্যাটাগরি লোড করা
    categories = cursor.execute("SELECT id, name_ar FROM categories").fetchall()
    return render_template('vendor/add_product.html', categories=categories)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
