from app import app
from models import db, Vendor, User
from datetime import datetime

with app.app_context():
    # আপনার ভেন্ডরকে খুঁজে বের করা
    vendor = Vendor.query.filter_by(vendor_code='HKO-001').first()
    
    if vendor:
        # এখানে যে ডাটাগুলো বাদ আছে সেগুলো সেট করুন
        vendor.phone = "+96512345678"
        vendor.nationality = "Bangladeshi"
        vendor.address = "Kuwait City, Al Asimah"
        vendor.business_type = "Retail"
        vendor.governorate = "Al Asimah"
        vendor.status = "active" # প্রোফাইল একটিভ করা
        
        db.session.commit()
        print("✅ Vendor profile (HKO-001) updated with missing data!")
    else:
        print("❌ Vendor not found! Please register first.")

