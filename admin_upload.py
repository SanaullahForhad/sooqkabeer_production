from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.secret_key = 'your-secret-key-here'

# Admin route
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST':
        # Check if file is uploaded
        if 'image' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['image']
        product_name = request.form.get('product_name', '').strip()
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file:
            # Create filename
            if product_name:
                filename = f"{product_name.lower().replace(' ', '_')}.jpg"
            else:
                filename = file.filename
            
            # Save file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Create link in main images folder
            link_path = os.path.join('static/images', filename)
            if os.path.exists(link_path):
                os.remove(link_path)
            os.symlink(f'products/{filename}', link_path)
            
            flash(f'Image uploaded: {filename}')
            return redirect(url_for('admin_upload'))
    
    # Get list of existing images
    images = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        images = os.listdir(app.config['UPLOAD_FOLDER'])
    
    return render_template('admin_upload.html', images=images)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
