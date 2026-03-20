# Code Validation Examples

## Example 1: Server Script with Import Error

### Code Submitted for Validation

```python
# Server Script: Document Event - Before Save on Sales Invoice
from frappe.utils import nowdate, getdate
import json

if doc.posting_date < getdate(nowdate()):
    data = json.loads(doc.custom_data)
    if data.get("allow_backdating"):
        pass
    else:
        frappe.throw("Backdating not allowed")
```

### Validation Report

```markdown
## Code Validation Report

### Code Type: Server Script (Document Event)
### Target DocType: Sales Invoice
### Event: validate (Before Save)

### CRITICAL ERRORS (Must Fix)

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 2 | `from frappe.utils import` - blocked in sandbox | Use `frappe.utils.nowdate()` directly |
| 2 | 3 | `import json` - blocked in sandbox | Use `frappe.parse_json()` |

### WARNINGS (Should Fix)

| # | Line | Issue | Recommendation |
|---|------|-------|----------------|
| 1 | 5 | No null check on `doc.custom_data` | Add `if doc.custom_data:` |
| 2 | 9 | Generic error message | Include date values |

### Corrected Code

```python
if doc.posting_date < frappe.utils.getdate(frappe.utils.nowdate()):
    if doc.custom_data:
        data = frappe.parse_json(doc.custom_data)
        if not data.get("allow_backdating"):
            frappe.throw(f"Backdating not allowed. Date {doc.posting_date} is before today.")
    else:
        frappe.throw(f"Backdating not allowed. Date {doc.posting_date} is before today.")
```

### Referenced Skills
- frappe-syntax-serverscripts: import rules, doc variable
- frappe-errors-serverscripts: error message patterns
```

---

## Example 2: Client Script with Async Issue

### Code Submitted

```javascript
frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        let customer_data = frappe.call({
            method: 'frappe.client.get_value',
            args: { doctype: 'Customer', filters: {name: frm.doc.customer}, fieldname: 'credit_limit' }
        });
        if (customer_data.message.credit_limit > 0) {
            frm.set_value('credit_limit', customer_data.message.credit_limit);
        }
    }
});
```

### Validation Report

```markdown
### CRITICAL ERRORS

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 3-6 | `frappe.call()` without callback returns undefined | Use callback pattern |
| 2 | 7-8 | Accessing `.message` on undefined value | Will throw TypeError |

### WARNINGS

| # | Line | Issue | Recommendation |
|---|------|-------|----------------|
| 1 | 3 | Missing check for `frm.doc.customer` | Add null check |
| 2 | 8 | No `refresh_field()` after `set_value()` | Add refresh |

### Corrected Code

```javascript
frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        if (!frm.doc.customer) return;

        frappe.call({
            method: 'frappe.client.get_value',
            args: { doctype: 'Customer', filters: {name: frm.doc.customer}, fieldname: 'credit_limit' },
            callback: function(r) {
                if (r.message && r.message.credit_limit > 0) {
                    frm.set_value('credit_limit', r.message.credit_limit);
                    frm.refresh_field('credit_limit');
                }
            }
        });
    }
});
```

### Referenced Skills
- frappe-syntax-clientscripts: async patterns
- frappe-errors-clientscripts: common JS errors
```

---

## Example 3: Controller with on_update Modification

### Code Submitted

```python
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def on_update(self):
        if self.sales_partner:
            commission = self.grand_total * 0.1
            self.commission_amount = commission
            self.custom_commission_status = "Calculated"
```

### Validation Report

```markdown
### CRITICAL ERRORS

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 7-8 | `self.*` in on_update won't be saved | Use `self.db_set()` |

### WARNINGS

| # | Line | Issue | Recommendation |
|---|------|-------|----------------|
| 1 | 4 | Missing `super().on_update()` | Add to preserve parent behavior |
| 2 | 6 | Hardcoded commission rate | Make configurable |

### Corrected Code

```python
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def on_update(self):
        super().on_update()
        if self.sales_partner:
            commission = self.grand_total * 0.1
            self.db_set({
                "commission_amount": commission,
                "custom_commission_status": "Calculated"
            })
```

### Referenced Skills
- frappe-syntax-controllers: lifecycle hooks
- frappe-errors-controllers: on_update pitfall
```

---

## Example 4: v16 extend_doctype_class Missing super()

### Code Submitted

```python
# hooks.py
extend_doctype_class = {
    "Sales Invoice": "my_app.overrides.CustomSalesInvoice"
}
```

```python
# my_app/overrides.py
class CustomSalesInvoice:
    def validate(self):
        self.custom_profit = self.grand_total - self.total_cost
```

### Validation Report

```markdown
### CRITICAL ERRORS

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 3 | Missing `super().validate()` in extend_doctype_class mixin | ALWAYS call super() first |
| 2 | - | `extend_doctype_class` is v16 only | Will fail on v14/v15 |

### Corrected Code

```python
class CustomSalesInvoice:
    def validate(self):
        super().validate()  # MANDATORY in extend_doctype_class
        self.custom_profit = self.grand_total - self.total_cost
```

### Version Compatibility

| Version | Status | Notes |
|---------|--------|-------|
| v14 | FAIL | extend_doctype_class not supported |
| v15 | FAIL | extend_doctype_class not supported |
| v16 | PASS (after fix) | super() required |

### Referenced Skills
- frappe-syntax-hooks: extend_doctype_class syntax
- frappe-syntax-controllers: v16 mixin pattern
```

---

## Example 5: Ops Validation - Missing Migrate

### Scenario Submitted
> "I added scheduler_events to hooks.py and restarted bench, but my scheduled task never runs"

### Validation Report

```markdown
### CRITICAL ERRORS

| # | Issue | Fix |
|---|-------|-----|
| 1 | Missing `bench migrate` after hooks.py change | ALWAYS run `bench --site mysite migrate` after editing hooks.py |

### Diagnostic Steps

1. Run `bench --site mysite migrate`
2. Verify: `bench --site mysite scheduler status` shows "enabled"
3. Check: Setup > Scheduled Job Type > find your task
4. Verify: Task shows correct frequency, Stopped = No
5. Check: Scheduled Job Log for any execution attempts

### Referenced Skills
- frappe-ops-bench: bench migrate requirement
- frappe-impl-scheduler: scheduler registration
```

---

## Example 6: Clean Code (No Issues)

### Code Submitted

```python
# Server Script: Document Event - Before Save on Purchase Order
if doc.supplier:
    supplier = frappe.get_doc("Supplier", doc.supplier)
    if supplier.lead_time_days and doc.transaction_date:
        from_date = frappe.utils.getdate(doc.transaction_date)
        delivery_date = frappe.utils.add_days(from_date, supplier.lead_time_days)
        doc.schedule_date = delivery_date
```

### Validation Report

```markdown
### NO CRITICAL ERRORS
### NO WARNINGS

### SUGGESTIONS

| # | Line | Suggestion |
|---|------|------------|
| 1 | 3 | Use `frappe.db.get_value("Supplier", doc.supplier, "lead_time_days")` for better performance |

### Code Quality: EXCELLENT

- Uses frappe namespace correctly (no imports)
- Uses `doc.` for document access
- Has proper null checks
- Clear purpose

### Version Compatibility

| Version | Status |
|---------|--------|
| v14 | Compatible |
| v15 | Compatible |
| v16 | Compatible |
```

---

## Example 7: Security Validation

### Code Submitted

```python
# Whitelisted method
@frappe.whitelist()
def search_customers(query):
    return frappe.db.sql(f"SELECT name FROM tabCustomer WHERE name LIKE '%{query}%'")
```

### Validation Report

```markdown
### CRITICAL ERRORS

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 4 | SQL INJECTION - raw user input in SQL string | Use parameterized query |
| 2 | 4 | No permission check before database access | Add frappe.has_permission() |

### Corrected Code

```python
@frappe.whitelist()
def search_customers(query: str) -> list:
    if not frappe.has_permission("Customer", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    return frappe.db.sql(
        "SELECT name FROM tabCustomer WHERE name LIKE %s",
        [f"%{query}%"],
        as_dict=True
    )
```

### Referenced Skills
- frappe-core-database: parameterized queries
- frappe-core-permissions: permission checking
- frappe-errors-api: security patterns
```
