# Controller Complete Examples

## Example 1: Basic Document with Validation

```python
# apps/myapp/myapp/hr/doctype/leave_request/leave_request.py
import frappe
from frappe import _
from frappe.model.document import Document

class LeaveRequest(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_days()
        self.check_balance()

    def validate_dates(self):
        if self.from_date > self.to_date:
            frappe.throw(_("From Date cannot be after To Date"))
        if frappe.utils.getdate(self.from_date) < frappe.utils.getdate(frappe.utils.today()):
            frappe.throw(_("Cannot apply for past dates"))

    def calculate_days(self):
        self.total_days = frappe.utils.date_diff(self.to_date, self.from_date) + 1

    def check_balance(self):
        balance = frappe.db.get_value("Leave Allocation",
            {"employee": self.employee, "leave_type": self.leave_type},
            "total_leaves_allocated") or 0
        if self.total_days > balance:
            frappe.throw(_("Insufficient balance. Available: {0}").format(balance))

    def on_update(self):
        manager = frappe.db.get_value("Employee", self.employee, "reports_to")
        if manager:
            user = frappe.db.get_value("Employee", manager, "user_id")
            if user:
                frappe.sendmail(recipients=[user],
                    subject=_("Leave Request from {0}").format(self.employee_name),
                    message=_("{0} days from {1} to {2}").format(
                        self.total_days, self.from_date, self.to_date))
```

## Example 2: Submittable Document with Journal Entry

```python
# apps/myapp/myapp/expense/doctype/expense_claim/expense_claim.py
import frappe
from frappe import _
from frappe.model.document import Document

class ExpenseClaim(Document):
    def validate(self):
        self.validate_amounts()
        self.calculate_totals()

    def validate_amounts(self):
        for item in self.expenses:
            if item.amount <= 0:
                frappe.throw(_("Row {0}: Amount must be positive").format(item.idx))
            if item.amount > 500 and not item.receipt:
                frappe.throw(_("Row {0}: Receipt required for amounts over 500").format(item.idx))

    def calculate_totals(self):
        self.total_amount = sum(item.amount for item in self.expenses)
        self.total_approved = sum(item.approved_amount or 0 for item in self.expenses)

    def before_submit(self):
        if self.total_amount > 5000 and not self.manager_approval:
            frappe.throw(_("Manager approval required for claims over 5,000"))

    def on_submit(self):
        self.create_journal_entry()

    def create_journal_entry(self):
        if self.total_approved <= 0:
            return
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Expense Claim",
            "posting_date": self.posting_date,
            "accounts": [
                {"account": self.expense_account,
                 "debit_in_account_currency": self.total_approved},
                {"account": self.payable_account,
                 "credit_in_account_currency": self.total_approved,
                 "party_type": "Employee", "party": self.employee}
            ]
        })
        je.flags.ignore_permissions = True
        je.submit()
        frappe.db.set_value(self.doctype, self.name, "journal_entry", je.name)

    def before_cancel(self):
        if self.journal_entry:
            status = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
            if status == 1:
                frappe.throw(_("Cancel Journal Entry {0} first").format(self.journal_entry))

    def on_cancel(self):
        if self.advance_reference:
            frappe.db.set_value("Employee Advance", self.advance_reference,
                "claimed_amount", 0)
```

## Example 3: Custom Naming with Customer Code

```python
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries

class Project(Document):
    def autoname(self):
        code = self.get_customer_code()
        year = frappe.utils.getdate(self.start_date or frappe.utils.today()).year
        self.name = getseries(f"PRJ-{code}-{year}-", 3)

    def get_customer_code(self):
        if not self.customer:
            return "GEN"
        code = frappe.db.get_value("Customer", self.customer, "customer_code")
        return (code or self.customer)[:3].upper()

    def validate(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            frappe.throw(_("Start Date cannot be after End Date"))
        if self.tasks:
            completed = sum(1 for t in self.tasks if t.status == "Completed")
            self.percent_complete = (completed / len(self.tasks)) * 100
```

## Example 4: Change Detection with Audit Log

```python
import frappe
from frappe import _
from frappe.model.document import Document

class Contract(Document):
    TRACKED = ['status', 'contract_value', 'end_date', 'party']

    def validate(self):
        old = self.get_doc_before_save()
        if not old:
            self.flags.is_new = True
            return
        changes = []
        for field in self.TRACKED:
            old_val = getattr(old, field)
            new_val = getattr(self, field)
            if old_val != new_val:
                changes.append({'field': field, 'old': old_val, 'new': new_val})
        if changes:
            self.flags.changes = changes
            if any(c['field'] == 'contract_value' for c in changes):
                self.flags.value_changed = True

    def on_update(self):
        if self.flags.get('changes'):
            lines = [f"{frappe.bold(c['field'])}: {c['old']} -> {c['new']}"
                     for c in self.flags.changes]
            self.add_comment("Edit", "<br>".join(lines))

        if self.flags.get('value_changed'):
            for c in self.flags.changes:
                if c['field'] == 'contract_value':
                    frappe.sendmail(recipients=["legal@company.com"],
                        subject=f"Contract Value Changed: {self.name}",
                        message=f"Changed from {c['old']} to {c['new']}")
```

## Example 5: Controller Override with Loyalty Discount

```python
# hooks.py
override_doctype_class = {
    "Sales Invoice": "myapp.overrides.sales_invoice.CustomSalesInvoice"
}

# myapp/overrides/sales_invoice.py
import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        super().validate()
        self.apply_loyalty_discount()
        self.validate_credit_limit()

    def apply_loyalty_discount(self):
        if not self.customer:
            return
        tier = frappe.db.get_value("Customer", self.customer, "loyalty_tier")
        discount = {"Gold": 10, "Silver": 5, "Bronze": 2}.get(tier, 0)
        if discount and not self.loyalty_discount_applied:
            self.additional_discount_percentage = discount
            self.loyalty_discount_applied = 1

    def validate_credit_limit(self):
        if not self.customer or self.is_return:
            return
        limit = frappe.db.get_value("Customer", self.customer, "credit_limit") or 0
        if not limit:
            return
        outstanding = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabSales Invoice`
            WHERE customer = %s AND docstatus = 1 AND name != %s
        """, (self.customer, self.name))[0][0] or 0
        if outstanding + self.grand_total > limit:
            frappe.throw(_("Credit limit ({0}) exceeded").format(limit))

    def on_submit(self):
        super().on_submit()
        self.update_loyalty_points()

    def update_loyalty_points(self):
        if not self.customer:
            return
        points = int(self.grand_total / 100)
        if points > 0:
            current = frappe.db.get_value("Customer", self.customer, "loyalty_points") or 0
            frappe.db.set_value("Customer", self.customer, "loyalty_points", current + points)
```

## Example 6: Tree DocType (NestedSet)

```python
import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet

class Department(NestedSet):
    nsm_parent_field = "parent_department"

    def validate(self):
        if self.parent_department == self.name:
            frappe.throw(_("Cannot be its own parent"))
        if self.tasks:
            self.set_full_path()

    def set_full_path(self):
        parts = [self.department_name]
        parent = self.parent_department
        while parent:
            parts.insert(0, frappe.db.get_value("Department", parent, "department_name"))
            parent = frappe.db.get_value("Department", parent, "parent_department")
        self.full_path = " > ".join(parts)

    def on_trash(self):
        count = frappe.db.count("Employee", {"department": self.name})
        if count:
            frappe.throw(_("Cannot delete: {0} employees").format(count))
```

## Example 7: Whitelisted Methods (Client-Callable)

```python
class Quotation(Document):
    def validate(self):
        self.total = sum(item.amount for item in self.items)

    @frappe.whitelist()
    def apply_discount(self, discount_percent):
        if discount_percent < 0 or discount_percent > 100:
            frappe.throw(_("Discount must be 0-100"))
        self.discount_amount = self.total * (discount_percent / 100)
        self.grand_total = self.total - self.discount_amount
        self.save()
        return {"discount_amount": self.discount_amount,
                "grand_total": self.grand_total}

    @frappe.whitelist()
    def create_sales_order(self):
        if self.docstatus != 1:
            frappe.throw(_("Must be submitted"))
        so = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": self.party_name,
            "items": [{"item_code": i.item_code, "qty": i.qty, "rate": i.rate}
                      for i in self.items]
        })
        so.insert()
        return so.name
```

Client-side:
```javascript
frm.call('apply_discount', { discount_percent: 10 }).then(r => frm.reload_doc());
frm.call('create_sales_order').then(r => frappe.set_route('Form', 'Sales Order', r.message));
```

## Example 8: Virtual DocType (API-Backed)

```python
import frappe
from frappe.model.document import Document
import requests

class ExternalProduct(Document):
    @staticmethod
    def get_list(args):
        resp = requests.get("https://api.example.com/products",
            headers={"Authorization": f"Bearer {get_key()}"})
        if resp.status_code != 200:
            frappe.throw("Failed to fetch products")
        return [frappe._dict(p) for p in resp.json()]

    def load_from_db(self):
        resp = requests.get(f"https://api.example.com/products/{self.name}",
            headers={"Authorization": f"Bearer {get_key()}"})
        if resp.status_code != 200:
            frappe.throw("Not found")
        super(Document, self).__init__(resp.json())

    def db_insert(self, *args, **kwargs):
        data = self.get_valid_dict(convert_dates_to_str=True)
        resp = requests.post("https://api.example.com/products",
            json=data, headers={"Authorization": f"Bearer {get_key()}"})
        if resp.status_code != 201:
            frappe.throw("Failed to create")
        self.name = resp.json().get('id')

def get_key():
    return frappe.db.get_single_value("External API Settings", "api_key")
```
