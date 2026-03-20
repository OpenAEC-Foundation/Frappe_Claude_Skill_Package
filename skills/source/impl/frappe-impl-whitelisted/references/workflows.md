# Implementation Workflows

Step-by-step workflows for implementing Whitelisted Methods (APIs).

---

## Workflow 1: Basic CRUD API

**Goal**: Create API endpoints for reading and updating a custom DocType.

### Step 1: Create API file

```python
# myapp/api/inventory.py
import frappe
from frappe import _

@frappe.whitelist()
def get_item(item_code):
    """Get item details."""
    # Permission check
    if not frappe.has_permission("Item", "read", item_code):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Validate input
    if not item_code:
        frappe.throw(_("Item code required"), frappe.ValidationError)
    
    # Fetch and return
    item = frappe.get_doc("Item", item_code)
    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "stock_uom": item.stock_uom,
        "is_stock_item": item.is_stock_item
    }

@frappe.whitelist()
def update_item_price(item_code, price):
    """Update item's standard rate."""
    # Permission check
    if not frappe.has_permission("Item", "write", item_code):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Validate
    try:
        price = float(price)
    except (ValueError, TypeError):
        frappe.throw(_("Invalid price"), frappe.ValidationError)
    
    if price < 0:
        frappe.throw(_("Price cannot be negative"), frappe.ValidationError)
    
    # Update
    frappe.db.set_value("Item", item_code, "standard_rate", price)
    
    return {"success": True, "item_code": item_code, "new_price": price}
```

### Step 2: Client integration

```javascript
// Get item
frappe.call({
    method: 'myapp.api.inventory.get_item',
    args: { item_code: 'ITEM-001' }
}).then(r => {
    console.log(r.message);
});

// Update price
frappe.call({
    method: 'myapp.api.inventory.update_item_price',
    args: { item_code: 'ITEM-001', price: 99.99 }
}).then(r => {
    if (r.message.success) {
        frappe.msgprint(__('Price updated'));
    }
});
```

---

## Workflow 2: Public Contact Form API

**Goal**: Create a public API for website contact form submissions.

### Step 1: Create public API

```python
# myapp/api/public.py
import frappe
from frappe import _
from frappe.utils import validate_email_address, strip_html

@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_contact(name, email, phone=None, message=None, subject=None):
    """
    Public contact form submission.
    Accessible without login - requires strict validation.
    """
    # Required field validation
    if not name or not email:
        frappe.throw(_("Name and email are required"))
    
    # Email validation
    if not validate_email_address(email):
        frappe.throw(_("Please enter a valid email address"))
    
    # Sanitize inputs (prevent XSS)
    name = strip_html(name)[:100]
    email = email.strip().lower()[:200]
    phone = strip_html(phone)[:20] if phone else None
    message = strip_html(message)[:5000] if message else None
    subject = strip_html(subject)[:200] if subject else "Website Contact"
    
    # Check for spam (simple duplicate check)
    recent = frappe.db.exists("Lead", {
        "email_id": email,
        "creation": [">", frappe.utils.add_days(frappe.utils.nowdate(), -1)]
    })
    if recent:
        # Don't reveal this to potential spammers
        return {"success": True, "message": _("Thank you for your message")}
    
    # Create Lead
    try:
        lead = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": name,
            "email_id": email,
            "phone": phone,
            "notes": message,
            "source": "Website",
            "custom_subject": subject
        })
        lead.insert(ignore_permissions=True)
        
        # Send notification
        frappe.sendmail(
            recipients=["sales@company.com"],
            subject=f"New Contact: {subject}",
            message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n{message}"
        )
        
        return {"success": True, "message": _("Thank you for your message")}
        
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Contact Form Error")
        frappe.throw(_("Unable to submit. Please try again later."))
```

### Step 2: Client integration (website)

```javascript
// public/js/contact.js
document.getElementById('contact-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/api/method/myapp.api.public.submit_contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            body: JSON.stringify({
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                message: formData.get('message')
            })
        });
        
        const result = await response.json();
        if (result.message?.success) {
            alert('Thank you! We will contact you soon.');
            e.target.reset();
        }
    } catch (error) {
        alert('Error submitting form. Please try again.');
    }
});
```

---

## Workflow 3: Document Controller Method

**Goal**: Add a custom action button to a DocType form.

### Step 1: Add method to controller

```python
# myapp/doctype/sales_order/sales_order.py
import frappe
from frappe import _
from frappe.model.document import Document

class SalesOrder(Document):
    @frappe.whitelist()
    def send_to_customer(self):
        """Send order confirmation to customer."""
        # Validate state
        if self.docstatus != 1:
            frappe.throw(_("Order must be submitted first"))
        
        if not self.customer_email:
            frappe.throw(_("Customer email not set"))
        
        # Send email
        frappe.sendmail(
            recipients=[self.customer_email],
            subject=f"Order Confirmation: {self.name}",
            template="order_confirmation",
            args={"doc": self}
        )
        
        # Update status
        self.db_set("email_sent", 1)
        self.db_set("email_sent_on", frappe.utils.now())
        
        return {"success": True, "message": _("Email sent to {0}").format(self.customer_email)}
    
    @frappe.whitelist()
    def calculate_shipping(self, carrier, service_type="standard"):
        """Calculate shipping cost for given carrier."""
        if not self.shipping_address:
            frappe.throw(_("Shipping address required"))
        
        # Calculate based on carrier
        rates = get_shipping_rates(self.shipping_address, carrier, service_type)
        
        return {
            "carrier": carrier,
            "service": service_type,
            "cost": rates.get("cost", 0),
            "estimated_days": rates.get("days", 5)
        }
```

### Step 2: Add button to form

```javascript
// myapp/doctype/sales_order/sales_order.js
frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            // Add custom button
            frm.add_custom_button(__('Send to Customer'), function() {
                frm.call('send_to_customer').then(r => {
                    if (r.message?.success) {
                        frappe.msgprint(r.message.message);
                        frm.reload_doc();
                    }
                });
            }, __('Actions'));
            
            // Add shipping calculator
            frm.add_custom_button(__('Calculate Shipping'), function() {
                frappe.prompt([
                    {
                        fieldname: 'carrier',
                        label: __('Carrier'),
                        fieldtype: 'Select',
                        options: 'FedEx\nUPS\nDHL',
                        reqd: 1
                    },
                    {
                        fieldname: 'service',
                        label: __('Service Type'),
                        fieldtype: 'Select',
                        options: 'standard\nexpress\novernight',
                        default: 'standard'
                    }
                ],
                function(values) {
                    frm.call('calculate_shipping', {
                        carrier: values.carrier,
                        service_type: values.service
                    }).then(r => {
                        frappe.msgprint(
                            __('Shipping: {0} ({1}) - ${2}, {3} days', [
                                r.message.carrier,
                                r.message.service,
                                r.message.cost,
                                r.message.estimated_days
                            ])
                        );
                    });
                },
                __('Calculate Shipping'),
                __('Calculate')
                );
            }, __('Actions'));
        }
    }
});
```

---

## Workflow 4: Role-Restricted Admin API

**Goal**: Create admin-only APIs for system management.

### Step 1: Create admin API

```python
# myapp/api/admin.py
import frappe
from frappe import _

@frappe.whitelist()
def get_system_stats():
    """Get system statistics - System Manager only."""
    frappe.only_for("System Manager")
    
    return {
        "total_users": frappe.db.count("User", {"enabled": 1}),
        "total_documents": get_total_documents(),
        "database_size": get_database_size(),
        "error_count_today": frappe.db.count("Error Log", {
            "creation": [">=", frappe.utils.nowdate()]
        })
    }

@frappe.whitelist()
def clear_old_logs(days=30):
    """Clear old error logs - System Manager only."""
    frappe.only_for("System Manager")
    
    # Validate input
    days = int(days)
    if days < 7:
        frappe.throw(_("Cannot delete logs less than 7 days old"))
    
    cutoff = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    
    # Delete logs
    deleted = frappe.db.delete("Error Log", {"creation": ["<", cutoff]})
    frappe.db.commit()
    
    # Audit log
    frappe.log_error(
        f"Admin {frappe.session.user} deleted {deleted} error logs older than {days} days",
        "Admin Action"
    )
    
    return {"success": True, "deleted": deleted}

@frappe.whitelist()
def impersonate_user(user_email):
    """Login as another user - System Manager only."""
    frappe.only_for("System Manager")
    
    # Validate user exists
    if not frappe.db.exists("User", user_email):
        frappe.throw(_("User not found"), frappe.DoesNotExistError)
    
    # Cannot impersonate Administrator
    if user_email == "Administrator":
        frappe.throw(_("Cannot impersonate Administrator"))
    
    # Log this action
    frappe.log_error(
        f"System Manager {frappe.session.user} impersonated {user_email}",
        "Security Audit"
    )
    
    # Set session
    frappe.local.login_manager.login_as(user_email)
    
    return {"success": True, "message": _("Logged in as {0}").format(user_email)}

def get_total_documents():
    """Count documents across main DocTypes."""
    doctypes = ["Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice"]
    return sum(frappe.db.count(dt) for dt in doctypes)

def get_database_size():
    """Get database size in MB."""
    result = frappe.db.sql("""
        SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
        FROM information_schema.TABLES
        WHERE table_schema = DATABASE()
    """, as_dict=True)
    return result[0].size_mb if result else 0
```

### Step 2: Admin page integration

```javascript
// Admin dashboard page
frappe.pages['admin-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Admin Dashboard',
        single_column: true
    });
    
    // Load stats
    frappe.call({
        method: 'myapp.api.admin.get_system_stats'
    }).then(r => {
        const stats = r.message;
        $(page.body).html(`
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>${stats.total_users}</h3>
                    <p>Active Users</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.total_documents}</h3>
                    <p>Total Documents</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.database_size} MB</h3>
                    <p>Database Size</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.error_count_today}</h3>
                    <p>Errors Today</p>
                </div>
            </div>
        `);
    });
};
```

---

## Workflow 5: Paginated List API

**Goal**: Create an API that returns paginated results.

### Step 1: Create paginated API

```python
# myapp/api/reports.py
import frappe
from frappe import _

@frappe.whitelist()
def get_sales_data(
    page=1,
    page_size=20,
    from_date=None,
    to_date=None,
    customer=None,
    status=None
):
    """Get paginated sales invoice data with filters."""
    # Convert and validate pagination
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))  # Max 100 per page
    offset = (page - 1) * page_size
    
    # Build filters
    filters = {"docstatus": 1}
    
    if from_date:
        filters["posting_date"] = [">=", from_date]
    if to_date:
        filters.setdefault("posting_date", [])
        if isinstance(filters["posting_date"], list):
            filters["posting_date"] = ["between", [from_date, to_date]]
        else:
            filters["posting_date"] = ["<=", to_date]
    if customer:
        filters["customer"] = customer
    if status:
        filters["status"] = status
    
    # Get total count
    total = frappe.db.count("Sales Invoice", filters)
    
    # Get data
    data = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["name", "customer", "posting_date", "grand_total", "status"],
        order_by="posting_date desc",
        start=offset,
        limit=page_size
    )
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
```

### Step 2: Client with pagination

```javascript
class SalesDataTable {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = 1;
        this.page_size = 20;
        this.filters = {};
        this.render();
    }
    
    async loadData() {
        const r = await frappe.call({
            method: 'myapp.api.reports.get_sales_data',
            args: {
                page: this.page,
                page_size: this.page_size,
                ...this.filters
            }
        });
        
        this.data = r.message.data;
        this.pagination = r.message.pagination;
        this.renderTable();
        this.renderPagination();
    }
    
    renderPagination() {
        const { page, total_pages, has_prev, has_next } = this.pagination;
        
        $(this.wrapper).find('.pagination').html(`
            <button ${!has_prev ? 'disabled' : ''} data-action="prev">Previous</button>
            <span>Page ${page} of ${total_pages}</span>
            <button ${!has_next ? 'disabled' : ''} data-action="next">Next</button>
        `);
    }
    
    goToPage(newPage) {
        this.page = newPage;
        this.loadData();
    }
}
```

---

## Workflow 6: File Upload API

**Goal**: Create an API to handle file uploads.

### Step 1: Create upload API

```python
# myapp/api/files.py
import frappe
from frappe import _

@frappe.whitelist()
def upload_attachment(doctype, docname, file_url=None):
    """
    Attach uploaded file to a document.
    File is uploaded via standard Frappe file upload first.
    """
    # Permission check
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Get the uploaded file from request
    if not file_url and frappe.request.files:
        file = frappe.request.files.get('file')
        if file:
            # Save file
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file.filename,
                "attached_to_doctype": doctype,
                "attached_to_name": docname,
                "content": file.read(),
                "is_private": 1
            })
            file_doc.insert(ignore_permissions=True)
            file_url = file_doc.file_url
    
    if not file_url:
        frappe.throw(_("No file provided"))
    
    return {
        "success": True,
        "file_url": file_url,
        "message": _("File attached successfully")
    }

@frappe.whitelist()
def get_attachments(doctype, docname):
    """Get all attachments for a document."""
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": doctype,
            "attached_to_name": docname
        },
        fields=["name", "file_name", "file_url", "file_size", "creation"]
    )
    
    return files
```

### Step 2: Client file upload

```javascript
// File upload with progress
async function uploadFile(file, doctype, docname) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doctype', doctype);
    formData.append('docname', docname);
    
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                console.log(`Upload progress: ${percent.toFixed(1)}%`);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error('Upload failed'));
            }
        });
        
        xhr.addEventListener('error', () => reject(new Error('Upload error')));
        
        xhr.open('POST', '/api/method/myapp.api.files.upload_attachment');
        xhr.setRequestHeader('X-Frappe-CSRF-Token', frappe.csrf_token);
        xhr.send(formData);
    });
}
```

---

## Workflow 7: Webhook Receiver API

**Goal**: Create an API to receive webhooks from external services.

### Step 1: Create webhook receiver

```python
# myapp/api/webhooks.py
import frappe
import hmac
import hashlib
from frappe import _

@frappe.whitelist(allow_guest=True, methods=["POST"])
def stripe_webhook():
    """
    Receive Stripe webhooks.
    Must verify signature before processing.
    """
    # Get raw payload and signature
    payload = frappe.request.get_data(as_text=True)
    signature = frappe.request.headers.get("Stripe-Signature")
    
    if not signature:
        frappe.local.response["http_status_code"] = 400
        return {"error": "Missing signature"}
    
    # Get webhook secret from settings
    settings = frappe.get_single("Stripe Settings")
    webhook_secret = settings.webhook_secret
    
    # Verify signature
    if not verify_stripe_signature(payload, signature, webhook_secret):
        frappe.log_error("Invalid Stripe webhook signature", "Webhook Security")
        frappe.local.response["http_status_code"] = 401
        return {"error": "Invalid signature"}
    
    # Parse event
    try:
        event = frappe.parse_json(payload)
    except Exception:
        frappe.local.response["http_status_code"] = 400
        return {"error": "Invalid JSON"}
    
    # Process event
    try:
        process_stripe_event(event)
        return {"received": True}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Stripe Webhook Error")
        frappe.local.response["http_status_code"] = 500
        return {"error": "Processing failed"}

def verify_stripe_signature(payload, signature, secret):
    """Verify Stripe webhook signature."""
    try:
        # Parse signature header
        elements = dict(item.split("=") for item in signature.split(","))
        timestamp = elements.get("t")
        sig = elements.get("v1")
        
        if not timestamp or not sig:
            return False
        
        # Compute expected signature
        signed_payload = f"{timestamp}.{payload}"
        expected = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False

def process_stripe_event(event):
    """Process different Stripe event types."""
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    
    handlers = {
        "payment_intent.succeeded": handle_payment_success,
        "payment_intent.failed": handle_payment_failure,
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.deleted": handle_subscription_cancelled,
    }
    
    handler = handlers.get(event_type)
    if handler:
        handler(data)
    else:
        frappe.log_error(f"Unhandled Stripe event: {event_type}", "Stripe Webhook")
```

---

## Workflow 8: Background Job API

**Goal**: Trigger a long-running task from the UI that runs asynchronously.

### Step 1: Create the API trigger

```python
# myapp/api/export.py
import frappe
from frappe import _

@frappe.whitelist()
def start_export(doctype, filters=None):
    """Trigger background export — returns immediately."""
    frappe.only_for("System Manager")

    if isinstance(filters, str):
        filters = frappe.parse_json(filters)

    # Enqueue the heavy work
    frappe.enqueue(
        "myapp.tasks.run_export",
        queue="long",
        timeout=1500,  # 25 minutes
        doctype=doctype,
        filters=filters,
        user=frappe.session.user
    )

    return {"status": "queued", "message": _("Export started in background")}
```

### Step 2: Implement the background task

```python
# myapp/tasks.py
import frappe

def run_export(doctype, filters, user):
    """Background task — runs in worker process."""
    frappe.set_user(user)  # Set context for permissions

    data = frappe.get_all(doctype, filters=filters, fields=["*"])

    # Create CSV or file
    csv_content = generate_csv(data)

    # Save as file
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{doctype}_export.csv",
        "content": csv_content,
        "is_private": 1
    })
    file_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    # Notify user
    frappe.publish_realtime(
        "export_complete",
        {"file_url": file_doc.file_url},
        user=user
    )
```

### Step 3: Client integration

```javascript
frappe.call({
    method: 'myapp.api.export.start_export',
    args: { doctype: 'Sales Invoice', filters: {docstatus: 1} },
    callback(r) {
        frappe.show_alert(__('Export started. You will be notified when complete.'));
    }
});

// Listen for completion
frappe.realtime.on('export_complete', (data) => {
    frappe.show_alert({
        message: __('Export complete! <a href="{0}">Download</a>', [data.file_url]),
        indicator: 'green'
    });
});
```

---

## Workflow 9: Testing APIs with curl/Postman

### Token Authentication (Recommended)

```bash
# Generate API key in User > API Access > Generate Keys
# Use token format: api_key:api_secret

# GET request
curl -H "Authorization: token abc123:xyz789" \
  "https://site.com/api/method/myapp.api.get_data?param=value"

# POST request
curl -X POST \
  -H "Authorization: token abc123:api_secret" \
  -H "Content-Type: application/json" \
  -d '{"customer": "CUST-001", "limit": 10}' \
  "https://site.com/api/method/myapp.api.get_customer_data"
```

### Session Authentication

```bash
# Step 1: Login to get session cookie
curl -c cookies.txt -X POST \
  "https://site.com/api/method/login" \
  -d "usr=admin@example.com&pwd=password"

# Step 2: Use cookie for subsequent requests
curl -b cookies.txt \
  "https://site.com/api/method/myapp.api.get_data"
```

### Bearer Token (OAuth)

```bash
curl -H "Authorization: Bearer your_access_token" \
  "https://site.com/api/method/myapp.api.get_data"
```

### Postman Setup

1. Set Authorization: API Key or Bearer Token
2. Set Content-Type: application/json
3. For POST: put args in Body as raw JSON
4. Response is always `{"message": <your_return_value>}`

---

## Workflow 10: Migrating Server Script API to Whitelisted Method

### Step-by-Step

**Step 1: Identify the Server Script**
```
Setup > Server Script > [Your Script]
Note: Script Type, DocType Event or API method name, and the code
```

**Step 2: Create equivalent Python function**
```python
# myapp/api/migrated.py
import frappe
from frappe import _

# Was: Server Script "Get Customer Stats" (API type)
@frappe.whitelist()
def get_customer_stats(customer):
    """Migrated from Server Script."""
    if not frappe.has_permission("Customer", "read", customer):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    # Copy logic from Server Script, adapting as needed
    stats = frappe.db.sql("""...""", customer, as_dict=True)
    return stats
```

**Step 3: Update all client calls**
```javascript
// Before (Server Script):
frappe.call({method: 'get_customer_stats', args: {customer: name}});

// After (Whitelisted Method):
frappe.call({method: 'myapp.api.migrated.get_customer_stats', args: {customer: name}});
```

**Step 4: Disable the Server Script**

**Step 5: Deploy**
```bash
bench --site sitename migrate
```

---

## Anti-Patterns Quick Reference

| Anti-Pattern | Risk | Correct Approach |
|--------------|------|-----------------|
| No permission check | Data exposure | ALWAYS check permissions |
| SQL string interpolation | SQL injection | Use parameterized queries |
| `allow_guest` without validation | Arbitrary data creation | Validate ALL input, sanitize |
| Expose internal errors | Information leak | Log details, generic message |
| `ignore_permissions` without role check | Permission bypass | `frappe.only_for()` first |
| `methods=["GET"]` for writes | CSRF/caching issues | Use `methods=["POST"]` |
| Return all fields | Slow, data leak | Specify fields, paginate |
| No rate limit on guest API | Abuse, spam | `@rate_limit` (v15+) or cache throttle |
| Inconsistent error handling | Confusing API | Use frappe exceptions consistently |
