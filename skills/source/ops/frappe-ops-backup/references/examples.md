# Backup & Restore Examples

## Basic Backup Commands

```bash
# Database-only backup (fastest)
bench --site mysite.com backup
# Output: sites/mysite.com/private/backups/20240115_120000_abc123-database.sql.gz

# Full backup with files
bench --site mysite.com backup --with-files
# Creates:
# - *-database.sql.gz     (database dump)
# - *-site_config_backup.json  (site configuration)
# - *-files.tar           (public files)
# - *-private-files.tar   (private files)

# Compressed backup (.tgz)
bench --site mysite.com backup --with-files --compress
# Files archives use .tgz instead of .tar

# Selective backup — only specific DocTypes
bench --site mysite.com backup --only "Sales Invoice,Purchase Invoice,Journal Entry"

# Exclude large/unnecessary DocTypes
bench --site mysite.com backup --exclude "Error Log,Activity Log,Route History"

# Custom backup directory
bench --site mysite.com backup --with-files --backup-path /mnt/external/backups/
```

## Restore Examples

```bash
# Basic restore (database only)
bench --site mysite.com restore \
    sites/mysite.com/private/backups/20240115_120000_abc123-database.sql.gz

# Full restore with files
bench --site mysite.com restore \
    /path/to/20240115_120000_abc123-database.sql.gz \
    --with-public-files /path/to/20240115_120000_abc123-files.tar \
    --with-private-files /path/to/20240115_120000_abc123-private-files.tar

# Restore with new admin password
bench --site mysite.com restore \
    /path/to/backup.sql.gz \
    --admin-password NewSecurePassword123

# Restore with custom database name
bench --site mysite.com restore \
    /path/to/backup.sql.gz \
    --db-name custom_db_name \
    --db-root-password YOUR_ROOT_PASSWORD

# Restore and install apps
bench --site mysite.com restore \
    /path/to/backup.sql.gz \
    --install-app erpnext \
    --install-app custom_app
```

## Automated Backup Script with S3 Upload

```bash
#!/bin/bash
# frappe-backup-to-s3.sh
# Run via cron: 0 2 * * * /home/frappe/scripts/frappe-backup-to-s3.sh
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
SITE="mysite.com"
S3_BUCKET="s3://company-frappe-backups"
RETENTION_DAYS=30
LOG="/var/log/frappe-backup.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"; }

cd "$BENCH_DIR"

log "Starting backup for $SITE"

# Create backup
bench --site "$SITE" backup --with-files --compress 2>> "$LOG"

# Find latest backup files
BACKUP_DIR="sites/$SITE/private/backups"
LATEST_DB=$(ls -t "$BACKUP_DIR"/*-database.sql.gz 2>/dev/null | head -1)
LATEST_FILES=$(ls -t "$BACKUP_DIR"/*-files.tgz 2>/dev/null | head -1)
LATEST_PRIVATE=$(ls -t "$BACKUP_DIR"/*-private-files.tgz 2>/dev/null | head -1)
LATEST_CONFIG=$(ls -t "$BACKUP_DIR"/*-site_config_backup.json 2>/dev/null | head -1)

# Upload to S3
DATE_DIR=$(date +%Y-%m-%d)
for f in "$LATEST_DB" "$LATEST_FILES" "$LATEST_PRIVATE" "$LATEST_CONFIG"; do
    if [ -n "$f" ] && [ -f "$f" ]; then
        aws s3 cp "$f" "$S3_BUCKET/$SITE/$DATE_DIR/" >> "$LOG" 2>&1
    fi
done

# Cleanup old local backups
find "$BACKUP_DIR" -type f -mtime +7 -delete

# Cleanup old S3 backups
aws s3 ls "$S3_BUCKET/$SITE/" | while read -r line; do
    DIR=$(echo "$line" | awk '{print $2}' | tr -d '/')
    if [ -n "$DIR" ]; then
        DIR_DATE=$(date -d "$DIR" +%s 2>/dev/null || echo 0)
        CUTOFF=$(date -d "$RETENTION_DAYS days ago" +%s)
        if [ "$DIR_DATE" -lt "$CUTOFF" ] && [ "$DIR_DATE" -gt 0 ]; then
            aws s3 rm --recursive "$S3_BUCKET/$SITE/$DIR/"
            log "Removed old backup: $DIR"
        fi
    fi
done

log "Backup complete for $SITE"
```

## Backup Verification Script

```bash
#!/bin/bash
# verify-backup.sh — Automated backup integrity test
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
TEST_SITE="backup-verify.localhost"
DB_ROOT_PASSWORD="your_root_password"
BACKUP_SQL="$1"  # Pass backup file as argument

cd "$BENCH_DIR"

echo "Creating test site..."
bench new-site "$TEST_SITE" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "testpass" \
    --no-mariadb-socket

echo "Restoring backup..."
bench --site "$TEST_SITE" restore "$BACKUP_SQL" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --force

echo "Running migration..."
bench --site "$TEST_SITE" migrate

echo "Verifying data integrity..."
bench --site "$TEST_SITE" console <<'PYEOF'
import frappe
# Check critical tables exist and have data
checks = {
    "User": frappe.db.count("User"),
    "DocType": frappe.db.count("DocType"),
}
for dt, count in checks.items():
    assert count > 0, f"FAIL: {dt} has 0 records"
    print(f"  {dt}: {count} records")
print("\nAll integrity checks PASSED")
PYEOF

echo "Cleaning up test site..."
bench drop-site "$TEST_SITE" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --force

echo "Backup verification COMPLETE"
```

## Multi-Site Backup Script

```bash
#!/bin/bash
# backup-all-sites.sh — Backup all sites in bench
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
cd "$BENCH_DIR"

SITES=$(ls sites/*/site_config.json 2>/dev/null | xargs -I {} dirname {} | xargs -I {} basename {})

for site in $SITES; do
    [ "$site" = "assets" ] && continue
    echo "Backing up $site..."
    bench --site "$site" backup --with-files --compress || {
        echo "WARNING: Backup failed for $site"
        continue
    }
    echo "  Done: $site"
done

echo "All site backups complete"
```

## Docker Backup and Restore

```bash
# Backup from Docker container
docker compose exec backend bench --site mysite.com backup --with-files --compress

# Copy backup out of container
CONTAINER=$(docker compose ps -q backend)
docker cp "$CONTAINER:/home/frappe/frappe-bench/sites/mysite.com/private/backups/" ./backups/

# Restore into Docker container
docker cp ./backups/backup.sql.gz "$CONTAINER:/tmp/"
docker compose exec backend bench --site mysite.com restore /tmp/backup.sql.gz \
    --db-root-password "$DB_ROOT_PASSWORD"
docker compose exec backend rm /tmp/backup.sql.gz
```
