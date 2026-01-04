with open('templates/category.html', 'r') as f:
    content = f.read()

# ভুল পাথ ঠিক করুন
content = content.replace(
    "this.src = '/static/images/default_product.jpg';",
    "this.src = '{{ url_for(\"static\", filename=\"images/products/default_product.jpg\") }}';"
)

# alternative ভুল পাথ
content = content.replace(
    '/static/images/default_product.jpg',
    "{{ url_for('static', filename='images/products/default_product.jpg') }}"
)

with open('templates/category.html', 'w') as f:
    f.write(content)

print("✅ Fixed category.html")
