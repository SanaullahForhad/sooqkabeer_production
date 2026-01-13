import sqlite3

def fix_vendors_table():
    conn = sqlite3.connect('sooqkabeer.db')
    cursor = conn.cursor()
    
    print("🔄 Fixing vendors table...")
    
    try:
        # 1. Add cr_number column (without UNIQUE first)
        cursor.execute("SELECT COUNT(*) FROM pragma_table_info('vendors') WHERE name='cr_number'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE vendors ADD COLUMN cr_number TEXT")
            print("✅ Added cr_number column")
        
        # 2. Create UNIQUE index for cr_number
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_vendors_cr_number'")
        if not cursor.fetchone():
            cursor.execute("CREATE UNIQUE INDEX idx_vendors_cr_number ON vendors(cr_number) WHERE cr_number IS NOT NULL")
            print("✅ Created UNIQUE index for cr_number")
        
        # 3. Copy data from old columns to new columns
        # Copy vendor_name to name
        cursor.execute("UPDATE vendors SET name = vendor_name WHERE name IS NULL OR name = ''")
        print(f"✅ Copied data from vendor_name to name: {cursor.rowcount} rows updated")
        
        # Copy password_hash to password
        cursor.execute("UPDATE vendors SET password = password_hash WHERE password IS NULL OR password = ''")
        print(f"✅ Copied data from password_hash to password: {cursor.rowcount} rows updated")
        
        # 4. Set default values for new columns
        # Set default status to 'pending' for new form
        cursor.execute("UPDATE vendors SET status = 'pending' WHERE status = 'active'")
        print(f"✅ Set status to 'pending': {cursor.rowcount} rows updated")
        
        # Set agree_terms to 'yes'
        cursor.execute("UPDATE vendors SET agree_terms = 'yes' WHERE agree_terms IS NULL OR agree_terms = 'no'")
        print(f"✅ Set agree_terms to 'yes': {cursor.rowcount} rows updated")
        
        # Set country_code
        cursor.execute("UPDATE vendors SET country_code = '+965' WHERE country_code IS NULL")
        print(f"✅ Set country_code to '+965': {cursor.rowcount} rows updated")
        
        # 5. Ensure name has values (NOT NULL constraint)
        cursor.execute("SELECT COUNT(*) FROM vendors WHERE name IS NULL OR name = ''")
        null_names = cursor.fetchone()[0]
        
        if null_names > 0:
            cursor.execute("UPDATE vendors SET name = email WHERE name IS NULL OR name = ''")
            print(f"✅ Fixed {null_names} null names")
        
        # 6. Check data integrity
        cursor.execute('''
            SELECT 
                COUNT(*) as total_vendors,
                SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as null_names,
                SUM(CASE WHEN password IS NULL OR password = '' THEN 1 ELSE 0 END) as null_passwords,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_vendors,
                SUM(CASE WHEN agree_terms = 'yes' THEN 1 ELSE 0 END) as agreed_terms
            FROM vendors
        ''')
        
        result = cursor.fetchone()
        print("\n📊 Data Integrity Report:")
        print(f"   Total vendors: {result[0]}")
        print(f"   Null names: {result[1]}")
        print(f"   Null passwords: {result[2]}")
        print(f"   Pending vendors: {result[3]}")
        print(f"   Agreed to terms: {result[4]}")
        
        # 7. Show validation report
        print("\n🔍 Validation Report:")
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN name IS NULL OR name = '' THEN '❌ Missing name'
                    WHEN phone IS NULL OR phone = '' THEN '❌ Missing phone'
                    WHEN business_name IS NULL OR business_name = '' THEN '❌ Missing business_name'
                    WHEN agree_terms != 'yes' THEN '❌ Terms not agreed'
                    ELSE '✅ OK'
                END as validation,
                COUNT(*) as count
            FROM vendors
            GROUP BY validation
        ''')
        
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}")
        
        conn.commit()
        print("\n✅ Vendors table fixed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    
    finally:
        conn.close()

def show_current_columns():
    """Show current columns in vendors table"""
    conn = sqlite3.connect('sooqkabeer.db')
    cursor = conn.cursor()
    
    print("\n📋 Current columns in vendors table:")
    cursor.execute("PRAGMA table_info(vendors)")
    columns = cursor.fetchall()
    
    print("ID | Name | Type | Not Null | Default Value | Primary Key")
    print("-" * 80)
    for col in columns:
        print(f"{col[0]} | {col[1]:20} | {col[2]:10} | {col[3]:8} | {str(col[4]):15} | {col[5]}")
    
    conn.close()

if __name__ == "__main__":
    print("🔧 SooqKabeer Database Fix Tool")
    print("=" * 40)
    
    # Show current state
    show_current_columns()
    
    # Ask user if they want to proceed
    print("\n⚠️  Do you want to fix the vendors table? (yes/no)")
    response = input().lower()
    
    if response == 'yes':
        fix_vendors_table()
    else:
        print("Operation cancelled.")
