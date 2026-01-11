#!/usr/bin/env python3
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Sooq Kabeer B2B Marketplace starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)
