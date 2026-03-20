# Test API Reference

## Test Base Classes

### UnitTestCase (v15+)

**Import**: `from frappe.tests.classes import UnitTestCase`

**Inherits**: `unittest.TestCase`, `BaseTestCase`

**Class Attributes**:
- `doctype` — Auto-detected from module path (e.g., `myapp.mymodule.doctype.my_dt.test_my_dt` → `My Dt`)
- `module` — The test module reference

**Setup Methods**:

| Method | When Called | Purpose |
|--------|-----------|---------|
| `setUpClass()` | Once per class | Sets `frappe.set_user("Administrator")`, detects doctype |
| `setUp()` | Before each test | Override for per-test setup |
| `tearDown()` | After each test | Override for per-test cleanup |
| `tearDownClass()` | Once after all tests | Override for class-level cleanup |

**Assertion Methods**:

| Method | Signature | Purpose |
|--------|-----------|---------|
| `assertDocumentEqual` | `(expected: dict, actual: BaseDocument)` | Compare document fields — handles floats (precision-aware), ints, dates, child tables |
| `assertQueryEqual` | `(first: str, second: str)` | Compare SQL queries after normalization |
| `assertSequenceSubset` | `(larger: Sequence, smaller: Sequence)` | Assert smaller is subset of larger |

**Utility Methods**:

| Method | Signature | Returns | Purpose |
|--------|-----------|---------|---------|
| `normalize_html` | `(code: str)` | `str` | Format HTML for comparison (uses BeautifulSoup) |
| `normalize_sql` | `(query: str)` | `str` | Format SQL for comparison (uses sqlparse, handles PostgreSQL) |

### IntegrationTestCase (v15+)

**Import**: `from frappe.tests.classes import IntegrationTestCase`

**Inherits**: `UnitTestCase`

**Class Attributes**:
- `TEST_SITE = "test_site"` — Default test site name
- `SHOW_TRANSACTION_COMMIT_WARNINGS = False` — Log commits with stack traces when True
- `maxDiff = 10_000` — Maximum diff output size

**Setup Methods**:

| Method | When Called | Purpose |
|--------|-----------|---------|
| `setUpClass()` | Once per class | `frappe.init()`, DB connection, `make_test_records()`, snapshot globals |
| `setUp()` | Before each test | Enables fault handler (300s timeout) |
| `tearDown()` | After each test | Rollback DB, restore context |

**Connection Methods**:

| Method | Type | Purpose |
|--------|------|---------|
| `primary_connection()` | Context manager | Switch to primary DB connection |
| `secondary_connection()` | Context manager | Use secondary DB connection (lazy-initialized) |

**Assertion Context Managers**:

| Method | Signature | Purpose |
|--------|-----------|---------|
| `assertQueryCount` | `(count: int, *, query_type=None)` | Assert exact number of SQL queries executed |
| `assertRedisCallCounts` | `(**commands)` | Assert Redis command counts (exact or approximate) |
| `assertRowsRead` | `(count: int)` | Assert maximum rows read from DB |

### FrappeTestCase (v14, deprecated in v15+)

**Import**: `from frappe.tests.utils import FrappeTestCase`

**Behavior**: In v15+, this is a compatibility wrapper that maps to the old behavior. In v14, it is the primary test class.

**Key Differences from v15+ classes**:
- Single class for both unit and integration tests
- No distinction between DB and non-DB tests
- Same rollback behavior as IntegrationTestCase

## Context Managers

All context managers are available as static methods on UnitTestCase and IntegrationTestCase.

### set_user

```python
with self.set_user("test@example.com"):
    # Code runs as test@example.com
    pass
# User automatically restored to previous user
```

### change_settings

```python
# Positional dict style
with self.change_settings("Selling Settings", {"so_required": 1}):
    pass

# Keyword argument style
with self.change_settings("Selling Settings", so_required=1):
    pass

# With commit (ONLY use when testing code that reads from a separate transaction)
with self.change_settings("HR Settings", commit=True, auto_leave_encashment=1):
    pass
```

### patch_hooks

```python
with self.patch_hooks({"doc_events": {"Sales Order": {"on_submit": ["myapp.hooks.custom_submit"]}}}):
    # Custom hook is active
    pass
```

### freeze_time

```python
with self.freeze_time("2024-06-15 10:30:00"):
    now = frappe.utils.now_datetime()
    # now == datetime(2024, 6, 15, 10, 30, 0)

# With UTC flag
with self.freeze_time("2024-06-15 10:30:00", is_utc=True):
    pass
```

### enable_safe_exec

```python
with self.enable_safe_exec():
    # Server scripts can execute
    frappe.safe_eval("1 + 1")
```

### debug_on

```python
with self.debug_on(AssertionError, ValueError):
    # Drops into pdb on AssertionError or ValueError
    risky_function()
```

### timeout (Decorator)

```python
from frappe.tests.classes.context_managers import timeout

@timeout(seconds=10)
def test_must_be_fast(self):
    # Fails if test takes longer than 10 seconds
    pass
```

## CLI Reference: bench run-tests

| Flag | Purpose | Example |
|------|---------|---------|
| `--app APP` | Run tests for specific app | `--app erpnext` |
| `--doctype DOCTYPE` | Run tests for specific DocType | `--doctype "Sales Order"` |
| `--test TEST` | Run specific test method | `--test test_submit` |
| `--module MODULE` | Run tests in specific module | `--module "myapp.tests.test_utils"` |
| `--profile` | Run Python profiler | `--profile` |
| `--failfast` | Stop on first failure | `--failfast` |
| `--junit-xml-output PATH` | Generate JUnit XML report | `--junit-xml-output report.xml` |
| `--skip-test-records` | Skip loading test_records | `--skip-test-records` |
| `--skip-before-tests` | Skip before_tests hooks | `--skip-before-tests` |
| `--verbose` | Verbose output | `bench --verbose run-tests` |

## CLI Reference: bench run-parallel-tests

| Flag | Purpose | Example |
|------|---------|---------|
| `--total-builds N` | Total number of parallel builds | `--total-builds 4` |
| `--build-number N` | This build's index (0-based) | `--build-number 0` |
| `--use-orchestrator` | Use orchestrator for distribution | `--use-orchestrator` |

Environment variables for orchestrator mode:
- `CI_BUILD_ID` — Unique build identifier
- `ORCHESTRATOR_URL` — URL of the test orchestrator service

## Utility Functions

### frappe.tests.utils

| Function | Purpose |
|----------|---------|
| `toggle_test_mode(enable: bool)` | Enable/disable `frappe.in_test` flag |
| `whitelist_for_tests(**kwargs)` | Decorator: whitelist function for test access only |
| `check_orphaned_doctypes()` | Validate all DocTypes have controllers (post-patch) |
| `change_settings(dt, settings)` | Context manager for temporary settings changes |
| `patch_hooks(overrides)` | Context manager for temporary hook overrides |
| `debug_on(*exceptions)` | Context manager for interactive debugging |
| `timeout(seconds)` | Decorator for test timeout |

### frappe.flags for Testing

| Flag | Purpose |
|------|---------|
| `frappe.flags.in_test` | `True` when running under test runner |
| `frappe.flags.in_import` | `True` during data import |
| `frappe.flags.print_messages` | Set `False` to suppress messages in tests |

### frappe.in_test

Boolean property — `True` when the test runner is active. Equivalent to `frappe.flags.in_test` but preferred in v15+.
