# App Lifecycle Workflows

## Workflow 1: Create a New Frappe App from Scratch

### Step 1 — Scaffold
```bash
cd ~/frappe-bench
bench new-app my_inventory_app
# Answer prompts: title, description, publisher, email, license
```

### Step 2 — Enable Developer Mode
```bash
bench set-config -g developer_mode 1
bench start
```

### Step 3 — Create First Module
1. Open Desk > Module Def > New
2. Set Module Name = "Inventory Extensions"
3. Save

Verify `modules.txt` now contains "Inventory Extensions".

### Step 4 — Create First DocType
1. Open Desk > DocType > New
2. Set Name, Module = "Inventory Extensions"
3. Add fields, set naming, permissions
4. Save (generates JSON in `my_inventory_app/inventory_extensions/doctype/`)

### Step 5 — Install on Site
```bash
bench --site mysite install-app my_inventory_app
```

### Step 6 — Initialize Git
```bash
cd apps/my_inventory_app
git init
echo "__pycache__/\n*.pyc\nnode_modules/\n.eggs/" > .gitignore
git add -A
git commit -m "feat: initial app scaffold"
```

### Step 7 — Declare Dependencies
Edit `hooks.py`:
```python
required_apps = ["frappe", "erpnext"]
```

---

## Workflow 2: Install an Existing App from GitHub

### Step 1 — Get the App
```bash
# Public repo
bench get-app https://github.com/org/custom_app

# Private repo (SSH key must be configured)
bench get-app git@github.com:org/private_app.git

# Specific branch
bench get-app https://github.com/org/custom_app --branch v15
```

### Step 2 — Install on Site
```bash
bench --site mysite install-app custom_app
```

### Step 3 — Build Assets
```bash
bench build --app custom_app
```

### Step 4 — Verify
```bash
bench --site mysite list-apps
# Should show: frappe, erpnext, custom_app
```

---

## Workflow 3: Write and Deploy a Patch

### Step 1 — Create Patch File
```bash
mkdir -p apps/my_app/my_app/patches/v1_2/
```

Create `apps/my_app/my_app/patches/v1_2/update_item_defaults.py`:
```python
import frappe

def execute():
    frappe.reload_doc("inventory_extensions", "doctype", "custom_item_settings")
    items = frappe.get_all("Custom Item Settings",
        filters={"default_warehouse": ["is", "not set"]},
        pluck="name")
    for item in items:
        frappe.db.set_value("Custom Item Settings", item,
            "default_warehouse", "Main Warehouse - CO")
    frappe.db.commit()
```

### Step 2 — Register in patches.txt
Add to `patches.txt`:
```
[post_model_sync]
my_app.patches.v1_2.update_item_defaults
```

### Step 3 — Test Locally
```bash
bench --site mysite migrate
# Check logs for errors
```

### Step 4 — Verify in Console
```bash
bench --site mysite console
>>> frappe.get_all("Patch Log", filters={"patch": ["like", "%update_item_defaults%"]})
# Should return one entry confirming the patch ran
```

---

## Workflow 4: Set Up Production Deployment

### Step 1 — Disable Developer Mode
```bash
bench set-config -g developer_mode 0
```

### Step 2 — Build Production Assets
```bash
bench build
```

### Step 3 — Setup Production Services
```bash
sudo bench setup production LINUX_USERNAME
# This configures:
# - nginx (reverse proxy, SSL, static files)
# - supervisor (gunicorn workers, background workers, socketio)
# - fail2ban (optional, brute-force protection)
```

### Step 4 — Enable SSL (Optional)
```bash
sudo bench setup lets-encrypt mysite.com
```

### Step 5 — Verify
```bash
sudo supervisorctl status
# All processes should show RUNNING

curl -I https://mysite.com
# Should return 200 OK
```

---

## Workflow 5: Update an App on Production

### Step 1 — Backup
```bash
bench --site mysite backup --with-files
```

### Step 2 — Pull Updates
```bash
# Update all apps
bench update --pull

# Or update specific app only
cd apps/my_custom_app
git pull origin main
cd ../..
```

### Step 3 — Install Requirements
```bash
bench setup requirements --python
bench setup requirements --node
```

### Step 4 — Migrate
```bash
bench --site mysite migrate
```

### Step 5 — Build and Restart
```bash
bench build
bench restart
```

### Step 6 — Verify
```bash
bench version
bench --site mysite list-apps
```

---

## Workflow 6: Debug a Failed Migration

### Step 1 — Read the Error
```bash
bench --site mysite migrate 2>&1 | tail -50
# Look for the specific patch or DocType that failed
```

### Step 2 — Open Console
```bash
bench --site mysite console
```

### Step 3 — Test the Failing Patch
```python
from my_app.patches.v1_2.problematic_patch import execute
try:
    execute()
    frappe.db.commit()
except Exception as e:
    frappe.db.rollback()
    print(f"Error: {e}")
```

### Step 4 — Fix and Re-run
After fixing the patch code:
```bash
bench --site mysite migrate
```

If the patch already logged as "run" but failed, re-run by appending a version comment:
```
# In patches.txt, change:
my_app.patches.v1_2.problematic_patch
# To:
my_app.patches.v1_2.problematic_patch #2025-03-20-fix
```

---

## Workflow 7: Publish App to Frappe Marketplace

### Step 1 — Verify App Quality
```bash
# All tests pass
bench --site mysite run-tests --app my_custom_app

# Version is set
python -c "import my_custom_app; print(my_custom_app.__version__)"

# README exists
cat apps/my_custom_app/README.md
```

### Step 2 — Push to GitHub
```bash
cd apps/my_custom_app
git remote add origin https://github.com/org/my_custom_app.git
git push -u origin main
```

### Step 3 — Create Release Tag
```bash
git tag -a v1.0.0 -m "v1.0.0: Initial release"
git push origin v1.0.0
```

### Step 4 — Submit to Marketplace
1. Go to https://frappecloud.com/marketplace
2. Log in or create account
3. Click "Publish New App"
4. Enter GitHub repository URL
5. Select supported Frappe versions
6. Submit for review

### Step 5 — Maintain
- ALWAYS bump `__version__` in `__init__.py` before creating a new tag
- ALWAYS update `patches.txt` for data migrations
- ALWAYS test on a clean site: `bench new-site test && bench --site test install-app my_custom_app`
