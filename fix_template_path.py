import os

# ১. আপনার আসল app ফাইলটি পড়ুন
with open('app_before_login_fix.py', 'r') as f:
    content = f.read()

# ২. Flask app initialization খুঁজে বের করুন
if 'app = Flask(__name__)' in content:
    # টেমপ্লেট পাথ ঠিক করুন
    fixed_content = content.replace(
        'app = Flask(__name__)',
        '''import os
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
           static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))'''
    )
    
    # ফাইল সেভ করুন
    with open('app_before_login_fix_fixed.py', 'w') as f:
        f.write(fixed_content)
    
    print("✅ app_before_login_fix_fixed.py ফাইল তৈরি হয়েছে")
    print("📁 টেমপ্লেট ফোল্ডার: templates/")
    print("📁 স্ট্যাটিক ফোল্ডার: static/")
    
else:
    print("❌ Flask app initialization খুঁজে পাওয়া যায়নি")
