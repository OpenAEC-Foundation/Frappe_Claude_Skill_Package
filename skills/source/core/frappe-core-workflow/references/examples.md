# Workflow Engine Examples

## Example 1: Minimal Two-State Workflow

The simplest possible workflow — Draft to Approved.

```python
# Prerequisites: Workflow State "Draft" and "Approved" must exist
# Workflow Action Master "Approve" must exist

workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "Simple Approval",
    "document_type": "ToDo",  # Non-submittable
    "is_active": 1,
    "states": [
        {"state": "Draft", "doc_status": "0", "allow_edit": "All"},
        {"state": "Approved", "doc_status": "0", "allow_edit": "System Manager"},
    ],
    "transitions": [
        {
            "state": "Draft",
            "action": "Approve",
            "next_state": "Approved",
            "allowed": "System Manager",
        },
    ],
})
workflow.insert()
```

**Note:** Non-submittable DocType — ALL states MUST have `doc_status = 0`.

## Example 2: Submittable DocType with Full Lifecycle

```python
workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "Invoice Approval",
    "document_type": "Sales Invoice",
    "is_active": 1,
    "send_email_alert": 1,
    "states": [
        {"state": "Draft", "doc_status": "0", "allow_edit": "Accounts User"},
        {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Accounts Manager"},
        {"state": "Approved", "doc_status": "1", "allow_edit": "Accounts Manager"},
        {"state": "Cancelled", "doc_status": "2"},
    ],
    "transitions": [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Approval",
         "allowed": "Accounts User", "allow_self_approval": 1},
        {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
         "allowed": "Accounts Manager", "allow_self_approval": 0},
        {"state": "Pending Approval", "action": "Reject", "next_state": "Draft",
         "allowed": "Accounts Manager"},
        {"state": "Approved", "action": "Cancel", "next_state": "Cancelled",
         "allowed": "Accounts Manager"},
    ],
})
workflow.insert()
```

## Example 3: Conditional Transitions Based on Amount

```python
transitions = [
    # Low value — Team Lead can approve
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Team Lead", "condition": "doc.grand_total <= 10000"},
    # Medium value — Manager required
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Manager", "condition": "doc.grand_total > 10000 and doc.grand_total <= 100000"},
    # High value — Director required
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Director", "condition": "doc.grand_total > 100000"},
]
```

## Example 4: Querying Workflow State Programmatically

```python
from frappe.model.workflow import get_workflow_name, get_transitions, apply_workflow

# Check if a DocType has an active workflow
workflow_name = get_workflow_name("Purchase Order")
if workflow_name:
    print(f"Active workflow: {workflow_name}")

# Get available transitions for a document
doc = frappe.get_doc("Purchase Order", "PO-00001")
transitions = get_transitions(doc)
for t in transitions:
    print(f"Action: {t['action']} → {t['next_state']} (role: {t['allowed']})")

# Apply a workflow action
try:
    updated_doc = apply_workflow(doc, "Approve")
    print(f"New state: {updated_doc.workflow_state}")
except Exception as e:
    print(f"Cannot apply: {e}")
```

## Example 5: Bulk Workflow Approval

```python
import json
from frappe.model.workflow import bulk_workflow_approval

# Approve multiple documents at once
docnames = json.dumps(["PO-00001", "PO-00002", "PO-00003"])
bulk_workflow_approval(docnames, "Purchase Order", "Approve")
# < 20 docs: synchronous
# 20-500 docs: background job
# > 500 docs: error
```

## Example 6: Update Field on State Change

```python
# State that sets a custom field when entered
{"state": "Approved", "doc_status": "1",
 "allow_edit": "Manager",
 "update_field": "custom_approved_by",
 "update_value": "frappe.session.user",
 "evaluate_as_expression": 1}

# State that sets a static value
{"state": "On Hold", "doc_status": "0",
 "allow_edit": "Manager",
 "update_field": "status",
 "update_value": "On Hold"}
```

## Example 7: Email Notification Configuration

```python
# On the Workflow
{"send_email_alert": 1}

# On each state row
{"state": "Pending Approval", "doc_status": "0",
 "send_email": 1,
 "next_action_email_template": "Approval Request Template",
 "message": "Please review and approve this document."}
```

## Example 8: Client-Side Workflow Interaction

```javascript
// Get transitions and show custom dialog
frappe.xcall("frappe.model.workflow.get_transitions", {doc: cur_frm.doc})
    .then(transitions => {
        if (transitions.length === 0) {
            frappe.msgprint("No actions available");
            return;
        }
        let actions = transitions.map(t => t.action);
        frappe.prompt({
            fieldtype: "Select",
            label: "Action",
            fieldname: "action",
            options: actions.join("\n"),
            reqd: 1
        }, (values) => {
            frappe.xcall("frappe.model.workflow.apply_workflow", {
                doc: cur_frm.doc,
                action: values.action
            }).then(() => cur_frm.reload_doc());
        });
    });
```

## Example 9: Checking Workflow Status in Reports

```python
# Get document counts by workflow state
from frappe.workflow.doctype.workflow.workflow import get_workflow_state_count

counts = get_workflow_state_count(
    "Purchase Order",
    "workflow_state",
    json.dumps(["Cancelled"])  # Exclude cancelled
)
# Returns: [{"workflow_state": "Draft", "count": 12}, ...]
```

## Example 10: Testing Workflow with frappe.set_user

```python
# Test that only Manager can approve
frappe.set_user("manager@example.com")
doc = frappe.get_doc("Purchase Order", "PO-00001")
transitions = get_transitions(doc)
assert any(t["action"] == "Approve" for t in transitions)

# Test that regular user cannot approve
frappe.set_user("user@example.com")
doc = frappe.get_doc("Purchase Order", "PO-00001")
transitions = get_transitions(doc)
assert not any(t["action"] == "Approve" for t in transitions)

frappe.set_user("Administrator")  # ALWAYS reset user after testing
```
