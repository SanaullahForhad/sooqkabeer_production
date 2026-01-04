#!/bin/bash
# SooqKabeer Auto Backup System

BACKUP_DIR="$HOME/sooqkabeer_backups"
PROJECT_DIR="$HOME/sooqkabeer_production"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "🔧 SooqKabeer Backup Started"
echo "📅 Date: $(date)"
echo "📂 Project: $PROJECT_DIR"

CODE_BACKUP="$BACKUP_DIR/code_$DATE.tar.gz"
tar -czf "$CODE_BACKUP" -C "$PROJECT_DIR" .
echo "✅ Code backup done"

if [ -f "$PROJECT_DIR/sooq.db" ]; then
    cp "$PROJECT_DIR/sooq.db" "$BACKUP_DIR/db_$DATE.db"
    echo "✅ Database backup done"
fi

echo "🎉 Backup completed!"
echo "📁 Location: $BACKUP_DIR"
