import re

with open('app.py', 'r') as f:
    content = f.read()

# সরল query (যেহেতু customer_name কলাম এখন আছে)
new_query = """    recent_orders = db.execute('''
        SELECT id, user_id, customer_name, total_price, status, created_at
        FROM orders
        ORDER BY created_at DESC LIMIT 5
    ''').fetchall()"""

# admin_dashboard এর ভেতরকার ভুল কুয়েরি পরিবর্তন করার লজিক
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    if 'recent_orders = db.execute' in lines[i] and 'admin_dashboard' in '\n'.join(lines[max(0,i-10):i]):
        new_lines.append(new_query)
        # পুরনো মাল্টি-লাইন কুয়েরি স্কিপ করা হচ্ছে
        while i < len(lines) and "fetchall()" not in lines[i]:
            i += 1
        i += 1 
    else:
        new_lines.append(lines[i])
        i += 1

with open('app.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("#=== SUCCESS: Recent orders query has been fixed! ===#")
