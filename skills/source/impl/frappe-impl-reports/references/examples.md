# Report Examples

## Complete Script Report: Monthly Sales Analysis

### Python (monthly_sales_analysis.py)

```python
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary

def get_columns():
    return [
        {"fieldname": "month", "label": _("Month"), "fieldtype": "Data", "width": 100},
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link",
         "options": "Customer", "width": 180},
        {"fieldname": "invoice_count", "label": _("Invoices"), "fieldtype": "Int", "width": 80},
        {"fieldname": "total_qty", "label": _("Qty"), "fieldtype": "Float", "width": 80},
        {"fieldname": "grand_total", "label": _("Revenue"), "fieldtype": "Currency",
         "options": "Company:company:default_currency", "width": 140},
    ]

def get_data(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND si.company = %(company)s"
    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"

    return frappe.db.sql("""
        SELECT
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
            si.customer,
            COUNT(si.name) AS invoice_count,
            SUM(si.total_qty) AS total_qty,
            SUM(si.grand_total) AS grand_total
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
        GROUP BY month, si.customer
        ORDER BY month DESC, grand_total DESC
    """.format(conditions=conditions), filters, as_dict=True)

def get_chart(data):
    # Aggregate by month for chart
    month_totals = {}
    for row in data:
        month_totals.setdefault(row.month, 0)
        month_totals[row.month] += flt(row.grand_total)

    sorted_months = sorted(month_totals.keys())
    return {
        "data": {
            "labels": sorted_months,
            "datasets": [{"name": _("Revenue"), "values": [month_totals[m] for m in sorted_months]}]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }

def get_summary(data):
    total_revenue = sum(flt(d.grand_total) for d in data)
    total_invoices = sum(d.invoice_count for d in data)
    return [
        {"value": total_revenue, "label": _("Total Revenue"),
         "datatype": "Currency", "indicator": "Green"},
        {"value": total_invoices, "label": _("Total Invoices"),
         "datatype": "Int", "indicator": "Blue"},
    ]
```

### JavaScript (monthly_sales_analysis.js)

```javascript
frappe.query_reports["Monthly Sales Analysis"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("company"),
            reqd: 1
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        }
    ]
};
```

## Query Report: Work Order Status

```sql
SELECT
    `tabWork Order`.name AS "Work Order:Link/Work Order:200",
    `tabWork Order`.production_item AS "Item:Link/Item:150",
    `tabWork Order`.qty AS "Qty:Float:80",
    `tabWork Order`.produced_qty AS "Produced:Float:80",
    (`tabWork Order`.qty - `tabWork Order`.produced_qty) AS "Pending:Float:80",
    `tabWork Order`.status AS "Status:Data:100",
    `tabWork Order`.planned_start_date AS "Start Date:Date:100"
FROM `tabWork Order`
WHERE
    `tabWork Order`.docstatus = 1
    AND `tabWork Order`.status NOT IN ('Completed', 'Cancelled')
    AND `tabWork Order`.company = %(company)s
ORDER BY `tabWork Order`.planned_start_date ASC
```

## Custom Number Card Method

```python
@frappe.whitelist()
def get_overdue_invoices_amount():
    """Number Card: total overdue amount across all unpaid invoices."""
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as value
        FROM `tabSales Invoice`
        WHERE docstatus = 1
            AND outstanding_amount > 0
            AND due_date < CURDATE()
    """, as_dict=True)
    return {
        "value": result[0].value if result else 0,
        "fieldtype": "Currency",
        "route_options": {"outstanding_amount": [">", 0], "due_date": ["<", "today"]},
        "route": ["List", "Sales Invoice"]
    }
```

## Pie Chart Example

```python
def get_chart(data):
    status_counts = {}
    for row in data:
        status_counts.setdefault(row.status, 0)
        status_counts[row.status] += 1

    return {
        "data": {
            "labels": list(status_counts.keys()),
            "datasets": [{"values": list(status_counts.values())}]
        },
        "type": "donut",
        "height": 280
    }
```

## Multi-Dataset Line Chart

```python
def get_chart(current_data, previous_data):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return {
        "data": {
            "labels": months,
            "datasets": [
                {"name": "Current Year", "values": current_data},
                {"name": "Previous Year", "values": previous_data}
            ]
        },
        "type": "line",
        "colors": ["#7cd6fd", "#743ee2"],
        "lineOptions": {"regionFill": 1}
    }
```
