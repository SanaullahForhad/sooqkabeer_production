import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    print("✅ app module imported successfully")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Current Python path:", sys.path)
    exit(1)

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Sooq Kabeer...")
    app.run(debug=True)
