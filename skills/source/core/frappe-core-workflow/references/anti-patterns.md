# Workflow Engine Anti-Patterns

## Anti-Pattern 1: Calling doc.submit() on Workflow-Controlled Documents

**NEVER** call `doc.submit()` or `doc.cancel()` directly when a workflow is active.

```python
# WRONG — bypasses workflow validation
doc = frappe.get_doc("Purchase Order", "PO-00001")
doc.submit()  # Raises WorkflowPermissionError or creates inconsistent state

# CORRECT — use the workflow engine
from frappe.model.workflow import apply_workflow
apply_workflow(doc, "Approve")  # Engine handles submit/cancel internally
```

**Why:** The workflow engine manages docstatus transitions. Calling submit/cancel directly bypasses state validation, self-approval checks, and transition tasks.

## Anti-Pattern 2: DocStatus Going Backwards

**NEVER** create transitions where docstatus decreases.

```python
# WRONG — submitted (1) back to draft (0)
{"state": "Approved", "doc_status": "1"},   # source
{"state": "Revision", "doc_status": "0"},   # target — INVALID

# CORRECT — keep submitted documents at docstatus 1
{"state": "Approved", "doc_status": "1"},
{"state": "Under Revision", "doc_status": "1"},  # Still submitted, just different state
```

**Why:** Frappe enforces `1 → 0` is illegal. The engine will throw "Submitted Document cannot be converted back to draft."

## Anti-Pattern 3: Skipping DocStatus 1 (Draft to Cancelled)

**NEVER** create a transition from `doc_status = 0` to `doc_status = 2`.

```python
# WRONG — draft directly to cancelled
{"state": "Draft", "doc_status": "0"},
{"state": "Cancelled", "doc_status": "2"},  # Cannot cancel before submitting

# CORRECT — go through submitted first
{"state": "Draft", "doc_status": "0"},
{"state": "Approved", "doc_status": "1"},
{"state": "Cancelled", "doc_status": "2"},
```

## Anti-Pattern 4: Transitions from Cancelled State

**NEVER** add outgoing transitions from a state with `doc_status = 2`.

```python
# WRONG — cannot transition from cancelled
{"state": "Cancelled", "action": "Reopen", "next_state": "Draft"}
# Throws: "Cannot change state of Cancelled Document"

# CORRECT — use Amend (creates a new document) instead of reopen
```

## Anti-Pattern 5: Non-Submittable DocType with DocStatus > 0

**NEVER** set `doc_status = 1` or `doc_status = 2` on a non-submittable DocType.

```python
# WRONG — Task is not submittable
{"state": "Completed", "doc_status": "1"}
# Throws: "DocType 'Task' is not submittable. Only Document Status 0 is allowed"

# CORRECT
{"state": "Completed", "doc_status": "0"}
```

## Anti-Pattern 6: Dead-End States Without Intent

**NEVER** leave a state with no outgoing transitions unless it is a deliberate terminal state.

```python
# WRONG — "On Hold" has no way out
states = [
    {"state": "Draft", "doc_status": "0"},
    {"state": "On Hold", "doc_status": "0"},  # Dead end!
    {"state": "Approved", "doc_status": "1"},
]
transitions = [
    {"state": "Draft", "action": "Hold", "next_state": "On Hold", "allowed": "Manager"},
    {"state": "Draft", "action": "Approve", "next_state": "Approved", "allowed": "Manager"},
]
# Document gets stuck in "On Hold" forever

# CORRECT — add a way back
transitions = [
    {"state": "Draft", "action": "Hold", "next_state": "On Hold", "allowed": "Manager"},
    {"state": "On Hold", "action": "Resume", "next_state": "Draft", "allowed": "Manager"},
    {"state": "Draft", "action": "Approve", "next_state": "Approved", "allowed": "Manager"},
]
```

## Anti-Pattern 7: Missing Self-Approval Check on Approval Transitions

**ALWAYS** explicitly set `allow_self_approval = 0` on approval transitions in financial/compliance workflows.

```python
# WRONG — creator can approve their own expense claim (default is allow_self_approval=1)
{"state": "Pending", "action": "Approve", "next_state": "Approved",
 "allowed": "Expense Approver"}

# CORRECT — block self-approval
{"state": "Pending", "action": "Approve", "next_state": "Approved",
 "allowed": "Expense Approver", "allow_self_approval": 0}
```

## Anti-Pattern 8: Overlapping Conditions Without Full Coverage

**ALWAYS** ensure conditions cover all cases when using conditional transitions.

```python
# WRONG — gap: what if grand_total == 50000 exactly?
{"condition": "doc.grand_total < 50000", ...},
{"condition": "doc.grand_total > 50000", ...},
# Document with grand_total == 50000 has NO valid transition

# CORRECT — no gaps
{"condition": "doc.grand_total <= 50000", ...},
{"condition": "doc.grand_total > 50000", ...},
```

## Anti-Pattern 9: Using frappe.get_roles() in Condition Expressions

**NEVER** use `frappe.get_roles()` inside condition expressions — it is not available in the safe eval context.

```python
# WRONG — frappe.get_roles() not in safe globals
{"condition": "'Manager' in frappe.get_roles()"}

# CORRECT — role filtering is done by the transition's "allowed" field
# Use conditions only for document-field-based logic
{"condition": "doc.department == 'Finance'", "allowed": "Manager"}
```

## Anti-Pattern 10: Multiple Active Workflows for Same DocType

**NEVER** try to have two active workflows for the same DocType. Frappe automatically deactivates previous ones.

```python
# If you activate "Workflow B" for Purchase Order,
# "Workflow A" for Purchase Order is automatically deactivated.
# There is ALWAYS exactly 0 or 1 active workflow per DocType.
```

## Anti-Pattern 11: Setting workflow_state Directly

**NEVER** set the `workflow_state` field directly on a document.

```python
# WRONG — bypasses all validation
doc.workflow_state = "Approved"
doc.save()  # Will trigger validate_workflow and likely fail

# CORRECT
from frappe.model.workflow import apply_workflow
apply_workflow(doc, "Approve")
```

## Anti-Pattern 12: Forgetting to Create Workflow State Records

**ALWAYS** create Workflow State records before creating the Workflow.

```python
# WRONG — referencing states that don't exist in Workflow State DocType
# This will fail with LinkValidationError

# CORRECT — create states first
for state_name in ["Draft", "Pending", "Approved"]:
    if not frappe.db.exists("Workflow State", state_name):
        frappe.get_doc({"doctype": "Workflow State",
                        "workflow_state_name": state_name}).insert()
```
