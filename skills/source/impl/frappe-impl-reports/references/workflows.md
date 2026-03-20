# Report Building Workflows

## Workflow 1: Create a New Script Report

### Step 1 — Create Report Document
1. Navigate to Report List in Desk
2. Click "+ Add Report"
3. Set Report Name (e.g., "Sales Summary")
4. Set Report Type = "Script Report"
5. Set Reference DocType (e.g., "Sales Invoice") — controls permissions
6. Set Module (e.g., "Selling")
7. Check "Is Standard" = Yes (requires Developer Mode)
8. Save

### Step 2 — Write Python File
Location: `my_app/module/report/sales_summary/sales_summary.py`

```python
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "name", "label": _("Invoice"), "fieldtype": "Link",
         "options": "Sales Invoice", "width": 180},
        # Add more columns...
    ]

def get_data(filters):
    return frappe.db.sql("""...""", filters, as_dict=True)
```

### Step 3 — Write JavaScript File
Location: `my_app/module/report/sales_summary/sales_summary.js`

```javascript
frappe.query_reports["Sales Summary"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("company"),
            reqd: 1
        }
    ]
};
```

### Step 4 — Test
1. Run `bench build` to compile JS assets
2. Navigate to the report in Desk
3. Set filters and verify data
4. Check browser console for JS errors

### Step 5 — Add Chart and Summary (Optional)
Extend `execute()` to return chart and summary in positions 4 and 5.

---

## Workflow 2: Add a Dashboard to a Module

### Step 1 — Create Dashboard Charts
Create each chart via Desk > Dashboard Chart:
- Set Chart Name, Chart Type (Report / Group By), source, and time period

### Step 2 — Create Number Cards
Create each card via Desk > Number Card:
- Set Document Type or Report source
- Set aggregate function if Document Type based

### Step 3 — Create Dashboard
1. Desk > Dashboard > New
2. Set Dashboard Name and Module
3. Add charts (Full width or Half width)
4. Add Number Cards
5. Save

### Step 4 — Export as Fixtures
In `hooks.py`:
```python
fixtures = [
    {"dt": "Dashboard", "filters": [["module", "=", "My Module"]]},
    {"dt": "Dashboard Chart", "filters": [["module", "=", "My Module"]]},
    {"dt": "Number Card", "filters": [["module", "=", "My Module"]]},
]
```

Run: `bench --site mysite export-fixtures`

---

## Workflow 3: Convert Report to Prepared Report

### When to Convert
- Report consistently takes > 15 seconds
- Dataset exceeds 50,000 rows
- Users complain about timeouts

### Steps
1. Add `prepared_report: true` to the JS file
2. Test by running the report — it should show "Generate New Report" button
3. Verify background job completes via Background Jobs page
4. ALWAYS keep the Python `execute()` function efficient even for prepared reports — Frappe still calls it, just in a background worker

---

## Workflow 4: Debug a Report Returning Empty Data

### Checklist
1. **Check filters**: Are required filters (`reqd: 1`) set? Empty filters = empty data
2. **Check docstatus**: Are you filtering `docstatus = 1`? Draft documents have `docstatus = 0`
3. **Check column fieldnames**: Do column `fieldname` values match the SQL aliases exactly?
4. **Test SQL directly**: Run the SQL in `bench --site mysite console`:
   ```python
   frappe.db.sql("SELECT ... FROM ... WHERE ...", {"company": "My Company"}, as_dict=True)
   ```
5. **Check permissions**: Does the user have read access to the Reference DocType?
6. **Check return order**: Is `execute()` returning `columns, data` (not `data, columns`)?

---

## Workflow 5: Add Drill-Down Links to Report

Make report cells clickable to navigate to the source document:

```python
# Use Link fieldtype with options pointing to the DocType
{"fieldname": "invoice", "label": _("Invoice"), "fieldtype": "Link",
 "options": "Sales Invoice", "width": 180}
```

For dynamic links (different DocType per row), use `Dynamic Link`:
```python
{"fieldname": "reference_name", "label": _("Reference"), "fieldtype": "Dynamic Link",
 "options": "reference_type", "width": 180},
{"fieldname": "reference_type", "label": _("Type"), "fieldtype": "Data", "width": 120}
```
