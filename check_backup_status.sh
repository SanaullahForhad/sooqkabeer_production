#!/bin/bash
# Check Auto Backup System Status

echo "📊 Auto Backup System Status"
echo "============================"

# Check if service is running
if [ -f "backup_service.pid" ]; then
    BACKUP_PID=$(cat backup_service.pid)
    
    if ps -p $BACKUP_PID > /dev/null; then
        echo "✅ Status: RUNNING (PID: $BACKUP_PID)"
        
        # Show last log entries
        echo ""
        echo "📋 Recent Logs:"
        tail -10 logs/backup_service.log 2>/dev/null || echo "No logs found"
    else
        echo "❌ Status: STOPPED (PID file exists but process not running)"
        rm -f backup_service.pid
    fi
else
    echo "❌ Status: NOT RUNNING"
fi

# Show backup info
echo ""
echo "📁 Backup Information:"
echo "   Location: auto_backups/"
if [ -d "auto_backups" ]; then
    BACKUP_COUNT=$(find auto_backups -maxdepth 1 -type d | wc -l)
    echo "   Number of backups: $((BACKUP_COUNT - 1))"
    
    # Show latest backup
    LATEST_BACKUP=$(ls -td auto_backups/*/ 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_TIME=$(stat -c %y "$LATEST_BACKUP" 2>/dev/null || echo "Unknown")
        echo "   Latest backup: $(basename "$LATEST_BACKUP")"
        echo "   Backup time: $BACKUP_TIME"
    fi
else
    echo "   No backups directory found"
fi

# Show disk usage
echo ""
echo "💾 Disk Usage:"
du -sh auto_backups/ 2>/dev/null || echo "   No backups yet"
