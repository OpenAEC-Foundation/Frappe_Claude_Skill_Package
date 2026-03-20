# Unit & Integration Test Anti-Patterns

## Anti-Pattern 1: Calling frappe.db.commit() in Tests

```python
# WRONG — breaks test isolation, data persists across tests
class TestBadCommit(IntegrationTestCase):
    def test_something(self):
        doc = frappe.get_doc({"doctype": "ToDo", "description": "test"}).insert()
        frappe.db.commit()  # NEVER do this
```

```python
# CORRECT — let the test framework handle rollback
class TestGoodRollback(IntegrationTestCase):
    def test_something(self):
        doc = frappe.get_doc({"doctype": "ToDo", "description": "test"}).insert()
        # No commit — IntegrationTestCase rolls back automatically
```

## Anti-Pattern 2: Forgetting super().setUpClass()

```python
# WRONG — breaks fixture loading and user setup
class TestBroken(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        cls.custom_data = "something"
        # Missing super().setUpClass() — tests will fail unpredictably
```

```python
# CORRECT — ALWAYS call super first
class TestFixed(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.custom_data = "something"
```

## Anti-Pattern 3: Tests Depending on Execution Order

```python
# WRONG — test_b depends on test_a having run first
class TestOrderDependent(IntegrationTestCase):
    def test_a_create(self):
        frappe.get_doc({"doctype": "ToDo", "description": "_Order Test"}).insert()

    def test_b_read(self):
        # This WILL fail because test_a's insert was rolled back
        doc = frappe.get_doc("ToDo", {"description": "_Order Test"})
```

```python
# CORRECT — each test is self-contained
class TestIndependent(IntegrationTestCase):
    def test_create_and_read(self):
        doc = frappe.get_doc({"doctype": "ToDo", "description": "_Order Test"}).insert()
        fetched = frappe.get_doc("ToDo", doc.name)
        self.assertEqual(fetched.description, "_Order Test")
```

## Anti-Pattern 4: Not Resetting User Context (v14)

```python
# WRONG — user context leaks to next test
class TestLeakyUser(FrappeTestCase):
    def test_as_user(self):
        frappe.set_user("test@example.com")
        # ... test logic ...
        # No tearDown to reset user!
```

```python
# CORRECT — ALWAYS reset user in tearDown (v14 pattern)
class TestCleanUser(FrappeTestCase):
    def tearDown(self):
        frappe.set_user("Administrator")

    def test_as_user(self):
        frappe.set_user("test@example.com")
        # ... test logic ...
```

```python
# BEST (v15+) — use context manager, auto-resets
class TestContextUser(IntegrationTestCase):
    def test_as_user(self):
        with self.set_user("test@example.com"):
            # ... test logic ...
        # User automatically restored
```

## Anti-Pattern 5: Using UnitTestCase with Database Calls

```python
# WRONG — UnitTestCase has no database connection
class TestBadUnit(UnitTestCase):
    def test_fetch(self):
        doc = frappe.get_doc("ToDo", "TODO-001")  # WILL fail — no DB
```

```python
# CORRECT — use IntegrationTestCase for database operations
class TestGoodIntegration(IntegrationTestCase):
    def test_fetch(self):
        doc = frappe.get_doc({"doctype": "ToDo", "description": "test"}).insert()
        fetched = frappe.get_doc("ToDo", doc.name)
        self.assertEqual(fetched.description, "test")
```

## Anti-Pattern 6: Hardcoded Test Data Names

```python
# WRONG — may conflict with production data
class TestHardcoded(IntegrationTestCase):
    def test_customer(self):
        doc = frappe.get_doc({"doctype": "Customer", "customer_name": "Acme Corp"})
```

```python
# CORRECT — ALWAYS prefix with _Test
class TestPrefixed(IntegrationTestCase):
    def test_customer(self):
        doc = frappe.get_doc({"doctype": "Customer", "customer_name": "_Test Acme Corp"})
```

## Anti-Pattern 7: Duplicate Fixture Creation

```python
# WRONG — fixtures created multiple times, causing insert errors
def create_fixtures():
    frappe.get_doc({"doctype": "Item", "item_code": "_Test Item"}).insert()

class TestDuplicate(IntegrationTestCase):
    def setUp(self):
        create_fixtures()  # Called before EVERY test — fails on 2nd test
```

```python
# CORRECT — guard with frappe.flags
def create_fixtures():
    if frappe.flags.test_fixtures_created:
        return
    frappe.get_doc({"doctype": "Item", "item_code": "_Test Item"}).insert()
    frappe.flags.test_fixtures_created = True

class TestGuarded(IntegrationTestCase):
    def setUp(self):
        create_fixtures()  # Safe — only runs once
```

## Anti-Pattern 8: Skipping Validation with frappe.flags.in_test

```python
# WRONG — skipping validation defeats the purpose of testing
class MyDoctype(Document):
    def validate(self):
        if frappe.flags.in_test:
            return  # NEVER skip validation logic in tests
        self.validate_amounts()
```

```python
# CORRECT — use frappe.flags.in_test only for external side effects
class MyDoctype(Document):
    def validate(self):
        self.validate_amounts()  # ALWAYS validate

    def after_insert(self):
        if not frappe.flags.in_test:
            send_notification_email()  # OK to skip emails in tests
```

## Anti-Pattern 9: Testing Private Methods Directly

```python
# WRONG — testing implementation details
class TestPrivate(UnitTestCase):
    def test_internal_calculation(self):
        obj = MyClass()
        result = obj._calculate_internal_value()  # Testing private method
```

```python
# CORRECT — test through public interface
class TestPublic(UnitTestCase):
    def test_public_result(self):
        obj = MyClass()
        result = obj.get_total()  # Test the public method that uses _calculate_internal_value
        self.assertEqual(result, expected_value)
```

## Anti-Pattern 10: Not Using assertDocumentEqual

```python
# WRONG — manually checking each field
class TestManual(IntegrationTestCase):
    def test_fields(self):
        doc = frappe.get_doc("ToDo", name)
        self.assertEqual(doc.description, "test")
        self.assertEqual(doc.status, "Open")
        self.assertEqual(doc.priority, "Medium")
        # ... 20 more assertions
```

```python
# CORRECT — use assertDocumentEqual for bulk comparison
class TestBulk(IntegrationTestCase):
    def test_fields(self):
        doc = frappe.get_doc("ToDo", name)
        self.assertDocumentEqual(
            {"description": "test", "status": "Open", "priority": "Medium"},
            doc,
        )
```
