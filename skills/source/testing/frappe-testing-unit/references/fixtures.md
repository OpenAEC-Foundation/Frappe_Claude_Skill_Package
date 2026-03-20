# Test Fixtures in Depth

## Fixture Loading Order

The Frappe test runner loads fixtures in this order:

1. **Dependency resolution**: Link fields are inspected to determine which DocTypes must be created first
2. **test_records.json**: Loaded from the doctype directory (if present)
3. **_test_records**: Loaded from the test module (if present)
4. **make_test_records()**: Called by IntegrationTestCase.setUpClass()

ALWAYS ensure linked DocTypes have their own test records — the runner builds them automatically but ONLY if `test_records.json` or `_test_records` exists for those DocTypes.

## test_records.json Format

### Basic Records

```json
[
    {
        "doctype": "Item",
        "item_code": "_Test Item",
        "item_name": "_Test Item",
        "item_group": "_Test Item Group",
        "stock_uom": "_Test UOM"
    },
    {
        "doctype": "Item",
        "item_code": "_Test Item 2",
        "item_name": "_Test Item 2",
        "item_group": "_Test Item Group",
        "stock_uom": "_Test UOM"
    }
]
```

### Records with Child Tables

```json
[
    {
        "doctype": "Sales Order",
        "customer": "_Test Customer",
        "delivery_date": "2024-12-31",
        "items": [
            {
                "item_code": "_Test Item",
                "qty": 10,
                "rate": 100
            }
        ],
        "taxes": [
            {
                "charge_type": "On Net Total",
                "account_head": "_Test Account VAT - _TC",
                "rate": 21
            }
        ]
    }
]
```

### Naming Convention Rules

- ALWAYS prefix values with `_Test` — e.g., `_Test Customer`, `_Test Item`
- ALWAYS use `_Test` prefix for names that could collide with real data
- Child table rows do NOT need `doctype` field — it is inferred from the parent
- Date fields SHOULD use a future date to avoid past-date validation errors

## _test_records In-Module Format

```python
# In test_my_doctype.py

_test_records = [
    {
        "doctype": "My Doctype",
        "title": "_Test Record 1",
        "status": "Active",
    },
    {
        "doctype": "My Doctype",
        "title": "_Test Record 2",
        "status": "Inactive",
    },
]
```

This format is equivalent to `test_records.json` but lives in the Python test file. Use this when:
- You need to generate dynamic fixture values
- You want fixtures co-located with test logic
- The DocType has no dedicated directory (non-DocType tests)

## Programmatic Fixtures

### Simple Pattern with Flag Guard

```python
def create_test_items():
    if frappe.flags.test_items_created:
        return

    frappe.set_user("Administrator")

    items = [
        {"item_code": "_Test Widget A", "item_group": "Products", "stock_uom": "Nos"},
        {"item_code": "_Test Widget B", "item_group": "Products", "stock_uom": "Nos"},
    ]

    for item_data in items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            frappe.get_doc({"doctype": "Item", **item_data}).insert()

    frappe.flags.test_items_created = True
```

### Complex Fixtures with Dependencies

```python
def create_test_sales_setup():
    """Create a complete sales test environment."""
    if frappe.flags.test_sales_setup_done:
        return

    frappe.set_user("Administrator")

    # 1. Create customer group (dependency)
    if not frappe.db.exists("Customer Group", "_Test Group"):
        frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "_Test Group",
        }).insert()

    # 2. Create customer (depends on customer group)
    if not frappe.db.exists("Customer", "_Test Customer"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "_Test Customer",
            "customer_group": "_Test Group",
        }).insert()

    # 3. Create items
    for i in range(3):
        code = f"_Test Sale Item {i}"
        if not frappe.db.exists("Item", code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": code,
                "item_group": "Products",
                "stock_uom": "Nos",
            }).insert()

    frappe.flags.test_sales_setup_done = True
```

### Using setUpClass for One-Time Setup

```python
class TestSalesWorkflow(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_test_sales_setup()
        cls.customer = "_Test Customer"
        cls.items = [f"_Test Sale Item {i}" for i in range(3)]
```

## Fixture Cleanup

### Automatic (Recommended)

IntegrationTestCase rolls back all database changes after each test. NEVER manually delete test records — the rollback handles it.

### Manual Cleanup (Only for Non-Standard Cases)

```python
class TestWithCleanup(IntegrationTestCase):
    def setUp(self):
        self.created_docs = []

    def tearDown(self):
        for doc_name in reversed(self.created_docs):
            frappe.delete_doc("My Doctype", doc_name, force=True)

    def _create_doc(self, **kwargs):
        doc = frappe.get_doc({"doctype": "My Doctype", **kwargs}).insert()
        self.created_docs.append(doc.name)
        return doc
```

NEVER use manual cleanup with IntegrationTestCase — the automatic rollback is sufficient and more reliable.

## Fixture Best Practices

1. **ALWAYS use `frappe.db.exists()` before inserting** — prevents duplicate key errors when fixtures are shared across test classes
2. **ALWAYS use flag guards** (`frappe.flags.test_X_created`) — prevents re-insertion
3. **ALWAYS set user to Administrator** before creating fixtures — avoids permission errors
4. **NEVER hardcode auto-generated names** (like `ACC-001`) — use `frappe.db.get_value()` to look up
5. **ALWAYS create fixtures in dependency order** — parent records before child records
6. **NEVER use `frappe.db.commit()`** in fixture creation — let the framework handle transactions
