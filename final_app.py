from flask import Flask, render_template
import os

# সরাসরি পাথ সেট করুন
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        # যদি টেমপ্লেট না থাকে, আসল app_before_login_fix.py ইম্পোর্ট করুন
        from app_before_login_fix import app as original_app
        return original_app

if __name__ == '__main__':
    print("চালু হচ্ছে... আপনার আসল ডিজাইন দেখানোর চেষ্টা করছি")
    app.run(debug=True)
