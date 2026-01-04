with open('app.py', 'r') as f:
    content = f.read()

# ভুল SQL ঠিক করুন
correct_sql = '''    cursor.execute("""
        SELECT *,
               stock_quantity AS stock,
               visible AS is_active
        FROM products
        ORDER BY id DESC
    """)'''

# খারাপ SQL খুঁজে replace করুন
import re
pattern = r'cursor\.execute\("""[\s\S]*?"""\)'
content = re.sub(pattern, correct_sql, content, count=1)

with open('app.py', 'w') as f:
    f.write(content)

print("✅ Fixed SQL query")
