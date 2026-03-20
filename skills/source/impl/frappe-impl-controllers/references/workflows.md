# Controller Implementation Workflows

## Workflow 1: Field Validation Patterns

### Simple Required
```python
def validate(self):
    if not self.customer:
        frappe.throw(_("Customer is required"))
```

### Conditional Required
```python
def validate(self):
    if self.is_recurring and not self.end_date:
        frappe.throw(_("End Date required for recurring documents"))
```

### Cross-Field
```python
def validate(self):
    if self.from_date and self.to_date and self.from_date > self.to_date:
        frappe.throw(_("From Date cannot be after To Date"))
```

### Link Field
```python
def validate(self):
    if self.customer:
        customer = frappe.get_cached_doc("Customer", self.customer)
        if customer.disabled:
            frappe.throw(_("Customer {0} is disabled").format(self.customer))
```

### Child Table
```python
def validate(self):
    if not self.items:
        frappe.throw(_("At least one item is required"))
    for item in self.items:
        if item.qty <= 0:
            frappe.throw(_("Row {0}: Qty must be positive").format(item.idx))
```

## Workflow 2: Auto-Calculations

### Child Table Totals
```python
def validate(self):
    for item in self.items:
        item.amount = item.qty * item.rate
        item.net_amount = item.amount - (item.discount_amount or 0)
    self.net_total = sum(item.net_amount for item in self.items)
    self.tax_amount = self.net_total * (self.tax_rate / 100)
    self.grand_total = self.net_total + self.tax_amount
```

### Running Totals
```python
def validate(self):
    running = 0
    for item in self.items:
        running += item.amount
        item.running_total = running
```

## Workflow 3: Change Detection

### Detect and Flag
```python
TRACKED = ['status', 'priority', 'assigned_to']

def validate(self):
    old = self.get_doc_before_save()
    if not old:
        return
    changed = [f for f in TRACKED if getattr(old, f) != getattr(self, f)]
    if changed:
        self.flags.changed_fields = changed

def on_update(self):
    if not self.flags.get('changed_fields'):
        return
    changes = []
    old = self.get_doc_before_save()
    for field in self.flags.changed_fields:
        changes.append(f"{field}: {getattr(old, field)} -> {getattr(self, field)}")
    self.add_comment("Edit", "<br>".join(changes))
```

## Workflow 4: Post-Save Notifications

### Email on Status Change
```python
def on_update(self):
    old = self.get_doc_before_save()
    if old and old.status != self.status:
        frappe.sendmail(
            recipients=[self.owner],
            subject=f"{self.doctype} {self.name}: {self.status}",
            message=f"Status changed to {self.status}.")
```

### Background Email (Non-Blocking)
```python
def on_update(self):
    if self.flags.get('status_changed'):
        frappe.enqueue(
            'myapp.notifications.send_status_email',
            queue='short', doc_name=self.name, doctype=self.doctype)
```

## Workflow 5: Linked Documents

### Create Related Document on Insert
```python
def after_insert(self):
    frappe.get_doc({
        "doctype": "Task",
        "subject": f"Follow up: {self.name}",
        "project": self.name,
        "status": "Open"
    }).insert(ignore_permissions=True)
```

### Sync Status to Linked Docs
```python
def on_update(self):
    old = self.get_doc_before_save()
    if old and old.status != self.status:
        linked = frappe.get_all("Child DocType",
            filters={"parent_ref": self.name}, pluck="name")
        for name in linked:
            frappe.db.set_value("Child DocType", name,
                "parent_status", self.status)
```

## Workflow 6: Custom Naming

### Prefix Based on Field
```python
from frappe.model.naming import getseries

def autoname(self):
    prefix = "CUST" if self.party_type == "Customer" else "SUPP"
    self.name = getseries(f"P-{prefix}-", 3)  # P-CUST-001
```

### Date-Based
```python
def autoname(self):
    year = frappe.utils.getdate(self.posting_date).year
    self.name = getseries(f"INV-{year}-", 5)  # INV-2025-00001
```

### Conditional Series
```python
def before_naming(self):
    self.naming_series = "PRIORITY-.#####" if self.is_priority else "STD-.#####"
```

## Workflow 7: Submittable Documents

```python
class PurchaseOrder(Document):
    def validate(self):
        self.validate_items()
        self.calculate_totals()

    def before_submit(self):
        if self.total > 100000 and not self.manager_approval:
            frappe.throw(_("Approval required for POs over 100,000"))

    def on_submit(self):
        self.update_ordered_qty()

    def before_cancel(self):
        if self.has_linked_invoices():
            frappe.throw(_("Cancel linked invoices first"))

    def on_cancel(self):
        self.reverse_ordered_qty()

    def has_linked_invoices(self):
        return frappe.db.exists("Purchase Invoice",
            {"purchase_order": self.name, "docstatus": 1})
```

## Workflow 8: Controller Override

### Full Override
```python
# hooks.py
override_doctype_class = {
    "Sales Invoice": "myapp.overrides.CustomSalesInvoice"
}

# myapp/overrides.py
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        super().validate()  # ALWAYS call parent
        self.apply_loyalty_discount()
```

### Event Handler (No Override)
```python
# hooks.py
doc_events = {
    "Sales Invoice": {
        "validate": "myapp.events.si_validate",
        "on_submit": "myapp.events.si_on_submit"
    }
}

# myapp/events.py
def si_validate(doc, method=None):
    validate_territory_discount(doc)
```

## Workflow 9: Background Jobs

```python
def on_update(self):
    if self.requires_heavy_processing():
        frappe.enqueue(
            'myapp.tasks.process_document',
            queue='long', timeout=600,
            doc_name=self.name)

# myapp/tasks.py
def process_document(doc_name):
    doc = frappe.get_doc("MyDocType", doc_name)
    # Heavy processing
    doc.db_set("processed", 1)
    frappe.db.commit()
```

### With Deduplication (v15+)
```python
frappe.enqueue(
    'myapp.tasks.sync_external',
    queue='default',
    job_id=f"sync_{self.name}",
    deduplicate=True,
    doc_name=self.name)
```

## Workflow 10: Permissions in Controller

### Check Before Action
```python
def on_submit(self):
    if self.grand_total > 50000:
        if not frappe.has_permission(self.doctype, "submit"):
            frappe.throw(_("Not permitted for high-value docs"))
```

### Bypass for System Operations
```python
def after_insert(self):
    task = frappe.get_doc({"doctype": "Task", "subject": f"Follow up: {self.name}"})
    task.flags.ignore_permissions = True
    task.insert()
```

## Workflow 11: Type Annotations (v15+)

Enable in hooks.py:
```python
export_python_type_annotations = True
```

Controller gains auto-generated types:
```python
class Person(Document):
    # begin: auto-generated types
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from frappe.types import DF
        first_name: DF.Data
        last_name: DF.Data
    # end: auto-generated types
```
