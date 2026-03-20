# Step-by-Step Workflow Patterns

Detailed walkthroughs for common Frappe workflow implementations.

## Pattern A: Simple Single-Approver Workflow

**Use case:** Document needs one person's approval before submission.

### Step 1: Prerequisites

```python
# Ensure states exist
for state in ["Draft", "Pending Approval", "Approved", "Rejected", "Cancelled"]:
    if not frappe.db.exists("Workflow State", state):
        frappe.get_doc({"doctype": "Workflow State",
                        "workflow_state_name": state}).insert()

# Ensure actions exist
for action in ["Submit for Approval", "Approve", "Reject", "Cancel"]:
    if not frappe.db.exists("Workflow Action Master", action):
        frappe.get_doc({"doctype": "Workflow Action Master",
                        "workflow_action_name": action}).insert()
```

### Step 2: Create Workflow

```python
workflow = frappe.get_doc({
    "doctype": "Workflow",
    "workflow_name": "Simple Approval",
    "document_type": "Purchase Order",
    "is_active": 1,
    "states": [
        {"state": "Draft", "doc_status": "0", "allow_edit": "Purchase User"},
        {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Purchase Manager"},
        {"state": "Approved", "doc_status": "1", "allow_edit": "Purchase Manager"},
        {"state": "Rejected", "doc_status": "0", "allow_edit": "Purchase User"},
        {"state": "Cancelled", "doc_status": "2"},
    ],
    "transitions": [
        {"state": "Draft", "action": "Submit for Approval",
         "next_state": "Pending Approval", "allowed": "Purchase User"},
        {"state": "Pending Approval", "action": "Approve",
         "next_state": "Approved", "allowed": "Purchase Manager",
         "allow_self_approval": 0},
        {"state": "Pending Approval", "action": "Reject",
         "next_state": "Rejected", "allowed": "Purchase Manager"},
        {"state": "Rejected", "action": "Submit for Approval",
         "next_state": "Pending Approval", "allowed": "Purchase User"},
        {"state": "Approved", "action": "Cancel",
         "next_state": "Cancelled", "allowed": "Purchase Manager"},
    ],
})
workflow.insert()
```

### Step 3: Verify

```python
# Create test document
doc = frappe.get_doc({"doctype": "Purchase Order", "supplier": "Test Supplier"})
doc.insert()
assert doc.workflow_state == "Draft"

# Test transitions
from frappe.model.workflow import get_transitions
frappe.set_user("purchase_user@example.com")
transitions = get_transitions(doc)
assert len(transitions) == 1
assert transitions[0]["action"] == "Submit for Approval"
frappe.set_user("Administrator")
```

---

## Pattern B: Multi-Level Sequential Approval

**Use case:** Document passes through multiple approval levels before final submission.

### State Flow

```
Draft → L1 Review → L2 Review → L3 Review → Final Approved (submitted)
  ↑        ↓            ↓            ↓
  └── Rejected ←────────┴────────────┘
```

### Key Design Decisions

- ALL intermediate states have `doc_status = 0` (draft)
- ONLY "Final Approved" has `doc_status = 1` (submitted)
- ALL rejections return to "Rejected" state (not directly to Draft)
- From "Rejected", the creator revises and resubmits to L1

```python
states = [
    {"state": "Draft", "doc_status": "0", "allow_edit": "Creator Role"},
    {"state": "L1 Review", "doc_status": "0", "allow_edit": "L1 Reviewer"},
    {"state": "L2 Review", "doc_status": "0", "allow_edit": "L2 Reviewer"},
    {"state": "L3 Review", "doc_status": "0", "allow_edit": "L3 Reviewer"},
    {"state": "Final Approved", "doc_status": "1"},
    {"state": "Rejected", "doc_status": "0", "allow_edit": "Creator Role"},
    {"state": "Cancelled", "doc_status": "2"},
]

transitions = [
    {"state": "Draft", "action": "Submit", "next_state": "L1 Review",
     "allowed": "Creator Role"},
    {"state": "L1 Review", "action": "Approve", "next_state": "L2 Review",
     "allowed": "L1 Reviewer", "allow_self_approval": 0},
    {"state": "L1 Review", "action": "Reject", "next_state": "Rejected",
     "allowed": "L1 Reviewer"},
    {"state": "L2 Review", "action": "Approve", "next_state": "L3 Review",
     "allowed": "L2 Reviewer", "allow_self_approval": 0},
    {"state": "L2 Review", "action": "Reject", "next_state": "Rejected",
     "allowed": "L2 Reviewer"},
    {"state": "L3 Review", "action": "Approve", "next_state": "Final Approved",
     "allowed": "L3 Reviewer", "allow_self_approval": 0},
    {"state": "L3 Review", "action": "Reject", "next_state": "Rejected",
     "allowed": "L3 Reviewer"},
    {"state": "Rejected", "action": "Revise", "next_state": "Draft",
     "allowed": "Creator Role"},
    {"state": "Final Approved", "action": "Cancel", "next_state": "Cancelled",
     "allowed": "L3 Reviewer"},
]
```

---

## Pattern C: Conditional Amount-Based Routing

**Use case:** Low-value documents skip higher approval levels.

### State Flow

```
Draft → Pending Approval
  ├─ amount <= 10K  → [Team Lead approves] → Approved
  ├─ amount <= 100K → [Manager approves]   → Approved
  └─ amount > 100K  → [Director approves]  → Approved
```

### Implementation

```python
transitions = [
    {"state": "Draft", "action": "Submit", "next_state": "Pending Approval",
     "allowed": "Employee"},

    # Tier 1: Team Lead for small amounts
    {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "Team Lead", "allow_self_approval": 0,
     "condition": "doc.total_amount <= 10000"},

    # Tier 2: Manager for medium amounts
    {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "Department Manager", "allow_self_approval": 0,
     "condition": "doc.total_amount > 10000 and doc.total_amount <= 100000"},

    # Tier 3: Director for large amounts
    {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "Director", "allow_self_approval": 0,
     "condition": "doc.total_amount > 100000"},

    # Universal reject
    {"state": "Pending Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "Team Lead"},
    {"state": "Pending Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "Department Manager"},
    {"state": "Pending Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "Director"},
]
```

**CRITICAL:** Ensure conditions are mutually exclusive — no gaps, no overlaps.

---

## Pattern D: Department-Based Routing

**Use case:** Different departments have different approvers.

```python
transitions = [
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Finance Manager",
     "condition": "doc.department == 'Finance'"},
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "HR Manager",
     "condition": "doc.department == 'Human Resources'"},
    {"state": "Pending", "action": "Approve", "next_state": "Approved",
     "allowed": "Operations Manager",
     "condition": "doc.department not in ('Finance', 'Human Resources')"},
]
```

**ALWAYS** include a catch-all condition for departments not explicitly listed.

---

## Pattern E: Workflow Migration for Existing DocType

**Use case:** Adding a workflow to a DocType that already has documents.

### Step 1: Audit Existing Data

```python
# Check current docstatus distribution
counts = frappe.db.sql("""
    SELECT docstatus, COUNT(*) as cnt
    FROM `tabPurchase Order`
    GROUP BY docstatus
""", as_dict=True)
print(counts)
# Example: [{docstatus: 0, cnt: 50}, {docstatus: 1, cnt: 200}, {docstatus: 2, cnt: 30}]
```

### Step 2: Ensure State Coverage

Create states that cover ALL existing docstatus values:

```python
states = [
    {"state": "Draft", "doc_status": "0"},        # Maps to existing docstatus=0
    {"state": "Approved", "doc_status": "1"},      # Maps to existing docstatus=1
    {"state": "Cancelled", "doc_status": "2"},     # Maps to existing docstatus=2
]
```

### Step 3: Activate and Verify

```python
# After workflow activation, verify mapping
unmapped = frappe.db.sql("""
    SELECT name, docstatus
    FROM `tabPurchase Order`
    WHERE IFNULL(workflow_state, '') = ''
""", as_dict=True)
if unmapped:
    print(f"WARNING: {len(unmapped)} documents without workflow state")
```

### Step 4: Handle Edge Cases

```python
# Manually set state for documents that did not auto-map
for doc_name in unmapped:
    frappe.db.set_value("Purchase Order", doc_name["name"],
                        "workflow_state", "Draft")
```
