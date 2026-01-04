#!/usr/bin/env python3
"""
SooqKabeer Permanent Server Solution
This script will always find an available port and start the server
"""

import os
import sys
import socket
import subprocess
import time
import signal

def find_free_port(start_port=3000, end_port=9000):
    """Find a free port between start_port and end_port"""
    for port in range(start_port, end_port + 1):
        try:
            # Try to create a socket to check if port is free
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:  # Port is free
                return port
        except:
            continue
    return 8080  # Fallback port

def kill_existing_servers():
    """Kill any existing Python/Flask servers"""
    try:
        # Kill processes using ports 3000-9000
        os.system("pkill -f 'python.*app.py' 2>/dev/null")
        os.system("pkill -f 'flask' 2>/dev/null")
        time.sleep(2)
    except:
        pass

def backup_database():
    """Create backup of database"""
    import datetime
    if os.path.exists('sooqkabeer.db'):
        backup_name = f"backups/sooqkabeer_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.makedirs('backups', exist_ok=True)
        os.system(f"cp sooqkabeer.db {backup_name}")
        print(f"📦 Database backed up: {backup_name}")

def main():
    print("🚀 SooqKabeer Server - Permanent Solution")
    print("=" * 50)
    
    # Step 1: Kill existing servers
    print("🔧 Stopping existing servers...")
    kill_existing_servers()
    
    # Step 2: Backup database
    print("💾 Creating database backup...")
    backup_database()
    
    # Step 3: Find free port
    port = find_free_port()
    print(f"🔍 Found free port: {port}")
    
    # Step 4: Start server
    print(f"🌐 Starting server on port {port}...")
    print(f"   Admin: http://127.0.0.1:{port}/admin/login")
    print(f"   Register: http://127.0.0.1:{port}/register")
    print(f"   Home: http://127.0.0.1:{port}/")
    print("\n📢 Press Ctrl+C to stop the server\n")
    
    # Start Flask server
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    os.system(f"python app.py --host=127.0.0.1 --port={port}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
