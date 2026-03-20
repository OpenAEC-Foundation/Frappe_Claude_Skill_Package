# Server Script Anti-Patterns

## Sandbox Violations

### AP-1: Using Import Statements

```python
# WRONG — All imports blocked
import json
from datetime import datetime
from frappe.utils import nowdate
```

```python
# CORRECT — Use pre-loaded namespace
data = frappe.parse_json(doc.custom_json)   # or json.loads()
today = frappe.utils.now()
date = frappe.utils.nowdate()
```

### AP-2: File System Access

```python
# WRONG — open() is blocked
with open('/tmp/data.json', 'r') as f:
    data = f.read()
```

```python
# CORRECT — Use Frappe's file handling
file_doc = frappe.get_doc("File", {"file_url": doc.attachment})
content = file_doc.get_content()
```

### AP-3: Dynamic Code Execution

```python
# WRONG — eval/exec blocked
result = eval(doc.price_formula)
```

```python
# CORRECT — Explicit logic or safe_eval (v15+)
if doc.price_type == "markup":
    result = doc.cost * (1 + doc.markup_percent / 100)
```

## Database Mistakes

### AP-4: SQL Injection

```python
# WRONG — String formatting
results = frappe.db.sql(f"SELECT * FROM `tabItem` WHERE name = '{name}'")
```

```python
# CORRECT — Parameterized queries
results = frappe.db.sql("""
    SELECT * FROM `tabItem` WHERE name = %(name)s
""", {"name": name}, as_dict=True)
```

### AP-5: N+1 Query Problem

```python
# WRONG — Query per item
for item in doc.items:
    stock = frappe.db.get_value("Bin",
        {"item_code": item.item_code}, "actual_qty")
```

```python
# CORRECT — Batch fetch
codes = [item.item_code for item in doc.items]
stock_data = frappe.db.get_all("Bin",
    filters={"item_code": ["in", codes]},
    fields=["item_code", "actual_qty"])
stock_map = {s["item_code"]: s["actual_qty"] for s in stock_data}
for item in doc.items:
    item.available_qty = stock_map.get(item.item_code, 0)
```

### AP-6: Commit in Document Events

```python
# WRONG — Framework handles commits in doc events
doc.total = calculate_total(doc)
frappe.db.commit()
```

```python
# CORRECT — No commit needed
doc.total = calculate_total(doc)
```

### AP-7: Missing Commit in Scheduler

```python
# WRONG — Changes may not persist
for inv in overdue:
    frappe.db.set_value("Sales Invoice", inv.name, "overdue_notified", 1)
# Missing commit!
```

```python
# CORRECT — ALWAYS commit in scheduler scripts
for inv in overdue:
    frappe.db.set_value("Sales Invoice", inv.name, "overdue_notified", 1)
frappe.db.commit()
```

## Event Selection Mistakes

### AP-8: Validation in After Save

```python
# WRONG — Document already saved
# Event: After Save
if doc.grand_total < 0:
    frappe.throw("Total cannot be negative")  # Too late!
```

```python
# CORRECT — Validate in Before Save
# Event: Before Save
if doc.grand_total < 0:
    frappe.throw("Total cannot be negative")  # Prevents save
```

### AP-9: Creating Documents in Before Save

```python
# WRONG — doc.name may not exist yet
# Event: Before Save
frappe.get_doc({"doctype": "ToDo",
    "reference_name": doc.name}).insert()  # doc.name is None!
```

```python
# CORRECT — Use After Insert or After Save
# Event: After Insert
frappe.get_doc({"doctype": "ToDo",
    "reference_name": doc.name}).insert()  # doc.name guaranteed
```

### AP-10: doc.save() in Before Save

```python
# WRONG — Infinite loop
# Event: Before Save
doc.total = recalculate(doc)
doc.save()  # Triggers Before Save again!
```

```python
# CORRECT — Modify doc directly
# Event: Before Save
doc.total = recalculate(doc)
# Framework saves automatically
```

## API Script Mistakes

### AP-11: Missing Permission Check

```python
# WRONG — Anyone can access
data = frappe.get_doc("Customer", customer).as_dict()
frappe.response["message"] = data
```

```python
# CORRECT — Check permissions
if not frappe.has_permission("Customer", "read", customer):
    frappe.throw("Permission denied", frappe.PermissionError)
data = frappe.db.get_value("Customer", customer,
    ["name", "customer_name"], as_dict=True)  # Only needed fields
frappe.response["message"] = data
```

### AP-12: Not Validating Input

```python
# WRONG — User controls limit
limit = frappe.form_dict.get("limit")
items = frappe.db.get_all("Item", limit=limit)  # Could be 1000000
```

```python
# CORRECT — Validate and cap
limit = min(frappe.utils.cint(frappe.form_dict.get("limit", 20)), 100)
items = frappe.db.get_all("Item", limit=limit)
```

## General Mistakes

### AP-13: Silent Error Swallowing

```python
# WRONG
try:
    process_data()
except:
    pass
```

```python
# CORRECT
try:
    process_data()
except Exception:
    frappe.log_error(f"Failed for {doc.name}", "Processing Error")
```

### AP-14: Using msgprint for Validation

```python
# WRONG — Does NOT stop save
if doc.total < 0:
    frappe.msgprint("Total cannot be negative")
```

```python
# CORRECT — Stops execution and prevents save
if doc.total < 0:
    frappe.throw("Total cannot be negative")
```

### AP-15: Hardcoded Values

```python
# WRONG
if doc.grand_total > 10000:
    doc.requires_approval = 1
```

```python
# CORRECT — Use configurable settings
threshold = frappe.db.get_single_value("Selling Settings",
    "approval_threshold") or 10000
if doc.grand_total > threshold:
    doc.requires_approval = 1
```

### AP-16: get_all in User-Facing Code

```python
# WRONG — get_all bypasses permission query
docs = frappe.db.get_all("Sales Invoice")
```

```python
# CORRECT — get_list applies permission query
docs = frappe.db.get_list("Sales Invoice")
```

## Quick Reference

| Do NOT | Do Instead |
|--------|------------|
| `import json` | `json.loads()` (pre-loaded) or `frappe.parse_json()` |
| `import datetime` | `frappe.utils.getdate()` |
| `open(file)` | `frappe.get_doc("File")` |
| `eval(expr)` | Explicit logic |
| SQL string formatting | Parameterized queries `%(var)s` |
| Query in loop | Batch fetch with `["in", list]` |
| `frappe.db.commit()` in events | Let framework handle |
| Validate in After Save | Validate in Before Save |
| Create docs in Before Save | Create in After Insert/Save |
| `get_all` for user data | `get_list` with permissions |
| `except: pass` | Log and handle errors |
| `msgprint` for errors | `throw` for validation |
