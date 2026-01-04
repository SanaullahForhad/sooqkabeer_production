from flask import Flask
import sys

# ডিবাগ মোডে অ্যাপ তৈরি
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sooqkabeer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'debug-secret-key-123'
app.debug = True

# মডেলস ইম্পোর্ট
print("মডেলস লোড করার চেষ্টা করছি...")
try:
    from models import db, Admin, Vendor, Product
    db.init_app(app)
    
    with app.app_context():
        # ডাটাবেস তৈরি
        db.create_all()
        print("✅ ডাটাবেস টেবিল তৈরি করা হয়েছে")
        
        # ডিফল্ট অ্যাডমিন তৈরি (যদি না থাকে)
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            from models import Admin
            admin = Admin(
                username='admin',
                password='admin123',  # পরে হ্যাশ করতে হবে
                email='admin@sooqkabeer.com'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ ডিফল্ট অ্যাডমিন ইউজার তৈরি করা হয়েছে")
        
        print(f"✅ মোট অ্যাডমিন: {Admin.query.count()}")
        print(f"✅ মোট ভেন্ডর: {Vendor.query.count()}")
        print(f"✅ মোট প্রোডাক্ট: {Product.query.count()}")
        
except Exception as e:
    print(f"❌ এরর: {e}")
    import traceback
    traceback.print_exc()

# রাউট ডিফাইন
@app.route('/debug-test')
def debug_test():
    return "✅ ডিবাগ পেজ কাজ করছে!"

@app.route('/')
def home():
    return "✅ হোমপেজ কাজ করছে!"

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ডিবাগ সার্ভার শুরু হচ্ছে...")
    print("URL: http://localhost:8080")
    print("ডিবাগ পেজ: http://localhost:8080/debug-test")
    print("অ্যাডমিন: http://localhost:8080/admin/login")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8080, debug=True)
