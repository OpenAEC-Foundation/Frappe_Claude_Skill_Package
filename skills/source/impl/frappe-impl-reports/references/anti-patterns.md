# Report Anti-Patterns

## AP-1: Using SELECT * in Report Queries

**WRONG:**
```python
data = frappe.db.sql("SELECT * FROM `tabSales Invoice` WHERE docstatus = 1", as_dict=True)
```

**RIGHT:**
```python
data = frappe.db.sql("""
    SELECT name, customer, grand_total, posting_date
    FROM `tabSales Invoice`
    WHERE docstatus = 1
""", as_dict=True)
```

**Why**: `SELECT *` fetches unnecessary columns, wastes memory, and breaks when schema changes. ALWAYS specify exact columns.

## AP-2: Loading Full Documents in Report Loops

**WRONG:**
```python
def get_data(filters):
    invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1})
    data = []
    for inv in invoices:
        doc = frappe.get_doc("Sales Invoice", inv.name)  # N+1 query!
        data.append({"name": doc.name, "total": doc.grand_total})
    return data
```

**RIGHT:**
```python
def get_data(filters):
    return frappe.db.sql("""
        SELECT name, grand_total as total
        FROM `tabSales Invoice`
        WHERE docstatus = 1
    """, as_dict=True)
```

**Why**: `frappe.get_doc()` inside a loop creates N+1 queries. For 10,000 invoices, that is 10,001 database calls. ALWAYS use SQL or `frappe.get_all()` with `fields` parameter.

## AP-3: Missing docstatus Filter

**WRONG:**
```python
data = frappe.db.sql("SELECT customer, grand_total FROM `tabSales Invoice`", as_dict=True)
```

**RIGHT:**
```python
data = frappe.db.sql("""
    SELECT customer, grand_total
    FROM `tabSales Invoice`
    WHERE docstatus = 1
""", as_dict=True)
```

**Why**: Without `docstatus = 1`, the report includes Draft (0) and Cancelled (2) documents, producing incorrect totals.

## AP-4: Wrong Column Definition Format

**WRONG — missing fieldtype causes "undefined" display:**
```python
columns = [
    {"fieldname": "customer", "label": "Customer", "width": 200}
]
```

**RIGHT:**
```python
columns = [
    {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link",
     "options": "Customer", "width": 200}
]
```

**Why**: Every column MUST have `fieldtype`. Link columns MUST have `options` pointing to the target DocType. ALWAYS wrap labels in `_()` for translation.

## AP-5: String Concatenation for SQL Filters

**WRONG — SQL injection risk:**
```python
def get_data(filters):
    query = "SELECT name FROM `tabSales Invoice` WHERE customer = '" + filters.get("customer") + "'"
    return frappe.db.sql(query, as_dict=True)
```

**RIGHT:**
```python
def get_data(filters):
    return frappe.db.sql("""
        SELECT name FROM `tabSales Invoice`
        WHERE customer = %(customer)s
    """, filters, as_dict=True)
```

**Why**: NEVER concatenate filter values into SQL strings. ALWAYS use parameterized queries with `%(name)s` placeholders.

## AP-6: Wrong Return Order from execute()

**WRONG — chart in position 3 (message slot):**
```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, chart  # chart is in message position!
```

**RIGHT:**
```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart  # None for message, chart in position 4
```

**Why**: The return order is fixed: columns, data, message, chart, report_summary. Putting chart in position 3 makes Frappe treat it as a message string.

## AP-7: Not Using Prepared Reports for Large Datasets

**WRONG — report times out on production:**
```javascript
frappe.query_reports["Huge Report"] = {
    filters: [ /* ... */ ]
    // No prepared_report flag
};
```

**RIGHT:**
```javascript
frappe.query_reports["Huge Report"] = {
    filters: [ /* ... */ ],
    prepared_report: true
};
```

**Why**: Reports exceeding 50k rows or 30 seconds execution time MUST use `prepared_report: true` to run as background jobs.

## AP-8: Hardcoded Currency in Summary

**WRONG:**
```python
{"value": total, "label": "Revenue", "datatype": "Currency", "currency": "USD"}
```

**RIGHT:**
```python
company_currency = frappe.get_cached_value("Company", filters.get("company"), "default_currency")
{"value": total, "label": _("Revenue"), "datatype": "Currency", "currency": company_currency}
```

**Why**: NEVER hardcode currency. ALWAYS derive it from the Company's default_currency or the transaction's currency field.
