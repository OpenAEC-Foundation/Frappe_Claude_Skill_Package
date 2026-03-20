# App Lifecycle Anti-Patterns

## AP-1: Forgetting to Add Module to modules.txt

**WRONG:**
Create a new module directory but skip `modules.txt`:
```
my_app/
├── custom_reports/
│   ├── __init__.py
│   └── report/...
├── modules.txt         # ← "Custom Reports" not listed here
```

**RIGHT:**
```
# modules.txt
My Custom App
Custom Reports
```

**Why**: Frappe reads `modules.txt` to register modules. Missing modules cause "Module not found" errors during migration and DocType creation.

## AP-2: Not Declaring required_apps

**WRONG:**
```python
# hooks.py — no dependency declaration
app_name = "my_app"
```

**RIGHT:**
```python
# hooks.py
app_name = "my_app"
required_apps = ["frappe", "erpnext"]
```

**Why**: Without `required_apps`, users can install your app without ERPNext, causing import errors and broken DocType links. ALWAYS declare all app dependencies.

## AP-3: Running migrate Without Backup on Production

**WRONG:**
```bash
bench --site production-site migrate
```

**RIGHT:**
```bash
bench --site production-site backup
bench --site production-site migrate
```

**Why**: Migrations can fail mid-way, leaving the database in an inconsistent state. ALWAYS backup before migrating production sites.

## AP-4: Editing DocTypes Without Developer Mode

**WRONG:**
Manually editing DocType JSON files and running migrate.

**RIGHT:**
```bash
# Enable developer mode first
bench set-config -g developer_mode 1
# Edit DocTypes in Desk UI
# Frappe auto-generates JSON files
bench --site mysite migrate
```

**Why**: Frappe generates DocType JSON from the UI. Manual edits may have incorrect checksums and be overwritten. ALWAYS use the Desk UI in developer mode.

## AP-5: Putting Patches in Wrong Section

**WRONG — accessing a new field in pre_model_sync:**
```
[pre_model_sync]
my_app.patches.v1_2.fill_new_field     # New field doesn't exist yet!
```

**RIGHT:**
```
[post_model_sync]
my_app.patches.v1_2.fill_new_field     # Schema already synced, field exists
```

**Why**: `[pre_model_sync]` patches run BEFORE schema changes. If your patch needs a field that was just added to the DocType JSON, it MUST be in `[post_model_sync]`.

## AP-6: Forgetting frappe.reload_doc in Pre-Sync Patches

**WRONG:**
```python
def execute():
    # Tries to access new field, but DocType meta is stale
    frappe.db.set_value("My DocType", "doc1", "new_field", "value")
```

**RIGHT:**
```python
def execute():
    frappe.reload_doc("module_name", "doctype", "my_doctype")
    frappe.db.set_value("My DocType", "doc1", "new_field", "value")
```

**Why**: In `[pre_model_sync]`, the DocType meta is from the OLD schema. Call `frappe.reload_doc()` to load the new JSON before accessing new fields.

## AP-7: Hardcoding Site Name in Scripts

**WRONG:**
```python
site_config = frappe.get_site_config("mysite.localhost")
```

**RIGHT:**
```python
site_config = frappe.get_site_config()  # Uses current site context
```

**Why**: Site name differs between dev, staging, and production. NEVER hardcode site names. Frappe ALWAYS knows the current site from context.

## AP-8: Not Running bench build After JS Changes

**WRONG:**
```bash
# Edit JS file
vim apps/my_app/my_app/public/js/custom.js
# Expect changes to appear immediately
```

**RIGHT:**
```bash
# Edit JS file, then build
bench build --app my_app
# Or use watch mode during development
bench watch
```

**Why**: JS/CSS files must be compiled into bundles. Without `bench build`, Desk serves stale cached assets. Use `bench watch` during development for auto-rebuild.

## AP-9: Using bench update Without Testing on Staging

**WRONG:**
```bash
# Directly on production
bench update
```

**RIGHT:**
```bash
# On staging first
bench update
bench --site staging run-tests
# Verify in browser
# Then on production
bench --site production backup
bench update
```

**Why**: `bench update` pulls ALL app updates, runs ALL pending migrations, and rebuilds ALL assets. A breaking change in any app can take down the site. ALWAYS test on staging first.

## AP-10: Committing __pycache__ and .pyc Files

**WRONG:**
```
git add -A  # Includes __pycache__/ directories
```

**RIGHT — ensure .gitignore contains:**
```
__pycache__/
*.pyc
*.pyo
```

**Why**: Compiled Python files are platform-specific and cause merge conflicts. ALWAYS add `__pycache__/` to `.gitignore` before the first commit.
