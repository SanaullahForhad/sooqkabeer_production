import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Now import your original app
from app_before_login_fix import app

if __name__ == '__main__':
    app.run(debug=True)
