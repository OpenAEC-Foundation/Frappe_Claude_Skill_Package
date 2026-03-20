# Workflow Implementation Anti-Patterns

## Anti-Pattern 1: Starting Implementation Without State Diagram

**NEVER** start building a workflow directly in the UI without designing the state machine first.

```
WRONG:
  Open Workflow form → start adding states randomly → add transitions → debug

CORRECT:
  1. Draw state diagram on paper/whiteboard
  2. List all states with doc_status values
  3. List all transitions with roles and conditions
  4. Verify all paths have entry AND exit
  5. Then implement
```

**Why:** Ad-hoc workflow design leads to dead-end states, missing transitions, and circular paths that trap documents.

## Anti-Pattern 2: Using Submitted State for Intermediate Approvals

**NEVER** set `doc_status = 1` on an intermediate approval state.

```python
# WRONG — once submitted, document cannot return to draft
{"state": "L1 Approved", "doc_status": "1"},  # Too early!
{"state": "L2 Approved", "doc_status": "1"},
# If L2 rejects, document is stuck — cannot go back to draft

# CORRECT — keep intermediate states at doc_status 0
{"state": "L1 Approved", "doc_status": "0"},
{"state": "L2 Approved", "doc_status": "0"},
{"state": "Final Approved", "doc_status": "1"},  # Only final state is submitted
```

## Anti-Pattern 3: Missing Rejection Path

**ALWAYS** provide a rejection/send-back path from every approval state.

```python
# WRONG — no way to reject after reaching Pending Approval
transitions = [
    {"state": "Draft", "action": "Submit", "next_state": "Pending Approval", ...},
    {"state": "Pending Approval", "action": "Approve", "next_state": "Approved", ...},
]
# If the approver wants to reject, they have no action available

# CORRECT — add rejection path
transitions = [
    {"state": "Draft", "action": "Submit", "next_state": "Pending Approval", ...},
    {"state": "Pending Approval", "action": "Approve", "next_state": "Approved", ...},
    {"state": "Pending Approval", "action": "Reject", "next_state": "Draft", ...},
]
```

## Anti-Pattern 4: Overlapping Role-Based Conditions Without Clear Precedence

**NEVER** create transitions where the same role has multiple actions with overlapping conditions.

```python
# WRONG — Manager sees both Approve options when amount is exactly 50000
{"state": "Pending", "action": "Approve", "next_state": "Approved",
 "allowed": "Manager", "condition": "doc.amount <= 50000"},
{"state": "Pending", "action": "Approve", "next_state": "Escalated",
 "allowed": "Manager", "condition": "doc.amount >= 50000"},
# amount == 50000 matches BOTH — user sees duplicate buttons

# CORRECT — mutually exclusive conditions
{"condition": "doc.amount <= 50000"},
{"condition": "doc.amount > 50000"},
```

## Anti-Pattern 5: Testing Only the Happy Path

**ALWAYS** test rejection loops, self-approval blocking, edge-case conditions, and concurrent user scenarios.

```
WRONG: Test only: Draft → Approve → Submitted. Ship it.

CORRECT test plan:
  □ Happy path: Draft → Pending → Approved → Submitted
  □ Rejection loop: Draft → Pending → Rejected → Draft → Pending → Approved
  □ Self-approval: Creator tries to approve their own doc (should fail)
  □ Wrong role: User without approval role tries to approve (should see no button)
  □ Condition boundaries: Test with exact boundary values
  □ Concurrent: Two approvers act on same doc simultaneously
  □ Existing documents: Check docs created before workflow activation
```

## Anti-Pattern 6: Not Setting allow_edit on States

**ALWAYS** set `allow_edit` to restrict who can modify documents in each state.

```python
# WRONG — anyone can edit in any state
{"state": "Pending Approval", "doc_status": "0"},  # No allow_edit set

# CORRECT — only the approver can edit during their review
{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Approver Role"},
```

**Why:** Without `allow_edit`, any user with DocType write permission can modify the document while it awaits approval.

## Anti-Pattern 7: Activating Workflow Without Checking Existing Documents

**NEVER** activate a workflow on a DocType with existing documents without verifying state mapping.

```python
# When activated, the engine runs update_default_workflow_status:
# - Docs with docstatus=0 get mapped to first state with doc_status=0
# - Docs with docstatus=1 get mapped to first state with doc_status=1
# - Docs with docstatus=2 get mapped to first state with doc_status=2

# WRONG — workflow has no state with doc_status=1, but submitted POs exist
# Submitted POs get empty workflow_state → stuck

# CORRECT — ensure a state exists for every docstatus your existing docs have
```

## Anti-Pattern 8: Using Workflow for Simple Status Tracking

**NEVER** use a Workflow when a simple Select field would suffice.

```
WRONG: Single-user status tracking (Open → In Progress → Done)
       → No approval, no role restrictions, no conditions
       → A workflow adds unnecessary overhead

CORRECT use cases for Workflow:
  ✓ Multi-user approval chains
  ✓ Role-based state transitions
  ✓ Conditional routing by document values
  ✓ Self-approval prevention
  ✓ Controlling when docstatus changes
```

## Anti-Pattern 9: Circular Workflows Without Exit

**NEVER** create cycles that have no terminal state reachable from the cycle.

```python
# WRONG — infinite loop with no way to finish
{"state": "Review", "action": "Send Back", "next_state": "Revision"},
{"state": "Revision", "action": "Resubmit", "next_state": "Review"},
# No "Approve" transition → document loops forever

# CORRECT — cycle with exit
{"state": "Review", "action": "Send Back", "next_state": "Revision"},
{"state": "Review", "action": "Approve", "next_state": "Approved"},  # Exit!
{"state": "Revision", "action": "Resubmit", "next_state": "Review"},
```

## Anti-Pattern 10: Ignoring Email Template Setup

**NEVER** enable `send_email_alert` without configuring proper email templates.

```python
# WRONG — emails enabled but no template
{"send_email_alert": 1}
# States have send_email=1 (default) but no next_action_email_template
# Users get generic/empty notifications

# CORRECT — configure templates
{"state": "Pending Approval", "send_email": 1,
 "next_action_email_template": "Workflow Approval Request",
 "message": "Document {{ doc.name }} requires your approval."}
```
