# Backup Anti-Patterns

## 1. Never testing restore from backups

```bash
# WRONG — assuming backups work because the command succeeded
bench backup --with-files
# "We have backups!" — but have you ever restored one?

# CORRECT — ALWAYS test restore regularly
bench new-site test-restore.localhost --db-root-password $DB_ROOT_PW --admin-password test
bench --site test-restore.localhost restore /path/to/backup.sql.gz --db-root-password $DB_ROOT_PW
bench --site test-restore.localhost migrate
# Verify data, then drop the test site
bench drop-site test-restore.localhost --db-root-password $DB_ROOT_PW --force
```

**Why**: Corrupt backups, incompatible versions, and missing files are only discovered during restore. A backup that cannot be restored is worthless.

## 2. Database-only backup before major changes

```bash
# WRONG — forgetting --with-files before upgrade
bench backup
bench update

# CORRECT — ALWAYS include files before upgrades
bench backup --with-files --compress
bench update --pull --patch --build --requirements
```

**Why**: Without `--with-files`, uploaded documents, images, and private attachments are not backed up. Restoring database without files creates broken file references.

## 3. Storing backups only on the same server

```bash
# WRONG — backups in sites/{site}/private/backups/ only
# Server disk failure = data AND backups lost

# CORRECT — offsite copies
bench backup --with-files --compress
aws s3 sync sites/mysite.com/private/backups/ s3://my-backups/
# OR use S3 Backup Settings DocType for automated offsite backups
```

## 4. No backup rotation / unlimited retention

```bash
# WRONG — backups accumulate until disk is full
bench setup backups
# Months later: disk full, site down

# CORRECT — implement retention policy
# Delete local backups older than 7 days
find sites/mysite.com/private/backups/ -type f -mtime +7 -delete
# Keep 30 days on S3, then delete
```

## 5. Storing encryption keys with the backups

```bash
# WRONG — key stored next to encrypted backup
gpg --symmetric backup.sql.gz
echo "password123" > /mnt/backups/encryption-key.txt
# Attacker who accesses backups also gets the key

# CORRECT — store keys in separate location
# Use a password manager, HSM, or separate secrets vault
# NEVER store decryption keys in the same storage as encrypted backups
```

## 6. Using --force on restore to bypass version warnings

```bash
# WRONG — forcing a downgrade restore
bench --site mysite.com restore backup-from-v15.sql.gz --force
# Database schema incompatible, site broken

# CORRECT — ALWAYS restore to matching version
# Install same Frappe/ERPNext version as the backup source
# Then restore, then upgrade if needed
```

**Why**: Downgrades are NOT supported. Schema changes between versions are one-directional. Forcing a downgrade corrupts data.

## 7. Not backing up site_config.json separately

```bash
# WRONG — only backing up database
bench backup
# site_config.json contains DB credentials, encryption key, custom settings

# CORRECT — bench backup includes site_config automatically
bench backup --with-files
# Verify: ls sites/mysite.com/private/backups/*site_config*
```

## 8. Running backups during peak hours

```bash
# WRONG — backup during business hours
# 0 9 * * * bench backup --with-files  (9 AM — peak usage)
# Large database locks can slow the application

# CORRECT — schedule during off-peak hours
# 0 2 * * * bench backup --with-files  (2 AM — minimal usage)
```

## 9. Ignoring backup failures silently

```bash
# WRONG — no error handling in backup scripts
bench backup --with-files
aws s3 cp backup.sql.gz s3://bucket/
# If either fails, nobody knows

# CORRECT — check exit codes, send alerts
bench backup --with-files || {
    echo "BACKUP FAILED" | mail -s "Frappe Backup Alert" admin@example.com
    exit 1
}
```

## 10. Not excluding unnecessary DocTypes for faster backups

```bash
# WRONG — backing up everything including logs
bench backup  # Includes Error Log (millions of rows), Activity Log, etc.

# CORRECT — exclude log DocTypes for faster, smaller backups
bench backup --exclude "Error Log,Activity Log,Route History,Access Log,Scheduled Job Log"
# Keep full backups weekly, exclude logs for daily backups
```
