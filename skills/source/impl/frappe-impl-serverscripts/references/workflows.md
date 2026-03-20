# Server Script Implementation Workflows

## Category 1: Validation Patterns

### Multi-Field Validation (Collect All Errors)

```python
# Type: Document Event | Event: Before Save | DocType: Sales Order
errors = []

if not doc.customer:
    errors.append("Customer is required")
if doc.delivery_date and doc.delivery_date < frappe.utils.today():
    errors.append("Delivery date cannot be in the past")
if not doc.items or len(doc.items) == 0:
    errors.append("At least one item is required")
for item in doc.items:
    if item.qty <= 0:
        errors.append(f"Row {item.idx}: Quantity must be positive")

if errors:
    frappe.throw("<br>".join(errors), title="Validation Error")
```

### Cross-Document Validation

```python
# Type: Document Event | Event: Before Save | DocType: Delivery Note
if doc.sales_order:
    so = frappe.db.get_value("Sales Order", doc.sales_order,
        ["docstatus", "status"], as_dict=True)
    if not so:
        frappe.throw(f"Sales Order {doc.sales_order} not found")
    if so.docstatus != 1:
        frappe.throw(f"Sales Order {doc.sales_order} is not submitted")
    if so.status == "Closed":
        frappe.throw(f"Sales Order {doc.sales_order} is closed")
```

### Conditional Required Fields

```python
# Type: Document Event | Event: Before Save | DocType: Sales Invoice
if not doc.payment_terms_template and not doc.due_date:
    frappe.throw("Due Date is required when Payment Terms is not set")
if doc.is_shipping_required and not doc.shipping_address:
    frappe.throw("Shipping Address required when shipping is enabled")
```

## Category 2: Auto-Calculation Patterns

### Child Table Aggregation

```python
# Type: Document Event | Event: Before Save | DocType: Purchase Order
for item in doc.items:
    item.amount = (item.qty or 0) * (item.rate or 0)
    item.net_amount = item.amount - (item.discount_amount or 0)

doc.total_qty = sum(item.qty or 0 for item in doc.items)
doc.net_total = sum(item.net_amount or 0 for item in doc.items)

tax_rate = frappe.db.get_value("Tax Template", doc.tax_template, "rate") or 0
doc.tax_amount = doc.net_total * (tax_rate / 100)
doc.grand_total = doc.net_total + doc.tax_amount
```

### Date Calculations

```python
# Type: Document Event | Event: Before Save | DocType: Project
if doc.expected_start_date and doc.estimated_days:
    doc.expected_end_date = frappe.utils.add_days(
        doc.expected_start_date, doc.estimated_days)
if doc.actual_start_date and doc.actual_end_date:
    doc.actual_days = frappe.utils.date_diff(
        doc.actual_end_date, doc.actual_start_date)
```

## Category 3: Notification Patterns

### Conditional Notification on Submit

```python
# Type: Document Event | Event: After Submit | DocType: Sales Order
if doc.grand_total > 100000:
    managers = frappe.get_all("User",
        filters={"role": "Sales Manager", "enabled": 1}, pluck="name")
    for manager in managers:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"High-Value Order: {doc.name}",
            "for_user": manager,
            "type": "Alert",
            "document_type": "Sales Order",
            "document_name": doc.name
        }).insert(ignore_permissions=True)
```

### Email Notification

```python
# Type: Document Event | Event: After Submit | DocType: Purchase Order
email = frappe.db.get_value("Supplier", doc.supplier, "email_id")
if email:
    frappe.sendmail(
        recipients=[email],
        subject=f"Purchase Order {doc.name}",
        message=f"Dear {doc.supplier_name},\n\nPO {doc.name} for {doc.grand_total}.",
        reference_doctype="Purchase Order",
        reference_name=doc.name)
```

## Category 4: Status Management

### Auto-Status Based on Child Items

```python
# Type: Document Event | Event: Before Save | DocType: Sales Order
total_ordered = sum(item.qty or 0 for item in doc.items)
total_delivered = sum(item.delivered_qty or 0 for item in doc.items)

if total_delivered == 0:
    doc.delivery_status = "Not Delivered"
elif total_delivered < total_ordered:
    doc.delivery_status = "Partially Delivered"
else:
    doc.delivery_status = "Fully Delivered"
```

### Cascading Status Update (After Save)

```python
# Type: Document Event | Event: After Save | DocType: Task
if not doc.project:
    return

tasks = frappe.get_all("Task",
    filters={"project": doc.project}, fields=["status"])
total = len(tasks)
completed = len([t for t in tasks if t.status == "Completed"])

status = "Completed" if completed == total else "Open" if completed > 0 else "Pending"
percent = (completed / total * 100) if total > 0 else 0

frappe.db.set_value("Project", doc.project, {
    "status": status, "percent_complete": percent
}, update_modified=False)
```

## Category 5: API Patterns

### Paginated List API

```python
# Type: API | Method: get_orders | Allow Guest: No
page = frappe.utils.cint(frappe.form_dict.get("page", 1))
page_size = min(frappe.utils.cint(frappe.form_dict.get("page_size", 20)), 100)

filters = {"docstatus": 1}
customer = frappe.form_dict.get("customer")
if customer:
    filters["customer"] = customer

if "Sales Manager" not in frappe.get_roles():
    filters["owner"] = frappe.session.user

orders = frappe.get_all("Sales Order",
    filters=filters,
    fields=["name", "customer", "grand_total", "status"],
    order_by="transaction_date desc",
    limit_start=(page - 1) * page_size,
    limit_page_length=page_size)

total = frappe.db.count("Sales Order", filters)

frappe.response["message"] = {
    "data": orders, "page": page, "page_size": page_size,
    "total": total, "pages": -(-total // page_size)
}
```

### Action API with Validation

```python
# Type: API | Method: approve_order | Allow Guest: No
order_name = frappe.form_dict.get("order")
if not order_name:
    frappe.throw("Order parameter is required")

if not frappe.has_permission("Sales Order", "write", order_name):
    frappe.throw("No permission", frappe.PermissionError)
if "Sales Manager" not in frappe.get_roles():
    frappe.throw("Only Sales Managers can approve orders")

order = frappe.get_doc("Sales Order", order_name)
if order.docstatus != 0:
    frappe.throw("Only draft orders can be approved")

order.approval_status = "Approved"
order.approved_by = frappe.session.user
order.save()

frappe.response["message"] = {"success": True, "order": order_name}
```

## Category 6: Scheduler Patterns

### Batch Processing with Chunking

```python
# Type: Scheduler Event | Cron: 0 3 * * *
BATCH_SIZE = 100
processed = 0

while True:
    records = frappe.get_all("Sales Invoice",
        filters={"status": "Unpaid",
                 "due_date": ["<", frappe.utils.add_days(frappe.utils.today(), -30)],
                 "overdue_notified": 0},
        fields=["name"], limit=BATCH_SIZE)
    if not records:
        break
    for rec in records:
        try:
            frappe.db.set_value("Sales Invoice", rec.name, "overdue_notified", 1)
            processed += 1
        except Exception:
            frappe.log_error(f"Failed: {rec.name}", "Overdue Processing")
    frappe.db.commit()

frappe.log_error(f"Processed {processed} invoices", "Overdue Complete")
```

### Weekly Report Generation

```python
# Type: Scheduler Event | Cron: 0 7 * * 1 (Monday 7:00 AM)
week_start = frappe.utils.add_days(frappe.utils.today(), -7)
week_end = frappe.utils.add_days(frappe.utils.today(), -1)

summary = frappe.db.sql("""
    SELECT COUNT(*) as orders, SUM(grand_total) as revenue,
           COUNT(DISTINCT customer) as customers
    FROM `tabSales Order`
    WHERE transaction_date BETWEEN %(s)s AND %(e)s AND docstatus = 1
""", {"s": week_start, "e": week_end}, as_dict=True)[0]

frappe.get_doc({
    "doctype": "Weekly Report",
    "report_date": frappe.utils.today(),
    "total_orders": summary.orders,
    "total_revenue": summary.revenue
}).insert(ignore_permissions=True)
frappe.db.commit()
```

## Category 7: Permission Query Patterns

### Multi-Company Access

```python
# Type: Permission Query | DocType: Sales Invoice
allowed = frappe.get_all("User Permission",
    filters={"user": user, "allow": "Company"}, pluck="for_value")
user_roles = frappe.get_roles(user)

if "System Manager" in user_roles:
    conditions = ""
elif allowed:
    company_list = ", ".join(frappe.db.escape(c) for c in allowed)
    conditions = f"`tabSales Invoice`.company IN ({company_list})"
else:
    default = frappe.db.get_single_value("Global Defaults", "default_company")
    conditions = f"`tabSales Invoice`.company = {frappe.db.escape(default)}" if default else "1=0"
```

### Date-Restricted Access

```python
# Type: Permission Query | DocType: Expense Claim
user_roles = frappe.get_roles(user)

if "System Manager" in user_roles or "HR Manager" in user_roles:
    conditions = ""
elif "Expense Approver" in user_roles:
    team = frappe.get_all("Employee",
        filters={"reports_to": frappe.db.get_value("Employee", {"user_id": user}, "name")},
        pluck="user_id")
    team.append(user)
    user_list = ", ".join(frappe.db.escape(u) for u in team if u)
    conditions = f"`tabExpense Claim`.owner IN ({user_list})"
else:
    month_start = frappe.utils.get_first_day(frappe.utils.today())
    conditions = (f"`tabExpense Claim`.owner = {frappe.db.escape(user)} "
                  f"AND `tabExpense Claim`.posting_date >= {frappe.db.escape(month_start)}")
```
