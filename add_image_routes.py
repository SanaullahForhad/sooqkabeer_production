import os

# Read current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if image routes already exist
if '@app.route(\'/apple.jpg\')' in content:
    print("Image routes already exist in app.py")
else:
    # Add image routes before the if __name__ == '__main__' line
    if 'if __name__ == \'__main__\':' in content:
        # Add routes before this line
        image_routes = '''
# ==========================================================
# IMAGE ROUTES - FIXED
# ==========================================================

@app.route('/apple.jpg')
def apple_image():
    """Serve apple image"""
    image_path = 'static/images/products/apple.jpg'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return send_file('static/images/default_product.jpg', mimetype='image/jpeg')

@app.route('/banana.jpg')
def banana_image():
    """Serve banana image"""
    image_path = 'static/images/products/banana.jpg'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return send_file('static/images/default_product.jpg', mimetype='image/jpeg')

@app.route('/dates.jpg')
def dates_image():
    """Serve dates image"""
    image_path = 'static/images/products/dates.jpg'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return send_file('static/images/default_product.jpg', mimetype='image/jpeg')

@app.route('/saffron.jpg')
def saffron_image():
    """Serve saffron image"""
    image_path = 'static/images/products/saffron.jpg'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return send_file('static/images/default_product.jpg', mimetype='image/jpeg')

@app.route('/offers/<filename>.jpg')
def offer_image(filename):
    """Serve images for offers pages"""
    image_path = f'static/images/products/{filename}.jpg'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    return send_file('static/images/default_product.jpg', mimetype='image/jpeg')

'''
        
        # Insert before if __name__ == '__main__':
        parts = content.split('if __name__ == \'__main__\':')
        if len(parts) == 2:
            new_content = parts[0] + image_routes + '\nif __name__ == \'__main__\':' + parts[1]
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ Image routes added to app.py")
        else:
            print("❌ Could not find if __name__ == '__main__': in app.py")
