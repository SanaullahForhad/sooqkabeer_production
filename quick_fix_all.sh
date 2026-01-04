#!/bin/bash

echo "🛠️ সব সমস্যা ফিক্স করা হচ্ছে..."

# 1. টেমপ্লেট ফোল্ডার তৈরি
mkdir -p templates/{admin,user,errors}

# 2. app.py এর backup নিন
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)

# 3. app.py-তে error handler যোগ করুন
if ! grep -q "@app.errorhandler(404)" app.py; then
    echo -e "\n# 404 Error Handler (Added by fix script)" >> app.py
    echo "@app.errorhandler(404)" >> app.py
    echo "def page_not_found(e):" >> app.py
    echo "    return render_template('errors/404.html'), 404" >> app.py
fi

# 4. commission রাউট চেক করুন
if ! grep -q "@app.route.*commission" app.py; then
    echo -e "\n# Commission Route (Added by fix script)" >> app.py
    echo "@app.route('/admin/commissions')" >> app.py
    echo "def commissions():" >> app.py
    echo "    return render_template('admin/commission.html')" >> app.py
fi

# 5. user dashboard রাউট চেক করুন
if ! grep -q "@app.route.*user/dashboard" app.py; then
    echo -e "\n# User Dashboard Route (Added by fix script)" >> app.py
    echo "@app.route('/user/dashboard')" >> app.py
    echo "def user_dashboard():" >> app.py
    echo "    return render_template('user/dashboard.html')" >> app.py
fi

echo "✅ সব ফিক্স সম্পূর্ণ!"
echo "📋 পরবর্তী ধাপ: python app.py চালান"
