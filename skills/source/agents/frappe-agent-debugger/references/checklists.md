# Debugging Checklists

## Pre-Debug Information Gathering

ALWAYS collect this information before starting diagnosis:

- [ ] Exact error message or traceback (copy-paste, not paraphrased)
- [ ] When does it occur? (form save, submit, page load, scheduled, API call)
- [ ] Is it reproducible? (always, sometimes, first-time only)
- [ ] What changed recently? (code deploy, bench update, new app installed)
- [ ] Frappe/ERPNext version (`bench version`)
- [ ] Site name and environment (development, staging, production)

## Python Error Checklist

### Server Script Errors
- [ ] No `import` statements (Server Scripts CANNOT import)
- [ ] Using `doc` variable (NOT `self`, NOT `document`)
- [ ] Correct event selected (validate vs on_update vs on_submit)
- [ ] No `doc.save()` inside the script (causes infinite loop)
- [ ] Null checks before accessing nested attributes
- [ ] `frappe.throw()` for user-facing errors (NOT `raise`)
- [ ] Script is enabled (not disabled in Server Script list)
- [ ] Correct DocType reference in Server Script configuration

### Controller Errors
- [ ] `super().method()` called in overrides
- [ ] NOT modifying `self.*` in `on_update` (use `self.db_set()` instead)
- [ ] NOT calling `self.save()` inside lifecycle hooks
- [ ] Imports at module level (top of file)
- [ ] `frappe.throw()` for validation errors
- [ ] Transaction awareness (changes before `frappe.throw()` are rolled back)

### Whitelisted Method Errors
- [ ] `@frappe.whitelist()` decorator present
- [ ] `allow_guest=True` if called by guest users
- [ ] Parameter types match what frontend sends (all strings from JS)
- [ ] Return value is JSON-serializable
- [ ] Permission check inside method body

## JavaScript Error Checklist

### Client Script Errors
- [ ] NO server-side calls (`frappe.db.*`, `frappe.get_doc()`)
- [ ] `frappe.call()` uses callback or async/await
- [ ] `frm.refresh_fields()` after `frm.set_value()`
- [ ] Using `frm` parameter (NOT `cur_frm`)
- [ ] Field names match DocType definition exactly
- [ ] Script type matches purpose (Form, List, etc.)
- [ ] Correct DocType reference in Client Script configuration
- [ ] Check `frm.doc.__islocal` before accessing saved-only fields

### API Call Errors
- [ ] Correct method path in `frappe.call()`
- [ ] Method is whitelisted on server
- [ ] Arguments match server function signature
- [ ] Response handler checks for `r.message` (not `r.data`)
- [ ] Error callback handles failures gracefully

## Database Error Checklist

- [ ] Run `bench migrate` after any DocType field change
- [ ] Check table exists: `bench mariadb` → `SHOW TABLES LIKE 'tab%'`
- [ ] Check column exists: `DESCRIBE \`tab{DocType}\``
- [ ] Check for duplicate entries causing IntegrityError
- [ ] Check foreign key references exist (Link field targets)
- [ ] Check character encoding for special characters
- [ ] Verify autoname/naming_series configuration

## Permission Error Checklist

- [ ] Role has the required permission level (read, write, create, submit, cancel, delete)
- [ ] User has the role assigned
- [ ] User Permission restrictions checked (per-document filtering)
- [ ] `if_owner` permission considered
- [ ] For API: `@frappe.whitelist()` decorator present
- [ ] For guest access: `allow_guest=True` in whitelist
- [ ] Custom permission checks in code use `frappe.has_permission()`

## Hook Error Checklist

- [ ] hooks.py has valid Python syntax
- [ ] Function dotted paths are correct and exist
- [ ] Event names are spelled correctly
- [ ] `bench migrate` run after hooks.py changes
- [ ] No circular imports in referenced functions
- [ ] `required_apps` lists all dependencies
- [ ] v16-only hooks not used on v14/v15

## Scheduler Error Checklist

- [ ] Scheduler is enabled: `bench doctor`
- [ ] Workers are running: check supervisor/systemd
- [ ] Job function path is correct in hooks.py
- [ ] `frappe.init()` and `frappe.connect()` for standalone scripts
- [ ] Long-running jobs use `frappe.enqueue()` (not direct execution)
- [ ] Check RQ failed queue: `bench doctor`
- [ ] Check scheduler log: `sites/{site}/logs/scheduler.log`

## Build Error Checklist

- [ ] `bench build` completes without errors
- [ ] Node.js version compatible (check `.nvmrc` or `package.json`)
- [ ] `yarn install` completed in `apps/{app}`
- [ ] Frontend file paths correct in `hooks.py` (app_include_js/css)
- [ ] No circular imports in JavaScript modules
- [ ] Clear browser cache after rebuild
- [ ] For production: `bench build --production`

## Post-Fix Verification Checklist

After applying any fix, ALWAYS verify:

- [ ] Original error no longer occurs
- [ ] No new errors introduced (check Error Log DocType)
- [ ] Related functionality still works (regression check)
- [ ] Fix works on target Frappe version
- [ ] Logs are clean: `tail -f sites/{site}/logs/frappe.log`
