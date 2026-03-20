# Backup Workflows

## Workflow 1: Setup Automated Daily Backups

```
1. Choose backup strategy
   |
   +-- Simple (cron only)?
   |   $ bench setup backups
   |   (adds cron entry for every-6-hour backups)
   |
   +-- Offsite (S3)?
       Go to Setup > S3 Backup Settings in ERPNext
       Configure: bucket, credentials, frequency
       Enable and test
   |
2. Verify backup runs
   $ ls -la sites/mysite.com/private/backups/
   (check timestamps match expected schedule)
   |
3. Setup retention cleanup
   Add to cron:
   0 3 * * * find ~/frappe-bench/sites/*/private/backups/ -mtime +7 -delete
   |
4. Setup backup monitoring
   Add to cron:
   0 8 * * * /home/frappe/scripts/check-backup-age.sh
   (alert if latest backup is > 24 hours old)
   |
5. Schedule weekly restore test
   0 4 * * 0 /home/frappe/scripts/verify-backup.sh
```

## Workflow 2: Pre-Update Backup

```
1. Create full backup with files
   $ bench --site mysite.com backup --with-files --compress
   |
2. Verify backup was created
   $ ls -la sites/mysite.com/private/backups/ | tail -5
   |
3. Copy backup to safe location
   $ cp sites/mysite.com/private/backups/latest* /mnt/safe-backup/
   |
4. Proceed with update
   $ bench update --pull --patch --build --requirements
   |
5. If update fails — restore
   $ bench --site mysite.com restore /mnt/safe-backup/backup.sql.gz \
       --with-public-files /mnt/safe-backup/files.tar \
       --with-private-files /mnt/safe-backup/private-files.tar
```

## Workflow 3: Disaster Recovery

```
SCENARIO: Production server lost (hardware failure, ransomware, etc.)

1. Provision new server
   Same OS, install Docker or bench dependencies
   |
2. Install Frappe/ERPNext (SAME version as backup)
   $ bench init frappe-bench --frappe-branch version-15
   $ cd frappe-bench
   $ bench get-app erpnext --branch version-15
   |
3. Create blank site
   $ bench new-site mysite.com --db-root-password $DB_PW --admin-password temp
   |
4. Download latest backup from offsite storage
   $ aws s3 cp s3://backups/mysite.com/latest/ /tmp/restore/ --recursive
   |
5. Decrypt if encrypted
   $ gpg --decrypt /tmp/restore/backup.sql.gz.gpg > /tmp/restore/backup.sql.gz
   |
6. Restore
   $ bench --site mysite.com restore /tmp/restore/backup.sql.gz \
       --with-public-files /tmp/restore/files.tar \
       --with-private-files /tmp/restore/private-files.tar \
       --db-root-password $DB_PW
   |
7. Run migrations
   $ bench --site mysite.com migrate
   |
8. Setup production
   $ sudo bench setup production $(whoami)
   |
9. Update DNS to point to new server
   |
10. Setup SSL
    $ sudo -H bench setup lets-encrypt mysite.com
    |
11. Verify functionality
    Login as Administrator, check key workflows
    |
12. Post-mortem
    Document what happened, update DR plan
```

## Workflow 4: Clone Production to Staging

```
1. Backup production
   $ bench --site prod.example.com backup --with-files --compress
   |
2. Copy backup to staging server
   $ scp sites/prod.example.com/private/backups/latest* staging:/tmp/
   |
3. On staging server — create site from backup
   $ bench new-site staging.example.com \
       --db-root-password $DB_PW --admin-password staging123
   $ bench --site staging.example.com restore /tmp/backup.sql.gz \
       --with-public-files /tmp/files.tgz \
       --with-private-files /tmp/private-files.tgz \
       --db-root-password $DB_PW
   |
4. Sanitize staging data (CRITICAL for privacy)
   $ bench --site staging.example.com console
   >>> frappe.db.sql("UPDATE tabUser SET email = CONCAT(name, '@staging.local') WHERE name != 'Administrator'")
   >>> frappe.db.commit()
   |
5. Clear sensitive settings
   $ bench --site staging.example.com set-config \
       mail_server "" mail_login "" mail_password ""
```

## Workflow 5: Migrate Site Between Servers

```
1. Backup source site
   $ bench --site mysite.com backup --with-files --compress
   |
2. Transfer backup to destination
   $ rsync -avz sites/mysite.com/private/backups/latest* \
       destination:/home/frappe/frappe-bench/
   |
3. On destination — restore
   $ bench new-site mysite.com --db-root-password $DB_PW --admin-password temp
   $ bench --site mysite.com restore /home/frappe/frappe-bench/backup.sql.gz \
       --with-public-files /home/frappe/frappe-bench/files.tgz \
       --with-private-files /home/frappe/frappe-bench/private-files.tgz \
       --db-root-password $DB_PW
   |
4. Run migrations and build
   $ bench --site mysite.com migrate
   $ bench build
   |
5. Setup production on new server
   $ sudo bench setup production $(whoami)
   |
6. Update DNS to point to new server
   Wait for propagation (check with dig mysite.com)
   |
7. Verify and decommission old server
```
