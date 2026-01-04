#!/bin/bash
# Start SooqKabeer Auto Backup System

echo "🛡️ Starting Auto Backup System..."
echo "================================"

# Check if auto_backup.py exists
if [ ! -f "auto_backup.py" ]; then
    echo "❌ auto_backup.py not found!"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Run in background and save PID
python auto_backup.py start > logs/backup_service.log 2>&1 &
BACKUP_PID=$!

# Save PID to file
echo $BACKUP_PID > backup_service.pid

echo "✅ Auto Backup System started (PID: $BACKUP_PID)"
echo "📁 Backups will be saved in: auto_backups/"
echo "📋 Logs: logs/backup_service.log"
echo "⏰ Scheduled: Weekly backup every Sunday at 2 AM"
echo "🗑️  Retention: 7 days"
echo ""
echo "🔧 Management Commands:"
echo "  ./stop_auto_backup.sh     - Stop backup service"
echo "  ./check_backup_status.sh  - Check status"
echo "  python auto_backup.py list - List backups"
