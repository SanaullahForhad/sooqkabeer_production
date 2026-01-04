#!/bin/bash
# Stop Auto Backup System

if [ -f "backup_service.pid" ]; then
    BACKUP_PID=$(cat backup_service.pid)
    
    if ps -p $BACKUP_PID > /dev/null; then
        kill $BACKUP_PID
        echo "✅ Auto Backup System stopped (PID: $BACKUP_PID)"
    else
        echo "⚠️  Backup service not running"
    fi
    
    rm -f backup_service.pid
else
    echo "ℹ️  No backup service running"
fi
