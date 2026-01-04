import sqlite3

# Define the correct home function code
correct_home_code = """
@app.route('/')
def home():
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    if 'user_id' in session:
        cursor.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if user:
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'vendor':
                return redirect(url_for('vendor_dashboard'))

    cursor.execute("SELECT * FROM products WHERE visible = 1")
    products = cursor.fetchall()
    return render_template('templates_index.html', products=products)
"""

with open('app.py', 'r') as f:
    lines = f.readlines()

# Find and replace the home function carefully
new_lines = []
skip = False
for line in lines:
    if line.strip().startswith("@app.route('/')"):
        new_lines.append(correct_home_code)
        skip = True
    elif skip and (line.startswith("@app.route") or (line.strip() == "" and len(new_lines) > 0 and "@app.route" in new_lines[-1])):
        skip = False
        if line.strip().startswith("@app.route"):
            new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Indentation fixed successfully!")
