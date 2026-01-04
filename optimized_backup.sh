#!/bin/bash
# SooqKabeer Optimized Backup System - Space Saver

BACKUP_DIR="$HOME/sooqkabeer_backups"
PROJECT_DIR="$HOME/sooqkabeer_production"
DATE=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=5  # শুধু শেষ 5টি ব্যাকআপ রাখুন

mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/latest"  # লিংক এরর ফিক্স

echo "🔧 SooqKabeer Optimized Backup Started"
echo "📅 Date: $(date)"

# 1. কোড ব্যাকআপ (compressed) - শুধু গুরুত্বপূর্ণ ফাইল
CODE_BACKUP="$BACKUP_DIR/code_$DATE.tar.gz"
tar -czf "$CODE_BACKUP" \
    -C "$PROJECT_DIR" \
    app.py \
    requirements.txt \
    templates/ \
    --exclude="__pycache__" \
    --exclude="*.log" \
    2>/dev/null
echo "✅ Code backup: $(du -h "$CODE_BACKUP" | cut -f1)"

# 2. ডাটাবেস ব্যাকআপ (compressed) - sqlite3 চেক
if [ -f "$PROJECT_DIR/sooq.db" ]; then
    if command -v sqlite3 &> /dev/null; then
        DB_BACKUP="$BACKUP_DIR/db_$DATE.sql.gz"
        sqlite3 "$PROJECT_DIR/sooq.db" .dump | gzip -9 > "$DB_BACKUP"
        echo "✅ Database backup (compressed): $(du -h "$DB_BACKUP" | cut -f1)"
    else
        # fallback: simple copy
        cp "$PROJECT_DIR/sooq.db" "$BACKUP_DIR/db_$DATE.db"
        echo "⚠️  Database backup (simple copy): sqlite3 not installed"
    fi
fi

# 3. কনফিগ ফাইল (যদি থাকে)
for config_file in config.py .env settings.py; do
    if [ -f "$PROJECT_DIR/$config_file" ]; then
        cp "$PROJECT_DIR/$config_file" "$BACKUP_DIR/${config_file}_$DATE"
    fi
done

# 4. পুরোনো ব্যাকআপ ডিলিট (MAX_BACKUPS এর বেশি না)
cd "$BACKUP_DIR"
# Code backups
BACKUP_COUNT=$(ls -1 code_*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    ls -1t code_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
    echo "🗑️  Old code backups cleaned (keeping last $MAX_BACKUPS)"
fi

# Database backups
DB_COUNT=$(ls -1 db_*.db db_*.sql.gz 2>/dev/null | wc -l)
if [ "$DB_COUNT" -gt "$MAX_BACKUPS" ]; then
    ls -1t db_*.db db_*.sql.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
    echo "🗑️  Old database backups cleaned"
fi

# 5. Temporary files cleanup (project directory থেকে)
echo "🧹 Cleaning temporary files..."
find "$PROJECT_DIR" -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null
find "$PROJECT_DIR" -name "*.log" -size +1M -delete 2>/dev/null

# 6. Backup statistics
echo ""
echo "📊 Backup Statistics:"
echo "   Code backup: $(ls -lh code_$DATE.tar.gz 2>/dev/null | awk '{print $5}')"
if [ -f "db_$DATE.sql.gz" ]; then
    echo "   Database backup: $(ls -lh db_$DATE.sql.gz | awk '{print $5}')"
elif [ -f "db_$DATE.db" ]; then
    echo "   Database backup: $(ls -lh db_$DATE.db | awk '{print $5}')"
fi
echo "   Total backups: $BACKUP_COUNT files"
echo "   Directory size: $(du -sh "$BACKUP_DIR" | cut -f1)"

echo ""
echo "🎉 Backup completed successfully!"
echo "📁 Location: $BACKUP_DIR"
