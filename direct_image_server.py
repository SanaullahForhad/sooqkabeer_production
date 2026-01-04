from flask import Flask, send_file, send_from_directory
import os

app = Flask(__name__)

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

@app.route('/static/images/products/<filename>')
def product_images(filename):
    return send_from_directory('static/images/products', filename)

@app.route('/static/images/<filename>')
def static_images(filename):
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    print("🖼️ Image server running on http://127.0.0.1:8081")
    app.run(port=8081, debug=True)
