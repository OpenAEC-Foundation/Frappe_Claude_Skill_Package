# Debugging Examples

## Example 1: Server Script Import Error

### Input
```
Error: ImportError: import not allowed in Server Scripts
Script: "Calculate Total" on Sales Invoice validate
```

### Debug Walkthrough

**Step 1 — Classify**: Python error (ImportError in Server Script)

**Step 2 — Mechanism**: Server Script (validate event)

**Step 3 — Locate**: Desk > Server Script > "Calculate Total"

**Step 4 — Diagnose**:
```python
# BROKEN — Server Scripts CANNOT import
import json
data = json.loads(doc.custom_data)
total = sum(item["amount"] for item in data)
doc.grand_total = total
```
Root cause: Server Scripts run in a restricted sandbox. `import` statements are forbidden.

**Step 5 — Fix**:
```python
# CORRECT — use frappe.utils or built-in functions
data = frappe.parse_json(doc.custom_data)
total = sum(item["amount"] for item in data)
doc.grand_total = total
```

**Verification**: Save the Server Script, open a Sales Invoice, modify and save — no error.

**Referenced Skills**: `frappe-errors-serverscripts`, `frappe-syntax-serverscripts`

---

## Example 2: Client Script Async Error

### Input
```
User reports: "I click Calculate button but nothing happens"
No visible error in the form
```

### Debug Walkthrough

**Step 1 — Classify**: JavaScript error (silent failure, check browser console)

**Step 2 — Mechanism**: Client Script (custom button)

**Step 3 — Locate**: Browser DevTools Console shows:
```
Uncaught TypeError: Cannot read properties of undefined (reading 'message')
```

**Step 4 — Diagnose**:
```javascript
// BROKEN — frappe.call is async, result is undefined synchronously
frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        frm.add_custom_button('Calculate', () => {
            let result = frappe.call({
                method: 'myapp.api.calculate',
                args: { invoice: frm.doc.name }
            });
            frm.set_value('grand_total', result.message);  // result is undefined!
        });
    }
});
```
Root cause: `frappe.call()` is asynchronous. The return value is not the response.

**Step 5 — Fix**:
```javascript
// CORRECT — use callback or async/await
frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        frm.add_custom_button('Calculate', () => {
            frappe.call({
                method: 'myapp.api.calculate',
                args: { invoice: frm.doc.name },
                callback(r) {
                    if (r.message) {
                        frm.set_value('grand_total', r.message);
                    }
                }
            });
        });
    }
});
```

**Verification**: Click Calculate button, check that grand_total updates.

**Referenced Skills**: `frappe-errors-clientscripts`, `frappe-impl-clientscripts`

---

## Example 3: Database Column Missing After Deploy

### Input
```
OperationalError: (1054, "Unknown column 'custom_approval_status' in 'field list'")
Traceback points to: frappe/model/db_query.py
```

### Debug Walkthrough

**Step 1 — Classify**: Database error (OperationalError 1054 — column missing)

**Step 2 — Mechanism**: Database query (column does not exist in table)

**Step 3 — Locate**:
```bash
bench --site mysite mariadb
# Then:
DESCRIBE `tabSales Invoice`;
# Confirm: custom_approval_status column is NOT present
```

**Step 4 — Diagnose**:
The Custom Field or DocType field was added but `bench migrate` was not run on this site. The schema is out of sync.

**Step 5 — Fix**:
```bash
# Run migration to sync database schema
bench --site mysite migrate

# Verify column now exists
bench --site mysite mariadb -e "DESCRIBE \`tabSales Invoice\`" | grep custom_approval_status
```

**Verification**: Repeat the operation that caused the error — it should succeed.

**Referenced Skills**: `frappe-errors-database`, `frappe-ops-bench`

---

## Example 4: Permission Error on API Call

### Input
```
frappe.PermissionError: No permission to read Sales Invoice
User: john@example.com, Role: Sales User
But John CAN see Sales Invoices in the list view!
```

### Debug Walkthrough

**Step 1 — Classify**: Permission error

**Step 2 — Mechanism**: API call (whitelisted method or REST endpoint)

**Step 3 — Locate**:
```python
# In bench console, check permissions
frappe.set_user("john@example.com")
frappe.has_permission("Sales Invoice", "read")  # Returns True
frappe.has_permission("Sales Invoice", "read", doc="SINV-00042")  # Returns False!
```

**Step 4 — Diagnose**:
User Permission exists that restricts John to specific company records. SINV-00042 belongs to a different company.

```python
# Check User Permissions
frappe.get_all("User Permission",
    filters={"user": "john@example.com", "allow": "Company"},
    fields=["for_value"])
# Returns: [{"for_value": "My Company LLC"}]

# Check invoice company
frappe.db.get_value("Sales Invoice", "SINV-00042", "company")
# Returns: "Other Company Inc"
```

**Step 5 — Fix**: Either:
1. Add User Permission for "Other Company Inc" for John, OR
2. Remove the Company-level User Permission restriction if John should see all

**Verification**: Re-run `frappe.has_permission("Sales Invoice", "read", doc="SINV-00042")` — returns True.

**Referenced Skills**: `frappe-core-permissions`, `frappe-errors-permissions`

---

## Example 5: Scheduler Job Silently Failing

### Input
```
"My scheduled task should run every hour but nothing happens"
No errors visible in the UI
```

### Debug Walkthrough

**Step 1 — Classify**: Scheduler issue (silent failure)

**Step 2 — Mechanism**: Scheduler event (hooks.py `scheduler_events`)

**Step 3 — Locate**:
```bash
# Check scheduler health
bench doctor
# Output: "Scheduler is disabled for mysite"
```

**Step 4 — Diagnose**:
```bash
# Check scheduler status
bench --site mysite scheduler status
# Output: disabled

# Also check worker status
bench --site mysite worker status
```

Root cause: Scheduler was disabled (common after `bench update` or site restore).

**Step 5 — Fix**:
```bash
# Enable scheduler
bench --site mysite scheduler enable

# Verify
bench doctor
# Should show: scheduler is running

# Check logs for next execution
tail -f sites/mysite/logs/scheduler.log
```

**Verification**: Wait for next scheduled interval, confirm task executes in scheduler.log.

**Referenced Skills**: `frappe-ops-bench`, `frappe-impl-scheduler`

---

## Example 6: v16 extend_doctype_class Missing super()

### Input
```
ValueError: Workflow State not set during Sales Invoice submission
Works in v15, fails in v16 after migration
```

### Debug Walkthrough

**Step 1 — Classify**: Python error (v16 migration issue)

**Step 2 — Mechanism**: Controller using `extend_doctype_class` (v16)

**Step 3 — Locate**:
```python
# In hooks.py (v16 pattern):
# extend_doctype_class = {"Sales Invoice": "myapp.overrides.CustomSalesInvoice"}
```

**Step 4 — Diagnose**:
```python
# BROKEN — missing super() call
class CustomSalesInvoice(SalesInvoice):
    def on_submit(self):
        # Custom logic only — skips ERPNext's on_submit!
        self.create_delivery_note()
```
Root cause: Without `super().on_submit()`, the base class workflow state transition is skipped.

**Step 5 — Fix**:
```python
# CORRECT — ALWAYS call super() first in extend_doctype_class
class CustomSalesInvoice(SalesInvoice):
    def on_submit(self):
        super().on_submit()  # REQUIRED — runs ERPNext's on_submit
        self.create_delivery_note()
```

**Verification**: Submit a Sales Invoice — workflow state transitions correctly and custom logic runs.

**Referenced Skills**: `frappe-errors-controllers`, `frappe-syntax-controllers`
