import hashlib

login_code = """
#=== INTERNATIONAL LOGIN ROUTE ===#
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email') or request.form.get('username')
        password = request.form.get('password', '')
        if not login_input or not password:
            flash('Please provide both email/username and password', 'warning')
            return render_template('login.html')
        salt = "sooqkabeer_salt_"
        hashed_pw = hashlib.sha256((salt + password).encode()).hexdigest()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? OR username = ?', (login_input, login_input)).fetchone()
        if user and user['password'] == hashed_pw:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['vendor_id_code'] = user.get('vendor_id_code', '')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] in ['vendor', 'referrer']:
                return redirect(url_for('vendor_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
"""

with open('app.py', 'r') as f:
    lines = f.readlines()

# Find the best place (after Flask app initialization)
insert_pos = 0
for i, line in enumerate(lines):
    if 'app = Flask(__name__)' in line:
        insert_pos = i + 1
        break

if insert_pos > 0:
    lines.insert(insert_pos, login_code)
    with open('app.py', 'w') as f:
        f.writelines(lines)
    print("#=== SUCCESS: Login route added after app init! ===#")
else:
    print("#=== ERROR: Could not find app init line! ===#")
