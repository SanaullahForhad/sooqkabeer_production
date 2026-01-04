#!/bin/bash

echo "🔄 অ্যাপ্লিকেশন চেক করা হচ্ছে..."

# টেমপ্লেট চেক
if [ ! -f "templates/index.html" ]; then
    echo "❌ templates/index.html নেই"
    exit 1
fi

# app.py চেক
if [ ! -f "app.py" ]; then
    echo "❌ app.py নেই"
    exit 1
fi

# ডাটাবেস চেক
if [ -f "sooqkabeer.db" ]; then
    echo "✅ ডাটাবেস ফাইল আছে (পুরাতন ডাটা সংরক্ষিত)"
else
    echo "⚠️  নতুন ডাটাবেস তৈরি হবে"
fi

echo ""
echo "🚀 SooqKabeer Kuwait চালু হচ্ছে..."
echo "=" * 50
echo "🌐 URL: http://127.0.0.1:8080"
echo "👨‍💼 Admin: http://127.0.0.1:8080/admin/login"
echo "🔑 Username: admin | Password: admin123"
echo "🏪 Vendors: http://127.0.0.1:8080/vendors"
echo "=" * 50
echo ""

python app.py
