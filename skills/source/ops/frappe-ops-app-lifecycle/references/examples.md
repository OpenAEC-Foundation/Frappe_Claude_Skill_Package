# App Lifecycle Examples

## Complete hooks.py for a Custom App

```python
# my_custom_app/hooks.py

app_name = "my_custom_app"
app_title = "My Custom App"
app_publisher = "Your Company"
app_description = "Custom ERPNext extensions for inventory management"
app_email = "dev@yourcompany.com"
app_license = "MIT"
app_version = "1.0.0"

# App dependencies — ALWAYS declare these
required_apps = ["frappe", "erpnext"]

# Asset injection
app_include_js = "my_custom_app.bundle.js"       # v15+
app_include_css = "my_custom_app.bundle.css"      # v15+

# Lifecycle hooks
after_install = "my_custom_app.setup.after_install"
after_migrate = "my_custom_app.setup.after_migrate"

# DocType overrides
doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Customer": "public/js/customer.js"
}

# Document events
doc_events = {
    "Sales Invoice": {
        "on_submit": "my_custom_app.events.sales_invoice.on_submit",
        "on_cancel": "my_custom_app.events.sales_invoice.on_cancel"
    },
    "*": {
        "after_insert": "my_custom_app.events.common.log_creation"
    }
}

# Scheduled tasks
scheduler_events = {
    "daily": [
        "my_custom_app.tasks.daily_sync"
    ],
    "hourly": [
        "my_custom_app.tasks.check_stock_levels"
    ],
    "cron": {
        "0 9 * * 1": [
            "my_custom_app.tasks.weekly_report"
        ]
    }
}

# Permissions
permission_query_conditions = {
    "Custom DocType": "my_custom_app.permissions.get_conditions"
}

has_permission = {
    "Custom DocType": "my_custom_app.permissions.has_permission"
}

# Fixtures — export these DocTypes as JSON
fixtures = [
    "Custom Field",
    {"dt": "Property Setter", "filters": [["module", "=", "My Custom App"]]},
    {"dt": "Role", "filters": [["name", "in", ["Inventory Analyst"]]]},
]
```

## Complete __init__.py

```python
# my_custom_app/__init__.py
__version__ = "1.0.0"
```

## Complete patches.txt

```
# my_custom_app/patches.txt

[pre_model_sync]
# v1.0 — Initial release patches
my_custom_app.patches.v1_0.create_custom_roles

[post_model_sync]
# v1.0 — Data migration after schema sync
my_custom_app.patches.v1_0.set_default_values
my_custom_app.patches.v1_0.migrate_legacy_data

# v1.1 — Feature additions
my_custom_app.patches.v1_1.add_inventory_categories
my_custom_app.patches.v1_1.update_existing_items
```

## Example Patch: Pre-Model-Sync

```python
# my_custom_app/patches/v1_0/create_custom_roles.py
import frappe

def execute():
    """Create custom roles before DocType sync so permissions are ready."""
    if not frappe.db.exists("Role", "Inventory Analyst"):
        doc = frappe.new_doc("Role")
        doc.role_name = "Inventory Analyst"
        doc.desk_access = 1
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
```

## Example Patch: Post-Model-Sync

```python
# my_custom_app/patches/v1_1/update_existing_items.py
import frappe

def execute():
    """Set default category for items that don't have one (new field added in v1.1)."""
    # No need for reload_doc — post_model_sync already applied schema
    frappe.db.sql("""
        UPDATE `tabItem`
        SET custom_category = 'General'
        WHERE custom_category IS NULL OR custom_category = ''
    """)
    frappe.db.commit()
```

## Example after_install Setup

```python
# my_custom_app/setup.py (not the package setup.py)
import frappe

def after_install():
    """Run after bench --site SITE install-app my_custom_app."""
    create_default_settings()
    setup_email_templates()

def create_default_settings():
    if not frappe.db.exists("My App Settings", "My App Settings"):
        doc = frappe.new_doc("My App Settings")
        doc.enabled = 1
        doc.sync_interval = 60
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

def setup_email_templates():
    templates = [
        {"name": "Stock Alert", "subject": "Low Stock Alert: {item_name}",
         "response": "Item {item_name} has fallen below minimum stock level."}
    ]
    for tmpl in templates:
        if not frappe.db.exists("Email Template", tmpl["name"]):
            doc = frappe.new_doc("Email Template")
            doc.update(tmpl)
            doc.insert(ignore_permissions=True)
    frappe.db.commit()
```

## modules.txt Example

```
My Custom App
Inventory Extensions
Custom Reports
```

ALWAYS add a new line to `modules.txt` when creating a new module. Frappe reads this file to register modules.

## pyproject.toml (v15+ Full Example)

```toml
[project]
name = "my_custom_app"
dynamic = ["version"]
description = "Custom ERPNext extensions for inventory management"
authors = [
    {name = "Your Company", email = "dev@yourcompany.com"}
]
requires-python = ">=3.10,<3.13"
readme = "README.md"
license = {text = "MIT"}
dependencies = []

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core:buildapi"

[tool.bench.dev-dependencies]
pytest = "~=7.4"
coverage = "~=7.3"
```

## setup.py (v14 Full Example)

```python
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="my_custom_app",
    version="1.0.0",
    description="Custom ERPNext extensions for inventory management",
    author="Your Company",
    author_email="dev@yourcompany.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.8",
)
```
