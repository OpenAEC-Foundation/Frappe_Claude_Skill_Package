---
name: frappe-errors-controllers
description: >
  Use when debugging or preventing errors in Frappe Document Controllers.
  Prevents autoname failures, validate loops, on_submit without is_submittable,
  wrong lifecycle hook choice, get_list permission errors, NestedSet errors,
  extend_doctype_class conflicts, missing super() calls, and recursion without
  flags. Covers error diagnosis by lifecycle phase for v14/v15/v16.
  Keywords: controller error, autoname, validate loop, on_submit, is_submittable,
  get_list, NestedSet, extend_doctype_class, super, flags, recursion guard.
license: MIT
compatibility: "Claude Code, Claude.ai Projects, Claude API. Frappe v14-v16."
metadata:
  author: OpenAEC-Foundation
  version: "2.0"
---

# Controller Errors — Diagnosis and Resolution

Cross-refs: `frappe-syntax-controllers` (syntax), `frappe-impl-controllers` (workflows), `frappe-errors-serverscripts` (server scripts).

---

## Error Diagnosis by Lifecycle Phase

```
CONTROLLER ERROR
│
├─► NAMING PHASE (autoname / before_naming)
│   ├─► NamingSeries not set → Add naming_series field or autoname property
│   ├─► DuplicateEntryError → Name collision, check uniqueness
│   └─► "name cannot be set directly" → Use autoname method, not self.name = x
│
├─► VALIDATION PHASE (before_validate / validate / before_save)
│   ├─► Infinite recursion → doc.save() called inside validate
│   ├─► Validation skipped → Missing super().validate() in override
│   └─► Wrong error timing → Use validate, not on_update, to block save
│
├─► SAVE PHASE (before_save / on_update / after_insert)
│   ├─► Changes lost in on_update → Use db_set(), not self.field = x
│   ├─► Infinite loop → self.save() in on_update triggers on_update again
│   └─► Transaction broken → frappe.db.commit() in controller (DON'T)
│
├─► SUBMIT PHASE (before_submit / on_submit)
│   ├─► "Not allowed to submit" → DocType missing is_submittable = 1
│   ├─► Partial state → Validation in on_submit (too late, already submitted)
│   └─► Stock/GL failures → Entries fail but docstatus already = 1
│
├─► CANCEL PHASE (before_cancel / on_cancel)
│   ├─► "Cannot cancel: linked docs" → Check and handle linked documents
│   └─► Partial cleanup → One reversal fails, rest skipped
│
└─► PERMISSION PHASE (has_permission / get_list)
    ├─► "Not permitted" → has_permission returns None (should be True/False)
    ├─► get_list returns nothing → permission_query_conditions SQL error
    └─► SQL injection → User input in conditions without escape
```

---

## Error Message → Cause → Fix Table

| Error Message | Cause | Fix |
|---------------|-------|-----|
| `NamingSeries is not set` | DocType uses naming_series but field is missing | Add `naming_series` field to DocType or set `autoname` in controller |
| `DuplicateEntryError` | `autoname` generated non-unique name | Use `naming_series` with counter, or add hash suffix |
| `Maximum recursion depth exceeded` | `self.save()` called in validate/on_update | NEVER call `self.save()` in hooks; use `self.db_set()` in on_update |
| `Not allowed to submit` | DocType lacks `is_submittable = 1` | Enable "Is Submittable" in DocType settings |
| `Cannot cancel: linked docs exist` | Submitted linked documents block cancellation | Cancel linked docs first, or use `before_cancel` to check |
| `AttributeError: super()` | Missing `super()` call in overridden hook | ALWAYS call `super().method_name()` first in overrides |
| `Value missing for: field` | Controller validate skipped parent logic | Ensure `super().validate()` is called |
| `frappe.db.commit() breaks transactions` | Manual commit in controller hook | NEVER call `frappe.db.commit()` in controllers |
| `Changes lost in on_update` | Set `self.field = x` instead of `self.db_set()` | Use `self.db_set("field", value)` after save hooks |
| `NestedSet: root cannot be child` | Parent set to itself or circular reference | Validate parent != self in validate, check `lft`/`rgt` |
| `extend_doctype_class conflict` [v16+] | Multiple apps extend same class with conflicting methods | Use MRO-aware design, check method resolution order |
| `has_permission returns wrong result` | Function returns None instead of True/False | ALWAYS return explicit True or False |
| `permission_query_conditions SQL error` | Malformed WHERE clause fragment | Test conditions string independently, use `frappe.db.escape()` |

---

## Critical Error Patterns

### 1. Autoname Failures

```python
# ❌ WRONG — Setting name directly fails
class CustomDoc(Document):
    def autoname(self):
        self.name = f"DOC-{self.customer}"  # May cause DuplicateEntryError

# ✅ CORRECT — Use naming utilities
class CustomDoc(Document):
    def autoname(self):
        # Option 1: Naming series
        from frappe.model.naming import set_name_by_naming_series
        set_name_by_naming_series(self)

        # Option 2: Safe format with counter
        self.name = frappe.model.naming.make_autoname(
            f"DOC-.{self.customer}.-.####"
        )

        # Option 3: Hash for guaranteed uniqueness
        # Set autoname = "hash" in DocType JSON instead
```

**Autoname options**: `naming_series`, `field:fieldname`, `format:PREFIX-{fieldname}-.####`, `hash`, `Prompt`, or custom `autoname()` method.

### 2. Validate Loop: self.save() in Hooks

```python
# ❌ WRONG — Infinite recursion
class SalesOrder(Document):
    def validate(self):
        self.calculate_totals()
        self.save()  # Triggers validate again → infinite loop!

    def on_update(self):
        self.status = "Updated"
        self.save()  # Triggers on_update again → infinite loop!

# ✅ CORRECT — Framework handles save; use db_set after save
class SalesOrder(Document):
    def validate(self):
        self.calculate_totals()
        # No save() — framework saves after validate completes

    def on_update(self):
        self.db_set("status", "Updated")  # Direct DB write, no trigger
```

### 3. on_submit Without is_submittable

```python
# ❌ ERROR — "Not allowed to submit"
class MyDoc(Document):
    def on_submit(self):
        self.create_entries()
# This fails if DocType JSON lacks: "is_submittable": 1

# ✅ FIX — Enable in DocType definition
# In my_doc.json:
# { "is_submittable": 1 }
# Then before_submit and on_submit hooks work
```

### 4. Wrong Lifecycle Hook: Error Timing

```python
# ❌ WRONG — Validation in on_submit (document already submitted!)
class SalesOrder(Document):
    def on_submit(self):
        if not self.has_stock():
            frappe.throw(_("Insufficient stock"))  # docstatus already = 1!

# ✅ CORRECT — ALWAYS validate in before_submit
class SalesOrder(Document):
    def before_submit(self):
        if not self.has_stock():
            frappe.throw(_("Insufficient stock"))  # Clean abort, stays Draft

    def on_submit(self):
        self.create_stock_entries()  # Only post-submit actions here
```

**Transaction Rollback Rules by Hook:**

| Hook | `frappe.throw()` Effect |
|------|------------------------|
| `validate` / `before_save` | Full rollback — document NOT saved |
| `before_submit` | Full rollback — stays Draft |
| `before_cancel` | Full rollback — stays Submitted |
| `on_update` / `after_insert` | Document IS saved — error shown but doc persists |
| `on_submit` | docstatus = 1 — error shown but ALREADY submitted |
| `on_cancel` | docstatus = 2 — error shown but ALREADY cancelled |

### 5. Missing super() in Overrides

```python
# ❌ WRONG — Parent validation completely skipped
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

class CustomSalesOrder(SalesOrder):
    def validate(self):
        # Parent validate() never runs! All ERPNext validations bypassed!
        self.custom_check()

# ✅ CORRECT — ALWAYS call super() first
class CustomSalesOrder(SalesOrder):
    def validate(self):
        super().validate()  # Run all parent validations first
        self.custom_check()  # Then add custom logic
```

### 6. extend_doctype_class [v16+]

```python
# In hooks.py — v16+ preferred approach
extend_doctype_class = {
    "Sales Order": ["myapp.overrides.sales_order.SalesOrderMixin"]
}

# myapp/overrides/sales_order.py
class SalesOrderMixin:
    """Mixin class — extends, does not replace."""
    def validate(self):
        super().validate()  # ALWAYS call super — runs original + other mixins
        self.custom_validation()
```

**Resolution order**: `class ExtendedSalesOrder(Mixin2, Mixin1, OriginalSalesOrder)` — last mixin listed has highest priority.

### 7. Flags for Recursion Guard

```python
# ❌ WRONG — on_update of linked doc triggers this doc's on_update
class SalesOrder(Document):
    def on_update(self):
        self.update_quotation()  # Quotation.on_update triggers back here

# ✅ CORRECT — Use flags to prevent recursion
class SalesOrder(Document):
    def on_update(self):
        if self.flags.get("skip_linked_update"):
            return
        self.flags.skip_linked_update = True
        self.update_quotation()

    def update_quotation(self):
        if self.quotation:
            q = frappe.get_doc("Quotation", self.quotation)
            q.flags.skip_linked_update = True  # Prevent back-trigger
            q.db_set("status", "Ordered")
```

### 8. get_list Permission Errors

```python
# ❌ WRONG — permission_query_conditions returns None (fallback to no filter)
def get_permission_query(user):
    pass  # Returns None — shows ALL records!

# ❌ WRONG — SQL injection
def get_permission_query(user):
    dept = frappe.db.get_value("User", user, "department")
    return f"department = '{dept}'"  # INJECTION RISK

# ✅ CORRECT — Explicit conditions with escape
def get_permission_query(user):
    if "System Manager" in frappe.get_roles(user):
        return ""  # No filter — full access
    dept = frappe.db.get_value("User", user, "department")
    if dept:
        return f"department = {frappe.db.escape(dept)}"
    return "owner = {0}".format(frappe.db.escape(user))
```

**Note**: `permission_query_conditions` affects `frappe.db.get_list()` only, NOT `frappe.db.get_all()`.

### 9. NestedSet Errors

```python
# ❌ WRONG — Circular reference causes lft/rgt corruption
class Territory(NestedSet):
    def validate(self):
        # No parent validation!
        pass

# ✅ CORRECT — Validate parent chain
class Territory(NestedSet):
    def validate(self):
        super().validate()
        if self.parent_territory == self.name:
            frappe.throw(_("Territory cannot be its own parent"))
        # NestedSet.validate() checks circular refs automatically
        # but explicit check gives better error message
```

---

## on_cancel: Isolate Cleanup Operations

```python
# ❌ WRONG — First failure stops all cleanup
def on_cancel(self):
    self.reverse_stock()     # If this fails...
    self.reverse_gl()        # ...this never runs
    self.update_linked()     # ...neither does this

# ✅ CORRECT — Isolate each reversal
def on_cancel(self):
    errors = []
    for operation, label in [
        (self.reverse_stock, "Stock reversal"),
        (self.reverse_gl, "GL reversal"),
        (self.update_linked, "Linked docs"),
    ]:
        try:
            operation()
        except Exception as e:
            errors.append(f"{label}: {str(e)}")
            frappe.log_error(frappe.get_traceback(), f"{label} Error")

    if errors:
        frappe.msgprint(
            _("Cancelled with errors:<br>{0}").format("<br>".join(errors)),
            indicator="orange"
        )
```

---

## ALWAYS / NEVER Rules

### ALWAYS

1. **Call `super().method()` in overridden hooks** — Preserve parent logic
2. **Validate in `before_submit`** not `on_submit` — Last clean abort point
3. **Use `self.db_set()` in `on_update`** — Direct `self.field = x` is lost
4. **Use `self.flags` for recursion guards** — Prevent circular hook triggers
5. **Isolate cleanup operations in `on_cancel`** — Don't let one failure stop all
6. **Use `frappe.db.escape()` in permission queries** — Prevent SQL injection
7. **Return explicit True/False from `has_permission`** — None falls back to default
8. **Use `frappe.log_error()` for unexpected exceptions** — Never swallow silently
9. **Use `_()` wrapper for all user-facing error messages** — Enable translation

### NEVER

1. **NEVER call `self.save()` in validate/on_update** — Causes infinite recursion
2. **NEVER call `frappe.db.commit()` in controllers** — Framework manages transactions
3. **NEVER put blocking validation in `on_submit`** — Document already submitted
4. **NEVER skip `super()` in overridden methods** — Breaks parent class logic
5. **NEVER return None from `has_permission`** — Returns unpredictable results
6. **NEVER swallow exceptions with bare `except: pass`** — Always log errors
7. **NEVER use `override_doctype_class` when `extend_doctype_class` works** [v16+]
8. **NEVER put heavy operations in `validate`** — Use `frappe.enqueue()` from `on_update`

---

## Reference Files

| File | Contents |
|------|----------|
| `references/examples.md` | Real controller error scenarios with diagnosis |
| `references/anti-patterns.md` | Common controller mistakes with fixes |
| `references/patterns.md` | Defensive error handling patterns by lifecycle hook |
