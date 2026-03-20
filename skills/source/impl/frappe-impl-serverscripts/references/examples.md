# Server Script Complete Examples

## Example 1: Comprehensive Invoice Validation

```python
# Type: Document Event | Event: Before Save | DocType: Sales Invoice

errors = []

# Customer validation
if not doc.customer:
    errors.append("Customer is required")
else:
    cust = frappe.db.get_value("Customer", doc.customer,
        ["disabled", "is_frozen"], as_dict=True)
    if cust and cust.disabled:
        errors.append(f"Customer {doc.customer} is disabled")
    if cust and cust.is_frozen:
        errors.append(f"Customer {doc.customer} is frozen")

# Date validation
if doc.posting_date and doc.posting_date > frappe.utils.today():
    errors.append("Posting date cannot be in the future")

# Items validation
if not doc.items:
    errors.append("At least one item is required")
else:
    for item in doc.items:
        if item.qty <= 0:
            errors.append(f"Row {item.idx}: Quantity must be positive")
        if item.rate < 0:
            errors.append(f"Row {item.idx}: Rate cannot be negative")

if doc.discount_percentage and doc.discount_percentage > 50:
    errors.append("Discount cannot exceed 50%")

if errors:
    frappe.throw("<br>".join(errors), title="Validation Errors")
```

## Example 2: Stock Availability Check (Before Submit)

```python
# Type: Document Event | Event: Before Submit | DocType: Sales Order

errors = []
for item in doc.items:
    is_stock = frappe.db.get_value("Item", item.item_code, "is_stock_item")
    if not is_stock:
        continue

    available = frappe.db.get_value("Bin",
        {"item_code": item.item_code, "warehouse": item.warehouse},
        "actual_qty") or 0

    reserved = frappe.db.sql("""
        SELECT COALESCE(SUM(soi.qty - soi.delivered_qty), 0)
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON soi.parent = so.name
        WHERE soi.item_code = %(item)s AND soi.warehouse = %(wh)s
        AND so.docstatus = 1 AND so.name != %(exclude)s
    """, {"item": item.item_code, "wh": item.warehouse,
          "exclude": doc.name})[0][0] or 0

    net = available - reserved
    if item.qty > net:
        errors.append(f"Row {item.idx}: {item.item_code} — "
                      f"Need: {item.qty}, Available: {net}")

if errors:
    frappe.throw("Insufficient stock:<br>" + "<br>".join(errors))
```

## Example 3: Approval Workflow Logic

```python
# Type: Document Event | Event: Before Save | DocType: Purchase Order

MATRIX = [
    {"min": 0, "max": 10000, "role": None},
    {"min": 10000, "max": 50000, "role": "Purchase Manager"},
    {"min": 50000, "max": 100000, "role": "Finance Manager"},
    {"min": 100000, "max": 999999999, "role": "Director"}
]

required_role = None
for level in MATRIX:
    if level["min"] <= doc.grand_total < level["max"]:
        required_role = level["role"]
        break

if required_role is None:
    doc.approval_status = "Approved"
    doc.approved_by = frappe.session.user
elif doc.approval_status == "Approved" and doc.approved_by:
    if required_role not in frappe.get_roles(doc.approved_by):
        frappe.throw(f"Requires approval from {required_role}")
else:
    doc.approval_status = "Pending"
    doc.required_approver_role = required_role
```

## Example 4: CRUD REST API

```python
# Type: API | Method: manage_bookmark | Allow Guest: No

action = frappe.form_dict.get("action")
user = frappe.session.user

if action == "list":
    bookmarks = frappe.get_all("Bookmark",
        filters={"owner": user},
        fields=["name", "title", "url", "category", "creation"],
        order_by="creation desc", limit=50)
    frappe.response["message"] = {"bookmarks": bookmarks}

elif action == "create":
    title = frappe.form_dict.get("title")
    url = frappe.form_dict.get("url")
    if not title or not url:
        frappe.throw("Title and URL are required")
    bm = frappe.get_doc({
        "doctype": "Bookmark", "title": title, "url": url,
        "category": frappe.form_dict.get("category", "General")
    }).insert()
    frappe.response["message"] = {"success": True, "id": bm.name}

elif action == "delete":
    bm_id = frappe.form_dict.get("id")
    if not bm_id:
        frappe.throw("Bookmark ID required")
    bm = frappe.get_doc("Bookmark", bm_id)
    if bm.owner != user:
        frappe.throw("Access denied", frappe.PermissionError)
    bm.delete()
    frappe.response["message"] = {"success": True}

else:
    frappe.throw("Invalid action. Use: list, create, delete")
```

## Example 5: Customer Health Scoring (Scheduler)

```python
# Type: Scheduler Event | Cron: 0 4 * * * (daily 4:00 AM)

BATCH_SIZE = 50
processed = 0
today = frappe.utils.today()
year_ago = frappe.utils.add_days(today, -365)

customers = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name")

for i in range(0, len(customers), BATCH_SIZE):
    batch = customers[i:i + BATCH_SIZE]
    for customer in batch:
        try:
            orders = frappe.db.sql("""
                SELECT COUNT(*) as cnt, COALESCE(SUM(grand_total), 0) as total
                FROM `tabSales Order`
                WHERE customer = %(c)s AND transaction_date >= %(y)s AND docstatus = 1
            """, {"c": customer, "y": year_ago}, as_dict=True)[0]

            outstanding = frappe.db.get_value("Sales Invoice",
                {"customer": customer, "docstatus": 1, "status": "Unpaid"},
                "sum(outstanding_amount)") or 0

            score = 50
            score += 20 if orders.cnt >= 12 else 10 if orders.cnt >= 6 else 0
            score += 15 if orders.total >= 100000 else 10 if orders.total >= 50000 else 0
            score -= 20 if outstanding > 50000 else 10 if outstanding > 10000 else 0
            score = max(0, min(100, score))

            frappe.db.set_value("Customer", customer, {
                "health_score": score, "last_score_date": today
            }, update_modified=False)
            processed += 1
        except Exception:
            frappe.log_error(f"Failed: {customer}", "Health Scoring")
    frappe.db.commit()

frappe.log_error(f"Scored {processed} customers", "Health Scoring Complete")
```

## Example 6: Audit Trail Logger

```python
# Type: Document Event | Event: After Save | DocType: Employee

TRACKED = ["employee_name", "department", "designation", "status",
           "employment_type", "branch", "reports_to"]

if not doc.is_new():
    old = frappe.db.get_value("Employee", doc.name, TRACKED, as_dict=True)
    changes = []
    for field in TRACKED:
        old_val = old.get(field) if old else None
        new_val = doc.get(field)
        if old_val != new_val:
            changes.append({"field": field,
                            "old": str(old_val) if old_val else "",
                            "new": str(new_val) if new_val else ""})

    if changes:
        frappe.get_doc({
            "doctype": "Audit Log",
            "reference_doctype": "Employee",
            "reference_name": doc.name,
            "action": "Update",
            "changed_by": frappe.session.user,
            "changes": frappe.as_json(changes)
        }).insert(ignore_permissions=True)
```

## Example 7: Linked Document Prevention (Before Delete)

```python
# Type: Document Event | Event: Before Delete | DocType: Item

linked = []
for child_dt, label in [
    ("Sales Order Item", "Sales Orders"),
    ("Purchase Order Item", "Purchase Orders"),
    ("Sales Invoice Item", "Sales Invoices"),
    ("Stock Entry Detail", "Stock Entries")]:
    count = frappe.db.count(child_dt, {"item_code": doc.name})
    if count:
        linked.append(f"{label}: {count} line(s)")

stock = frappe.db.get_value("Bin",
    {"item_code": doc.name}, "sum(actual_qty)") or 0
if stock != 0:
    linked.append(f"Current Stock: {stock}")

if linked:
    frappe.throw(f"Cannot delete {doc.name}:<br>" + "<br>".join(linked),
                 title="Deletion Blocked")
```

## Example 8: Hierarchical Territory Permission

```python
# Type: Permission Query | DocType: Customer

user_roles = frappe.get_roles(user)

if "System Manager" in user_roles:
    conditions = ""
else:
    user_territory = frappe.db.get_value("User", user, "territory")
    if user_territory:
        # Get all child territories using lft/rgt
        parent = frappe.db.get_value("Territory", user_territory,
            ["lft", "rgt"], as_dict=True)
        if parent:
            territories = frappe.db.sql("""
                SELECT name FROM `tabTerritory`
                WHERE lft >= %(lft)s AND rgt <= %(rgt)s
            """, parent, pluck="name")
            t_list = ", ".join(frappe.db.escape(t) for t in territories)
            conditions = f"`tabCustomer`.territory IN ({t_list})"
        else:
            conditions = f"`tabCustomer`.owner = {frappe.db.escape(user)}"
    else:
        conditions = f"`tabCustomer`.owner = {frappe.db.escape(user)}"
```

## Example 9: Client + Server Combined Pattern

Client Script:
```javascript
frappe.call({
    method: 'check_credit_limit',
    args: { customer: frm.doc.customer, amount: frm.doc.grand_total },
    callback: function(r) {
        if (!r.message.allowed)
            frappe.throw(__('Credit limit exceeded'));
    }
});
```

Server Script (API type, method: check_credit_limit):
```python
customer = frappe.form_dict.get("customer")
amount = frappe.utils.flt(frappe.form_dict.get("amount"))

credit_limit = frappe.db.get_value("Customer", customer, "credit_limit") or 0
outstanding = frappe.db.get_value("Sales Invoice",
    {"customer": customer, "docstatus": 1, "status": "Unpaid"},
    "sum(outstanding_amount)") or 0

frappe.response["message"] = {
    "allowed": (outstanding + amount) <= credit_limit or credit_limit == 0,
    "available": max(0, credit_limit - outstanding)
}
```
