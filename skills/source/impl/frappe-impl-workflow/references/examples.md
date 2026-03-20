# Workflow Implementation Examples

## Example 1: Leave Approval Workflow

A standard HR leave approval pattern with employee submission, approver review, and HR cancellation capability.

### State Design

| State | doc_status | allow_edit | Style |
|-------|:-:|------------|-------|
| Applied | 0 | Employee | Primary |
| Approved | 1 | Leave Approver | Success |
| Rejected | 0 | Employee | Danger |
| Cancelled | 2 | — | Inverse |

### Implementation

```python
workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "Leave Approval",
    "document_type": "Leave Application",
    "is_active": 1,
    "send_email_alert": 1,
    "states": [
        {"state": "Applied", "doc_status": "0", "allow_edit": "Employee",
         "send_email": 1, "message": "Your leave application has been submitted."},
        {"state": "Approved", "doc_status": "1", "allow_edit": "Leave Approver",
         "update_field": "status", "update_value": "Approved"},
        {"state": "Rejected", "doc_status": "0", "allow_edit": "Employee",
         "update_field": "status", "update_value": "Rejected"},
        {"state": "Cancelled", "doc_status": "2"},
    ],
    "transitions": [
        {"state": "Applied", "action": "Approve", "next_state": "Approved",
         "allowed": "Leave Approver", "allow_self_approval": 0},
        {"state": "Applied", "action": "Reject", "next_state": "Rejected",
         "allowed": "Leave Approver", "allow_self_approval": 0},
        {"state": "Rejected", "action": "Submit for Review", "next_state": "Applied",
         "allowed": "Employee"},
        {"state": "Approved", "action": "Cancel", "next_state": "Cancelled",
         "allowed": "HR Manager"},
    ],
})
workflow.insert()
```

## Example 2: Purchase Order Multi-Level Approval

Amount-based routing with two approval tiers.

### State Design

```
Draft → Pending L1 Approval → Pending L2 Approval (if > 50000) → Approved → Cancelled
                             └→ Approved (if <= 50000)
```

### Implementation

```python
workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "PO Multi-Level Approval",
    "document_type": "Purchase Order",
    "is_active": 1,
    "states": [
        {"state": "Draft", "doc_status": "0", "allow_edit": "Purchase User"},
        {"state": "Pending L1 Approval", "doc_status": "0", "allow_edit": "Purchase Manager"},
        {"state": "Pending L2 Approval", "doc_status": "0", "allow_edit": "Director"},
        {"state": "Approved", "doc_status": "1", "allow_edit": "Purchase Manager"},
        {"state": "Rejected", "doc_status": "0", "allow_edit": "Purchase User"},
        {"state": "Cancelled", "doc_status": "2"},
    ],
    "transitions": [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Pending L1 Approval",
         "allowed": "Purchase User"},
        # L1 approves small orders directly
        {"state": "Pending L1 Approval", "action": "Approve", "next_state": "Approved",
         "allowed": "Purchase Manager", "allow_self_approval": 0,
         "condition": "doc.grand_total <= 50000"},
        # L1 escalates large orders to L2
        {"state": "Pending L1 Approval", "action": "Escalate", "next_state": "Pending L2 Approval",
         "allowed": "Purchase Manager",
         "condition": "doc.grand_total > 50000"},
        # L2 approves large orders
        {"state": "Pending L2 Approval", "action": "Approve", "next_state": "Approved",
         "allowed": "Director", "allow_self_approval": 0},
        # Rejection at any level goes back to draft
        {"state": "Pending L1 Approval", "action": "Reject", "next_state": "Rejected",
         "allowed": "Purchase Manager"},
        {"state": "Pending L2 Approval", "action": "Reject", "next_state": "Rejected",
         "allowed": "Director"},
        {"state": "Rejected", "action": "Revise", "next_state": "Draft",
         "allowed": "Purchase User"},
        {"state": "Approved", "action": "Cancel", "next_state": "Cancelled",
         "allowed": "Purchase Manager"},
    ],
})
workflow.insert()
```

## Example 3: Document Review Workflow (Non-Submittable)

For non-submittable DocTypes like custom document management.

```python
# ALL states MUST have doc_status = 0 for non-submittable DocTypes
workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "Document Review",
    "document_type": "Custom Document",
    "is_active": 1,
    "states": [
        {"state": "Draft", "doc_status": "0", "allow_edit": "All"},
        {"state": "Under Review", "doc_status": "0", "allow_edit": "Reviewer"},
        {"state": "Changes Requested", "doc_status": "0", "allow_edit": "All"},
        {"state": "Reviewed", "doc_status": "0", "allow_edit": "Reviewer"},
        {"state": "Published", "doc_status": "0", "allow_edit": "System Manager"},
    ],
    "transitions": [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Under Review",
         "allowed": "All"},
        {"state": "Under Review", "action": "Request Changes", "next_state": "Changes Requested",
         "allowed": "Reviewer"},
        {"state": "Under Review", "action": "Approve", "next_state": "Reviewed",
         "allowed": "Reviewer", "allow_self_approval": 0},
        {"state": "Changes Requested", "action": "Resubmit", "next_state": "Under Review",
         "allowed": "All"},
        {"state": "Reviewed", "action": "Publish", "next_state": "Published",
         "allowed": "System Manager"},
    ],
})
workflow.insert()
```

## Example 4: Expense Claim with Department-Based Routing

```python
transitions = [
    # Finance department — approved by Finance Manager
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Finance Manager", "allow_self_approval": 0,
     "condition": "doc.department == 'Finance'"},
    # HR department — approved by HR Manager
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "HR Manager", "allow_self_approval": 0,
     "condition": "doc.department == 'HR'"},
    # All other departments — approved by Department Head
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Department Head", "allow_self_approval": 0,
     "condition": "doc.department not in ('Finance', 'HR')"},
]
```

## Example 5: Programmatic Workflow Status Check

```python
def get_pending_approvals(doctype, role):
    """Get all documents pending approval for a specific role."""
    from frappe.model.workflow import get_workflow_name, get_workflow

    workflow_name = get_workflow_name(doctype)
    if not workflow_name:
        return []

    workflow = get_workflow(doctype)

    # Find states that have outgoing transitions for this role
    pending_states = set()
    for t in workflow.transitions:
        if t.allowed == role:
            pending_states.add(t.state)

    if not pending_states:
        return []

    return frappe.get_all(doctype,
        filters={workflow.workflow_state_field: ["in", list(pending_states)]},
        fields=["name", workflow.workflow_state_field, "owner", "creation"])
```

## Example 6: Workflow with Auto-Set Fields

```python
states = [
    {"state": "Draft", "doc_status": "0", "allow_edit": "Employee"},
    {"state": "Approved", "doc_status": "1",
     "update_field": "custom_approved_by", "update_value": "frappe.session.user",
     "evaluate_as_expression": 1},
    {"state": "Approved", "doc_status": "1",
     "update_field": "custom_approval_date", "update_value": "frappe.utils.now()",
     "evaluate_as_expression": 1},
]
```

**Note:** Each state row can only update ONE field. To update multiple fields on the same state, use a Server Script triggered by workflow state change instead.
