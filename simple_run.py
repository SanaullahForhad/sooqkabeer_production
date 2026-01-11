from flask import Flask, render_template
import os

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    # টেমপ্লেট আছে কিনা চেক করুন
    template_path = os.path.join(app.template_folder, 'index.html')
    if os.path.exists(template_path):
        return render_template('index.html')
    else:
        return f"টেমপ্লেট খুঁজে পাওয়া যাচ্ছে না: {template_path}"

if __name__ == '__main__':
    print("টেমপ্লেট ফোল্ডার:", app.template_folder)
    app.run(debug=True)
