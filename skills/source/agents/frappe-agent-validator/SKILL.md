---
name: frappe-agent-validator
description: "Use when reviewing or validating Frappe/ERPNext code against best practices and common pitfalls. Checks generated code before deployment, validates against all 61 frappe-* skills, catches v16 patterns (extend_doctype_class, type annotations), validates ops patterns (bench commands, deployment), and generates correction reports. Keywords: review code, check script, validate deployment, find bugs, code quality, check my code, is this correct, code review, before deploying, best practices check."
license: MIT
compatibility: "Claude Code, Claude.ai Projects, Claude API. Frappe v14-v16."
metadata:
  author: OpenAEC-Foundation
  version: "2.0"
---

# Frappe Code Validator Agent

Validates Frappe/ERPNext code against the complete 61-skill knowledge base, catching errors BEFORE deployment.

**Purpose**: Catch errors before deployment, not after

## Validation Workflow

```
STEP 1: IDENTIFY CODE TYPE
  Client Script | Server Script | Controller | hooks.py |
  Jinja | Whitelisted | Bench/Ops | DocType JSON

STEP 2: RUN TYPE-SPECIFIC CHECKS
  Apply checklist for identified code type
  → If CRITICAL errors found: generate corrected code, then re-run from Step 1

STEP 3: CHECK UNIVERSAL RULES
  Error handling | Security | Performance | User feedback

STEP 4: VERIFY VERSION COMPATIBILITY
  v14/v15/v16 features | Deprecated patterns
  → If version-incompatible patterns found: flag and provide version-safe alternative

STEP 5: VALIDATE AGAINST SKILL CATALOG
  Cross-reference with relevant frappe-* skills

STEP 6: GENERATE VALIDATION REPORT
  Critical errors | Warnings | Suggestions | Corrected code
  → If any CRITICAL/FATAL: corrected code is REQUIRED in report
```

See [references/workflow.md](references/workflow.md) for detailed steps.

## Critical Checks by Code Type

### Server Script Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| Import statements | FATAL | `import X` or `from X import Y` | Use `frappe.utils.X()` directly |
| Wrong doc variable | FATAL | `self.field` or `document.field` | Use `doc.field` |
| Wrong event for purpose | ERROR | Validation code in on_update | Move to validate event |
| try/except blocks | WARNING | `try: ... except:` | Use `frappe.throw()` for validation |
| No null checks | WARNING | `doc.field.lower()` | Add `if doc.field:` guard |

### Client Script Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| Server-side API calls | FATAL | `frappe.db.get_value()` | Use `frappe.call()` |
| Missing async handling | FATAL | `let x = frappe.call()` | Use callback or async/await |
| No refresh after set_value | ERROR | `frm.set_value()` alone | Add `frm.refresh_field()` |
| Using cur_frm | WARNING | `cur_frm.doc.field` | Use `frm` parameter |
| No form state check | WARNING | Missing `__islocal`/`docstatus` | Add state guards |

### Controller Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| self.* in on_update | FATAL | `self.field = X` in on_update | Use `self.db_set()` |
| Circular save | FATAL | `self.save()` in lifecycle hook | Remove self.save() |
| Missing super() | ERROR | Override without super() | Add `super().method()` |
| v16 extend_doctype_class | ERROR | Missing super() in mixin | ALWAYS call super() first |
| No type annotations | SUGGESTION | Missing type hints (v16) | Add type annotations |

### hooks.py Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| Invalid Python syntax | FATAL | Syntax errors | Fix dict/list structure |
| Wrong event names | FATAL | Typo in event name | Use correct event names |
| Invalid function paths | FATAL | Wrong dotted path | Verify path exists |
| v16-only hooks on v14/v15 | ERROR | `extend_doctype_class` | Use `doc_events` instead |
| Missing required_apps | WARNING | No dependency declaration | Add all dependencies |

### Ops/Bench Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| No migrate after hooks | FATAL | hooks.py changed, no migrate | Run `bench migrate` |
| Wrong bench command syntax | ERROR | Incorrect CLI args | Check `frappe-ops-bench` |
| Missing backup before upgrade | ERROR | Upgrade without backup | ALWAYS backup first |
| Production without supervisor | WARNING | No process manager | Use supervisor/systemd |
| No SSL in production | WARNING | HTTP-only deployment | Configure SSL/TLS |

### DocType JSON Checks

| Check | Severity | Pattern | Fix |
|-------|----------|---------|-----|
| Missing mandatory fields | ERROR | No primary identifier | Add name or autoname |
| Duplicate fieldnames | FATAL | Same fieldname twice | Use unique fieldnames |
| Wrong fieldtype for data | WARNING | Text for short values | Use Data/Small Text |
| No permissions defined | WARNING | Empty permission list | Add role permissions |

## v16 Specific Validations

### extend_doctype_class Pattern
```python
# VALIDATE: Mixin class MUST call super()
class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        super().validate()       # REQUIRED - never skip
        self.custom_validation()

    def on_submit(self):
        super().on_submit()      # REQUIRED - never skip
        self.custom_on_submit()
```

### Type Annotations (v16 best practice)
```python
# v16 recommended pattern
def get_customer_balance(customer: str) -> float:
    ...

# Validate: type hints on public API methods
@frappe.whitelist()
def process_order(order_name: str, action: str = "approve") -> dict:
    ...
```

### Data Masking (v16)
```python
# Validate: sensitive fields should use data masking
# Check if PII fields have mask_with configured in DocType JSON
# Example: DocType JSON field definition for masked phone number
{
    "fieldname": "phone",
    "fieldtype": "Data",
    "options": "Phone",
    "mask_with": "X"  # Displays as "XXXXXXX1234" to unauthorized users
}
```

## Universal Validation Rules

### Security Checks (ALL code types)

| Check | Severity | Description |
|-------|----------|-------------|
| SQL Injection | CRITICAL | Raw user input in SQL |
| Permission bypass | CRITICAL | Missing permission checks |
| XSS vulnerability | HIGH | Unescaped user input in HTML |
| Sensitive data exposure | HIGH | Logging passwords/tokens |
| Hardcoded credentials | CRITICAL | API keys in source code |

### Performance Checks (ALL code types)

| Check | Severity | Description |
|-------|----------|-------------|
| Query in loop | HIGH | `frappe.db.*` inside for loop |
| Unbounded query | MEDIUM | SELECT without LIMIT |
| Unnecessary get_doc | LOW | get_doc when get_value suffices |
| Missing index | MEDIUM | Filter on non-indexed field |
| No batch commit | HIGH | Commit per record in bulk ops |

### Error Handling Checks (ALL code types)

| Check | Severity | Description |
|-------|----------|-------------|
| Silent failures | HIGH | `except: pass` without logging |
| Missing user feedback | MEDIUM | Errors not shown to user |
| Generic error messages | LOW | "An error occurred" |
| No rollback on failure | HIGH | Partial data on error |

## Validation Report Format

ALWAYS generate reports in this format:

```markdown
## Code Validation Report

### Code Type: [type]
### Target: [DocType / App / File]
### Event/Trigger: [if applicable]

### CRITICAL ERRORS (Must Fix)
| # | Line | Issue | Fix |
|---|------|-------|-----|

### WARNINGS (Should Fix)
| # | Line | Issue | Recommendation |
|---|------|-------|----------------|

### SUGGESTIONS (Nice to Have)
| # | Line | Suggestion |
|---|------|------------|

### Corrected Code
[If critical errors found, provide corrected version]

### Version Compatibility
| Version | Status | Notes |
|---------|--------|-------|
| v14 | [status] | |
| v15 | [status] | |
| v16 | [status] | |

### Referenced Skills
- frappe-skill-name: [what was validated against]
```

## Validation Depth Levels

| Level | Checks | Use When |
|-------|--------|----------|
| Quick | Fatal errors only | Initial scan |
| Standard | + Warnings + Security | Pre-deployment (DEFAULT) |
| Deep | + Suggestions + Performance + Ops | Production review |

See [references/skill-catalog.md](references/skill-catalog.md) for the full 61-skill cross-reference catalog.
See [references/checklists.md](references/checklists.md) for quick-check summaries per code type.

## Example: End-to-End Validation

Given this Server Script:

```python
# Server Script: before_save on Sales Invoice
import json
try:
    total = self.grand_total
    if total > 100000:
        frappe.throw("Amount too high")
except:
    pass
```

The validator produces:

```markdown
### CRITICAL ERRORS (Must Fix)
| # | Line | Issue | Fix |
|---|------|-------|-----|
| 1 | 2 | `import json` — imports are forbidden in Server Scripts | Remove import; use `frappe.parse_json()` instead |
| 2 | 4 | `self.grand_total` — wrong doc variable | Change to `doc.grand_total` |

### WARNINGS (Should Fix)
| # | Line | Issue | Recommendation |
|---|------|-------|----------------|
| 1 | 3-6 | `try/except: pass` silences errors | Remove try/except; use `frappe.throw()` for validation |
```

Corrected code:

```python
# Server Script: before_save on Sales Invoice
if doc.grand_total and doc.grand_total > 100000:
    frappe.throw("Amount exceeds approval threshold of 100,000")
```

See [references/checklists.md](references/checklists.md) for complete checklists.
See [references/examples.md](references/examples.md) for validation examples.
