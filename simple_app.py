from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>SooqKabeer - Working!</h1>
    <ul>
        <li><a href="/admin/login">Admin</a></li>
        <li><a href="/referral">Referral</a></li>
        <li><a href="/user/dashboard">User Dashboard</a></li>
        <li><a href="/vendor/login">Vendor Login</a></li>
    </ul>
    '''

@app.route('/admin/login')
def admin():
    return "<h1>Admin Login</h1>"

@app.route('/referral')
def referral():
    return "<h1>Referral Program</h1>"

@app.route('/user/dashboard')
def user():
    return "<h1>User Dashboard</h1>"

@app.route('/vendor/login')
def vendor():
    return "<h1>Vendor Login</h1>"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
