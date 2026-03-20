# Upgrade Examples

## Example 1: Standard v14 → v15 Upgrade on Staging

```bash
# Clone production to staging
bench --site production.example.com backup --with-files
bench new-site staging.example.com --admin-password admin
bench --site staging.example.com restore \
  /path/to/production-database.sql.gz \
  --with-public-files /path/to/files.tar \
  --with-private-files /path/to/private-files.tar

# Switch to v15
bench switch-to-branch version-15 frappe erpnext

# Update (installs deps, builds, migrates)
bench update

# Verify key functionality
bench --site staging.example.com console
>>> frappe.get_doc("Company", frappe.defaults.get_defaults().company)
>>> frappe.db.count("Sales Invoice")

# Check for errors in logs
tail -f logs/frappe.log
```

## Example 2: Upgrading with Custom Apps

```bash
# 1. Backup
bench --site mysite backup --with-files

# 2. Check custom app compatibility FIRST
cd apps/custom_app
# Search for removed APIs
grep -r "db\.set(" . --include="*.py"
grep -r "as_utf8" . --include="*.py"
grep -r "frappe.compare(" . --include="*.py"

# 3. Fix deprecated code in custom app BEFORE switching branches
# Example: db.set() → doc.db_set()
# Example: frappe.db.set_value("Single", None, ...) → frappe.db.set_single_value(...)

# 4. Commit custom app fixes
cd apps/custom_app
git add -A && git commit -m "fix: migrate deprecated APIs for v15 compatibility"

# 5. Switch Frappe/ERPNext to v15
bench switch-to-branch version-15 frappe erpnext

# 6. Update
bench update
```

## Example 3: Enabling Server Scripts After v15 Upgrade

```bash
# Server Scripts are disabled by default in v15+
# If your site uses Server Scripts, Script Reports, or System Console:
bench set-config -g server_script_enabled 1

# Restart to apply
bench restart
```

## Example 4: Writing a Data Migration Patch

```python
# myapp/patches/v15_0/migrate_old_field_to_new.py
import frappe

def execute():
    # Reload DocType to get new schema
    frappe.reload_doc("selling", "doctype", "sales_order")

    # Migrate data from old field to new field
    frappe.db.sql("""
        UPDATE `tabSales Order`
        SET new_status_field = CASE
            WHEN old_status = 'Open' THEN 'Draft'
            WHEN old_status = 'Closed' THEN 'Completed'
            ELSE old_status
        END
        WHERE old_status IS NOT NULL
    """)

    frappe.db.commit()
```

Add to `patches.txt`:
```ini
[post_model_sync]
myapp.patches.v15_0.migrate_old_field_to_new
```

## Example 5: Full Rollback After Failed v15 Upgrade

```bash
# 1. Stop everything
bench stop

# 2. Check which backup to restore
ls sites/mysite/private/backups/

# 3. Restore pre-upgrade backup
bench --site mysite restore \
  sites/mysite/private/backups/20250320_120000-mysite-database.sql.gz \
  --with-public-files sites/mysite/private/backups/20250320_120000-mysite-files.tar \
  --with-private-files sites/mysite/private/backups/20250320_120000-mysite-private-files.tar

# 4. Switch back to v14
bench switch-to-branch version-14 frappe erpnext

# 5. Reinstall v14 dependencies
bench setup requirements

# 6. Rebuild v14 assets
bench build

# 7. Start
bench start
```

## Example 6: Handling Stuck Patch During Migration

```bash
# Migration fails with: "PatchError: myapp.patches.v15_0.broken_patch"
# Check the error log
tail -50 logs/frappe.log

# Option A: Fix the patch and re-run
# Edit the patch file, then:
bench --site mysite migrate

# Option B: Skip the patch (if safe to skip)
bench --site mysite console
>>> frappe.db.sql("INSERT INTO __patches (patch) VALUES ('myapp.patches.v15_0.broken_patch')")
>>> frappe.db.commit()
# Then re-run migrate to continue with remaining patches
bench --site mysite migrate

# Option C: Force re-run a previously executed patch
# In patches.txt, add date suffix:
# myapp.patches.v15_0.broken_patch #2025-03-20
bench --site mysite migrate
```

## Example 7: v15 → v16 Upgrade — Handling Sort Order Change

```python
# v16 changes default sort from 'modified' to 'creation'
# If your code relies on modified-first ordering, update explicitly:

# BEFORE (worked in v15, breaks in v16):
items = frappe.get_all("Sales Invoice", limit=10)
# Returns sorted by 'creation' in v16, was 'modified' in v15

# AFTER (explicit, works in both):
items = frappe.get_all("Sales Invoice", order_by="modified desc", limit=10)
```

## Example 8: Installing Separated Modules After v16 Upgrade

```bash
# v16 separates Blog, Newsletter, Energy Points, Backup Integrations
# If you used these features, install them as separate apps:

bench get-app https://github.com/frappe/blog.git
bench --site mysite install-app blog

bench get-app https://github.com/frappe/newsletter.git
bench --site mysite install-app newsletter

bench get-app https://github.com/frappe/eps.git
bench --site mysite install-app eps

bench get-app https://github.com/frappe/offsite_backups.git
bench --site mysite install-app offsite_backups
```
