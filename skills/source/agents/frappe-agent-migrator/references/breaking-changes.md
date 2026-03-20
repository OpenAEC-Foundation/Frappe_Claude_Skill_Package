# Breaking Changes Database

## v14 → v15 Breaking Changes (Detailed)

### 1. Scheduler Tick Interval Change
- **Before**: Default scheduler tick every 240 seconds
- **After**: Default scheduler tick every 60 seconds
- **Impact**: Scheduled tasks run 4x more frequently
- **Fix**: Review `scheduler_events` in hooks.py; add deduplication logic if tasks are not idempotent
- **Detection**: `grep -rn "scheduler_events" hooks.py`

### 2. Background Job Deduplication
- **Before**: Same job could be enqueued multiple times
- **After**: `job_id` parameter enables deduplication; duplicate jobs are silently dropped
- **Impact**: Code relying on multiple identical jobs executing will behave differently
- **Fix**: Review `frappe.enqueue()` calls; ensure `job_id` is set correctly or omitted
- **Detection**: `grep -rn "frappe.enqueue" --include="*.py"`

### 3. Workspace Replaces Module Def Pages
- **Before**: Module pages defined via Module Def
- **After**: Workspace DocType replaces Module Def pages
- **Impact**: Custom module pages will not display
- **Fix**: Migrate module pages to Workspace configuration
- **Detection**: `grep -rn "Module Def" --include="*.py" --include="*.json"`

### 4. Print Format Engine Changes
- **Before**: wkhtmltopdf used for all PDF generation
- **After**: Updated PDF generation pipeline
- **Impact**: Print format layouts may render differently
- **Fix**: Test all print formats on staging; adjust CSS/HTML as needed
- **Detection**: Visual inspection required

### 5. MariaDB 10.6+ Required
- **Before**: MariaDB 10.3+ supported
- **After**: MariaDB 10.6+ required
- **Impact**: Server must be upgraded before Frappe upgrade
- **Fix**: Upgrade MariaDB to 10.6+ before starting migration
- **Detection**: `mysql --version`

### 6. Python 3.10+ Required
- **Before**: Python 3.8+ supported
- **After**: Python 3.10+ required
- **Impact**: Some Python 3.8/3.9 syntax patterns may differ
- **Fix**: Upgrade Python; check for deprecated stdlib usage
- **Detection**: `python3 --version`

### 7. Client API Changes
- **Before**: `frappe.set_route()` with different signature
- **After**: Router API updated
- **Impact**: Custom JavaScript navigation code may break
- **Fix**: Update to new `frappe.router` API
- **Detection**: `grep -rn "frappe.set_route\|cur_page" --include="*.js"`

### 8. Stricter Permission Checks on API
- **Before**: Some API endpoints accessible without explicit permission
- **After**: Stricter permission validation on all API calls
- **Impact**: Guest or low-privilege API calls may fail
- **Fix**: Add `allow_guest=True` where needed; verify `@frappe.whitelist()` decorators
- **Detection**: `grep -rn "frappe.whitelist" --include="*.py"`

### 9. Frontend Build System Changes
- **Before**: Older webpack/rollup configuration
- **After**: Updated build toolchain
- **Impact**: Custom JS bundles may need rebuild configuration
- **Fix**: Update `package.json` and build scripts; run `bench build`
- **Detection**: `bench build --verbose` (check for errors)

### 10. Boot Session Hook Changes
- **Before**: `boot_session` hook with certain signature
- **After**: Updated boot session mechanism
- **Impact**: Custom boot data injection may fail
- **Fix**: Update boot session hooks to new signature
- **Detection**: `grep -rn "boot_session" hooks.py`

### 11. Database Query API Changes
- **Before**: `frappe.db.sql_list()` and `frappe.db.sql_ddl()` available
- **After**: Deprecated in favor of `frappe.db.get_all()` with `pluck`
- **Impact**: Code using deprecated methods may fail
- **Fix**: Replace with modern equivalents
- **Detection**: `grep -rn "sql_list\|sql_ddl" --include="*.py"`

### 12. Report Builder Updates
- **Before**: Older report rendering API
- **After**: Updated Report Builder with new API
- **Impact**: Custom Script Reports may need query/column updates
- **Fix**: Test all reports; update `execute()` function if needed
- **Detection**: Test each report individually

---

## v15 → v16 Breaking Changes (Detailed)

### 1. extend_doctype_class (New Pattern)
- **Before**: Override controllers via `doc_events` in hooks.py
- **After**: `extend_doctype_class` enables proper class inheritance
- **Impact**: Old pattern still works but new pattern is preferred; mixins MUST call `super()`
- **Fix**: Refactor controller overrides to use `extend_doctype_class`
- **Detection**: `grep -rn "doc_events" hooks.py` (look for method overrides)

### 2. Chrome-Based PDF Rendering
- **Before**: wkhtmltopdf for PDF generation
- **After**: Chrome/Chromium-based PDF rendering
- **Impact**: Print format CSS and layout rendering changes
- **Fix**: Test all print formats; adjust CSS for Chrome rendering
- **Detection**: Visual inspection of all print formats

### 3. Data Masking Feature
- **Before**: No built-in PII masking
- **After**: `mask_with` field option in DocType JSON
- **Impact**: Sensitive fields should be configured for masking
- **Fix**: Add `mask_with` to PII fields (email, phone, etc.)
- **Detection**: Review DocType JSON for sensitive fields

### 4. UUID Naming Rule
- **Before**: Naming rules: autoincrement, hash, expression, field, series
- **After**: New `uuid` naming rule option
- **Impact**: New DocTypes can use UUID; migration does not auto-convert
- **Fix**: Optionally adopt UUID naming for new DocTypes
- **Detection**: No action required for existing DocTypes

### 5. Python 3.11+ Required
- **Before**: Python 3.10+ supported
- **After**: Python 3.11+ required
- **Impact**: Some library compatibility changes
- **Fix**: Upgrade Python to 3.11+
- **Detection**: `python3 --version`

### 6. Node.js 18+ Required
- **Before**: Node 16+ supported
- **After**: Node 18+ required
- **Impact**: Build system requires newer Node
- **Fix**: Upgrade Node.js to 18+ (use nvm)
- **Detection**: `node --version`

### 7. Redis 7+ Required
- **Before**: Redis 6+ supported
- **After**: Redis 7+ required
- **Impact**: Cache and queue operations
- **Fix**: Upgrade Redis to 7+
- **Detection**: `redis-server --version`

### 8. Type Annotations Best Practice
- **Before**: Type hints optional
- **After**: Type annotations recommended for all public methods
- **Impact**: Not breaking but strongly encouraged
- **Fix**: Add type hints to `@frappe.whitelist()` and public methods
- **Detection**: `grep -rn "def.*whitelist" --include="*.py"` (check for missing hints)

### 9. Deprecated API Removals
- **Before**: Various deprecated APIs still functional
- **After**: Some deprecated APIs removed entirely
- **Impact**: Code using removed APIs will crash
- **Fix**: Replace with current equivalents (see list below)
- **Detection**: Grep for each deprecated pattern

### 10. Workflow Engine Updates
- **Before**: Workflow with specific state handling
- **After**: Updated workflow transition logic
- **Impact**: Custom workflow state handlers may need review
- **Fix**: Test all workflows on staging
- **Detection**: `frappe.get_all("Workflow", fields=["name", "document_type"])`

### 11. Portal Page Rendering
- **Before**: Portal pages with certain template engine
- **After**: Updated portal rendering
- **Impact**: Custom portal templates may render differently
- **Fix**: Test all portal pages; adjust templates
- **Detection**: `grep -rn "website_route_rules\|get_website_page" --include="*.py"`

### 12. RQ Version Upgrade
- **Before**: Older RQ (Redis Queue) version
- **After**: RQ upgraded with serialization changes
- **Impact**: Background job argument serialization may change
- **Fix**: Ensure job arguments are simple types (str, int, float, dict, list)
- **Detection**: `grep -rn "frappe.enqueue" --include="*.py"` (check argument types)

---

## Deprecated API Mapping

### Methods Removed or Changed in v15

| Deprecated | Replacement |
|-----------|-------------|
| `frappe.db.sql_list()` | `frappe.db.get_all(..., pluck="name")` |
| `frappe.db.sql_ddl()` | Direct `frappe.db.sql()` with DDL |
| `frappe.get_module_path()` (old sig) | `frappe.get_module_path(module, ...)` |
| `cur_page` (JS) | `frappe.router.current_route` |

### Methods Removed or Changed in v16

| Deprecated | Replacement |
|-----------|-------------|
| `doc_events` controller override | `extend_doctype_class` |
| `override_doctype_class` | `extend_doctype_class` |
| `frappe.utils.pdf.get_pdf()` (old sig) | Updated PDF API |
| `frappe.get_hooks("boot_session")` (old sig) | Updated boot hooks |
