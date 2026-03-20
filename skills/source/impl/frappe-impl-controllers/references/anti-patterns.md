# Controller Anti-Patterns

## AP-1: Modifying self After on_update

```python
# WRONG — Changes are NOT saved after on_update
def on_update(self):
    self.status = "Completed"           # LOST
    self.processed_date = frappe.utils.today()  # LOST
```

```python
# CORRECT — Use db_set or set_value
def on_update(self):
    frappe.db.set_value(self.doctype, self.name, {
        "status": "Completed",
        "processed_date": frappe.utils.today()
    })
```

## AP-2: Calling self.save() in on_update

```python
# WRONG — Infinite loop: save → on_update → save → on_update...
def on_update(self):
    self.counter = (self.counter or 0) + 1
    self.save()
```

```python
# CORRECT — db_set does NOT trigger hooks
def on_update(self):
    new_counter = (self.counter or 0) + 1
    frappe.db.set_value(self.doctype, self.name, "counter", new_counter,
                       update_modified=False)
```

## AP-3: Manual Commits in Hooks

```python
# WRONG — Breaks transaction management
def validate(self):
    self.do_something()
    frappe.db.commit()  # Breaks rollback on error
```

```python
# CORRECT — Let framework handle transactions
def validate(self):
    self.do_something()
    # No commit — Frappe commits after successful save
```

## AP-4: Heavy Operations in validate

```python
# WRONG — Blocks user UI
def validate(self):
    self.process_large_dataset()    # 30 seconds
    self.sync_to_external_api()     # Network call
```

```python
# CORRECT — Queue heavy work
def validate(self):
    self.validate_fields()       # Quick checks only
    self.calculate_totals()

def on_update(self):
    if self.needs_processing:
        frappe.enqueue('myapp.tasks.process_document',
            queue='long', timeout=300, doc_name=self.name)
```

## AP-5: Not Calling super() in Override

```python
# WRONG — Skips ALL standard ERPNext validation
class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        self.custom_validation()  # Parent validate never runs!
```

```python
# CORRECT — ALWAYS call parent first
class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        super().validate()
        self.custom_validation()
```

## AP-6: Assuming Hook Order Across Documents

```python
# WRONG — Nested hook cycles are unpredictable
def on_update(self):
    other = frappe.get_doc("Other", self.link)
    other.field = "value"
    other.save()  # Triggers Other's full hook cycle
    # Assuming Other's on_update has completed here
```

```python
# CORRECT — Use db_set or flags
def on_update(self):
    frappe.db.set_value("Other", self.link, "field", "value")

# OR with flags to prevent recursion
def on_update(self):
    other = frappe.get_doc("Other", self.link)
    other.flags.from_parent_update = True
    other.field = "value"
    other.save()
```

## AP-7: Bypassing Permissions Without Reason

```python
# WRONG — Security hole
def after_insert(self):
    doc = frappe.get_doc({"doctype": "Task", "subject": "Test"})
    doc.flags.ignore_permissions = True  # Always bypassing
    doc.insert()
```

```python
# CORRECT — Only bypass when justified
def after_insert(self):
    doc = frappe.get_doc({"doctype": "Task", "subject": "Test"})
    # System-generated docs need permission bypass
    doc.flags.ignore_permissions = True
    doc.insert()
    # Document reason: auto-created by system
```

## AP-8: get_doc in Loops

```python
# WRONG — N database queries for same document
def validate(self):
    for item in self.items:
        customer = frappe.get_doc("Customer", self.customer)  # Same query N times
        item.credit_limit = customer.credit_limit
```

```python
# CORRECT — Cache or fetch once
def validate(self):
    customer = frappe.get_cached_doc("Customer", self.customer)
    for item in self.items:
        item.credit_limit = customer.credit_limit

# Or for single values
def validate(self):
    limit = frappe.db.get_value("Customer", self.customer, "credit_limit")
    for item in self.items:
        item.credit_limit = limit
```

## AP-9: Silent Error Swallowing

```python
# WRONG — Errors hidden, impossible to debug
def on_update(self):
    try:
        self.send_notification()
        self.update_external()
    except:
        pass
```

```python
# CORRECT — Log non-critical, fail loudly for critical
def on_update(self):
    try:
        self.send_notification()  # Non-critical
    except Exception:
        frappe.log_error(f"Notification failed: {self.name}")

    self.update_ledger()  # Critical — let it throw
```

## AP-10: Duplicate Logic in validate and before_submit

```python
# WRONG — validate ALREADY runs before before_submit
def validate(self):
    if not self.items:
        frappe.throw(_("Items required"))
    self.total = sum(item.amount for item in self.items)

def before_submit(self):
    if not self.items:                     # Duplicate!
        frappe.throw(_("Items required"))
    self.total = sum(...)                  # Duplicate!
```

```python
# CORRECT — Put common in validate, submit-only in before_submit
def validate(self):
    self.validate_items()
    self.calculate_totals()

def before_submit(self):
    # ONLY submit-specific checks
    if self.total > 50000 and not self.approval:
        frappe.throw(_("Approval required"))
```

## AP-11: Using datetime Instead of frappe.utils

```python
# WRONG — Timezone issues, format incompatibilities
from datetime import datetime, timedelta
self.due_date = datetime.now() + timedelta(days=30)
```

```python
# CORRECT — Uses Frappe's timezone and format handling
self.due_date = frappe.utils.add_days(frappe.utils.today(), 30)
```

## AP-12: Hardcoded Values

```python
# WRONG — Requires code changes for different values
if self.amount > 50000:
    self.requires_approval = 1
self.tax_rate = 0.18
```

```python
# CORRECT — Configurable via Settings
settings = frappe.get_cached_doc("My Settings", "My Settings")
if self.amount > settings.approval_threshold:
    self.requires_approval = 1
self.tax_rate = settings.default_tax_rate
```

## AP-13: Synchronous Emails in Bulk

```python
# WRONG — Blocks until all sent, fails if email server down
def on_submit(self):
    for recipient in self.get_all_recipients():
        frappe.sendmail(recipients=[recipient], subject=..., message=...)
```

```python
# CORRECT — Queue for background
def on_submit(self):
    frappe.sendmail(
        recipients=self.get_all_recipients(),
        subject=f"Document {self.name} submitted",
        message="Submitted.",
        now=False)  # Queue for background sending
```

## Quick Reference

| Do NOT | Do Instead |
|--------|------------|
| `self.x = y` in on_update | `frappe.db.set_value(...)` |
| `self.save()` in on_update | `frappe.db.set_value(...)` |
| `frappe.db.commit()` in hooks | Let framework handle |
| Heavy processing in validate | `frappe.enqueue()` |
| Skip `super().validate()` | ALWAYS call parent |
| `except: pass` | Log errors properly |
| `frappe.get_doc()` in loops | `frappe.get_cached_doc()` |
| Hardcode thresholds/rates | Use Settings DocType |
| Synchronous bulk emails | `now=False` or `frappe.enqueue` |
| Duplicate across hooks | Shared methods |
| `datetime.now()` | `frappe.utils.now()` |
