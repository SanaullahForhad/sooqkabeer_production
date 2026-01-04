with open('app.py', 'r') as f:
    content = f.read()

# Find and fix the broken SQL block
import re
pattern = r'cursor\.execute\("SELECT \* FROM commissions ORDER BY created_at DESC"\)\n    # Calculate summary statistics for commissions\n    cursor\.execute\(\'\'\'\n        SELECT\n            SUM\(CASE WHEN status = \'pending\' THEN amount ELSE 0 END\) as pending_total,\n            SUM\(CASE WHEN status = \'paid\' THEN amount ELSE 0 END\) as paid_total,\n            COUNT\(\*\) as total_commissions\n    commissions = cursor\.fetchall\(\).*?\n        FROM commissions\n    \'\'\'\)'

fixed_block = '''cursor.execute("SELECT * FROM commissions ORDER BY created_at DESC")
    commissions = cursor.fetchall()

    # Calculate summary statistics for commissions
    cursor.execute(\'''
        SELECT
            SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_total,
            SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as paid_total,
            COUNT(*) as total_commissions
        FROM commissions
    \''')'''

content = re.sub(pattern, fixed_block, content, flags=re.DOTALL)

with open('app.py', 'w') as f:
    f.write(content)

print('✅ Fixed broken SQL block')
