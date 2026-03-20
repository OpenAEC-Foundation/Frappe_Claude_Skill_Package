# Frappe Hook Implementation Workflows

Step-by-step implementation patterns for each hook type.

---

## Workflow 1: Basic doc_events Setup

### Use Case
React to document events on an external DocType (ERPNext/Frappe).

### Steps

**Step 1: Plan your handlers**
```
DocType: Sales Invoice
Events needed:
- validate: Check credit limit
- on_submit: Create external record
```

**Step 2: Add to hooks.py**
```python
# myapp/hooks.py

doc_events = {
    "Sales Invoice": {
        "validate": "myapp.events.sales_invoice.check_credit",
        "on_submit": "myapp.events.sales_invoice.create_external"
    }
}
```

**Step 3: Create events module**
```bash
# Create directory structure
mkdir -p myapp/events
touch myapp/events/__init__.py
touch myapp/events/sales_invoice.py
```

**Step 4: Implement handlers**
```python
# myapp/events/sales_invoice.py
import frappe

def check_credit(doc, method=None):
    """
    Runs before save.
    Changes to doc ARE automatically saved.
    """
    customer_credit = get_customer_credit(doc.customer)
    if doc.grand_total > customer_credit:
        frappe.throw(f"Exceeds credit limit of {customer_credit}")

def create_external(doc, method=None):
    """
    Runs after submit.
    Document already saved - use db_set_value for changes.
    """
    external_id = send_to_external_system(doc)
    frappe.db.set_value("Sales Invoice", doc.name, 
                        "custom_external_id", external_id)
```

**Step 5: Deploy**
```bash
bench --site sitename migrate
```

**Step 6: Test**
```python
# In console
doc = frappe.get_doc("Sales Invoice", "INV-001")
doc.save()  # Should trigger validate
doc.submit()  # Should trigger on_submit
```

---

## Workflow 2: Wildcard Event Handler

### Use Case
Audit trail for all document changes.

### Steps

**Step 1: Add wildcard handler**
```python
# myapp/hooks.py

doc_events = {
    "*": {
        "after_insert": "myapp.audit.log_creation",
        "on_update": "myapp.audit.log_update",
        "on_trash": "myapp.audit.log_deletion"
    }
}
```

**Step 2: Implement audit module**
```python
# myapp/audit.py
import frappe

def log_creation(doc, method=None):
    """Log all document creations"""
    if should_audit(doc.doctype):
        create_audit_log(doc, "Created")

def log_update(doc, method=None):
    """Log all document updates"""
    if should_audit(doc.doctype):
        create_audit_log(doc, "Updated")

def log_deletion(doc, method=None):
    """Log all document deletions"""
    if should_audit(doc.doctype):
        create_audit_log(doc, "Deleted")

def should_audit(doctype):
    """Skip system doctypes"""
    skip = ["Error Log", "Activity Log", "Custom Audit Log"]
    return doctype not in skip

def create_audit_log(doc, action):
    """Create audit record"""
    frappe.get_doc({
        "doctype": "Custom Audit Log",
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "action": action,
        "user": frappe.session.user,
        "timestamp": frappe.utils.now()
    }).insert(ignore_permissions=True)
```

---

## Workflow 3: Scheduler Task Setup

### Use Case
Daily cleanup of old records + weekly report.

### Steps

**Step 1: Add scheduler events**
```python
# myapp/hooks.py

scheduler_events = {
    "daily": [
        "myapp.tasks.cleanup_old_logs"
    ],
    "weekly": [
        "myapp.tasks.send_weekly_summary"
    ],
    "cron": {
        "0 9 * * 1-5": [
            "myapp.tasks.weekday_morning_check"
        ]
    }
}
```

**Step 2: Implement tasks**
```python
# myapp/tasks.py
import frappe
from frappe.utils import add_days, today

def cleanup_old_logs():
    """
    Daily task - NO arguments!
    Runs in default queue (5 min timeout)
    """
    cutoff = add_days(today(), -30)
    
    old_logs = frappe.get_all(
        "Error Log",
        filters={"creation": ["<", cutoff]},
        pluck="name",
        limit=1000  # Process in batches
    )
    
    for name in old_logs:
        frappe.delete_doc("Error Log", name, ignore_permissions=True)
    
    frappe.db.commit()

def send_weekly_summary():
    """Weekly summary email"""
    data = compile_weekly_stats()
    
    frappe.sendmail(
        recipients=get_managers(),
        subject="Weekly Summary",
        message=render_summary(data)
    )

def weekday_morning_check():
    """Runs at 9 AM on weekdays"""
    check_pending_approvals()
    notify_overdue_tasks()
```

**Step 3: Deploy and enable**
```bash
bench --site sitename migrate
bench --site sitename scheduler enable
```

**Step 4: Verify**
```bash
# Check scheduler status
bench --site sitename scheduler status

# Run task manually for testing
bench --site sitename execute myapp.tasks.cleanup_old_logs
```

---

## Workflow 4: Long Running Task

### Use Case
Heavy data processing that takes 10-20 minutes.

### Steps

**Step 1: Use _long variant**
```python
# myapp/hooks.py

scheduler_events = {
    "daily_long": [
        "myapp.tasks.heavy_data_sync"
    ]
}
```

**Step 2: Implement with progress commits**
```python
# myapp/tasks.py
import frappe

def heavy_data_sync():
    """
    Long task - up to 25 minutes
    Commit periodically to save progress
    """
    records = get_all_records_to_process()
    total = len(records)
    
    for i, record in enumerate(records):
        try:
            process_record(record)
            
            # Commit every 100 records
            if i % 100 == 0:
                frappe.db.commit()
                frappe.publish_progress(
                    percent=int((i / total) * 100),
                    title="Data Sync"
                )
        except Exception as e:
            frappe.log_error(f"Failed {record}: {e}")
            continue
    
    frappe.db.commit()
```

---

## Workflow 5: extend_doctype_class (V16+)

### Use Case
Add custom methods and properties to Sales Invoice without replacing it.

### Steps

**Step 1: Add to hooks.py**
```python
# myapp/hooks.py

extend_doctype_class = {
    "Sales Invoice": ["myapp.extensions.sales_invoice.SalesInvoiceExtension"]
}
```

**Step 2: Create extension class**
```python
# myapp/extensions/sales_invoice.py
import frappe
from frappe.model.document import Document

class SalesInvoiceExtension(Document):
    """
    Mixin class - extends Sales Invoice
    All methods/properties added to Sales Invoice
    """
    
    @property
    def profit_margin_percent(self):
        """Computed property - access as doc.profit_margin_percent"""
        if not self.grand_total:
            return 0
        cost = sum(item.amount for item in self.items)
        return ((self.grand_total - cost) / self.grand_total) * 100
    
    def validate(self):
        """Extend validation"""
        super().validate()  # ALWAYS call super() first!
        self.validate_profit_margin()
        self.set_custom_fields()
    
    def validate_profit_margin(self):
        """Custom validation"""
        if self.profit_margin_percent < 5:
            frappe.msgprint(
                f"Warning: Low margin ({self.profit_margin_percent:.1f}%)",
                indicator="orange"
            )
    
    def set_custom_fields(self):
        """Auto-set custom fields"""
        self.custom_margin = self.profit_margin_percent
    
    def send_to_external_erp(self):
        """Custom method - callable as doc.send_to_external_erp()"""
        # Implementation
        pass
```

**Step 3: Deploy**
```bash
bench --site sitename migrate
```

**Step 4: Use in code**
```python
doc = frappe.get_doc("Sales Invoice", "INV-001")

# Access computed property
print(doc.profit_margin_percent)

# Call custom method
doc.send_to_external_erp()
```

---

## Workflow 6: override_doctype_class (V14/V15)

### Use Case
Modify Sales Invoice behavior when extend is not available.

### Steps

**Step 1: Add to hooks.py**
```python
# myapp/hooks.py

override_doctype_class = {
    "Sales Invoice": "myapp.overrides.sales_invoice.CustomSalesInvoice"
}
```

**Step 2: Create override class**
```python
# myapp/overrides/sales_invoice.py
import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    """
    Complete override - REPLACES SalesInvoice class
    ⚠️ Last installed app wins if multiple apps override!
    """
    
    def validate(self):
        # CRITICAL: Always call super() first!
        super().validate()
        self.custom_validation()
    
    def on_submit(self):
        super().on_submit()
        self.post_submit_actions()
    
    def custom_validation(self):
        if self.grand_total > 1000000:
            frappe.throw("Amount exceeds limit. Use Purchase Order workflow.")
    
    def post_submit_actions(self):
        self.notify_finance_team()
```

---

## Workflow 7: Permission Hooks

### Use Case
Sales users only see their own invoices, managers see all.

### Steps

**Step 1: Add permission hooks**
```python
# myapp/hooks.py

permission_query_conditions = {
    "Sales Invoice": "myapp.permissions.sales_invoice.get_query_conditions"
}

has_permission = {
    "Sales Invoice": "myapp.permissions.sales_invoice.has_permission"
}
```

**Step 2: Implement permission handlers**
```python
# myapp/permissions/sales_invoice.py
import frappe

def get_query_conditions(user):
    """
    Filter for LIST views only.
    Returns SQL WHERE clause fragment.
    
    ⚠️ Only works with get_list, NOT get_all!
    """
    if not user:
        user = frappe.session.user
    
    # Admins and managers see all
    if "System Manager" in frappe.get_roles(user):
        return ""
    if "Sales Manager" in frappe.get_roles(user):
        return ""
    
    # Sales users see only their own
    if "Sales User" in frappe.get_roles(user):
        return f"`tabSales Invoice`.owner = {frappe.db.escape(user)}"
    
    # Others see nothing
    return "1=0"

def has_permission(doc, user=None, permission_type=None):
    """
    Document-level permission check.
    
    Returns:
        True: Allow access
        False: Deny access
        None: Use default permission system
    
    ⚠️ Can only DENY permissions, not grant new ones!
    """
    if not user:
        user = frappe.session.user
    
    # Block editing of closed invoices
    if permission_type == "write" and doc.status == "Closed":
        frappe.throw("Cannot edit closed invoices")
        return False
    
    # Block cancellation after 30 days
    if permission_type == "cancel":
        days_old = frappe.utils.date_diff(frappe.utils.today(), doc.posting_date)
        if days_old > 30:
            frappe.throw("Cannot cancel invoices older than 30 days")
            return False
    
    # Use default for everything else
    return None
```

---

## Workflow 8: extend_bootinfo

### Use Case
Send configuration to client JavaScript.

### Steps

**Step 1: Add to hooks.py**
```python
# myapp/hooks.py

extend_bootinfo = "myapp.boot.extend_with_config"
```

**Step 2: Implement boot handler**
```python
# myapp/boot.py
import frappe

def extend_with_config(bootinfo):
    """
    Add data to frappe.boot object.
    Available in client JS as frappe.boot.xxx
    
    ⚠️ Never send sensitive data (passwords, secrets)!
    """
    # Add app settings
    settings = frappe.get_single("My App Settings")
    bootinfo.my_app = {
        "feature_enabled": settings.feature_enabled,
        "max_items": settings.max_items,
        "api_endpoint": settings.public_api_endpoint
    }
    
    # Add user-specific data
    bootinfo.my_app["user_preferences"] = frappe.db.get_value(
        "User Preference",
        {"user": frappe.session.user},
        ["theme", "notifications"],
        as_dict=True
    ) or {}
```

**Step 3: Access in JavaScript**
```javascript
// Available immediately in any JS file
console.log(frappe.boot.my_app.feature_enabled);

if (frappe.boot.my_app.max_items > 100) {
    // Handle large item lists differently
}
```

---

## Workflow 9: Fixtures Setup

### Use Case
Export Custom Fields and Roles for deployment.

### Steps

**Step 1: Add fixtures configuration**
```python
# myapp/hooks.py

fixtures = [
    # Custom Fields created by this app
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "My App"]]
    },
    # Property Setters (field modifications)
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "My App"]]
    },
    # Custom Roles
    {
        "dt": "Role",
        "filters": [["name", "like", "MyApp%"]]
    },
    # Custom DocType data
    {
        "dt": "My App Config",
        "filters": [["is_default", "=", 1]]
    }
]
```

**Step 2: Export fixtures**
```bash
# Creates JSON files in myapp/fixtures/
bench --site sitename export-fixtures
```

**Step 3: Import on other site**
```bash
# Imports from fixtures folder
bench --site newsite migrate
```

---

## Workflow 10: doctype_js Form Extension

### Use Case
Add custom buttons and behavior to Sales Invoice form.

### Steps

**Step 1: Add to hooks.py**
```python
# myapp/hooks.py

doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js"
}
```

**Step 2: Create JS file**
```javascript
// myapp/public/js/sales_invoice.js

frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
        // Add custom button on submitted invoices
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Send to External ERP"), function() {
                frm.trigger("send_to_erp");
            }, __("Actions"));
        }
        
        // Add indicator
        if (frm.doc.custom_external_id) {
            frm.dashboard.add_indicator(
                __("Synced: {0}", [frm.doc.custom_external_id]),
                "green"
            );
        }
    },
    
    customer: function(frm) {
        // React to customer change
        if (frm.doc.customer) {
            frappe.call({
                method: "myapp.api.get_customer_discount",
                args: { customer: frm.doc.customer },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("discount_percentage", r.message);
                    }
                }
            });
        }
    },
    
    send_to_erp: function(frm) {
        frappe.call({
            method: "myapp.api.send_to_external",
            args: { invoice: frm.doc.name },
            freeze: true,
            freeze_message: __("Sending..."),
            callback: function(r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __("Sent successfully"),
                        indicator: "green"
                    });
                }
            }
        });
    }
});
```

**Step 3: Build assets**
```bash
bench build --app myapp
```

---

## Workflow 11: Website Hooks

### Use Case
Customize portal behavior, add menu items, set up route rules.

### Steps

**Step 1: Add website hooks**
```python
# myapp/hooks.py

# Custom portal menu
portal_menu_items = [
    {"title": "My Orders", "route": "/my-orders", "role": "Customer"},
    {"title": "Support", "route": "/support", "role": "Customer"}
]

# URL routing rules
website_route_rules = [
    {"from_route": "/shop/<category>", "to_route": "shop"},
    {"from_route": "/invoice/<name>", "to_route": "invoice-view"}
]

# Inject context into all web pages
update_website_context = "myapp.website.update_context"

# Custom home page per role
role_home_page = {
    "Customer": "my-orders",
    "Supplier": "my-purchase-orders"
}
```

**Step 2: Implement context handler**
```python
# myapp/website.py
import frappe

def update_context(context):
    """Add data to all web pages."""
    context.company_name = frappe.db.get_single_value(
        "Website Settings", "company"
    ) or "My Company"
```

**Step 3: Deploy**
```bash
bench --site sitename migrate
```

---

## Workflow 12: Session & Auth Hooks

### Use Case
Execute code on login, logout, or session creation.

### Steps

**Step 1: Add session hooks**
```python
# myapp/hooks.py
on_login = "myapp.auth.on_login"
on_session_creation = "myapp.auth.on_session_creation"
on_logout = "myapp.auth.on_logout"
```

**Step 2: Implement handlers**
```python
# myapp/auth.py
import frappe

def on_login(login_manager):
    """Runs after successful login."""
    user = login_manager.user
    frappe.logger().info(f"User logged in: {user}")

    # Example: enforce IP whitelist for admin
    if "System Manager" in frappe.get_roles(user):
        allowed_ips = ["10.0.0.0/8", "192.168.0.0/16"]
        # Validate IP...

def on_session_creation(login_manager):
    """Runs when session is created."""
    pass

def on_logout():
    """Runs on logout — no arguments."""
    frappe.logger().info(f"User logged out: {frappe.session.user}")
```

---

## Workflow 13: Debugging Hooks That Don't Fire

### Checklist

1. **Did you migrate?** `bench --site sitename migrate` — ALWAYS required
2. **Is the path correct?** The dotted path in hooks.py must match the actual module path
3. **Is the module importable?** Run `bench --site sitename execute myapp.events.handler`
4. **Is __init__.py present?** Every directory in the path needs `__init__.py`
5. **Is the app installed?** Check `bench --site sitename list-apps`
6. **For scheduler:** Is scheduler enabled? `bench --site sitename scheduler status`
7. **For scheduler:** Is the worker running? Check `bench --site sitename doctor`
8. **Cache issue?** `bench --site sitename clear-cache`

### Quick Debug Pattern

```python
# Add at the top of your handler to verify it fires
import frappe
def my_handler(doc, method=None):
    frappe.logger("myapp").info(f"Hook fired: {doc.doctype} {doc.name}")
    # ... rest of handler
```

---

## Anti-Patterns to Avoid (Quick Reference)

| Anti-Pattern | Risk | Correct Approach |
|--------------|------|-----------------|
| `frappe.db.commit()` in doc_events | Breaks transaction | Let Frappe commit |
| Modify `doc` in `on_update` | Changes lost | Use `frappe.db.set_value()` |
| Scheduler task with args | Silent failure | No args, fetch data inside |
| Heavy task in default queue | Timeout (5 min) | Use `_long` variant |
| Missing `super()` in override | Breaks core logic | ALWAYS call `super()` first |
| `get_all` with permission_query | Not filtered | Use `get_list` instead |
| Secrets in bootinfo | Exposed in browser | Only public config |
| Fixtures without filters | Captures all apps | ALWAYS filter by module |
| `on_change` + `db_set_value` | Infinite loop | Use flags or `on_update` |
| Multiple apps override same DocType | Last wins (V14/V15) | Use `extend` (V16) |
