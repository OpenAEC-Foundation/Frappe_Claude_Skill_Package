# Server Script Decision Trees

## Decision 1: Server Script vs Controller vs hooks.py?

```
WHAT DO YOU NEED?
│
├── Document automation (validation, auto-fill, notifications)?
│   ├── Need external libraries or complex transactions?
│   │   ├── YES → Controller in custom app
│   │   └── NO  → Server Script: Document Event
│   └── Run on MULTIPLE doctypes?
│       ├── YES → hooks.py doc_events
│       └── NO  → Server Script: Document Event
│
├── Custom REST API endpoint?
│   ├── Need file uploads, streaming, or complex auth?
│   │   ├── YES → @frappe.whitelist() in custom app
│   │   └── NO  → Server Script: API
│   └── Need database transaction control?
│       ├── YES → Controller whitelisted method
│       └── NO  → Server Script: API
│
├── Scheduled/background task?
│   ├── Simple task (< 100 records, no external calls)?
│   │   └── Server Script: Scheduler Event
│   ├── Complex task or external integrations?
│   │   └── hooks.py scheduler_events + custom method
│   └── Need frappe.enqueue() for background job?
│       └── Controller method (enqueue not in sandbox)
│
└── Dynamic permission filtering?
    ├── Filter list view per user/role?
    │   └── Server Script: Permission Query
    └── Custom has_permission logic?
        └── hooks.py has_permission
```

## Decision 2: Which Document Event?

```
WHAT TRIGGERS YOUR CODE?
│
├── BEFORE document operations
│   ├── Before any validation runs?
│   │   └── Before Validate (before_validate)
│   │       Use for: Pre-processing, setting defaults
│   │
│   ├── Validate data / auto-calculate before save?
│   │   └── Before Save (validate)  ← MOST COMMON
│   │       Use for: Validation, calculations, auto-fill
│   │       Changes to doc: SAVED automatically
│   │
│   ├── Check conditions before submit?
│   │   └── Before Submit (before_submit)
│   │       Use for: Submit-time checks, approval validation
│   │
│   └── Prevent or validate cancel?
│       └── Before Cancel (before_cancel)
│           Use for: Check linked docs, block cancel
│
├── AFTER document operations
│   ├── React to new document (first save only)?
│   │   └── After Insert (after_insert)
│   │       Use for: Welcome emails, create related docs
│   │       doc.name: GUARANTEED to exist
│   │
│   ├── React to any save (new or update)?
│   │   └── After Save (on_update)
│   │       Use for: Audit logs, notifications, sync
│   │       Changes to doc: NOT saved — use db_set
│   │
│   ├── React to submission?
│   │   └── After Submit (on_submit)
│   │       Use for: Ledger entries, stock updates
│   │
│   └── React to cancellation?
│       └── After Cancel (on_cancel)
│           Use for: Reverse entries, cleanup
│
└── DELETE operations
    ├── Prevent or validate delete?
    │   └── Before Delete (on_trash)
    └── Cleanup after delete?
        └── After Delete (after_delete)
```

## Decision 3: Validation Location

```
WHERE SHOULD VALIDATION HAPPEN?
│
├── UX feedback only (can be bypassed via API)?
│   └── Client Script validate event
│
├── MUST always run, even via API/import?
│   ├── Simple validation (single doctype, no imports)?
│   │   └── Server Script: Before Save
│   └── Complex validation or multiple doctypes?
│       └── Controller validate method
│
└── Data integrity (can NEVER be violated)?
    └── BOTH client + server validation
        (Server is authoritative)
```

## Decision 4: API Authentication

```
WHO CAN ACCESS YOUR API?
│
├── Anyone (public, no login)?
│   └── Server Script API + Allow Guest: Yes
│       ALWAYS validate/sanitize all inputs
│
├── Any logged-in user?
│   └── Server Script API + Allow Guest: No
│       Add: Permission check in script body
│
├── Specific roles only?
│   └── Server Script API + Allow Guest: No
│       Add: frappe.get_roles() check
│
└── External systems (API key auth)?
    └── @frappe.whitelist() in custom app
        Use: frappe.get_request_header("Authorization")
```

## Document Lifecycle Order

```
NEW DOCUMENT:
  before_insert → before_validate → validate → after_insert → on_update

EXISTING DOCUMENT:
  before_validate → validate → on_update

SUBMIT:
  before_submit → on_submit

CANCEL:
  before_cancel → on_cancel

DELETE:
  on_trash → after_delete
```

## Scheduler Cron Patterns

| Pattern | Meaning | Use Case |
|---------|---------|----------|
| `*/15 * * * *` | Every 15 min | Status updates, queue processing |
| `0 * * * *` | Every hour | Aggregations, cache refresh |
| `0 9 * * *` | Daily 9:00 | Morning reports, reminders |
| `0 2 * * *` | Daily 2:00 | Nightly cleanup, data sync |
| `0 9 * * 1` | Monday 9:00 | Weekly reports |
| `0 6 1 * *` | 1st of month | Monthly reports, billing |
