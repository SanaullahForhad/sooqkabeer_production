import re

with open('app.py', 'r') as f:
    content = f.read()

# টেমপ্লেট পাথ ম্যাপিং
template_mapping = {
    'admin_users.html': 'admin/users.html',
    'admin_commissions.html': 'admin/admin_commissions.html',
    'admin_withdrawals.html': 'admin/admin_withdrawals.html',
    'admin_settings.html': 'admin/admin_settings.html',
    'admin_messages.html': 'admin/admin_messages.html',
    'admin_reports.html': 'admin/admin_reports.html'
}

for old_path, new_path in template_mapping.items():
    pattern = f"render_template\\(\\s*['\"]{re.escape(old_path)}['\"]"
    replacement = f"render_template('{new_path}'"
    content = re.sub(pattern, replacement, content)

with open('app.py', 'w') as f:
    f.write(content)

print("সব টেমপ্লেট পাথ ঠিক করা হয়েছে")
