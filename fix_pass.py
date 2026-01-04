#=== Script to update all user passwords to a default one ===#
import sqlite3
import hashlib

def fix_passwords():
    #=== Database name ===#
    db_path = 'sooqkabeer.db'
    
    #=== Default password to set ===#
    new_password = "123456"
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        #=== Update all users with the hashed password ===#
        cursor.execute("UPDATE users SET password = ?", (hashed_password,))
        
        conn.commit()
        print(f"Success! All user passwords have been set to: {new_password}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_passwords()
