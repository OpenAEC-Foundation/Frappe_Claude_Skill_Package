# Unit & Integration Test Examples

## Complete DocType Test (v15+ IntegrationTestCase)

```python
import frappe
from frappe.tests.classes import IntegrationTestCase


class TestTodoItem(IntegrationTestCase):
    """Tests for the Todo Item DocType."""

    @classmethod
    def setUpClass(cls):
        # ALWAYS call super() first
        super().setUpClass()
        cls.test_user = "test_todo@example.com"

    def test_create_todo(self):
        """Test basic document creation."""
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Todo Description",
            "status": "Open",
        }).insert()

        self.assertEqual(doc.status, "Open")
        self.assertTrue(doc.name)

    def test_update_status(self):
        """Test status transition."""
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Todo Update",
        }).insert()

        doc.status = "Closed"
        doc.save()
        doc.reload()

        self.assertEqual(doc.status, "Closed")

    def test_permission_restricted_user(self):
        """Test that restricted user cannot access other users' todos."""
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Private Todo",
            "allocated_to": "Administrator",
        }).insert()

        with self.set_user(self.test_user):
            self.assertFalse(
                frappe.has_permission("ToDo", doc=doc.name, ptype="read")
            )

    def test_validation_error_on_empty_description(self):
        """Test that validation prevents empty description."""
        self.assertRaises(
            frappe.ValidationError,
            frappe.get_doc,
            {"doctype": "ToDo", "description": ""},
        )

    def test_query_count_on_list(self):
        """Test that listing todos uses reasonable query count."""
        # Create test data
        for i in range(5):
            frappe.get_doc({
                "doctype": "ToDo",
                "description": f"_Test Query Count {i}",
            }).insert()

        with self.assertQueryCount(5):
            frappe.get_list("ToDo", filters={"description": ["like", "_Test Query%"]})


class TestTodoWorkflow(IntegrationTestCase):
    """Tests for Todo workflow transitions."""

    def test_complete_lifecycle(self):
        """Test Open → Closed lifecycle."""
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Lifecycle",
            "status": "Open",
        }).insert()

        self.assertEqual(doc.docstatus, 0)

        doc.status = "Closed"
        doc.save()

        self.assertEqual(doc.status, "Closed")
```

## Complete DocType Test (v14 FrappeTestCase)

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestEvent(FrappeTestCase):
    def setUp(self):
        create_events()

    def tearDown(self):
        # ALWAYS reset user in v14 pattern
        frappe.set_user("Administrator")

    def test_allowed_public(self):
        frappe.set_user("test1@example.com")
        doc = frappe.get_doc("Event", frappe.db.get_value(
            "Event", {"subject": "_Test Event 1"}
        ))
        self.assertTrue(frappe.has_permission("Event", doc=doc))

    def test_not_allowed_private(self):
        frappe.set_user("test1@example.com")
        doc = frappe.get_doc("Event", frappe.db.get_value(
            "Event", {"subject": "_Test Event 2"}
        ))
        self.assertFalse(frappe.has_permission("Event", doc=doc))


def create_events():
    if frappe.flags.test_events_created:
        return

    frappe.set_user("Administrator")

    frappe.get_doc({
        "doctype": "Event",
        "subject": "_Test Event 1",
        "starts_on": "2024-01-01",
        "event_type": "Public",
    }).insert()

    frappe.get_doc({
        "doctype": "Event",
        "subject": "_Test Event 2",
        "starts_on": "2024-01-02",
        "event_type": "Private",
    }).insert()

    frappe.flags.test_events_created = True
```

## Pure Unit Test (v15+ UnitTestCase)

```python
from frappe.tests.classes import UnitTestCase
from myapp.utils.calculations import calculate_discount, format_currency


class TestCalculations(UnitTestCase):
    """Pure unit tests — no database access."""

    def test_discount_percentage(self):
        result = calculate_discount(1000, 10)
        self.assertEqual(result, 900)

    def test_discount_zero(self):
        result = calculate_discount(1000, 0)
        self.assertEqual(result, 1000)

    def test_discount_exceeds_total(self):
        self.assertRaises(ValueError, calculate_discount, 1000, 150)

    def test_format_currency(self):
        self.assertEqual(format_currency(1234.56, "USD"), "$1,234.56")
```

## Testing with Mocked External Services

```python
from unittest.mock import patch, MagicMock
from frappe.tests.classes import IntegrationTestCase


class TestPaymentIntegration(IntegrationTestCase):

    @patch("myapp.integrations.stripe_client.requests.post")
    def test_successful_payment(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "succeeded", "id": "pi_123"},
        )

        result = process_stripe_payment(amount=5000, currency="eur")

        self.assertEqual(result["status"], "succeeded")
        mock_post.assert_called_once()

    @patch("myapp.integrations.stripe_client.requests.post")
    def test_failed_payment(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=402,
            json=lambda: {"error": {"message": "Card declined"}},
        )

        self.assertRaises(
            PaymentError,
            process_stripe_payment, amount=5000, currency="eur",
        )
```

## Testing with Time Freeze

```python
from frappe.tests.classes import IntegrationTestCase


class TestScheduledTask(IntegrationTestCase):

    def test_overdue_detection(self):
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Overdue",
            "date": "2024-01-15",
        }).insert()

        with self.freeze_time("2024-01-20"):
            overdue = get_overdue_todos()
            self.assertIn(doc.name, [t.name for t in overdue])

    def test_not_overdue_before_deadline(self):
        doc = frappe.get_doc({
            "doctype": "ToDo",
            "description": "_Test Not Overdue",
            "date": "2024-01-15",
        }).insert()

        with self.freeze_time("2024-01-10"):
            overdue = get_overdue_todos()
            self.assertNotIn(doc.name, [t.name for t in overdue])
```

## Testing Submittable Documents

```python
import frappe
from frappe.tests.classes import IntegrationTestCase


class TestSalesInvoice(IntegrationTestCase):

    def test_submit_creates_gl_entries(self):
        si = create_test_sales_invoice()
        si.submit()

        gl_entries = frappe.get_all(
            "GL Entry",
            filters={"voucher_no": si.name},
            fields=["account", "debit", "credit"],
        )

        self.assertTrue(len(gl_entries) > 0)
        total_debit = sum(e.debit for e in gl_entries)
        total_credit = sum(e.credit for e in gl_entries)
        self.assertEqual(total_debit, total_credit)

    def test_cancel_reverses_gl_entries(self):
        si = create_test_sales_invoice()
        si.submit()
        si.cancel()

        gl_entries = frappe.get_all(
            "GL Entry",
            filters={"voucher_no": si.name, "is_cancelled": 0},
        )
        self.assertEqual(len(gl_entries), 0)


def create_test_sales_invoice():
    return frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": "_Test Customer",
        "items": [{
            "item_code": "_Test Item",
            "qty": 1,
            "rate": 100,
        }],
    }).insert()
```
