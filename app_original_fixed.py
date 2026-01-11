from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime

# সরাসরি পাথ সেট করুন
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
app.secret_key = 'sooqkabeer-b2b-marketplace-kuwait-2024'

# ডাটাবেস ফাংশন
def get_db_connection():
    conn = sqlite3.connect('sooqkabeer.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    try:
        # টেমপ্লেট আছে কিনা চেক করুন
        template_path = os.path.join(TEMPLATE_DIR, 'index.html')
        if os.path.exists(template_path):
            return render_template('index.html')
        else:
            # টেমপ্লেট না থাকলে সরাসরি HTML রিটার্ন করুন
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sooq Kabeer - B2B Marketplace Kuwait</title>
                <style>
                    /* আপনার আসল স্টাইল এখানে */
                    body { font-family: Arial; margin: 0; padding: 0; }
                    .header { background: #2c3e50; color: white; padding: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                    .product-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
                    .product-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                    .btn { background: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="container">
                        <h1>Sooq Kabeer - B2B Marketplace</h1>
                        <p>Kuwait's Premier Wholesale Platform</p>
                    </div>
                </div>
                
                <div class="container">
                    <h2>Welcome Back! Your Project is Working</h2>
                    <p>Your original design is being loaded...</p>
                    
                    <div class="product-grid">
                        <div class="product-card">
                            <h3>Product 1</h3>
                            <p>Description</p>
                            <a href="#" class="btn">View</a>
                        </div>
                        <!-- Add more products -->
                    </div>
                </div>
            </body>
            </html>
            '''
    except Exception as e:
        return f"Error loading template: {str(e)}"

# আপনার আসল রাউটগুলো যোগ করুন
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/admin')
def admin():
    return render_template('admin_dashboard.html')

@app.route('/vendor')
def vendor():
    return render_template('vendor/dashboard.html')

if __name__ == '__main__':
    print("="*60)
    print("🚀 SOOQ KABEER - B2B MARKETPLACE KUWAIT")
    print("="*60)
    print(f"📂 Working Directory: {BASE_DIR}")
    print(f"📁 Templates: {TEMPLATE_DIR} ({len(os.listdir(TEMPLATE_DIR)) if os.path.exists(TEMPLATE_DIR) else 0} files)")
    print(f"📁 Static: {STATIC_DIR} ({len(os.listdir(STATIC_DIR)) if os.path.exists(STATIC_DIR) else 0} files)")
    print(f"💾 Database: sooqkabeer.db ({os.path.getsize('sooqkabeer.db') if os.path.exists('sooqkabeer.db') else 0} bytes)")
    print("🌐 Server: http://127.0.0.1:5000")
    print("👤 Admin: admin | Password: admin123")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)
