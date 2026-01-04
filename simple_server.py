from flask import Flask, send_file, send_from_directory
import os
import sqlite3

app = Flask(__name__)

# সরাসরি ইমেজ সার্ভ করুন
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

# হোমপেজ
@app.route('/')
def home():
    return '''
    <h1>سوق كبير - Souk Kabir</h1>
    <p>🇰🇼 Kuwait Fresh Food Marketplace</p>
    <hr>
    <h3>ইমেজ টেস্ট:</h3>
    <ul>
        <li><a href="/apple.jpg">Apple Image</a></li>
        <li><a href="/banana.jpg">Banana Image</a></li>
        <li><a href="/dates.jpg">Dates Image</a></li>
        <li><a href="/saffron.jpg">Saffron Image</a></li>
    </ul>
    <hr>
    <h3>পেজ টেস্ট:</h3>
    <ul>
        <li><a href="/vendors">Vendors</a></li>
        <li><a href="/offers/discount">Discount</a></li>
        <li><a href="/category/1">Category 1</a></li>
    </ul>
    '''

# অন্যান্য রুট
@app.route('/vendors')
def vendors():
    return "<h2>Vendors Page</h2><p>Coming soon</p>"

@app.route('/offers/discount')
def discount():
    return "<h2>Discount Offers</h2><p>Coming soon</p>"

@app.route('/category/<int:cat_id>')
def category(cat_id):
    return f"<h2>Category {cat_id}</h2><p>Products will be shown here</p>"

if __name__ == '__main__':
    print("="*60)
    print("🚀 Simple Server Starting...")
    print("📡 http://127.0.0.1:8082")
    print("🌐 http://10.84.179.168:8082")
    print("="*60)
    app.run(host='0.0.0.0', port=8082, debug=True)
