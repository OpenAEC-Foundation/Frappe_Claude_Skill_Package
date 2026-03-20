# Code Validation Checklists

## Server Script Checklist

### Fatal Errors (Code Will Not Work)

- [ ] **No import statements**
  - `import json` --> Use `frappe.parse_json()`
  - `from frappe.utils import nowdate` --> Use `frappe.utils.nowdate()`
  - `from datetime import datetime` --> Use `frappe.utils.*`
  - `import requests` --> IMPOSSIBLE in Server Script, use Controller

- [ ] **Correct document variable**
  - `self.field_name` --> Use `doc.field_name`
  - `document.field_name` --> Use `doc.field_name`

- [ ] **No undefined variables**
  - Only available: `doc`, `frappe`, `None`, `True`, `False`
  - Built-in types: `int`, `float`, `str`, `list`, `dict`, `set`, `tuple`

- [ ] **Correct event for purpose**
  - Validation logic --> must be in `validate` event
  - Post-save logic --> must be in `on_update` event
  - Pre-submit logic --> must be in `before_submit` event

### Errors (Code May Fail)

- [ ] **API Script has method and returns response**
- [ ] **Permission Query returns condition string or None**
- [ ] **Scheduler has proper cron syntax**

### Warnings (Should Fix)

- [ ] **No try/except blocks** (just use frappe.throw())
- [ ] **Null checks before operations**
- [ ] **Using frappe.throw() not frappe.msgprint() for blocking**

---

## Client Script Checklist

### Fatal Errors

- [ ] **No server-side APIs**
  - `frappe.db.get_value()` --> Use `frappe.call()`
  - `frappe.db.set_value()` --> Use `frappe.call()`
  - `frappe.get_doc()` --> Use `frappe.call()`

- [ ] **Async handling for frappe.call()**
  - WRONG: `let result = frappe.call({method: 'x'})`
  - CORRECT: Use callback or async/await

- [ ] **Correct form event structure**
  - Must wrap in `frappe.ui.form.on('DocType', {...})`

### Errors

- [ ] **refresh_field after set_value**
- [ ] **Use frm parameter, not cur_frm**

### Warnings

- [ ] **Check form state** (__islocal, docstatus)
- [ ] **Await or callback for async operations**

---

## Controller Checklist

### Fatal Errors

- [ ] **No self modification in on_update**
  - Use `self.db_set()` or `frappe.db.set_value()`

- [ ] **No circular save**
  - `self.save()` in lifecycle hooks causes infinite loop

- [ ] **Correct class inheritance**
  - Must extend Document or specific DocType class

### Errors

- [ ] **Call super() in overrides**
  - v16 extend_doctype_class: MANDATORY
  - v14/v15 overrides: strongly recommended

- [ ] **Understand transaction behavior**
  - validate, before_*: rollback on exception
  - on_update, on_*: NO automatic rollback

### v16 Specific

- [ ] **extend_doctype_class uses mixin pattern correctly**
- [ ] **Type annotations on public methods**
- [ ] **super() called in EVERY overridden method**

### Warnings

- [ ] **Error handling for external calls**
- [ ] **Logging for important operations**

---

## hooks.py Checklist

### Fatal Errors

- [ ] **Valid Python syntax**
- [ ] **Correct hook names** (doc_events, scheduler_events, etc.)
- [ ] **Valid function paths** (dotted Python module paths)

### Errors

- [ ] **Version-specific hooks marked**
  - `extend_doctype_class`: v16+ only
  - `override_doctype_class`: v14+ (deprecated in v16)

- [ ] **required_apps includes all dependencies**
- [ ] **Fixture filters present** for shared DocTypes

### Warnings

- [ ] **Permission hooks return values, not throw**
- [ ] **Scheduler event handler paths are valid**

---

## Ops/Bench Checklist

### Required Actions

- [ ] **bench migrate** after hooks.py or DocType changes
- [ ] **bench build** after JS/CSS changes
- [ ] **bench clear-cache** after Python changes
- [ ] **bench restart** for production changes

### Deployment Checks

- [ ] **Backup before destructive operations**
- [ ] **Scheduler enabled** (`bench --site X scheduler enable`)
- [ ] **Workers running** (check supervisor status)
- [ ] **SSL configured** for production
- [ ] **Nginx configured** for production

### Upgrade Checks

- [ ] **Backup taken** before upgrade
- [ ] **Custom app compatibility** verified
- [ ] **Patches tested** on staging
- [ ] **Fixtures re-exported** if needed

---

## DocType JSON Checklist

### Required

- [ ] **Naming configured** (autoname or naming_rule)
- [ ] **Module specified** and exists in modules.txt
- [ ] **Permissions defined** for at least one role
- [ ] **Fieldnames unique** within DocType

### Warnings

- [ ] **No duplicate fieldnames** across sections
- [ ] **Appropriate fieldtypes** for data
- [ ] **Link fields have valid options** (target DocType)
- [ ] **Required fields marked as reqd**

---

## Universal Security Checklist

### Critical

- [ ] **No SQL injection** - Use parameterized queries
- [ ] **Permission checks present** - frappe.has_permission()
- [ ] **No hardcoded credentials** - Use frappe.conf.get()

### High

- [ ] **XSS prevention** - frappe.utils.escape_html()
- [ ] **Sensitive data not logged** - Mask passwords/tokens

---

## Universal Performance Checklist

- [ ] **No query in loop** - Single query before loop
- [ ] **Bounded queries** - LIMIT on large tables
- [ ] **get_value over get_doc** - When only one field needed
- [ ] **Batch commits** - Every 100-500 records, not per record
- [ ] **Cache used** - For frequently accessed static data

---

## Quick Reference: Regex Patterns for Detection

### Server Script Issues
```
Import:        ^import |^from .* import
Self usage:    \bself\.\w+
Try/except:    \btry\s*:|except\s
```

### Client Script Issues
```
Server API:    frappe\.db\.(get_value|set_value|sql|get_all|get_list)
Async issue:   (let|const|var)\s+\w+\s*=\s*frappe\.call\s*\((?!.*callback)
cur_frm:       \bcur_frm\b
```

### Controller Issues
```
on_update mod:  def on_update\(self\):[\s\S]*?self\.\w+\s*=
circular save:  def (validate|on_update)\(self\):[\s\S]*?self\.save\(\)
missing super:  def (validate|on_submit)\(self\):(?![\s\S]*?super\(\))
```

### Security Issues
```
SQL injection:  f["'].*\{.*\}.*["']\s*\)  (in SQL context)
Hardcoded key:  (api_key|password|secret|token)\s*=\s*["'][^"']+["']
```
