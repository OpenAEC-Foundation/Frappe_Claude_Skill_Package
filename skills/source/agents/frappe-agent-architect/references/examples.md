# Architecture Design Examples

## Example 1: E-Commerce Extension for ERPNext

### Input
"We have ERPNext running for accounting and inventory. We want to add a Shopify integration, custom product catalog with extra fields, and a customer portal for order tracking."

### Architecture Design

**Step 1 — Requirement Analysis**:

| # | Requirement | DocTypes | Mechanism |
|---|------------|----------|-----------|
| 1 | Shopify product sync | Item (extend) | Scheduled job + API |
| 2 | Shopify order sync | Sales Order (extend) | Webhook + API |
| 3 | Extra product fields | Item (extend) | Custom Fields |
| 4 | Customer portal | Portal pages | Website templates |
| 5 | Order tracking | Sales Order (read) | Portal + permissions |

**Step 2 — App Boundaries**:

Decision: TWO apps.
- `shopify_connector`: Integration logic (sync, webhooks, API mapping)
- `customer_portal`: Portal pages, custom views, frontend

Rationale: Integration and portal have different release cycles, different teams, and can be installed independently.

**Step 3 — Dependencies**:
```
frappe
└── erpnext
    ├── shopify_connector (requires: frappe, erpnext)
    └── customer_portal (requires: frappe, erpnext)
```
No dependency between shopify_connector and customer_portal — they are independent.

**Step 4 — Data Model**:

| DocType | App | Purpose | Key Fields |
|---------|-----|---------|------------|
| Shopify Settings | shopify_connector | API credentials | api_key, api_secret, shop_url |
| Shopify Log | shopify_connector | Sync audit trail | sync_type, status, error_message |
| Custom Fields on Item | shopify_connector | Shopify product ID | custom_shopify_id, custom_shopify_url |
| Custom Fields on Sales Order | shopify_connector | Shopify order ID | custom_shopify_order_id |
| Portal Settings (extend) | customer_portal | Portal configuration | Custom Fields for branding |

**Step 5 — Roadmap**:

| Phase | App | Deliverables |
|-------|-----|-------------|
| 1 | shopify_connector | App scaffold, Settings DocType, Item sync |
| 2 | shopify_connector | Order sync, webhook handler |
| 3 | customer_portal | Portal templates, order list view |
| 4 | Both | Testing, deployment |

---

## Example 2: Manufacturing Extension

### Input
"We use ERPNext Manufacturing. We need to add quality inspection checklists per work order, a machine maintenance scheduler, and production analytics dashboards."

### Architecture Design

**Step 1 — Requirement Analysis**:

| # | Requirement | DocTypes | Mechanism |
|---|------------|----------|-----------|
| 1 | Quality checklists | Quality Checklist (new), Quality Check Item (child) | Controller |
| 2 | Link to work order | Work Order (extend) | Custom Field + hook |
| 3 | Machine maintenance | Machine (new), Maintenance Schedule (new) | Controller + scheduler |
| 4 | Production analytics | Script Reports | Query Report |

**Step 2 — App Boundaries**:

Decision: SINGLE APP (`custom_manufacturing`).

Rationale: All requirements are in the same domain (manufacturing), maintained by one team, < 15 DocTypes total, tight data coupling between quality and maintenance.

**Step 3 — Dependencies**:
```
frappe
└── erpnext
    └── custom_manufacturing (requires: frappe, erpnext)
```

**Step 4 — Data Model**:

| DocType | Module | Purpose | Links To |
|---------|--------|---------|----------|
| Quality Checklist | Quality | Inspection template | Work Order (Link) |
| Quality Check Item | Quality | Child table of Checklist | — (child) |
| Machine | Maintenance | Equipment registry | — |
| Maintenance Schedule | Maintenance | Planned maintenance | Machine (Link) |
| Maintenance Log | Maintenance | Completed maintenance | Machine (Link), Maintenance Schedule (Link) |

Cross-app hooks:
```python
# hooks.py
doc_events = {
    "Work Order": {
        "on_submit": "custom_manufacturing.quality.handlers.create_quality_checklist"
    }
}

scheduler_events = {
    "daily": [
        "custom_manufacturing.maintenance.tasks.check_upcoming_maintenance"
    ]
}
```

**Step 5 — Roadmap**:

| Phase | Module | Deliverables |
|-------|--------|-------------|
| 1 | Core | App scaffold, Machine DocType |
| 2 | Quality | Quality Checklist + Work Order hook |
| 3 | Maintenance | Maintenance Schedule + Scheduler |
| 4 | Analytics | Script Reports + dashboard |

---

## Example 3: Multi-Company HR Extension

### Input
"We have 3 companies in ERPNext. Each company has different HR policies. We need custom leave types per company, a recruitment pipeline, and employee self-service portal."

### Architecture Design

**Step 1 — Requirement Analysis**:

| # | Requirement | DocTypes | Mechanism |
|---|------------|----------|-----------|
| 1 | Company-specific leave types | Leave Type (extend) | Custom Fields + Permission |
| 2 | Recruitment pipeline | Job Opening (extend), Interview (new), Candidate (new) | Controller + Workflow |
| 3 | Employee self-service | Portal pages | Website templates + permissions |
| 4 | Multi-company isolation | User Permissions | Company-based filtering |

**Step 2 — App Boundaries**:

Decision: TWO apps.
- `hr_extensions`: Recruitment pipeline, custom leave logic (backend-heavy)
- `hr_portal`: Employee self-service portal (frontend-heavy)

Rationale: Portal and backend extensions have very different development patterns. Portal can be installed independently for companies that do not need custom recruitment.

**Step 3 — Dependencies**:
```
frappe
└── erpnext (includes hrms module)
    ├── hr_extensions (requires: frappe, erpnext)
    └── hr_portal (requires: frappe, erpnext, hr_extensions)
```

Note: hr_portal depends on hr_extensions because it displays recruitment data.

**Step 4 — Data Model**:

| DocType | App | Purpose |
|---------|-----|---------|
| Candidate | hr_extensions | Applicant tracking |
| Interview | hr_extensions | Interview scheduling |
| Interview Feedback | hr_extensions | Child table of Interview |
| Custom Fields on Leave Type | hr_extensions | company-specific settings |
| Custom Fields on Job Opening | hr_extensions | Pipeline stage tracking |

Multi-company design:
- EVERY custom DocType has a `company` Link field
- User Permissions on Company enforce data isolation
- Leave policies filtered by company in all queries

**Step 5 — Roadmap**:

| Phase | App | Deliverables |
|-------|-----|-------------|
| 1 | hr_extensions | Candidate + Interview DocTypes |
| 2 | hr_extensions | Workflow for recruitment pipeline |
| 3 | hr_extensions | Custom leave type per company |
| 4 | hr_portal | Employee self-service pages |
| 5 | Both | Multi-company testing, deployment |

---

## Anti-Pattern Examples

### Anti-Pattern 1: The Mega-App

```
BAD: single_app/ (45 DocTypes across HR, CRM, Manufacturing, Accounting)
- Impossible to test in isolation
- One bug blocks all releases
- New developers overwhelmed

GOOD: Split into 4 focused apps
- hr_custom/ (12 DocTypes)
- crm_custom/ (10 DocTypes)
- manufacturing_custom/ (13 DocTypes)
- accounting_custom/ (10 DocTypes)
```

### Anti-Pattern 2: Circular Dependencies

```
BAD:
  app_sales requires app_inventory
  app_inventory requires app_sales
  (Cannot install either without the other)

GOOD:
  app_base (shared DocTypes: Item, Customer)
  app_sales requires app_base
  app_inventory requires app_base
  (Each can be installed independently after base)
```

### Anti-Pattern 3: Duplicating ERPNext

```
BAD: Creating "Custom Invoice" DocType that duplicates Sales Invoice
- Double data entry or complex sync
- Loses all ERPNext reporting
- Must maintain accounting logic yourself

GOOD: Extend Sales Invoice with Custom Fields + hooks
- Use Custom Fields for extra data
- Use hooks for custom validation
- All ERPNext reports still work
```

### Anti-Pattern 4: No Module Organization

```
BAD:
  myapp/myapp/doctype/
    ├── customer_complaint/
    ├── machine/
    ├── quality_report/
    ├── maintenance_log/
    ├── shift_schedule/
    └── (30 more DocTypes in flat structure)

GOOD:
  myapp/myapp/
    ├── quality/doctype/
    │   ├── customer_complaint/
    │   └── quality_report/
    ├── maintenance/doctype/
    │   ├── machine/
    │   └── maintenance_log/
    └── operations/doctype/
        └── shift_schedule/
```
