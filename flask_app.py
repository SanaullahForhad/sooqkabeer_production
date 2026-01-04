from flask import Flask, send_file, render_template, send_from_directory
import os
import sqlite3

app = Flask(__name__, static_folder='.', static_url_path='')

# সরাসরি ইমেজ সার্ভ
@app.route('/apple.jpg')
def apple():
    return send_file('static/images/products/apple.jpg')

@app.route('/banana.jpg')
def banana():
    return send_file('static/images/products/banana.jpg')

@app.route('/dates.jpg')
def dates():
    return send_file('static/images/products/dates.jpg')

@app.route('/saffron.jpg')
def saffron():
    return send_file('static/images/products/saffron.jpg')

# Static files
@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# হোমপেজ
@app.route('/')
def home():
    return render_template('index.html')

# অন্যান্য পেজ
@app.route('/<page>')
def show_page(page):
    pages = {
        'vendors': 'البائعون',
        'login': 'تسجيل الدخول',
        'register': 'تسجيل جديد',
        'referral': 'الربح من الإحالة'
    }
    if page in pages:
        return f"<h1>{pages[page]}</h1><p>هذه الصفحة تحت التطوير</p><a href='/'>العودة</a>"
    return "الصفحة غير موجودة", 404

if __name__ == '__main__':
    print("="*60)
    print("🚀 سوق كبير - Souk Kabir")
    print("="*60)
    print("🌐 الموقع: http://10.84.179.168:8080")
    print("💻 محلي: http://127.0.0.1:8080")
    print("🇰🇼 الكويت - سوق الطعام الطازج")
    print("💬 اللغة: العربية | الإنجليزية | البنغالية")
    print("="*60)
    app.run(host='0.0.0.0', port=8080, debug=True)
