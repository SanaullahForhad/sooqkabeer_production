with open('app.py', 'r') as f:
    lines = f.readlines()

# Find admin_dashboard return statement
for i in range(len(lines)):
    if 'return render_template' in lines[i] and 'admin_dashboard.html' in lines[i]:
        # Fix the next 4 lines
        lines[i] = '    return render_template("admin/admin_dashboard.html",\n'
        lines[i+1] = '                         recent_orders=recent_orders,\n'
        lines[i+2] = '                         total_products=total_products,\n'
        lines[i+3] = '                         total_users=total_users,\n'
        lines[i+4] = '                         total_vendors=total_vendors)'
        break

with open('app.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed admin_dashboard indentation")
