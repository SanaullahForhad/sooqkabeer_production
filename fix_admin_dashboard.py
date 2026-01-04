with open('app.py', 'r') as f:
    lines = f.readlines()

# লাইন 1630 (0-indexed 1629) খুঁজে বের করুন
for i in range(len(lines)):
    if i > 1625 and i < 1640 and 'recent_orders = db.execute' in lines[i]:
        # পরের কয়েক লাইন পাওয়া পর্যন্ত
        query_start = i
        query_lines = []
        j = i
        while j < len(lines) and "'''" not in lines[j] and "fetchall()" not in lines[j]:
            query_lines.append(lines[j])
            j += 1
        if j < len(lines):
            query_lines.append(lines[j])
        
        # নতুন query
        new_query = '''    recent_orders = db.execute(\'\'\'
        SELECT o.id, o.user_id, COALESCE(u.username, u.email, \\'Customer\\') as customer_name, o.total_price, o.status, o.created_at
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 5
    \'\'\').fetchall()'''
        
        lines[i] = new_query + '\\n'
        # পরের লাইনগুলো মুছুন (যদি একাধিক লাইন হয়)
        for k in range(i+1, j+1):
            if k < len(lines):
                lines[k] = ''
        break

with open('app.py', 'w') as f:
    f.writelines(lines)

print("admin_dashboard ফাংশনের query ঠিক করা হয়েছে")
