#!/usr/bin/env python3
"""
SooqKabeer Auto Backup System
Automatically backs up database and code every week
"""

import os
import sys
import shutil
import sqlite3
import datetime
import schedule
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

class AutoBackupSystem:
    def __init__(self):
        self.backup_dir = Path("auto_backups")
        self.db_file = "sooqkabeer.db"
        self.keep_days = 7  # Keep backups for 7 days
        
    def setup_directories(self):
        """Create necessary directories"""
        self.backup_dir.mkdir(exist_ok=True)
        logging.info(f"Backup directory: {self.backup_dir.absolute()}")
    
    def create_backup(self):
        """Create a new backup"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"sooqkabeer_backup_{timestamp}"
            
            # Create backup directory for this backup
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # Backup files
            files_to_backup = [
                self.db_file,
                "app.py",
                "requirements.txt"
            ]
            
            # Copy files
            for file in files_to_backup:
                if os.path.exists(file):
                    shutil.copy2(file, backup_path / file)
                    logging.info(f"✓ Backed up: {file}")
            
            # Backup templates directory
            if os.path.exists("templates"):
                templates_backup = backup_path / "templates"
                shutil.copytree("templates", templates_backup, dirs_exist_ok=True)
                logging.info("✓ Backed up: templates/")
            
            # Backup static directory
            if os.path.exists("static"):
                static_backup = backup_path / "static"
                shutil.copytree("static", static_backup, dirs_exist_ok=True)
                logging.info("✓ Backed up: static/")
            
            # Backup tests directory
            if os.path.exists("tests"):
                tests_backup = backup_path / "tests"
                shutil.copytree("tests", tests_backup, dirs_exist_ok=True)
                logging.info("✓ Backed up: tests/")
            
            # Create backup info file
            info_content = f"""SooqKabeer Auto Backup
========================
Backup Time: {datetime.datetime.now()}
Database Size: {os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0} bytes
Files Backed Up: {len(files_to_backup)} + directories
Backup ID: {backup_name}
"""
            with open(backup_path / "BACKUP_INFO.txt", "w") as f:
                f.write(info_content)
            
            # Export database to SQL (for easy restoration)
            if os.path.exists(self.db_file):
                sql_dump = backup_path / "database_dump.sql"
                self.export_database_to_sql(sql_dump)
            
            logging.info(f"✅ Backup created: {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Backup failed: {e}")
            return False
    
    def export_database_to_sql(self, output_file):
        """Export SQLite database to SQL file"""
        try:
            conn = sqlite3.connect(self.db_file)
            with open(output_file, 'w') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            conn.close()
            logging.info(f"✓ Database exported to SQL: {output_file}")
        except Exception as e:
            logging.error(f"Database export failed: {e}")
    
    def cleanup_old_backups(self):
        """Delete backups older than 7 days"""
        try:
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=self.keep_days)
            deleted_count = 0
            
            for backup_folder in self.backup_dir.iterdir():
                if backup_folder.is_dir():
                    # Extract timestamp from folder name
                    try:
                        folder_time_str = backup_folder.name.split('_')[-2] + '_' + backup_folder.name.split('_')[-1]
                        folder_time = datetime.datetime.strptime(folder_time_str, "%Y%m%d_%H%M%S")
                        
                        if folder_time < cutoff_time:
                            shutil.rmtree(backup_folder)
                            deleted_count += 1
                            logging.info(f"🗑️ Deleted old backup: {backup_folder.name}")
                    except (ValueError, IndexError):
                        # If folder name doesn't match pattern, check creation time
                        folder_ctime = datetime.datetime.fromtimestamp(backup_folder.stat().st_ctime)
                        if folder_ctime < cutoff_time:
                            shutil.rmtree(backup_folder)
                            deleted_count += 1
                            logging.info(f"🗑️ Deleted old backup (by ctime): {backup_folder.name}")
            
            if deleted_count > 0:
                logging.info(f"🧹 Cleaned up {deleted_count} old backups")
            else:
                logging.info("🧹 No old backups to clean up")
                
        except Exception as e:
            logging.error(f"Cleanup failed: {e}")
    
    def restore_backup(self, backup_name=None):
        """Restore from a specific backup (or latest if not specified)"""
        try:
            if not backup_name:
                # Get latest backup
                backups = sorted([d for d in self.backup_dir.iterdir() if d.is_dir()], 
                               key=lambda x: x.stat().st_ctime, reverse=True)
                if not backups:
                    logging.error("No backups available")
                    return False
                backup_name = backups[0].name
            
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logging.error(f"Backup not found: {backup_name}")
                return False
            
            # Restore files
            restored_files = []
            
            # Restore database
            db_backup = backup_path / self.db_file
            if db_backup.exists():
                # Create backup of current database before restore
                if os.path.exists(self.db_file):
                    current_backup = f"{self.db_file}.pre_restore"
                    shutil.copy2(self.db_file, current_backup)
                
                shutil.copy2(db_backup, self.db_file)
                restored_files.append(self.db_file)
                logging.info(f"✓ Restored database")
            
            # Restore other files
            files_to_restore = ["app.py", "requirements.txt"]
            for file in files_to_restore:
                file_backup = backup_path / file
                if file_backup.exists():
                    shutil.copy2(file_backup, file)
                    restored_files.append(file)
            
            # Restore directories
            dirs_to_restore = ["templates", "static", "tests"]
            for directory in dirs_to_restore:
                dir_backup = backup_path / directory
                if dir_backup.exists():
                    if os.path.exists(directory):
                        shutil.rmtree(directory)
                    shutil.copytree(dir_backup, directory)
                    restored_files.append(f"{directory}/")
            
            logging.info(f"✅ Restored {len(restored_files)} items from backup: {backup_name}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Restore failed: {e}")
            return False
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        for backup_folder in sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_ctime, reverse=True):
            if backup_folder.is_dir():
                size = sum(f.stat().st_size for f in backup_folder.rglob('*') if f.is_file())
                backups.append({
                    'name': backup_folder.name,
                    'size': self.human_readable_size(size),
                    'date': datetime.datetime.fromtimestamp(backup_folder.stat().st_ctime),
                    'path': backup_folder
                })
        
        if backups:
            print(f"\n📦 Available Backups ({len(backups)}):")
            print("=" * 70)
            for i, backup in enumerate(backups, 1):
                print(f"{i:2}. {backup['name']}")
                print(f"    📅 {backup['date']} | 📊 {backup['size']}")
            print("=" * 70)
        else:
            print("📭 No backups available")
        
        return backups
    
    def human_readable_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def run_scheduled_backup(self):
        """Run scheduled backup job"""
        logging.info("🕐 Running scheduled weekly backup...")
        self.create_backup()
        self.cleanup_old_backups()
        logging.info("✅ Scheduled backup completed")
    
    def start_scheduler(self):
        """Start the auto backup scheduler"""
        logging.info("🚀 Starting Auto Backup System...")
        logging.info(f"📁 Backup directory: {self.backup_dir.absolute()}")
        logging.info(f"⏰ Will run backups weekly (every Sunday at 02:00)")
        logging.info(f"🗑️ Will keep backups for {self.keep_days} days")
        
        # Schedule weekly backup (every Sunday at 2 AM)
        schedule.every().sunday.at("02:00").do(self.run_scheduled_backup)
        
        # Also run daily cleanup
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        # Run immediate backup on startup
        self.create_backup()
        
        logging.info("🎯 Auto Backup System is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("👋 Auto Backup System stopped by user")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🛡️  SOOQKABEER AUTO BACKUP SYSTEM")
    print("="*60)
    
    backup_system = AutoBackupSystem()
    backup_system.setup_directories()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "backup":
            backup_system.create_backup()
            backup_system.cleanup_old_backups()
        
        elif command == "restore":
            if len(sys.argv) > 2:
                backup_system.restore_backup(sys.argv[2])
            else:
                backups = backup_system.list_backups()
                if backups:
                    choice = input(f"\nRestore latest backup? ({backups[0]['name']}) [y/N]: ")
                    if choice.lower() == 'y':
                        backup_system.restore_backup()
        
        elif command == "list":
            backup_system.list_backups()
        
        elif command == "cleanup":
            backup_system.cleanup_old_backups()
        
        elif command == "start":
            backup_system.start_scheduler()
        
        elif command == "test":
            print("🧪 Testing backup system...")
            backup_system.create_backup()
            backup_system.list_backups()
        
        else:
            print(f"Unknown command: {command}")
            print_help()
    
    else:
        print_help()

def print_help():
    """Print help message"""
    print("\n📚 Available Commands:")
    print("  backup      - Create a new backup")
    print("  restore     - Restore from backup")
    print("  list        - List all backups")
    print("  cleanup     - Clean up old backups")
    print("  start       - Start auto backup scheduler")
    print("  test        - Test backup system")
    print("\n📝 Examples:")
    print("  python auto_backup.py backup")
    print("  python auto_backup.py restore")
    print("  python auto_backup.py list")
    print("\n🔧 Auto Mode:")
    print("  python auto_backup.py start  # Runs in background")
    print("\n📊 Backup Location: auto_backups/")
    print("📋 Logs: backup.log")

if __name__ == "__main__":
    main()
