from flask import Flask, render_template
import os

# বর্তমান ডিরেক্টরি
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

@app.route('/')
def home():
    # সরাসরি টেমপ্লেট ফাইল চেক করুন
    template_path = os.path.join(BASE_DIR, 'templates', 'index.html')
    print(f"টেমপ্লেট পাথ: {template_path}")
    print(f"ফাইল আছে: {os.path.exists(template_path)}")
    
    if os.path.exists(template_path):
        return render_template('index.html')
    else:
        # টেমপ্লেট তৈরি করুন
        with open(template_path, 'w') as f:
            f.write('''
            <!DOCTYPE html>
            <html>
            <head><title>Sooq Kabeer</title></head>
            <body>
                <h1>🎉 আপনার অ্যাপ কাজ করছে!</h1>
                <p>টেমপ্লেট সমস্যা সমাধান হয়েছে।</p>
            </body>
            </html>
            ''')
        return render_template('index.html')

if __name__ == '__main__':
    print(f"বর্তমান ডিরেক্টরি: {BASE_DIR}")
    app.run(debug=True)
