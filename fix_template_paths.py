import re

with open('app.py', 'r') as f:
    content = f.read()

# admin টেমপ্লেট পাথগুলো আপডেট করুন
replacements = [
    ('render_template\(\s*[\'"](admin_users.html)[\'"]', 'admin/users.html'),
    ('render_template\(\s*[\'"](admin_commissions.html)[\'"]', 'admin/admin_commissions.html'),
    ('render_template\(\s*[\'"](admin_withdrawals.html)[\'"]', 'admin/admin_withdrawals.html'),
    ('render_template\(\s*[\'"](admin_settings.html)[\'"]', 'admin/admin_settings.html'),
    ('render_template\(\s*[\'"](admin_messages.html)[\'"]', 'admin/admin_messages.html'),
    ('render_template\(\s*[\'"](admin_reports.html)[\'"]', 'admin/admin_reports.html'),
    ('render_template\(\s*[\'"](admin\/dashboard.html)[\'"]', 'admin/admin_dashboard.html'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, f"render_template('{replacement}'", content)

with open('app.py', 'w') as f:
    f.write(content)

print("টেমপ্লেট পাথগুলো আপডেট করা হয়েছে")
