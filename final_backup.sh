#!/bin/bash
BACKUP_DIR="$HOME/sooqkabeer_backups"
PROJECT_DIR="$HOME/sooqkabeer_production"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "🔧 SooqKabeer Backup v2.0"
echo "📅 $(date)"

# 1. Optimize database first
if [ -f "$PROJECT_DIR/sooq.db" ] && command -v sqlite3 &> /dev/null; then
    sqlite3 "$PROJECT_DIR/sooq.db" "VACUUM;"
fi

# 2. Backup only essential files (24KB)
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
    -C "$PROJECT_DIR" \
    --exclude="__pycache__" \
    --exclude="*.log" \
    --exclude="*.pyc" \
    --exclude="static/images/*" \
    app.py \
    *.db \
    requirements.txt \
    templates/ \
    2>/dev/null

# 3. Clean old backups (keep last 7)
cd "$BACKUP_DIR"
BACKUP_LIST=$(ls -1t backup_*.tar.gz 2>/dev/null)
COUNT=$(echo "$BACKUP_LIST" | wc -l)
if [ $COUNT -gt 7 ]; then
    echo "$BACKUP_LIST" | tail -n +8 | xargs rm -f
    echo "🗑️  Cleaned $(($COUNT - 7)) old backups"
fi

# 4. Project cleanup
find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null
find "$PROJECT_DIR" -name "*.log" -delete 2>/dev/null

# 5. Report
echo "✅ Backup: $(ls -lh backup_$DATE.tar.gz | awk '{print $5}')"
echo "📁 Total backups: $(ls -1 *.tar.gz 2>/dev/null | wc -l) files"
echo "💾 Backup dir size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "🎉 Done!"
