#!/bin/bash
BACKUP_DIR="$HOME/sooqkabeer_backups"

# Keep: 
# - Last 7 daily backups
# - Last 4 weekly backups (Sunday)
# - Last 12 monthly backups (1st of month)

cd "$BACKUP_DIR"

# Daily - keep last 7
ls -1t code_*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null

# Weekly (Sunday) - keep special标记
if [ $(date +%u) -eq 7 ]; then  # Sunday
    cp code_$(date +%Y%m%d_%H%M%S).tar.gz weekly_$(date +%Y%m%d).tar.gz 2>/dev/null
fi
ls -1t weekly_*.tar.gz 2>/dev/null | tail -n +5 | xargs rm -f 2>/dev/null

# Monthly (1st of month)
if [ $(date +%d) -eq "01" ]; then
    cp code_$(date +%Y%m%d_%H%M%S).tar.gz monthly_$(date +%Y%m).tar.gz 2>/dev/null
fi
ls -1t monthly_*.tar.gz 2>/dev/null | tail -n +13 | xargs rm -f 2>/dev/null

echo "Backup rotation done"
