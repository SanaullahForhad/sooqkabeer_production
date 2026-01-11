from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = 'sooqkabeer-b2b-marketplace'

# Database connection
def get_db():
    conn = sqlite3.connect('sooqkabeer.db')
    conn.row_factory = sqlite3.Row
    return conn

# Your original routes from app_before_login_fix.py
@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {str(e)}<br>Template path: {app.template_folder}"

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Your login logic here
        return redirect('/')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Your registration logic here
        return redirect('/login')
    return render_template('register.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/admin')
def admin():
    return render_template('admin_panel.html')

@app.route('/vendor')
def vendor():
    return render_template('vendor/dashboard.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

if __name__ == '__main__':
    print("="*70)
    print("🚀 SOOQ KABEER - YOUR ORIGINAL DESIGN")
    print("="*70)
    print(f"📁 Templates: {len(os.listdir('templates')) if os.path.exists('templates') else 0} files")
    print(f"📁 Static: {len(os.listdir('static')) if os.path.exists('static') else 0} files")
    print(f"📊 Database: sooqkabeer.db")
    print("🌐 Open: http://127.0.0.1:5000")
    print("="*70)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
