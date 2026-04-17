---
name: frappe-syntax-serverscripts
description: "Use when writing Python code for ERPNext/Frappe Server Scripts including Document Events, API endpoints, Scheduler Events, and Permission Queries. Prevents the #1 AI mistake: using import statements in Server Scripts (sandbox blocks ALL imports). Covers frappe.* methods, event name mapping, and correct v14/v15/v16 syntax. Keywords: Server Script, frappe, ERPNext, sandbox, import, doc event, validate, on_submit, before_save, server script example, import not allowed, sandbox rules, which script type to use."
license: MIT
compatibility: "Claude Code, Claude.ai Projects, Claude API. Frappe v14-v16."
metadata:
  author: OpenAEC-Foundation
  version: "2.0"
---

# Frappe Server Scripts — Complete Reference

Server Scripts are Python scripts managed via **Setup > Server Script** in the
Frappe/ERPNext UI. They run inside a **RestrictedPython sandbox**.

## CRITICAL: The Sandbox Rule

```
┌──────────────────────────────────────────────────────────────────┐
│  ALL import STATEMENTS ARE BLOCKED                               │
│                                                                  │
│  import json             → ImportError: __import__ not found     │
│  from datetime import *  → ImportError: __import__ not found     │
│  import frappe           → ImportError (even frappe itself!)     │
│                                                                  │
│  EVERYTHING you need is pre-loaded in the frappe namespace.      │
│  NEVER write an import line. ALWAYS use frappe.utils.*, etc.     │
└──────────────────────────────────────────────────────────────────┘
```

**ALWAYS** use the pre-loaded namespace instead of imports:

| Blocked import | Use instead |
|---|---|
| `import json` | `frappe.parse_json()` / `frappe.as_json()` |
| `from datetime import date` | `frappe.utils.today()` / `frappe.utils.now_datetime()` |
| `from frappe.utils import cint` | `frappe.utils.cint()` (already loaded) |
| `import requests` | `frappe.make_get_request()` / `frappe.make_post_request()` |
| `import re` | Not available — restructure logic without regex |
| `import os` / `import sys` | Not available — use a custom app instead |

## Enabling Server Scripts

```bash
# v14: enabled by default
# v15+: DISABLED by default — you MUST enable explicitly:
bench set-config -g server_script_enabled 1
# Or set server_script_enabled: true in site_config.json
```

**NEVER** expect Server Scripts to work on Frappe Cloud shared benches — they
require a private bench.

## Script Types

| Type | Trigger | Key Variable |
|---|---|---|
| **Document Event** | Document lifecycle (save, submit, cancel) | `doc` |
| **API** | HTTP request to `/api/method/{name}` | `frappe.form_dict` |
| **Scheduler Event** | Cron schedule | (none) |
| **Permission Query** | Document list filtering | `user`, `conditions` |

## Event Name Mapping (Document Events)

**CRITICAL**: The UI names differ from internal hook names:

| Server Script UI | Internal Hook | Fires When |
|---|---|---|
| Before Insert | `before_insert` | Before new doc saved to DB |
| After Insert | `after_insert` | After first DB insert |
| Before Validate | `before_validate` | Before framework validation |
| **Before Save** | **`validate`** | Before save (new + update) |
| After Save | `on_update` | After successful save |
| Before Submit | `before_submit` | Before submit (docstatus 0→1) |
| After Submit | `on_submit` | After submit completes |
| Before Cancel | `before_cancel` | Before cancel (docstatus 1→2) |
| After Cancel | `on_cancel` | After cancel completes |
| Before Delete | `on_trash` | Before permanent delete |
| After Delete | `after_delete` | After permanent delete |

**NEVER** confuse "Before Save" with `before_save` — the UI label "Before Save"
maps to the `validate` hook. The actual `before_save` hook runs AFTER `validate`.

## Decision Tree: Server Script vs Document Controller

```
Need custom Python logic for a DocType?
│
├─► Can you install a custom Frappe app?
│   ├─► YES: Use a Document Controller when you need:
│   │   • import statements (any Python library)
│   │   • File system access
│   │   • Complex class inheritance
│   │   • autoname / before_naming hooks
│   │   • Unit-testable code
│   │
│   └─► NO: Use a Server Script when:
│       • You only have UI access (no bench CLI)
│       • Logic is simple validation / field calculation
│       • You need a quick API endpoint
│       • You need dynamic permission filtering
│
└─► Is logic > 50 lines or needs external libraries?
    ├─► YES → Document Controller in a custom app
    └─► NO  → Server Script is fine
```

## Quick Reference: Available in Sandbox

### Pre-loaded Objects

```python
doc                         # Current document (Document Event only)
frappe                      # Core namespace — ALWAYS available
frappe.db                   # Database operations
frappe.utils                # Date, number, string utilities
frappe.session              # Current session (user, csrf_token)
frappe.form_dict            # Request parameters (API scripts)
frappe.response             # Response object (API scripts)
frappe.request              # Werkzeug request object
frappe.qb                   # Query Builder (v14+)
json                        # Auto-injected by sandbox (no import needed)
```

### Most-Used Methods (Quick Reference)

```python
# Documents
frappe.get_doc(doctype, name)           # Fetch document
frappe.new_doc(doctype)                 # Create new document
frappe.get_all(doctype, filters, fields, order_by, limit)   # No permission check
frappe.db.get_value(doctype, name, fieldname)
frappe.db.set_value(doctype, name, fieldname, value)
frappe.db.exists(doctype, name_or_filters)
frappe.db.sql(query, values, as_dict)   # ALWAYS parameterize!

# Messaging & Errors
frappe.throw(msg, exc, title)           # Stop execution + show error
frappe.msgprint(msg, title, indicator)  # User notification
frappe.log_error(message, title)        # Error Log entry

# Utilities
frappe.utils.today()                    # "2024-01-15"
frappe.utils.now_datetime()             # datetime object
frappe.utils.add_days(date, n)          # Date arithmetic
frappe.utils.flt(val)                   # Safe float (None → 0.0)
frappe.utils.cint(val)                  # Safe int (None → 0)
frappe.parse_json(string)               # JSON string → dict/list
frappe.as_json(obj)                     # dict/list → JSON string
```

**BLOCKED builtins**: `open`, `eval`, `exec`, `compile`, `__import__`, `globals`, `locals`.
Standard types (`str`, `int`, `list`, `dict`, etc.), iteration (`range`, `enumerate`, `zip`),
and aggregation (`sum`, `min`, `max`, `len`, `sorted`) are all available.

See **[references/methods.md](references/methods.md)** for the complete sandbox API reference
(documents, querying, HTTP, email, session/permissions, and all builtins).

## Creating & Testing Server Scripts

1. **Create**: Go to **Setup > Server Script > + Add Server Script**
2. **Configure**: Set Script Type, Reference DocType (for Document Events), Event, and API Method name (for API scripts)
3. **Write**: Enter Python code — remember, **NO imports**
4. **Test**: Trigger the script by performing the action (save a doc, call the API endpoint, etc.)
5. **Debug**: Check **Help > Error Log** for sandbox violations — look for `ImportError` or `NameError`
6. **Iterate**: Fix errors, re-save the Server Script, and re-trigger — changes apply immediately (no bench restart needed)

```python
# Quick smoke test: add this to any script to verify it runs
frappe.msgprint("Script executed successfully!")
```

**Common sandbox errors and fixes:**
- `ImportError: __import__ not found` → Remove the import line, use `frappe.*` equivalent
- `NameError: name 'X' is not defined` → The variable/module is not available in sandbox
- Infinite loop on save → You called `doc.save()` inside a Before Save event — remove it

## Syntax Per Script Type

### Document Event

```python
# Config: Reference DocType = Sales Invoice, Event = Before Save
if doc.grand_total < 0:
    frappe.throw("Total MUST NOT be negative")

doc.requires_approval = 1 if doc.grand_total > 10000 else 0
```

### API

```python
# Config: API Method = get_customer_orders, Allow Guest = No
# Endpoint: /api/method/get_customer_orders
customer = frappe.form_dict.get("customer")
if not customer:
    frappe.throw("Parameter 'customer' is required")

orders = frappe.get_all("Sales Order",
    filters={"customer": customer, "docstatus": 1},
    fields=["name", "grand_total", "status"],
    order_by="creation desc",
    limit=20
)
frappe.response["message"] = {"orders": orders, "count": len(orders)}
```

### Scheduler Event

```python
# Config: Event Frequency = Cron, Cron Format = 0 9 * * *
overdue = frappe.get_all("Sales Invoice",
    filters={"status": "Unpaid", "due_date": ["<", frappe.utils.today()], "docstatus": 1},
    fields=["name", "customer", "grand_total"]
)
for inv in overdue:
    frappe.log_error(f"Overdue: {inv.name} ({inv.customer})", "Invoice Reminder")

frappe.db.commit()  # ALWAYS commit in Scheduler scripts
```

### Permission Query

```python
# Config: Reference DocType = Sales Invoice
# Variables available: user, conditions
roles = frappe.get_roles(user)
if "System Manager" in roles:
    conditions = ""
elif "Sales User" in roles:
    conditions = f"`tabSales Invoice`.owner = {frappe.db.escape(user)}"
else:
    conditions = "1=0"
```

## Version Differences

| Feature | v14 | v15 | v16 |
|---|---|---|---|
| Server Scripts enabled | By default | **Disabled by default** | Disabled by default |
| Enable command | Not needed | `bench set-config -g server_script_enabled 1` | Same as v15 |
| `frappe.qb` (Query Builder) | Available | Available | Available |
| `run_script()` for libraries | v13+ | Available | Available |
| `frappe.make_get_request()` | Available | Available | Available |
| Frappe Cloud shared bench | Supported | **NOT supported** | NOT supported |

## Top 5 Rules

1. **NEVER** write `import` — everything is in the `frappe` namespace
2. **NEVER** call `doc.save()` inside a Before Save script — causes infinite loop
3. **NEVER** call `frappe.db.commit()` in Document Event scripts — framework handles it
4. **ALWAYS** call `frappe.db.commit()` at the end of Scheduler scripts
5. **ALWAYS** use parameterized queries: `%(var)s` with dict, NEVER f-strings in SQL

## References

- **[references/methods.md](references/methods.md)** — Complete sandbox API reference
- **[references/events.md](references/events.md)** — Document lifecycle and execution order
- **[references/examples.md](references/examples.md)** — Working examples per script type
- **[references/anti-patterns.md](references/anti-patterns.md)** — Sandbox violations and common mistakes
- **[references/syntax.md](references/syntax.md)** — Quick syntax cheat sheet
- **[references/patterns.md](references/patterns.md)** — Common patterns (validation, auto-fill, API)
- **[references/hooks.md](references/hooks.md)** — Server Scripts vs hooks.py interaction

## Cross-References

- **frappe-syntax-api** — Frappe REST API and whitelisted methods
- **frappe-syntax-doctype** — DocType field types and schema
- **frappe-core-database** — frappe.db deep dive
- **frappe-core-permissions** — Permission system architecture
- **frappe-errors-common** — Error handling patterns
