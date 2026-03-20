# Debugging Workflow — Detailed Steps

## Step 1: Classify Error Type

### Input Analysis

ALWAYS start by reading the error input carefully:

1. **If traceback provided**: Read the LAST line first — it contains the actual exception
2. **If error message only**: Match against the Common Error Patterns Table in SKILL.md
3. **If symptom description**: Ask for Error Log DocType entries or browser console output

### Classification Rules

| Input Contains | Classification |
|----------------|---------------|
| `.py` file paths in traceback | Python |
| `frappe.` Python exceptions | Python |
| `TypeError`, `Uncaught`, browser console | JavaScript |
| `OperationalError`, `IntegrityError`, SQL keywords | Database |
| `PermissionError`, `403`, `Insufficient Permission` | Permission |
| `hooks.py`, `after bench migrate` | Hook |
| `worker`, `scheduler`, `RQ`, `enqueue` | Scheduler |
| `Module not found` (JS), blank page, `bench build` | Build |

## Step 2: Identify the Mechanism

### Traceback Path Analysis

Read the traceback to identify which Frappe mechanism is involved:

| Path in Traceback | Mechanism |
|--------------------|-----------|
| `{app}/{module}/{doctype}/{doctype}.py` | Controller |
| `frappe/core/doctype/server_script/` | Server Script |
| `frappe/handler.py` → `@frappe.whitelist` | Whitelisted method |
| `frappe/tasks.py` or `rq/worker.py` | Background job |
| `frappe/website/` | Website/portal |
| `frappe/patches/` | Migration patch |

### No Traceback Available

If no traceback, determine mechanism from context:

1. Error on form interaction → Client Script or Controller
2. Error on API call → Whitelisted method or Server Script API
3. Error in background → Scheduler or enqueue job
4. Error after deployment change → Hook or patch

## Step 3: Locate Relevant Code

### For Controller Issues
```bash
# Find the controller file
find apps/ -path "*/{doctype_folder}/{doctype_folder}.py" -type f

# Example: Sales Invoice controller
# apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py
```

### For Server Script Issues
```python
# In bench console:
frappe.get_all("Server Script",
    filters={"reference_doctype": "Sales Invoice", "disabled": 0},
    fields=["name", "script_type", "doctype_event"])
```

### For Hook Issues
```python
# In bench console:
import json
hooks = frappe.get_hooks("doc_events")
print(json.dumps(hooks.get("Sales Invoice", {}), indent=2))
```

### For Client Script Issues
```python
# In bench console:
frappe.get_all("Client Script",
    filters={"dt": "Sales Invoice", "enabled": 1},
    fields=["name", "script"])
```

## Step 4: Apply Diagnosis Checklist

### Python Error Diagnosis

1. Read the exception type and message
2. Check if it is a Frappe-specific exception (see SKILL.md table)
3. Identify the line number in the traceback
4. Check variable state at that point using `bench console`
5. Verify the code against `frappe-errors-*` skills

### JavaScript Error Diagnosis

1. Open Browser DevTools Console tab
2. Reproduce the error
3. Check the Network tab for failed API calls
4. Read the response body of failed calls (contains Python traceback)
5. Verify Client Script syntax against `frappe-syntax-clientscripts`

### Database Error Diagnosis

1. Connect via `bench mariadb`
2. Check table structure: `SHOW CREATE TABLE \`tab{DocType}\``
3. Check recent schema changes: `SELECT * FROM \`tabPatch Log\` ORDER BY creation DESC LIMIT 10`
4. Verify column existence for the field causing the error
5. Run `bench migrate` if schema is out of sync

### Permission Error Diagnosis

1. Check Role Permission Manager for the DocType
2. Check User Permissions for the specific user
3. Verify `frappe.has_permission()` returns expected result in bench console
4. Check if `ignore_permissions=True` was incorrectly used (or missing)
5. For API: verify `@frappe.whitelist()` decorator and `allow_guest` flag

## Step 5: Suggest Fix

### Fix Quality Rules

- ALWAYS provide the corrected code, not just a description
- ALWAYS reference the relevant `frappe-*` skill
- ALWAYS include verification steps
- NEVER suggest `ignore_permissions=True` as a fix for permission errors
- NEVER suggest disabling validation as a fix
- ALWAYS consider version compatibility (v14/v15/v16)

### Fix Verification

After suggesting a fix, ALWAYS include:

1. How to test the fix (specific steps)
2. What to check in logs after applying
3. How to confirm the root cause is resolved (not just suppressed)

## Escalation Rules

If the debugging workflow does not resolve the issue:

| Condition | Action |
|-----------|--------|
| Error is in Frappe core code | Check Frappe GitHub issues |
| Error only on specific version | Reference `frappe-agent-migrator` for version-specific bugs |
| Error involves multiple apps | Reference `frappe-agent-architect` for dependency issues |
| Error requires code review | Reference `frappe-agent-validator` for comprehensive check |
