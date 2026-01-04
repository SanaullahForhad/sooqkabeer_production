#!/bin/bash
BACKUP_DIR="/sdcard/sooqkabeer_backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/sooqkabeer_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf $BACKUP_FILE -C ~/sooqkabeer_production .
echo "✅ Backup created: $BACKUP_FILE"
