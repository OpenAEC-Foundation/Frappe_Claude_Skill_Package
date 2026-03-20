# Workflow Implementation Decision Tree

Use this decision tree when designing a new Frappe workflow. Work through each decision point in order.

## Decision 1: Do You Need a Workflow?

```
Does the document require...
├── Multi-user approval chain?               → YES, use Workflow
├── Role-based state transitions?            → YES, use Workflow
├── Conditional routing by field values?     → YES, use Workflow
├── Self-approval prevention?                → YES, use Workflow
├── Controlled docstatus transitions?        → YES, use Workflow
├── Just status tracking (no approval)?      → NO, use Select field
├── Just notifications (no state machine)?   → NO, use Notification DocType
└── Just permission control (no states)?     → NO, use Permission Level / User Permission
```

## Decision 2: DocType Characteristics

```
Is the DocType submittable?
├── YES (has is_submittable = 1)
│   ├── States CAN use doc_status 0, 1, and 2
│   ├── MUST have at least one state with doc_status = 1 (for submission)
│   ├── doc_status transitions: 0→0, 0→1, 1→1, 1→2 (ONLY these are valid)
│   └── NEVER go backwards: 1→0 or 2→anything
│
└── NO (regular DocType)
    ├── ALL states MUST have doc_status = 0
    ├── States represent logical stages, not Frappe docstatus
    └── Use update_field to set a status-like field if needed
```

## Decision 3: Approval Structure

```
How many approval levels?
│
├── Single approver
│   ├── States: Draft → Pending → Approved [→ Submitted → Cancelled]
│   ├── Simple, most common pattern
│   └── Add Rejected state for rejection loop
│
├── Sequential multi-level (L1 → L2 → L3)
│   ├── States: Draft → L1 → L2 → L3 → Approved [→ Submitted]
│   ├── ALL intermediate states: doc_status = 0
│   ├── ONLY final approval state: doc_status = 1
│   └── Rejection can go to any previous state or to "Rejected"
│
├── Conditional routing (amount/department-based)
│   ├── Single "Pending" state with multiple transitions
│   ├── Each transition has a condition expression
│   ├── MUST cover all cases (no gaps in conditions)
│   └── Conditions MUST be mutually exclusive (no overlaps)
│
└── Hybrid (conditional + sequential)
    ├── Route by condition to different approval paths
    ├── Each path may have its own approval chain
    └── All paths converge to single "Approved" state
```

## Decision 4: Self-Approval Policy

```
Should document creators be able to approve their own documents?
│
├── YES (default behavior)
│   └── Leave allow_self_approval = 1 (or omit — default is 1)
│
├── NO — for specific transitions
│   ├── Set allow_self_approval = 0 on approval transitions
│   ├── Creator will NOT see the Approve button on their own documents
│   ├── Administrator is ALWAYS exempt
│   └── Other users with the role CAN still approve
│
└── MIXED — different rules per level
    ├── L1: allow_self_approval = 0 (creator cannot approve)
    ├── L2: allow_self_approval = 1 (L2 reviewer may also be creator)
    └── Set per transition row
```

## Decision 5: Rejection Handling

```
What happens when a document is rejected?
│
├── Return to Draft (most common)
│   ├── Creator can edit and resubmit
│   └── Full revision cycle
│
├── Return to previous approval level
│   ├── L3 rejects → back to L2 (not all the way to Draft)
│   └── Useful for minor corrections at higher levels
│
├── Go to dedicated "Rejected" state
│   ├── Creator must explicitly "Revise" to return to Draft
│   ├── Rejection is logged as a distinct state
│   └── Useful for audit trails
│
└── Terminal rejection (document is dead)
    ├── No outgoing transitions from Rejected
    ├── Creator must create a new document
    └── Use sparingly — most workflows need revision loops
```

## Decision 6: Notification Strategy

```
How should users be notified?
│
├── Email on every state change
│   ├── Set send_email_alert = 1 on Workflow
│   ├── Set send_email = 1 on each state (default)
│   └── Link Email Template for customized messages
│
├── Email on specific states only
│   ├── Set send_email = 0 on states that should NOT notify
│   ├── Set send_email = 1 on states that SHOULD notify
│   └── Useful to avoid noise on internal transitions
│
├── No workflow emails (use separate Notification)
│   ├── Set send_email_alert = 0 on Workflow
│   └── Create Notification DocType records for custom logic
│
└── Combination
    ├── Workflow emails for approvers (via send_email on states)
    └── Notification DocType for FYI recipients
```

## Decision 7: Field Updates on State Change

```
Should fields auto-update when entering a state?
│
├── YES — static value
│   ├── Set update_field and update_value on state row
│   ├── Example: update_field = "approval_status", update_value = "Approved"
│   └── evaluate_as_expression = 0 (default)
│
├── YES — dynamic value (expression)
│   ├── Set evaluate_as_expression = 1
│   ├── update_value is Python expression
│   ├── Example: "frappe.session.user" or "frappe.utils.now()"
│   └── Available globals: frappe.db, frappe.session, frappe.utils, doc
│
├── YES — multiple fields
│   ├── State row only supports ONE update_field per state
│   ├── For multiple fields: use Server Script on workflow state change
│   └── Or use Workflow Transition Tasks (v15+)
│
└── NO — no auto-updates needed
    └── Leave update_field empty
```

## Decision 8: Testing Strategy

```
How to validate the workflow?
│
├── Manual testing (ALWAYS required)
│   ├── Create test users with each required role
│   ├── Test every transition path (happy + rejection)
│   ├── Test self-approval blocking
│   ├── Test condition boundaries
│   └── Test with existing documents (if migration)
│
├── Automated testing
│   ├── Use frappe.set_user() to simulate different users
│   ├── Use get_transitions() to verify available actions
│   ├── Use apply_workflow() to test state changes
│   ├── Assert on workflow_state after each action
│   └── ALWAYS call frappe.set_user("Administrator") after tests
│
└── Load testing (for high-volume workflows)
    ├── Use bulk_workflow_approval() for batch testing
    ├── Test with > 20 documents (background job path)
    └── Monitor background job queue for failures
```

## Quick Decision Matrix

| Scenario | Pattern | Key Settings |
|----------|---------|-------------|
| Simple approval | A (single approver) | 2-3 states, 1 approval transition |
| Financial approval | C (amount-based) | Conditions on transitions |
| HR/Leave | A + self-approval block | allow_self_approval = 0 |
| Multi-department | D (department-based) | Conditions with department field |
| Compliance/Audit | B (multi-level) | Sequential states, all blocking |
| Document review | Non-submittable pattern | All doc_status = 0 |
| Migration | Pattern E | Audit existing data first |
