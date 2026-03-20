# Code Interpreter Examples

## Example 1: Auto-Calculate Request

### User Input
> "I want the total weight to automatically calculate based on item weights in the Sales Order"

### Interpretation Process

**Extract Intent:**
- Action: Auto-calculate (field computation)
- Subject: Total weight field, item weights in Sales Order
- Condition: When items change

**Identify Trigger:**
- Field change (item added/removed/modified) --> Client Script
- Before save (validation backup) --> Server Script

**Determine Mechanism:**
- Real-time UI update needed --> Client Script
- Save validation needed --> Server Script
- No external libraries --> Server Script OK

### Generated Specification

```markdown
## Technical Specification

### Summary
Auto-calculate total weight in Sales Order based on sum of item weights.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Sales Order, Sales Order Item |
| **Trigger** | Item table change + before save |
| **Mechanism** | Client Script + Server Script |
| **Version** | v14/v15/v16 |

### Data Flow
1. User modifies items table (add/remove/change qty)
2. Client Script triggers calculation
3. Sum: qty x weight_per_unit for each item
4. Update total_weight field
5. On save: Server Script recalculates and validates

### Error Handling
- Missing weight_per_unit: treat as 0, no error
- Negative result: frappe.throw() on save

### Required Skills
- [x] frappe-syntax-clientscripts
- [x] frappe-impl-clientscripts
- [x] frappe-syntax-serverscripts
- [x] frappe-impl-serverscripts
```

---

## Example 2: Notification Request

### User Input
> "Send email to manager when purchase order exceeds $10,000"

### Generated Specification

```markdown
## Technical Specification

### Summary
Email notification to manager when Purchase Order grand_total exceeds $10,000.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Purchase Order |
| **Trigger** | on_submit |
| **Mechanism** | Server Script (Document Event) |
| **Version** | v14/v15/v16 |

### Data Flow
1. User submits Purchase Order
2. Server Script checks if grand_total > 10000
3. If yes: frappe.sendmail() to manager

### Required Skills
- [x] frappe-syntax-serverscripts
- [x] frappe-impl-serverscripts
- [x] frappe-core-notifications

### Alternative: No-Code Solution
Use Notification DocType: Document Type = Purchase Order, Event = Submit, Condition = doc.grand_total > 10000
```

---

## Example 3: External Integration Request

### User Input
> "Sync inventory to our warehouse system via API when stock moves"

### Generated Specification

```markdown
## Technical Specification

### Summary
Sync stock movements to external warehouse system via REST API on Stock Entry submission.

### CRITICAL: Custom App Required
Server Scripts CANNOT import the `requests` library.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Stock Entry |
| **Trigger** | on_submit |
| **Mechanism** | Controller (custom app) |
| **Version** | v14/v15/v16 |

### Data Flow
1. Stock Entry submitted
2. Controller's on_submit hook triggers
3. Transform data to external API format
4. POST to external warehouse API
5. Log response; if failure: enqueue retry

### Required Skills
- [x] frappe-impl-customapp - Custom app structure
- [x] frappe-impl-integrations - Integration patterns
- [x] frappe-syntax-controllers - Controller class
- [x] frappe-impl-controllers - on_submit implementation
- [x] frappe-errors-controllers - Error handling
- [x] frappe-syntax-hooks - doc_events configuration
- [x] frappe-impl-scheduler - Retry queue (if needed)
```

---

## Example 4: Permission Filtering Request

### User Input
> "Sales reps should only see their own customers"

### Generated Specification

```markdown
## Technical Specification

### Summary
Filter Customer list view to show only customers assigned to the current sales representative.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Customer |
| **Trigger** | List view access |
| **Mechanism** | Server Script (Permission Query) |
| **Version** | v14/v15/v16 |

### Required Skills
- [x] frappe-syntax-serverscripts - Permission Query syntax
- [x] frappe-core-permissions - Permission patterns
- [x] frappe-errors-permissions - Permission error handling
```

---

## Example 5: Workflow Request

### User Input
> "Purchase orders over $5000 need manager approval before submission"

### Generated Specification

```markdown
## Technical Specification

### Summary
Approval workflow for Purchase Orders exceeding $5,000.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Purchase Order |
| **Trigger** | Document state changes |
| **Mechanism** | Built-in Workflow + optional Server Script |
| **Version** | v14/v15/v16 |

### States
1. Draft (default) 2. Pending Approval 3. Approved 4. Submitted 5. Rejected

### Required Skills
- [x] frappe-core-workflow - Workflow engine
- [x] frappe-impl-workflow - Workflow implementation
- [x] frappe-syntax-serverscripts - Optional custom logic
```

---

## Example 6: Scheduled Task Request

### User Input
> "Every night, check for overdue invoices and send reminders"

### Generated Specification

```markdown
## Technical Specification

### Summary
Daily scheduled task to identify overdue Sales Invoices and send payment reminders.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Sales Invoice |
| **Trigger** | Cron: 0 2 * * * (daily at 2 AM) |
| **Mechanism** | hooks.py scheduler_events (custom app) |
| **Version** | v14/v15/v16 |

### Required Skills
- [x] frappe-impl-scheduler - Scheduler implementation
- [x] frappe-syntax-scheduler - Cron syntax
- [x] frappe-impl-customapp - App structure
- [x] frappe-core-database - Query patterns
- [x] frappe-core-notifications - Email sending
```

---

## Example 7: Report Request

### User Input
> "I need a report showing monthly sales by territory with drill-down"

### Generated Specification

```markdown
## Technical Specification

### Summary
Script Report for monthly sales analysis by territory with drill-down capability.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Sales Invoice |
| **Trigger** | User opens report |
| **Mechanism** | Script Report |
| **Version** | v14/v15/v16 |

### Required Skills
- [x] frappe-syntax-reports - Report definition
- [x] frappe-impl-reports - Report building patterns
- [x] frappe-core-database - Aggregation queries
```

---

## Example 8: Deployment/Ops Request

### User Input
> "How do I deploy my custom app to production?"

### Generated Specification

```markdown
## Technical Specification

### Summary
Production deployment workflow for custom Frappe app.

### Implementation Steps
1. Prepare app for distribution (git, pyproject.toml)
2. Set up production bench
3. Install app on production site
4. Configure supervisor and nginx
5. Enable scheduler, set up backups

### Required Skills
- [x] frappe-ops-deployment - Deployment procedures
- [x] frappe-ops-bench - Bench commands
- [x] frappe-ops-backup - Backup configuration
- [x] frappe-ops-performance - Production tuning
- [x] frappe-impl-customapp - App packaging
```

---

## Pattern Recognition Summary

| User Phrase | Likely Mechanism | Key Skills |
|-------------|-----------------|------------|
| "auto-calculate" | Client Script + Server Script | `frappe-impl-clientscripts`, `frappe-impl-serverscripts` |
| "validate", "check" | Server Script (validate) | `frappe-impl-serverscripts` |
| "prevent", "block" | Server Script + frappe.throw() | `frappe-errors-serverscripts` |
| "send email", "notify" | Server Script or Notification | `frappe-core-notifications` |
| "sync", "API" | Controller (custom app) | `frappe-impl-integrations` |
| "every day", "schedule" | Scheduler or hooks.py | `frappe-impl-scheduler` |
| "only see their own" | Permission Query | `frappe-core-permissions` |
| "approval" | Built-in Workflow | `frappe-core-workflow`, `frappe-impl-workflow` |
| "add button" | Client Script | `frappe-impl-clientscripts` |
| "print format" | Jinja Template | `frappe-impl-jinja` |
| "report", "dashboard" | Script/Query Report | `frappe-impl-reports` |
| "deploy", "go live" | Deployment workflow | `frappe-ops-deployment` |
| "test", "CI" | Testing framework | `frappe-testing-unit`, `frappe-testing-cicd` |
| "cache", "speed" | Cache + optimization | `frappe-core-cache`, `frappe-ops-performance` |
| "website", "portal" | Web templates | `frappe-impl-website` |
| "upload", "file" | File handling | `frappe-core-files` |
