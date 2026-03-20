# Jinja Templates - Implementation Workflows

> Step-by-step implementation patterns for all template types.

---

## Workflow 1: Custom Print Format (Basic)

**Goal**: Create a simple custom invoice format

### Step 1: Create Print Format Record

```
Setup > Printing > Print Format > New

Fill in:
- Name: My Invoice Format
- DocType: Sales Invoice
- Module: Accounts (or your custom module)
- Standard: No (unchecked)
- Print Format Type: Jinja
```

### Step 2: Add Basic Structure

```jinja
<style>
    .print-format { font-family: Arial, sans-serif; font-size: 12px; }
    .header { margin-bottom: 20px; }
    .title { font-size: 24px; font-weight: bold; }
    .meta { color: #666; }
    .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .table th, .table td { border: 1px solid #ccc; padding: 8px; }
    .table th { background: #f0f0f0; }
    .text-right { text-align: right; }
</style>

<div class="header">
    <div class="title">{{ doc.select_print_heading or _("Invoice") }}</div>
    <div class="meta">
        {{ doc.name }} | {{ doc.get_formatted("posting_date") }}
    </div>
</div>

<p><strong>{{ doc.customer_name }}</strong></p>

<table class="table">
    <thead>
        <tr>
            <th>#</th>
            <th>{{ _("Item") }}</th>
            <th class="text-right">{{ _("Qty") }}</th>
            <th class="text-right">{{ _("Rate") }}</th>
            <th class="text-right">{{ _("Amount") }}</th>
        </tr>
    </thead>
    <tbody>
        {% for row in doc.items %}
        <tr>
            <td>{{ row.idx }}</td>
            <td>{{ row.item_name }}</td>
            <td class="text-right">{{ row.qty }}</td>
            <td class="text-right">{{ row.get_formatted("rate", doc) }}</td>
            <td class="text-right">{{ row.get_formatted("amount", doc) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<p class="text-right">
    <strong>{{ _("Total") }}: {{ doc.get_formatted("grand_total") }}</strong>
</p>
```

### Step 3: Test

1. Open any Sales Invoice
2. Menu > Print
3. Select "My Invoice Format"
4. Verify layout
5. Test PDF download

---

## Workflow 2: Print Format with Company Header

**Goal**: Professional format with company logo and address

### Step 1: Create Print Format (as above)

### Step 2: Add Company Header Section

```jinja
<style>
    .company-header { display: table; width: 100%; margin-bottom: 20px; }
    .company-logo { display: table-cell; width: 150px; vertical-align: top; }
    .company-logo img { max-width: 120px; max-height: 80px; }
    .company-info { display: table-cell; vertical-align: top; text-align: right; }
    .doc-header { display: table; width: 100%; margin: 20px 0; }
    .doc-title { display: table-cell; width: 50%; }
    .doc-meta { display: table-cell; width: 50%; text-align: right; }
</style>

{# Get company details #}
{% set company = frappe.get_doc("Company", doc.company) %}
{% set company_address = frappe.db.get_value("Dynamic Link", 
    {"link_doctype": "Company", "link_name": doc.company, "parenttype": "Address"},
    "parent") %}

<div class="company-header">
    <div class="company-logo">
        {% if company.company_logo %}
            <img src="{{ company.company_logo }}" alt="{{ company.company_name }}">
        {% endif %}
    </div>
    <div class="company-info">
        <strong>{{ company.company_name }}</strong><br>
        {% if company_address %}
            {% set addr = frappe.get_doc("Address", company_address) %}
            {{ addr.address_line1 }}<br>
            {% if addr.address_line2 %}{{ addr.address_line2 }}<br>{% endif %}
            {{ addr.city }}{% if addr.pincode %}, {{ addr.pincode }}{% endif %}<br>
        {% endif %}
        {% if company.phone_no %}{{ _("Tel") }}: {{ company.phone_no }}<br>{% endif %}
        {% if company.email %}{{ company.email }}{% endif %}
    </div>
</div>

<div class="doc-header">
    <div class="doc-title">
        <h1>{{ doc.select_print_heading or _("Invoice") }}</h1>
        <p><strong>{{ doc.name }}</strong></p>
    </div>
    <div class="doc-meta">
        <p><strong>{{ _("Date") }}:</strong> {{ doc.get_formatted("posting_date") }}</p>
        <p><strong>{{ _("Due Date") }}:</strong> {{ doc.get_formatted("due_date") }}</p>
    </div>
</div>

{# Rest of invoice content... #}
```

---

## Workflow 3: Multi-Page Print Format

**Goal**: Format with proper page breaks and headers/footers

### Step 1: Add Page Break CSS

```jinja
<style>
    @page {
        margin: 1.5cm;
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
        }
    }
    
    .page-break {
        page-break-before: always;
    }
    
    .avoid-break {
        page-break-inside: avoid;
    }
    
    /* Repeat table header on each page */
    thead { display: table-header-group; }
    tfoot { display: table-footer-group; }
</style>
```

### Step 2: Structure Content for Page Breaks

```jinja
{# Header on first page #}
<div class="first-page-header">
    {# Company info, document info #}
</div>

{# Items table with repeating header #}
<table class="items-table">
    <thead>
        <tr>
            <th>{{ _("Item") }}</th>
            <th>{{ _("Qty") }}</th>
            <th>{{ _("Amount") }}</th>
        </tr>
    </thead>
    <tbody>
        {% for row in doc.items %}
        <tr class="avoid-break">
            <td>{{ row.item_name }}</td>
            <td>{{ row.qty }}</td>
            <td>{{ row.get_formatted("amount", doc) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

{# Force totals to new page if needed #}
<div class="avoid-break">
    <table class="totals-table">
        <tr><td>{{ _("Subtotal") }}</td><td>{{ doc.get_formatted("net_total") }}</td></tr>
        <tr><td>{{ _("Tax") }}</td><td>{{ doc.get_formatted("total_taxes_and_charges") }}</td></tr>
        <tr><td><strong>{{ _("Total") }}</strong></td><td><strong>{{ doc.get_formatted("grand_total") }}</strong></td></tr>
    </table>
</div>

{# Signature section - always on its own space #}
<div class="page-break"></div>
<div class="signature-section">
    <h3>{{ _("Terms and Conditions") }}</h3>
    {{ doc.terms | safe if doc.terms else '' }}
    
    <div style="margin-top: 50px;">
        <div style="width: 200px; border-top: 1px solid #000;">
            {{ _("Authorized Signature") }}
        </div>
    </div>
</div>
```

---

## Workflow 4: Email Template for Notifications

**Goal**: Payment reminder email linked to Sales Invoice

### Step 1: Create Email Template

```
Setup > Email > Email Template > New

Fill in:
- Name: Payment Reminder
- Subject: Invoice {{ doc.name }} - Payment Reminder
- DocType: Sales Invoice
- Module: Accounts
```

### Step 2: Add Email Content

```jinja
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <p>{{ _("Dear") }} {{ doc.customer_name }},</p>
    
    <p>{{ _("This is a friendly reminder that the following invoice is due for payment:") }}</p>
    
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{{ _("Invoice Number") }}</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{ doc.name }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{{ _("Invoice Date") }}</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{ frappe.format_date(doc.posting_date) }}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{{ _("Due Date") }}</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd;">{{ frappe.format_date(doc.due_date) }}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{{ _("Amount Due") }}</strong></td>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #c00;">
                {{ doc.get_formatted("outstanding_amount") }}
            </td>
        </tr>
    </table>
    
    {% if doc.items %}
    <p><strong>{{ _("Invoice Items") }}:</strong></p>
    <ul style="padding-left: 20px;">
        {% for item in doc.items[:5] %}
        <li style="margin-bottom: 5px;">{{ item.item_name }} × {{ item.qty }}</li>
        {% endfor %}
        {% if doc.items | length > 5 %}
        <li style="color: #666;">{{ _("and {0} more items...").format(doc.items | length - 5) }}</li>
        {% endif %}
    </ul>
    {% endif %}
    
    <p>{{ _("Please make payment at your earliest convenience.") }}</p>
    
    <p>{{ _("If you have already made payment, please disregard this reminder.") }}</p>
    
    <p style="margin-top: 30px;">
        {{ _("Best regards") }},<br>
        <strong>{{ frappe.db.get_value("Company", doc.company, "company_name") }}</strong>
    </p>
</div>
```

### Step 3: Use in Notification or Code

**Option A: Notification (Auto-triggered)**

```
Setup > Notification > New

- Name: Payment Reminder
- Channel: Email
- Document Type: Sales Invoice
- Send Alert On: Days After (e.g., 7 days after due_date)
- Condition: doc.outstanding_amount > 0
- Message: Use Email Template > Payment Reminder
```

**Option B: Code (Manual trigger)**

```python
# In Server Script or Controller
def send_payment_reminder(doc):
    template = frappe.db.get_single_value("Email Template", "Payment Reminder")
    
    frappe.sendmail(
        recipients=[doc.contact_email or get_customer_email(doc.customer)],
        subject=frappe.render_template(template.subject, {"doc": doc}),
        message=frappe.render_template(template.response, {"doc": doc}),
        reference_doctype=doc.doctype,
        reference_name=doc.name
    )
```

---

## Workflow 5: Portal Page with User Data

**Goal**: Customer portal showing their orders

### Step 1: Create Directory Structure

```
myapp/
└── www/
    └── my-orders/
        ├── index.html
        └── index.py
```

### Step 2: Create Context (index.py)

```python
# myapp/www/my-orders/index.py
import frappe

def get_context(context):
    # Require login
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
    
    context.title = "My Orders"
    context.no_cache = True  # Always fresh data
    
    # Get customer linked to this user
    customer = get_customer_for_user(frappe.session.user)
    
    if not customer:
        context.orders = []
        context.message = "No customer account found"
        return context
    
    # Get orders
    context.orders = frappe.get_all(
        "Sales Order",
        filters={
            "customer": customer,
            "docstatus": ["!=", 2]  # Not cancelled
        },
        fields=[
            "name", 
            "transaction_date", 
            "grand_total",
            "status",
            "delivery_status"
        ],
        order_by="transaction_date desc",
        limit_page_length=50
    )
    
    return context

def get_customer_for_user(user):
    """Get customer linked to portal user"""
    return frappe.db.get_value(
        "Contact",
        {"user": user},
        "link_name"
    )
```

### Step 3: Create Template (index.html)

```jinja
{% extends "templates/web.html" %}

{% block title %}{{ _("My Orders") }}{% endblock %}

{% block page_content %}
<div class="container my-4">
    <h1>{{ _("My Orders") }}</h1>
    
    <p class="text-muted">
        {{ _("Welcome") }}, {{ frappe.get_fullname() }}
    </p>
    
    {% if message %}
        <div class="alert alert-info">{{ message }}</div>
    {% endif %}
    
    {% if orders %}
    <div class="table-responsive">
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>{{ _("Order") }}</th>
                    <th>{{ _("Date") }}</th>
                    <th>{{ _("Status") }}</th>
                    <th>{{ _("Delivery") }}</th>
                    <th class="text-right">{{ _("Total") }}</th>
                </tr>
            </thead>
            <tbody>
                {% for order in orders %}
                <tr>
                    <td>
                        <a href="/orders/{{ order.name }}">{{ order.name }}</a>
                    </td>
                    <td>{{ frappe.format_date(order.transaction_date) }}</td>
                    <td>
                        <span class="badge badge-{{ 'success' if order.status == 'Completed' else 'primary' if order.status == 'To Deliver and Bill' else 'secondary' }}">
                            {{ order.status }}
                        </span>
                    </td>
                    <td>{{ order.delivery_status or '-' }}</td>
                    <td class="text-right">
                        {{ frappe.format(order.grand_total, {'fieldtype': 'Currency'}) }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
        <div class="alert alert-secondary">
            {{ _("You don't have any orders yet.") }}
        </div>
    {% endif %}
</div>
{% endblock %}
```

### Step 4: Test

```
1. Login as a portal user
2. Navigate to /my-orders
3. Verify orders display correctly
4. Test with user who has no customer link
```

---

## Workflow 6: Custom Jinja Methods

**Goal**: Add reusable functions available in all templates

### Step 1: Register in hooks.py

```python
# myapp/hooks.py
jenv = {
    "methods": [
        "myapp.jinja_utils.methods"
    ],
    "filters": [
        "myapp.jinja_utils.filters"
    ]
}
```

### Step 2: Create Methods

```python
# myapp/jinja_utils/methods.py
import frappe

def get_company_logo(company_name):
    """
    Get company logo URL.
    Usage in template: {{ get_company_logo(doc.company) }}
    """
    logo = frappe.db.get_value("Company", company_name, "company_logo")
    return logo if logo else "/assets/myapp/images/default-logo.png"

def get_customer_balance(customer):
    """
    Get outstanding balance for customer.
    Usage: {{ get_customer_balance(doc.customer) }}
    """
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(debit - credit), 0)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
        AND party = %s
        AND is_cancelled = 0
    """, customer)
    return result[0][0] if result else 0

def get_item_image(item_code):
    """
    Get item image URL.
    Usage: {{ get_item_image(item.item_code) }}
    """
    image = frappe.db.get_value("Item", item_code, "image")
    return image if image else "/assets/myapp/images/no-image.png"

def format_address(address_name, separator="<br>"):
    """
    Format address document to display string.
    Usage: {{ format_address(doc.customer_address) | safe }}
    """
    if not address_name:
        return ""
    
    try:
        address = frappe.get_doc("Address", address_name)
        parts = []
        
        if address.address_line1:
            parts.append(address.address_line1)
        if address.address_line2:
            parts.append(address.address_line2)
        if address.city:
            city_line = address.city
            if address.state:
                city_line += f", {address.state}"
            if address.pincode:
                city_line += f" {address.pincode}"
            parts.append(city_line)
        if address.country:
            parts.append(address.country)
        
        return separator.join(parts)
    except Exception:
        return ""
```

### Step 3: Create Filters

```python
# myapp/jinja_utils/filters.py

def phone_format(value):
    """
    Format phone number.
    Usage: {{ doc.phone | phone_format }}
    """
    if not value:
        return ""
    # Remove non-digits
    digits = ''.join(c for c in str(value) if c.isdigit())
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return value

def initials(value):
    """
    Get initials from name.
    Usage: {{ doc.customer_name | initials }}
    """
    if not value:
        return ""
    words = str(value).split()
    return "".join(w[0].upper() for w in words[:2])

def nl2br(value):
    """
    Convert newlines to <br> tags.
    Usage: {{ doc.description | nl2br | safe }}
    """
    if not value:
        return ""
    return str(value).replace("\n", "<br>")

def money_words(amount, currency="USD"):
    """
    Simple number to words (for display only).
    Usage: {{ doc.grand_total | money_words }}
    """
    # Simplified - for production, use a proper library
    return f"{currency} {amount:,.2f}"
```

### Step 4: Deploy

```bash
bench --site sitename migrate
bench --site sitename clear-cache
```

### Step 5: Use in Templates

```jinja
{# In Print Format or Email Template #}

{# Methods #}
<img src="{{ get_company_logo(doc.company) }}" alt="Logo">
<p>{{ _("Balance") }}: {{ get_customer_balance(doc.customer) }}</p>
<p>{{ format_address(doc.customer_address) | safe }}</p>

{% for item in doc.items %}
    <img src="{{ get_item_image(item.item_code) }}" width="50">
{% endfor %}

{# Filters #}
<p>{{ _("Phone") }}: {{ doc.contact_phone | phone_format }}</p>
<p>{{ doc.customer_name | initials }}</p>
<p>{{ doc.notes | nl2br | safe }}</p>
<p>{{ doc.grand_total | money_words }}</p>
```

---

## Workflow 7: Letter Head Integration

**Goal**: Use Letter Head with Print Format

### Step 1: Create Letter Head

```
Setup > Printing > Letter Head > New

- Name: Company Letter Head
- Is Default: Yes
- Source: HTML
```

### Step 2: Letter Head HTML

```html
<div style="padding: 20px 0; border-bottom: 2px solid #333;">
    <table style="width: 100%;">
        <tr>
            <td style="width: 150px; vertical-align: top;">
                <img src="/files/company-logo.png" style="max-width: 120px;">
            </td>
            <td style="text-align: right; vertical-align: top;">
                <strong style="font-size: 18px;">My Company Name</strong><br>
                123 Business Street<br>
                City, State 12345<br>
                Tel: (123) 456-7890<br>
                www.mycompany.com
            </td>
        </tr>
    </table>
</div>
```

### Step 3: Use in Print Format

```jinja
{# Letter Head is automatically included if set as default #}
{# Your Print Format content starts below the letter head #}

<h1 style="margin-top: 20px;">{{ doc.select_print_heading or _("Invoice") }}</h1>

{# ... rest of document ... #}
```

### Step 4: Override Letter Head per Document

```jinja
{# Access letter head in template if needed #}
{% set letter_head = frappe.db.get_value("Letter Head", doc.letter_head, "content") %}

{# Or dynamically select based on condition #}
{% if doc.company == "Subsidiary Co" %}
    {% set letter_head_name = "Subsidiary Letter Head" %}
{% else %}
    {% set letter_head_name = "Main Letter Head" %}
{% endif %}
```

---

## Workflow 8: Report Print Format (JavaScript)

**Goal**: Print format for Query/Script Report (NOT Jinja!)

### Step 1: Create/Edit Report

```
Customize > Report > [Your Report] > Edit

Add to "Print Format" field or create separate Print Format linked to report
```

### Step 2: JavaScript Template

```html
<!-- ⚠️ THIS IS JAVASCRIPT TEMPLATING, NOT JINJA! -->
<style>
    .report-print { font-family: Arial, sans-serif; }
    .report-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .report-table { width: 100%; border-collapse: collapse; }
    .report-table th, .report-table td { border: 1px solid #ddd; padding: 6px; }
    .report-table th { background: #f0f0f0; }
</style>

<div class="report-print">
    <div class="report-title">{%= __("Sales Report") %}</div>
    
    <!-- Filters used -->
    {% if (filters.from_date) { %}
    <p>From: {%= frappe.datetime.str_to_user(filters.from_date) %}</p>
    {% } %}
    {% if (filters.to_date) { %}
    <p>To: {%= frappe.datetime.str_to_user(filters.to_date) %}</p>
    {% } %}
    
    <table class="report-table">
        <thead>
            <tr>
                {% for (var i=0; i<report_columns.length; i++) { %}
                    {% if (!report_columns[i].hidden) { %}
                    <th>{%= report_columns[i].label %}</th>
                    {% } %}
                {% } %}
            </tr>
        </thead>
        <tbody>
            {% for (var j=0; j<data.length; j++) { %}
            <tr>
                {% for (var i=0; i<report_columns.length; i++) { %}
                    {% if (!report_columns[i].hidden) { %}
                    <td>
                        {% var value = data[j][report_columns[i].fieldname]; %}
                        {% if (report_columns[i].fieldtype === "Currency") { %}
                            {%= format_currency(value) %}
                        {% } else if (report_columns[i].fieldtype === "Date") { %}
                            {%= frappe.datetime.str_to_user(value) %}
                        {% } else { %}
                            {%= value %}
                        {% } %}
                    </td>
                    {% } %}
                {% } %}
            </tr>
            {% } %}
        </tbody>
    </table>
    
    <!-- Summary if available -->
    {% if (report_summary && report_summary.length) { %}
    <div style="margin-top: 20px;">
        <strong>{%= __("Summary") %}:</strong>
        {% for (var k=0; k<report_summary.length; k++) { %}
        <p>{%= report_summary[k].label %}: {%= report_summary[k].value %}</p>
        {% } %}
    </div>
    {% } %}
</div>
```

### Key Differences from Jinja

| Aspect | Jinja (Print Format) | JS (Report Print) |
|--------|---------------------|-------------------|
| Output | `{{ variable }}` | `{%= variable %}` |
| Logic | `{% if %}` | `{% if () { %}` |
| Loop | `{% for x in y %}` | `{% for (var i=0; i<y.length; i++) { %}` |
| End | `{% endif %}` | `{% } %}` |
| Translation | `_("text")` | `__("text")` |
| Data source | `doc` object | `data[]` array |

---

## Workflow 9: Notification Template

**Goal**: Create system notifications with dynamic Jinja content

### Step 1: Create Notification

```
Setup > Notification > New

- Name: Low Stock Alert
- Channel: Email (or System Notification, Slack)
- Document Type: Stock Ledger Entry
- Send Alert On: Value Change
- Condition: doc.actual_qty < doc.reorder_level and doc.reorder_level > 0
```

### Step 2: Write Message (Jinja)

```jinja
<h3>{{ _("Low Stock Alert") }}</h3>

<table style="width: 100%; border-collapse: collapse;">
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{{ _("Item") }}</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.item_code }}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{{ _("Warehouse") }}</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.warehouse }}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{{ _("Current Qty") }}</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; color: red;">{{ doc.actual_qty }}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{{ _("Reorder Level") }}</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.reorder_level }}</td>
    </tr>
</table>

<p>{{ _("Please create a purchase order to replenish stock.") }}</p>
```

### Step 3: Configure Recipients

- Set recipients to specific roles, users, or use dynamic owner field

---

## Workflow 10: Debugging Templates

**Goal**: Diagnose and fix template rendering issues

### Step 1: Add debug output

```jinja
<!-- DEBUG START -->
<!-- doc exists: {{ 'YES' if doc else 'NO' }} -->
<!-- doc.name: {{ doc.name if doc else 'N/A' }} -->
<!-- items count: {{ doc.items | length if doc.items else 0 }} -->
<!-- DEBUG END -->
```

### Step 2: Check Error Log

```
Setup > Error Log
Search for "Jinja" or "template" errors
```

### Step 3: Test in bench console

```python
# Test a print format template
doc = frappe.get_doc("Sales Invoice", "INV-001")
template = """{{ doc.name }} - {{ doc.get_formatted("grand_total") }}"""
print(frappe.render_template(template, {"doc": doc}))

# Test an email template
template = frappe.get_doc("Email Template", "Payment Reminder")
rendered = frappe.render_template(template.response, {"doc": doc})
print(rendered)
```

### Step 4: Common fixes

| Problem | Diagnostic | Fix |
|---------|-----------|-----|
| Blank output | Check Error Log | Fix syntax error or missing variable |
| "None" in output | Field is empty | Use `\| default('')` filter |
| Wrong currency | Missing parent doc | Pass `doc` to `get_formatted()` |
| Slow rendering | N+1 queries in loop | Prefetch data in controller/context |
| PDF different from screen | wkhtmltopdf CSS limits | Avoid flexbox, test PDF after changes |

---

## Anti-Patterns Quick Reference

| Anti-Pattern | Risk | Correct Approach |
|--------------|------|-----------------|
| Jinja syntax in Report Print | Blank output | Use JS templating `{%= %}` |
| Raw values `{{ doc.amount }}` | Wrong format | Use `get_formatted()` |
| Missing parent in child formatting | Wrong currency | `row.get_formatted("rate", doc)` |
| DB queries in template loops | N+1 performance | Prefetch in controller |
| `\| safe` on user input | XSS vulnerability | Only for trusted system HTML |
| Hardcoded strings | Not translatable | Use `_("text")` |
| `<style>` in email | Stripped by clients | Inline styles only |
| Heavy computation in templates | Slow render | Move logic to Python |
| Writing to DB in jenv methods | Transaction corruption | Methods must be read-only |
| No PDF testing | Layout breaks in PDF | ALWAYS test PDF output |

---

## Quick Reference: Workflow Checklist

| Template Type | Location | Context | Key Steps |
|---------------|----------|---------|-----------|
| Print Format | Setup > Print | `doc`, `frappe` | Create record, Add HTML, Test print + PDF |
| Email Template | Setup > Email | `doc`, `frappe` | Create record, Add HTML, Link to Notification |
| Notification | Setup > Notification | `doc`, event data | Create rule, Write message, Set recipients |
| Portal Page | myapp/www/ | Custom | Create .py, Create .html, Test URL |
| Custom Methods | myapp/jinja_utils/ | N/A | Add to hooks.py, Create module, Migrate |
| Report Print | Report record | `data[]`, `filters` | Edit report, Add JS template |
