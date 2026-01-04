#=== Database Schema Upgrade: Financial Security & Vendor IDs ===#
import sqlite3
import hashlib
import secrets
import os
import shutil
from datetime import datetime

def create_backup():
    """Creates a safety backup before modifying database structure"""
    db_path = 'sooqkabeer.db'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('backups', exist_ok=True)
    backup_path = f'backups/sooqkabeer_backup_{timestamp}.db'
    try:
        shutil.copy2(db_path, backup_path)
        print(f"#=== STATUS: [BACKUP] Success: {backup_path} ===#")
        return True
    except Exception as e:
        print(f"#=== ERROR: [BACKUP] Failed: {str(e)} ===#")
        return False

def generate_vendor_id_code(username, vendor_id):
    """Generates a secure unique ID: VEN-USR-0001-XXXX"""
    prefix = "VEN"
    # Clean username for the code (first 3 chars)
    name_part = (username[:3] if username else "VND").upper().replace(" ", "X")
    serial_part = str(vendor_id).zfill(4)
    # 4 random hex characters for extra security
    random_part = secrets.token_hex(2).upper()
    return f"{prefix}-{name_part}-{serial_part}-{random_part}"

def update_database():
    db_path = 'sooqkabeer.db'
    conn = None
    try:
        print("#=== STATUS: [INIT] Starting Database Upgrade ===#")
        if not create_backup():
            print("#=== WARNING: [ABORT] Backup failed, update cancelled for safety. ===#")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Add vendor_id_code & vendor_verified if they don't exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'vendor_id_code' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN vendor_id_code TEXT")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_v_code ON users(vendor_id_code) WHERE vendor_id_code IS NOT NULL")
            print("#=== STATUS: [SCHEMA] Added vendor_id_code column. ===#")

        if 'vendor_verified' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN vendor_verified INTEGER DEFAULT 0")
            print("#=== STATUS: [SCHEMA] Added vendor_verified column. ===#")

        # 2. Generate codes for existing vendors (Mapping to 'username')
        cursor.execute("SELECT id, username FROM users WHERE role = 'vendor' AND (vendor_id_code IS NULL OR vendor_id_code = '')")
        existing_vendors = cursor.fetchall()
        
        for v_id, v_name in existing_vendors:
            v_code = generate_vendor_id_code(v_name, v_id)
            cursor.execute("UPDATE users SET vendor_id_code = ?, vendor_verified = 1 WHERE id = ?", (v_code, v_id))
            print(f"#=== DATA: Generated code {v_code} for Vendor ID {v_id} ===#")

        # 3. Create Transactions Table for financial logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'payout', 'commission', 'sale'
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                reference_no TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        print("#=== STATUS: [COMPLETE] Database updated successfully. ===#")

    except Exception as e:
        if conn: conn.rollback()
        print(f"#=== ERROR: [SYSTEM] {str(e)} ===#")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_database()

