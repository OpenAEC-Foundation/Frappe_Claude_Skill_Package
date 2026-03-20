# Frappe Hook Examples

Complete working code examples for common hook scenarios.

---

## Example 1: Credit Limit Check (doc_events.validate)

**Scenario**: Block Sales Invoice if customer exceeds credit limit.

```python
# myapp/hooks.py
doc_events = {
    "Sales Invoice": {
        "validate": "myapp.events.si_credit_check"
    }
}
```

```python
# myapp/events.py
import frappe

def si_credit_check(doc, method=None):
    """Block invoice if exceeds credit limit"""
    if doc.is_return:
        return  # Skip credit returns
    
    customer = frappe.get_doc("Customer", doc.customer)
    
    if not customer.credit_limit:
        return  # No limit set
    
    # Get outstanding amount
    outstanding = frappe.db.sql("""
        SELECT SUM(outstanding_amount)
        FROM `tabSales Invoice`
        WHERE customer = %s
          AND docstatus = 1
          AND name != %s
    """, (doc.customer, doc.name))[0][0] or 0
    
    # Check if new invoice exceeds limit
    total_exposure = outstanding + doc.grand_total
    
    if total_exposure > customer.credit_limit:
        frappe.throw(
            f"Credit limit exceeded. "
            f"Limit: {customer.credit_limit}, "
            f"Outstanding: {outstanding}, "
            f"This invoice: {doc.grand_total}"
        )
```

---

## Example 2: Auto-Create Follow-up Task (doc_events.on_submit)

**Scenario**: Create ToDo when Sales Order is submitted.

```python
# myapp/hooks.py
doc_events = {
    "Sales Order": {
        "on_submit": "myapp.events.create_followup_task"
    }
}
```

```python
# myapp/events.py
import frappe
from frappe.utils import add_days, today

def create_followup_task(doc, method=None):
    """Create follow-up task for sales team"""
    
    # Skip if no delivery date set
    if not doc.delivery_date:
        return
    
    # Create follow-up 2 days before delivery
    followup_date = add_days(doc.delivery_date, -2)
    
    # Don't create if already passed
    if followup_date < today():
        return
    
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": f"Follow up on delivery for {doc.name}",
        "reference_type": "Sales Order",
        "reference_name": doc.name,
        "allocated_to": doc.owner,
        "date": followup_date,
        "priority": "High" if doc.grand_total > 100000 else "Medium"
    })
    todo.insert(ignore_permissions=True)
    
    frappe.msgprint(f"Follow-up task created for {followup_date}")
```

---

## Example 3: Audit Trail (doc_events wildcard)

**Scenario**: Log all document changes for compliance.

```python
# myapp/hooks.py
doc_events = {
    "*": {
        "after_insert": "myapp.audit.log_insert",
        "on_update": "myapp.audit.log_update",
        "on_trash": "myapp.audit.log_delete",
        "on_submit": "myapp.audit.log_submit",
        "on_cancel": "myapp.audit.log_cancel"
    }
}
```

```python
# myapp/audit.py
import frappe
import json

# DocTypes to skip
SKIP_DOCTYPES = {
    "Error Log", "Activity Log", "Audit Log", 
    "Communication", "Email Queue", "Version"
}

def log_insert(doc, method=None):
    if doc.doctype not in SKIP_DOCTYPES:
        create_log(doc, "Created")

def log_update(doc, method=None):
    if doc.doctype not in SKIP_DOCTYPES:
        create_log(doc, "Updated")

def log_delete(doc, method=None):
    if doc.doctype not in SKIP_DOCTYPES:
        create_log(doc, "Deleted")

def log_submit(doc, method=None):
    if doc.doctype not in SKIP_DOCTYPES:
        create_log(doc, "Submitted")

def log_cancel(doc, method=None):
    if doc.doctype not in SKIP_DOCTYPES:
        create_log(doc, "Cancelled")

def create_log(doc, action):
    """Create audit log entry"""
    frappe.get_doc({
        "doctype": "Audit Log",
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "action": action,
        "user": frappe.session.user,
        "ip_address": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None,
        "data": json.dumps(doc.as_dict(), default=str)[:65535]
    }).insert(ignore_permissions=True)
```

---

## Example 4: Daily Cleanup Task (scheduler_events.daily)

**Scenario**: Clean up old error logs and temporary files.

```python
# myapp/hooks.py
scheduler_events = {
    "daily": [
        "myapp.tasks.daily_cleanup"
    ]
}
```

```python
# myapp/tasks.py
import frappe
from frappe.utils import add_days, today

def daily_cleanup():
    """
    Daily cleanup task - runs in default queue.
    NO arguments - scheduler calls without args.
    """
    cleanup_error_logs()
    cleanup_temp_files()
    cleanup_old_versions()
    
    frappe.db.commit()

def cleanup_error_logs():
    """Delete error logs older than 30 days"""
    cutoff = add_days(today(), -30)
    
    frappe.db.delete("Error Log", {
        "creation": ["<", cutoff]
    })
    
    frappe.logger().info(f"Cleaned error logs older than {cutoff}")

def cleanup_temp_files():
    """Delete temporary uploaded files"""
    cutoff = add_days(today(), -7)
    
    temp_files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "",
            "creation": ["<", cutoff]
        },
        pluck="name"
    )
    
    for name in temp_files:
        try:
            frappe.delete_doc("File", name, ignore_permissions=True)
        except Exception:
            pass

def cleanup_old_versions():
    """Keep only last 10 versions per document"""
    # Get documents with many versions
    docs_with_versions = frappe.db.sql("""
        SELECT ref_doctype, docname, COUNT(*) as cnt
        FROM tabVersion
        GROUP BY ref_doctype, docname
        HAVING cnt > 10
    """, as_dict=True)
    
    for row in docs_with_versions:
        # Get versions to delete (keep newest 10)
        to_delete = frappe.get_all(
            "Version",
            filters={
                "ref_doctype": row.ref_doctype,
                "docname": row.docname
            },
            order_by="creation desc",
            pluck="name",
            start=10
        )
        
        for name in to_delete:
            frappe.delete_doc("Version", name, ignore_permissions=True)
```

---

## Example 5: Weekly Report (scheduler_events.cron)

**Scenario**: Send sales summary every Monday at 9 AM.

```python
# myapp/hooks.py
scheduler_events = {
    "cron": {
        "0 9 * * 1": [  # Monday 9:00 AM
            "myapp.tasks.send_weekly_sales_report"
        ]
    }
}
```

```python
# myapp/tasks.py
import frappe
from frappe.utils import add_days, today, fmt_money

def send_weekly_sales_report():
    """Send weekly sales summary to managers"""
    
    # Get last week's date range
    end_date = add_days(today(), -1)  # Yesterday
    start_date = add_days(end_date, -6)  # 7 days ago
    
    # Compile statistics
    stats = get_sales_stats(start_date, end_date)
    
    # Get recipients
    recipients = frappe.get_all(
        "User",
        filters={
            "enabled": 1,
            "user_type": "System User"
        },
        or_filters=[
            ["role", "like", "%Sales Manager%"],
            ["role", "like", "%System Manager%"]
        ],
        pluck="email"
    )
    
    if not recipients:
        return
    
    # Send email
    frappe.sendmail(
        recipients=recipients,
        subject=f"Weekly Sales Report: {start_date} to {end_date}",
        message=render_report(stats, start_date, end_date),
        delayed=False
    )

def get_sales_stats(start_date, end_date):
    """Get sales statistics for date range"""
    return frappe.db.sql("""
        SELECT 
            COUNT(*) as invoice_count,
            SUM(grand_total) as total_sales,
            SUM(outstanding_amount) as outstanding,
            COUNT(DISTINCT customer) as unique_customers
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND posting_date BETWEEN %s AND %s
    """, (start_date, end_date), as_dict=True)[0]

def render_report(stats, start_date, end_date):
    """Render email content"""
    return f"""
    <h2>Weekly Sales Summary</h2>
    <p>Period: {start_date} to {end_date}</p>
    
    <table border="1" cellpadding="10">
        <tr><td><b>Total Invoices</b></td><td>{stats.invoice_count}</td></tr>
        <tr><td><b>Total Sales</b></td><td>{fmt_money(stats.total_sales)}</td></tr>
        <tr><td><b>Outstanding</b></td><td>{fmt_money(stats.outstanding)}</td></tr>
        <tr><td><b>Unique Customers</b></td><td>{stats.unique_customers}</td></tr>
    </table>
    """
```

---

## Example 6: Heavy Data Sync (scheduler_events.daily_long)

**Scenario**: Sync large dataset with external system (takes 15-20 minutes).

```python
# myapp/hooks.py
scheduler_events = {
    "daily_long": [  # Long queue - 25 min timeout
        "myapp.tasks.sync_external_data"
    ]
}
```

```python
# myapp/tasks.py
import frappe

def sync_external_data():
    """
    Heavy sync task - runs in LONG queue.
    Commits periodically to avoid losing progress.
    """
    records = get_records_to_sync()
    total = len(records)
    synced = 0
    failed = 0
    
    for i, record in enumerate(records):
        try:
            sync_single_record(record)
            synced += 1
        except Exception as e:
            frappe.log_error(
                f"Sync failed for {record.name}: {e}",
                "External Sync Error"
            )
            failed += 1
        
        # Commit every 50 records
        if (i + 1) % 50 == 0:
            frappe.db.commit()
            frappe.logger().info(f"Sync progress: {i+1}/{total}")
    
    # Final commit
    frappe.db.commit()
    
    # Log summary
    frappe.logger().info(
        f"Sync complete: {synced} synced, {failed} failed, {total} total"
    )

def get_records_to_sync():
    """Get records needing sync"""
    return frappe.get_all(
        "Customer",
        filters={
            "custom_needs_sync": 1,
            "custom_last_sync": ["<", frappe.utils.add_days(None, -1)]
        },
        fields=["name", "customer_name", "custom_external_id"]
    )

def sync_single_record(record):
    """Sync single record to external system"""
    # Your sync logic here
    pass
```

---

## Example 7: extend_doctype_class (V16+)

**Scenario**: Add profit margin tracking to Sales Invoice.

```python
# myapp/hooks.py
extend_doctype_class = {
    "Sales Invoice": ["myapp.extensions.SalesInvoiceProfitMixin"]
}
```

```python
# myapp/extensions.py
import frappe
from frappe.model.document import Document

class SalesInvoiceProfitMixin(Document):
    """
    Mixin to add profit tracking to Sales Invoice.
    V16+ only - multiple apps can extend same DocType.
    """
    
    @property
    def total_cost(self):
        """Calculate total cost from items"""
        return sum(
            (item.qty * (item.incoming_rate or 0))
            for item in self.items
        )
    
    @property
    def profit_amount(self):
        """Calculate profit"""
        return self.grand_total - self.total_cost
    
    @property
    def profit_margin_percent(self):
        """Calculate profit margin percentage"""
        if self.grand_total:
            return (self.profit_amount / self.grand_total) * 100
        return 0
    
    def validate(self):
        """Extend validation"""
        super().validate()
        self.validate_minimum_margin()
        self.set_profit_fields()
    
    def validate_minimum_margin(self):
        """Warn if margin too low"""
        min_margin = frappe.db.get_single_value(
            "Selling Settings", "custom_min_margin_percent"
        ) or 5
        
        if self.profit_margin_percent < min_margin:
            frappe.msgprint(
                f"Warning: Profit margin ({self.profit_margin_percent:.1f}%) "
                f"is below minimum ({min_margin}%)",
                indicator="orange",
                alert=True
            )
    
    def set_profit_fields(self):
        """Set custom profit fields"""
        self.custom_profit_amount = self.profit_amount
        self.custom_profit_margin = self.profit_margin_percent
    
    def get_profit_breakdown(self):
        """Custom method - get detailed profit breakdown"""
        breakdown = []
        for item in self.items:
            cost = item.qty * (item.incoming_rate or 0)
            profit = item.amount - cost
            margin = (profit / item.amount * 100) if item.amount else 0
            breakdown.append({
                "item_code": item.item_code,
                "amount": item.amount,
                "cost": cost,
                "profit": profit,
                "margin_percent": margin
            })
        return breakdown
```

**Usage**:
```python
doc = frappe.get_doc("Sales Invoice", "INV-001")
print(doc.profit_margin_percent)  # Property
print(doc.get_profit_breakdown())  # Method
```

---

## Example 8: Permission Query (permission_query_conditions)

**Scenario**: Territory-based access control.

```python
# myapp/hooks.py
permission_query_conditions = {
    "Customer": "myapp.permissions.customer_query",
    "Sales Invoice": "myapp.permissions.si_query"
}
```

```python
# myapp/permissions.py
import frappe

def customer_query(user):
    """
    Filter Customer list by user's territory.
    Returns SQL WHERE fragment.
    """
    if not user:
        user = frappe.session.user
    
    # System managers see all
    if "System Manager" in frappe.get_roles(user):
        return ""
    
    # Get user's territories
    territories = get_user_territories(user)
    
    if not territories:
        return "1=0"  # No access
    
    # Build territory filter
    territory_list = ", ".join(frappe.db.escape(t) for t in territories)
    return f"`tabCustomer`.territory IN ({territory_list})"

def si_query(user):
    """Filter Sales Invoice by customer territory"""
    if not user:
        user = frappe.session.user
    
    if "System Manager" in frappe.get_roles(user):
        return ""
    
    territories = get_user_territories(user)
    
    if not territories:
        return "1=0"
    
    # Join with Customer to filter by territory
    territory_list = ", ".join(frappe.db.escape(t) for t in territories)
    return f"""
        `tabSales Invoice`.customer IN (
            SELECT name FROM `tabCustomer` 
            WHERE territory IN ({territory_list})
        )
    """

def get_user_territories(user):
    """Get territories assigned to user"""
    return frappe.get_all(
        "User Territory",  # Custom DocType
        filters={"user": user},
        pluck="territory"
    )
```

---

## Example 9: Has Permission (Document-Level)

**Scenario**: Complex permission rules based on document state.

```python
# myapp/hooks.py
has_permission = {
    "Sales Invoice": "myapp.permissions.si_has_permission"
}
```

```python
# myapp/permissions.py
import frappe

def si_has_permission(doc, user=None, permission_type=None):
    """
    Document-level permission check.
    
    Returns:
        True: Allow
        False: Deny
        None: Use default
    
    NOTE: Can only DENY, not grant new permissions!
    """
    if not user:
        user = frappe.session.user
    
    # System managers always pass
    if "System Manager" in frappe.get_roles(user):
        return None
    
    # Rule 1: No editing closed invoices
    if permission_type == "write":
        if doc.status == "Closed":
            frappe.throw("Cannot edit closed invoices")
            return False
    
    # Rule 2: No cancellation after 30 days
    if permission_type == "cancel":
        days_old = frappe.utils.date_diff(
            frappe.utils.today(), 
            doc.posting_date
        )
        if days_old > 30:
            frappe.throw("Cannot cancel invoices older than 30 days")
            return False
    
    # Rule 3: Only finance can see draft invoices > 100k
    if permission_type == "read" and doc.docstatus == 0:
        if doc.grand_total > 100000:
            if "Accounts Manager" not in frappe.get_roles(user):
                return False
    
    # Rule 4: Only owner can delete drafts
    if permission_type == "delete":
        if doc.owner != user:
            frappe.throw("Only the creator can delete this invoice")
            return False
    
    # Use default permission system
    return None
```

---

## Example 10: Complete hooks.py Template

**Scenario**: Full-featured custom app hooks.

```python
# myapp/hooks.py

app_name = "myapp"
app_title = "My App"
app_publisher = "My Company"
app_description = "Custom ERPNext Extensions"
app_version = "1.0.0"

# Document Events
doc_events = {
    "*": {
        "after_insert": "myapp.audit.log_create",
        "on_trash": "myapp.audit.log_delete"
    },
    "Sales Invoice": {
        "validate": "myapp.events.si.validate",
        "on_submit": "myapp.events.si.on_submit"
    },
    "Sales Order": {
        "on_submit": "myapp.events.so.create_followup"
    }
}

# Scheduler Events
scheduler_events = {
    "daily": [
        "myapp.tasks.daily_cleanup"
    ],
    "daily_long": [
        "myapp.tasks.sync_external"
    ],
    "cron": {
        "0 9 * * 1": ["myapp.tasks.monday_report"],
        "0 17 * * 5": ["myapp.tasks.friday_summary"]
    }
}

# DocType Extensions (V16+)
extend_doctype_class = {
    "Sales Invoice": ["myapp.extensions.SalesInvoiceMixin"],
    "Customer": ["myapp.extensions.CustomerMixin"]
}

# Permission Hooks
permission_query_conditions = {
    "Customer": "myapp.permissions.customer_query",
    "Sales Invoice": "myapp.permissions.si_query"
}

has_permission = {
    "Sales Invoice": "myapp.permissions.si_permission"
}

# Boot Info
extend_bootinfo = "myapp.boot.extend"

# Fixtures
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "My App"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "My App"]]},
    {"dt": "Role", "filters": [["name", "like", "MyApp%"]]}
]

# Assets
app_include_js = "/assets/myapp/js/myapp.min.js"
app_include_css = "/assets/myapp/css/myapp.min.css"

doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Customer": "public/js/customer.js"
}

# Install/Migrate Hooks
after_install = "myapp.setup.after_install"
after_migrate = "myapp.setup.after_migrate"
```
