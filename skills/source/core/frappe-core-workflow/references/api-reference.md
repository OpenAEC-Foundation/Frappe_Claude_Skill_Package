# Workflow API Reference

Complete Python API for Frappe's workflow engine. Source: `frappe/model/workflow.py` and `frappe/workflow/doctype/workflow_action/workflow_action.py`.

## Core Functions

### `get_workflow_name(doctype) → str | None`

Returns the name of the active workflow for a DocType. Uses cache (`frappe.cache.hget("workflow", doctype)`).

```python
from frappe.model.workflow import get_workflow_name

workflow_name = get_workflow_name("Purchase Order")
# Returns: "Purchase Order Approval" or None
```

**ALWAYS** check for `None` return — not every DocType has an active workflow.

### `get_workflow(doctype) → Workflow`

Returns the cached Workflow document for a DocType. Calls `frappe.get_cached_doc("Workflow", get_workflow_name(doctype))`.

```python
from frappe.model.workflow import get_workflow

workflow = get_workflow("Purchase Order")
# Returns: Workflow document with .states and .transitions
```

### `get_transitions(doc, workflow=None, raise_exception=False) → list[dict]`

**Whitelisted.** Returns available transitions for the given document based on current user's roles and transition conditions.

```python
from frappe.model.workflow import get_transitions

doc = frappe.get_doc("Purchase Order", "PO-00001")
transitions = get_transitions(doc)
# Returns: [{"state": "Draft", "action": "Approve", "next_state": "Approved", "allowed": "Manager", ...}]
```

**Parameters:**
- `doc` — Document instance, JSON string, or dict. If not a Document, it is parsed and loaded from DB.
- `workflow` — Optional Workflow document (avoids re-fetching).
- `raise_exception` — If `True`, raises `WorkflowStateError` when workflow state is not set. Default: `False` (uses `frappe.throw`).

**Logic:**
1. Returns `[]` for new (unsaved) documents
2. Checks `doc.check_permission("read")`
3. Filters transitions by: `transition.state == current_state`
4. Filters by: `transition.allowed in frappe.get_roles()`
5. Evaluates `transition.condition` via `frappe.safe_eval()`
6. Returns matching transitions as list of dicts

### `apply_workflow(doc, action) → Document`

**Whitelisted.** Applies a workflow action to a document — the primary entry point for state changes.

```python
from frappe.model.workflow import apply_workflow

doc = frappe.get_doc("Purchase Order", "PO-00001")
updated_doc = apply_workflow(doc, "Approve")
```

**Parameters:**
- `doc` — Document instance, JSON string, or dict
- `action` — String matching a Workflow Action Master name (e.g., "Approve")

**Execution flow:**
1. Load document fresh from DB
2. Get available transitions via `get_transitions()`
3. Find transition matching `action`
4. Validate self-approval access
5. Set `workflow_state_field` to `transition.next_state`
6. Execute `update_field`/`update_value` if configured on target state
7. Execute transition tasks (sync, then async)
8. Handle docstatus transition:
   - Draft→Draft: `doc.save()`
   - Draft→Submitted: `doc.submit()` (or queue if `queue_in_background`)
   - Submitted→Submitted: `doc.save()`
   - Submitted→Cancelled: `doc.cancel()`
9. Add workflow comment
10. Return updated document

**Raises:**
- `WorkflowTransitionError` — Action not valid for current state/user
- `frappe.throw` — Self-approval blocked

### `validate_workflow(doc)`

Called automatically during document save. Validates that any manual workflow state change is a valid transition.

```python
# This is called internally — you do NOT call it directly
# It runs during doc.save() / doc.submit() when a workflow is active
```

**Logic:**
1. Gets current state from `doc._doc_before_save`
2. Gets next state from current document
3. If states differ, validates that a transition exists for the change
4. Raises `WorkflowPermissionError` if no valid transition found

### `has_approval_access(user, doc, transition) → bool`

Checks if a user can approve a document through a specific transition.

```python
from frappe.model.workflow import has_approval_access

can_approve = has_approval_access("user@example.com", doc, transition)
```

**Returns `True` if ANY of:**
- `user == "Administrator"`
- `transition.allow_self_approval == 1`
- `user != doc.owner` (user is not the document creator)

### `is_transition_condition_satisfied(transition, doc) → bool`

Evaluates a transition's Python condition expression.

```python
from frappe.model.workflow import is_transition_condition_satisfied

satisfied = is_transition_condition_satisfied(transition, doc)
```

Uses `frappe.safe_eval()` with restricted globals (see `get_workflow_safe_globals()`).

### `can_cancel_document(doctype) → bool`

Checks if documents of this DocType can be cancelled outside the workflow (e.g., via Amend).

```python
from frappe.model.workflow import can_cancel_document

can_cancel = can_cancel_document("Purchase Order")
```

Returns `True` if there are no cancelling states OR if no transitions lead to cancelling states.

### `bulk_workflow_approval(docnames, doctype, action)`

**Whitelisted.** Applies workflow action to multiple documents at once.

```python
import json
from frappe.model.workflow import bulk_workflow_approval

docnames = json.dumps(["PO-00001", "PO-00002", "PO-00003"])
bulk_workflow_approval(docnames, "Purchase Order", "Approve")
```

**Behavior:**
- < 20 documents: processed synchronously
- 20-500 documents: enqueued as background job
- > 500 documents: raises error ("Too Many Documents")

### `get_workflow_state_count(doctype, workflow_state_field, states) → list[dict]`

**Whitelisted.** Returns count of documents grouped by workflow state, excluding specified states.

```python
from frappe.workflow.doctype.workflow.workflow import get_workflow_state_count

counts = get_workflow_state_count("Purchase Order", "workflow_state", ["Draft"])
# Returns: [{"workflow_state": "Pending Approval", "count": 5}, ...]
```

## Condition Expression Globals

The `get_workflow_safe_globals()` function provides these objects inside condition expressions:

```python
{
    "frappe": {
        "db": {
            "get_value": frappe.db.get_value,
            "get_list": frappe.db.get_list,
        },
        "session": frappe.session,  # .user, .roles, etc.
        "utils": {
            "now_datetime": frappe.utils.now_datetime,
            "add_to_date": frappe.utils.add_to_date,
            "get_datetime": frappe.utils.get_datetime,
            "now": frappe.utils.now,
        },
    }
}
```

The document is available as `doc` (a dict from `doc.as_dict()`).

## Workflow Action Functions

### `process_workflow_actions(doc, state)`

Called automatically after document save. Creates/updates Workflow Action records for pending approvals.

### `get_next_possible_transitions(workflow_name, state, doc=None) → list`

Returns transitions from current state, filtering by condition satisfaction and skipping optional states.

### `clear_workflow_actions(doctype, name)`

Removes all Workflow Action records for a deleted document.

### `update_completed_workflow_actions(doc, user, workflow, workflow_state)`

Marks matching Workflow Actions as "Completed" after a transition.

## Exception Classes

```python
from frappe.model.workflow import (
    WorkflowStateError,       # Workflow state not set or invalid
    WorkflowTransitionError,  # Invalid action for current state
    WorkflowPermissionError,  # User lacks permission for transition
)
```

All three inherit from `frappe.ValidationError`.

## Hooks

### `workflow_methods`

Register custom task methods for Workflow Transition Tasks:

```python
# hooks.py
workflow_methods = [
    {"name": "Custom Task", "method": "myapp.utils.custom_workflow_task"}
]
```

### Built-in Transition Tasks (v15+)

- **Webhook** — Executes a Webhook document
- **Server Script** — Executes a Server Script via `execute_workflow_task`

## Client-Side API

```javascript
// Get available transitions for current document
frappe.xcall("frappe.model.workflow.get_transitions", {doc: cur_frm.doc})
    .then(transitions => console.log(transitions));

// Apply a workflow action
frappe.xcall("frappe.model.workflow.apply_workflow", {
    doc: cur_frm.doc,
    action: "Approve"
}).then(doc => cur_frm.reload_doc());

// Bulk approval
frappe.xcall("frappe.model.workflow.bulk_workflow_approval", {
    docnames: JSON.stringify(["PO-001", "PO-002"]),
    doctype: "Purchase Order",
    action: "Approve"
});
```
