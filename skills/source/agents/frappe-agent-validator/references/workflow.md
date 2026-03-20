# Code Validator Workflow - Detailed Steps

## Step 1: Identify Code Type

### Detection Rules

| If Code Contains... | Code Type |
|---------------------|-----------|
| `frappe.ui.form.on(` | Client Script |
| `# Server Script` or sandbox patterns | Server Script |
| `class X(Document):` | Controller |
| `doc_events = {`, `scheduler_events = {` | hooks.py |
| `{% ... %}`, `{{ ... }}` | Jinja Template |
| `@frappe.whitelist()` | Whitelisted Method |
| `bench ` commands | Ops/Bench |
| `.json` with `doctype` key | DocType JSON |
| `extend_doctype_class` | v16 hooks.py |

### When Ambiguous

Ask: "Is this code running in:"
- Browser (JavaScript) --> Client Script
- Frappe UI Server Script editor --> Server Script
- Python file in custom app --> Controller or Whitelisted
- hooks.py configuration --> Hooks
- Terminal/CLI --> Bench/Ops command

## Step 2: Type-Specific Validation

### Server Script Validation

```
1. IMPORT SCAN [FATAL]
   Regex: ^import |^from .* import
   If found: FATAL - imports blocked in sandbox

2. VARIABLE REFERENCE CHECK [FATAL]
   Check for: self.*, document.*, this.
   If found: FATAL - should use doc.*

3. TRY/EXCEPT SCAN [WARNING]
   Regex: try:|except
   If found: WARNING - usually wrong in Server Scripts

4. EVENT NAME VERIFICATION
   Before Save code --> should be validate hook
   After Save code --> should be on_update hook
   Mismatch: ERROR

5. AVAILABLE NAMESPACE CHECK
   Only allowed: frappe.*, doc, None, True, False,
   int, float, str, list, dict, set, tuple

6. FRAPPE API CHECK
   Verify valid: frappe.throw(), frappe.msgprint(),
   frappe.db.*, frappe.utils.*, frappe.get_doc(), etc.
```

### Client Script Validation

```
1. SERVER API MISUSE [FATAL]
   Check for: frappe.db.*, frappe.get_doc( (without frappe.call)

2. ASYNC HANDLING [FATAL]
   Check for: frappe.call() without callback/async
   Pattern: let x = frappe.call({...}) without callback

3. FORM STRUCTURE CHECK
   Must be inside: frappe.ui.form.on('DocType', {...})

4. FIELD OPERATIONS CHECK
   After frm.set_value(): should have frm.refresh_field()

5. FORM STATE CHECKS
   Operations on new doc: check frm.doc.__islocal
   Operations on submitted: check frm.doc.docstatus
```

### Controller Validation

```
1. CLASS STRUCTURE [ERROR]
   Must extend Document or specific DocType class

2. SUPER CALL CHECK [WARNING/ERROR]
   Override methods should call super()
   v16 extend_doctype_class: super() is MANDATORY

3. LIFECYCLE MODIFICATION CHECK [FATAL]
   In on_update: modifications to self.* won't save
   Should use: self.db_set() or frappe.db.set_value()

4. CIRCULAR SAVE CHECK [FATAL]
   Pattern: self.save() in lifecycle hooks

5. IMPORT VERIFICATION
   Imports ARE allowed (unlike Server Scripts)

6. TYPE ANNOTATIONS CHECK [SUGGESTION - v16]
   Public methods should have type hints
```

### hooks.py Validation

```
1. STRUCTURE CHECK
   Valid Python dict syntax
   No syntax errors

2. HOOK NAME VERIFICATION
   doc_events: valid event names
   scheduler_events: valid frequency keys

3. PATH VERIFICATION
   Dotted paths should be valid Python paths

4. VERSION-SPECIFIC HOOKS
   extend_doctype_class: v16+ only
   If found in v14/v15 code: ERROR

5. REQUIRED APPS CHECK
   All imported apps must be in required_apps

6. FIXTURE FILTER CHECK
   Shared DocTypes (Custom Field, etc.) must have filters
```

### Ops/Bench Validation

```
1. COMMAND SYNTAX CHECK
   bench --site sitename [command] format

2. MIGRATE REQUIREMENT CHECK
   After hooks.py changes: bench migrate required
   After DocType changes: bench migrate required

3. BUILD REQUIREMENT CHECK
   After JS/CSS changes: bench build required

4. BACKUP CHECK
   Before destructive operations: backup required

5. DEPLOYMENT CHECKS
   Production: supervisor/systemd configured
   Production: nginx configured
   Production: SSL/TLS configured
   Production: scheduler enabled
```

## Step 3: Universal Checks

### Security Validation

```
1. SQL INJECTION [CRITICAL]
   Pattern: f"...{user_input}..." in SQL
   Should use: parameterized queries or frappe.db.escape()

2. PERMISSION BYPASS [CRITICAL]
   Pattern: ignore_permissions=True without justification
   Should have: explicit permission checks

3. XSS VULNERABILITY [HIGH]
   Pattern: user input directly in HTML
   Should use: frappe.utils.escape_html()

4. SENSITIVE DATA [HIGH]
   Pattern: password, token, secret in log/print
   Should be: masked or omitted

5. HARDCODED CREDENTIALS [CRITICAL]
   Pattern: API keys, passwords in source
   Should use: frappe.conf.get() or settings DocType
```

### Error Handling Validation

```
1. SILENT FAILURE [HIGH]
   Pattern: except: pass
   Should have: logging or re-raise

2. USER FEEDBACK [MEDIUM]
   Error occurs but no frappe.throw/msgprint
   Should have: user notification

3. ROLLBACK HANDLING [HIGH]
   After failed operations: frappe.db.rollback()
   In batch processing: commit per batch, not per record
```

### Performance Validation

```
1. QUERY IN LOOP [HIGH]
   Pattern: for item in items: frappe.db.get_value()
   Should be: single query before loop

2. UNBOUNDED QUERY [MEDIUM]
   Pattern: frappe.get_all() without limit
   Should have: limit_page_length or filters

3. UNNECESSARY GET_DOC [LOW]
   Pattern: frappe.get_doc() when only one field needed
   Should be: frappe.db.get_value()

4. NO BATCH COMMIT [HIGH]
   Pattern: frappe.db.commit() per record
   Should be: commit every 100-500 records
```

## Step 4: Version Compatibility Check

```
V16-ONLY FEATURES (will fail on v14/v15):
- extend_doctype_class hook
- naming_rule = "UUID" in DocType
- pdf_renderer = "chrome" in Print Format
- data masking configuration
- Type annotations (best practice, not required)

DEPRECATED PATTERNS (warn):
- frappe.bean() --> use frappe.get_doc()
- frappe.msgprint(raise_exception=True) --> use frappe.throw()
- job_name parameter --> use job_id (v15+)
- setup.py --> use pyproject.toml (v15+)

BEHAVIORAL DIFFERENCES:
- Scheduler tick: 240s (v14) vs 60s (v15+)
- Job dedup: job_name (v14) vs job_id (v15+)
```

## Step 5: Validate Against Skill Catalog

Cross-reference code against relevant frappe-* skills:

| Code Type | Validate Against |
|-----------|-----------------|
| Server Script | `frappe-syntax-serverscripts`, `frappe-errors-serverscripts` |
| Client Script | `frappe-syntax-clientscripts`, `frappe-errors-clientscripts` |
| Controller | `frappe-syntax-controllers`, `frappe-errors-controllers` |
| hooks.py | `frappe-syntax-hooks`, `frappe-errors-hooks` |
| Jinja | `frappe-syntax-jinja` |
| Whitelisted | `frappe-syntax-whitelisted` |
| Scheduler | `frappe-syntax-scheduler`, `frappe-impl-scheduler` |
| Custom App | `frappe-syntax-customapp`, `frappe-impl-customapp` |
| Database ops | `frappe-core-database`, `frappe-errors-database` |
| Permissions | `frappe-core-permissions`, `frappe-errors-permissions` |
| API calls | `frappe-core-api`, `frappe-errors-api` |
| Workflow | `frappe-core-workflow`, `frappe-impl-workflow` |
| Reports | `frappe-syntax-reports`, `frappe-impl-reports` |
| Bench/Ops | `frappe-ops-bench`, `frappe-ops-deployment` |
| Testing | `frappe-testing-unit`, `frappe-testing-cicd` |

## Step 6: Generate Report

### Report Structure

```markdown
## Code Validation Report

### Summary
- Code Type: [type]
- Total Issues: X critical, Y warnings, Z suggestions
- Overall: [FAIL / PASS WITH WARNINGS / PASS]

### Critical Errors (Must Fix)
[Table of critical issues]

### Warnings (Should Fix)
[Table of warnings]

### Suggestions (Nice to Have)
[Table of suggestions]

### Corrected Code
[If critical errors exist, provide corrected version]

### Version Compatibility
[Compatibility matrix v14/v15/v16]

### Referenced Skills
[Which frappe-* skills were validated against]
```

### Severity Classification

| Severity | Criteria | Action Required |
|----------|----------|-----------------|
| CRITICAL | Code will fail/crash | Must fix before deployment |
| HIGH | Significant bug/security issue | Should fix before deployment |
| MEDIUM | Potential issues | Fix when possible |
| LOW | Style/optimization | Optional improvement |
| SUGGESTION | Best practice | Consider for future |
