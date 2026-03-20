# Code Interpreter Workflow - Detailed Steps

## Complete Interpretation Process

### Step 1: Extract Intent

**Goal**: Understand what the user actually wants to achieve.

#### 1.1 Identify the Action Verb

| User Says | Likely Intent |
|-----------|---------------|
| "auto-calculate", "automatically fill" | Field computation |
| "validate", "check", "ensure" | Data validation |
| "prevent", "block", "stop" | Operation blocking |
| "notify", "alert", "email" | Notification |
| "sync", "connect", "integrate" | External integration |
| "schedule", "daily", "every hour" | Scheduled task |
| "approve", "review", "authorize" | Workflow |
| "filter", "show only", "restrict view" | Permission/filtering |
| "add button", "add action" | UI customization |
| "format", "print", "PDF" | Print/report customization |
| "deploy", "go live", "production" | Deployment/ops |
| "test", "CI", "quality" | Testing |
| "cache", "speed up", "performance" | Optimization |
| "report", "dashboard", "analytics" | Reporting |
| "website", "portal", "public page" | Website development |
| "upload", "attachment", "file" | File handling |
| "backup", "restore" | Data safety |
| "upgrade", "migrate version" | Version management |

#### 1.2 Identify the Subject

What data/document is involved?
- Specific DocType mentioned?
- Field names mentioned?
- Related documents involved?

#### 1.3 Identify the Condition

When should this happen?
- Always?
- Only when specific field has value?
- Only for specific status?
- Only for specific user/role?

### Step 2: Identify Trigger Context

**Goal**: Determine WHEN the code should execute.

#### Decision Tree: Trigger Type

```
Is it triggered by...

USER ACTION ON FORM?
+-- Field value change
|   --> Client Script: on field change
+-- Form load
|   --> Client Script: refresh event
+-- Button click
|   --> Client Script: custom button with frappe.call
+-- Save button
|   --> Server Script: validate (before) or on_update (after)
+-- Submit button
|   --> Server Script: before_submit or on_submit
+-- Cancel button
    --> Server Script: before_cancel or on_cancel

TIME/SCHEDULE?
+-- Every X minutes/hours
|   --> Server Script Scheduler or hooks.py
+-- Daily at specific time
|   --> Server Script Scheduler (cron) or hooks.py
+-- Weekly/Monthly
    --> hooks.py scheduler_events

EXTERNAL EVENT?
+-- Webhook from external system
|   --> Server Script API or @frappe.whitelist
+-- API call
|   --> Server Script API or @frappe.whitelist
+-- Another app's action
    --> doc_events in hooks.py

PERMISSION CHECK?
+-- List view filtering
    --> Server Script Permission Query
```

### Step 3: Determine Mechanism

**Goal**: Select the right Frappe mechanism.

#### Primary Decision: Server Script vs Controller

```
CAN YOU USE SERVER SCRIPT?

Check these disqualifiers:
[ ] Need to import external library (requests, pandas, etc.)
[ ] Need complex try/except/finally with rollback
[ ] Need to modify multiple documents in transaction
[ ] Need to access file system
[ ] Need to run shell commands

If ANY checked --> Controller (custom app required)
If NONE checked --> Server Script acceptable
```

#### Secondary Decision: Client Script Needed?

```
ADD CLIENT SCRIPT WHEN:
[ ] Real-time UI feedback needed (instant calculation)
[ ] Field visibility/read-only based on other fields
[ ] Custom buttons needed
[ ] Form-level warnings/alerts
[ ] Auto-fetch from linked documents
```

#### v16 Decision: extend_doctype_class vs doc_events

```
TARGETING v16 ONLY?
+-- YES --> Use extend_doctype_class (cleaner, supports mixins)
+-- NO --> Use doc_events (works on v14/v15/v16)
```

#### Mechanism Selection Summary

| Requirement | Mechanism | Skills |
|-------------|-----------|--------|
| Quick validation | Server Script (validate) | `frappe-syntax-serverscripts`, `frappe-impl-serverscripts` |
| Real-time UI | Client Script + Server Script | `frappe-impl-clientscripts`, `frappe-impl-serverscripts` |
| Simple API endpoint | Server Script (API) | `frappe-syntax-serverscripts`, `frappe-core-api` |
| Complex API | @frappe.whitelist in custom app | `frappe-impl-whitelisted`, `frappe-impl-customapp` |
| Daily batch job (simple) | Server Script (Scheduler) | `frappe-syntax-scheduler`, `frappe-impl-scheduler` |
| Complex scheduled job | hooks.py scheduler_events | `frappe-impl-scheduler`, `frappe-impl-hooks` |
| List filtering per user | Server Script (Permission Query) | `frappe-core-permissions` |
| Multi-doc transaction | Controller in custom app | `frappe-impl-controllers`, `frappe-impl-customapp` |
| Approval process | Built-in Workflow | `frappe-core-workflow`, `frappe-impl-workflow` |
| Report/analytics | Script Report or Query Report | `frappe-impl-reports`, `frappe-syntax-reports` |
| Website/portal | Web template + routing | `frappe-impl-website`, `frappe-syntax-jinja` |
| Integration | Controller + hooks | `frappe-impl-integrations`, `frappe-impl-customapp` |
| File handling | File hooks + controller | `frappe-core-files`, `frappe-impl-controllers` |
| Notifications | Notification API | `frappe-core-notifications` |
| Cache optimization | Cache API | `frappe-core-cache`, `frappe-ops-performance` |
| Testing | Test framework | `frappe-testing-unit`, `frappe-testing-cicd` |
| Deployment | Bench commands | `frappe-ops-deployment`, `frappe-ops-bench` |

### Step 4: Generate Specification

**Goal**: Create actionable technical spec.

#### Specification Components

1. **Summary** (1 sentence) - What will be built, what problem it solves
2. **Business Requirement** (clarified) - Original request with ambiguities resolved
3. **Implementation Details** - DocType(s), trigger, mechanism, version
4. **Data Flow** - Read, process, write, output steps
5. **Error Handling** - What errors can occur, how handled
6. **Validation Criteria** - How to test it works, edge cases

### Step 5: Map to Skills

**Goal**: Identify which frappe-* skills are needed for implementation.

#### Skill Mapping Process

1. Based on mechanism, identify PRIMARY skills (syntax + impl)
2. Add ERROR HANDLING skills (frappe-errors-*)
3. Add CORE skills if needed (database, permissions, api, etc.)
4. Add OPS skills if deployment is involved
5. Add TESTING skills if test coverage requested
6. Check for CUSTOM APP requirement (frappe-impl-customapp)
7. Consider AGENT skills (frappe-agent-validator for review)

## Example Interpretation Walkthrough

### Input Request
> "When a Sales Invoice is submitted, check if customer credit limit is exceeded and block if so"

### Step 1: Extract Intent
- **Action**: "check" and "block" --> Validation that prevents action
- **Subject**: Sales Invoice, Customer credit limit
- **Condition**: On submit

### Step 2: Identify Trigger
- User action: Submit button
- Trigger: before_submit (must block BEFORE action completes)

### Step 3: Determine Mechanism
- No external libraries needed
- No complex transactions needed
- --> Server Script is acceptable

### Step 4: Generate Specification

```markdown
## Technical Specification

### Summary
Block Sales Invoice submission when customer's credit limit is exceeded.

### Implementation

| Aspect | Value |
|--------|-------|
| **DocType(s)** | Sales Invoice, Customer |
| **Trigger** | before_submit |
| **Mechanism** | Server Script (Document Event) |
| **Version** | v14/v15/v16 |

### Data Flow
1. Get customer from Sales Invoice
2. Query customer's current outstanding amount
3. Add current invoice grand_total
4. Compare with customer's credit_limit
5. If exceeded: frappe.throw() with message

### Required Skills
- [x] frappe-syntax-serverscripts
- [x] frappe-impl-serverscripts
- [x] frappe-errors-serverscripts
- [x] frappe-core-database
```

### Step 5: Map to Skills
- Primary: `frappe-syntax-serverscripts`, `frappe-impl-serverscripts`
- Error: `frappe-errors-serverscripts`
- Supporting: `frappe-core-database` (for outstanding calculation)
- Validation: `frappe-agent-validator` (review before deployment)
