#!/bin/bash

echo "🚀 SooqKabeer Kuwait - Complete Installation"
echo "============================================"

# Create virtual environment
echo "1. Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "2. Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "3. Installing requirements..."
pip install -r requirements.txt

# Create database directory
echo "4. Creating database directory..."
mkdir -p database backups static/uploads

# Run the application
echo "5. Starting application..."
echo ""
echo "============================================"
echo "🌐 Application URL: http://127.0.0.1:8080"
echo "👨‍💼 Admin Panel: http://127.0.0.1:8080/admin/login"
echo "🔑 Username: admin | Password: admin123"
echo "============================================"
echo ""

python app.py
