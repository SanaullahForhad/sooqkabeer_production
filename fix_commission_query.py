with open('app.py', 'r') as f:
    lines = f.readlines()

# Find admin_commissions function
for i, line in enumerate(lines):
    if 'def admin_commissions' in line:
        # Find the cursor.execute lines
        for j in range(i, min(i+30, len(lines))):
            if "cursor.execute('''" in lines[j] or 'cursor.execute("""' in lines[j]:
                # Replace with simple query
                lines[j] = '    cursor.execute("SELECT * FROM commissions ORDER BY created_at DESC")\n'
                break
        break

with open('app.py', 'w') as f:
    f.writelines(lines)

print("✅ Simplified commissions query")
