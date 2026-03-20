# Architecture Workflow — Detailed Steps

## Step 1: Analyze Requirements

### Input Gathering

ALWAYS collect this information before designing:

1. **Business domain**: What industry/function is this for?
2. **User roles**: Who will use the system? How many concurrent users?
3. **Core processes**: What are the 3-5 most critical business workflows?
4. **Data entities**: What "things" does the business track?
5. **Integrations**: What external systems must connect?
6. **Existing setup**: Is ERPNext already installed? Which modules are in use?
7. **Team structure**: Who will develop and maintain each component?
8. **Timeline**: What must be delivered first?

### Requirement-to-DocType Mapping

For each business requirement:

1. Identify the data entity (becomes a DocType)
2. Identify relationships to other entities (becomes Link fields)
3. Identify child data (becomes Child Table DocTypes)
4. Identify business rules (becomes Controller/Server Script logic)
5. Identify user interactions (becomes Client Scripts, buttons, workflows)

### ERPNext Coverage Check

Before creating ANY custom DocType, check if ERPNext already has it:

| Business Need | ERPNext DocType | Module |
|--------------|----------------|--------|
| Customers | Customer | Selling |
| Suppliers | Supplier | Buying |
| Products | Item | Stock |
| Sales orders | Sales Order | Selling |
| Purchase orders | Purchase Order | Buying |
| Invoices | Sales Invoice / Purchase Invoice | Accounts |
| Inventory | Stock Entry, Stock Ledger | Stock |
| Employees | Employee | HR |
| Projects | Project, Task | Projects |
| Support tickets | Issue | Support |
| CRM leads | Lead, Opportunity | CRM |
| Manufacturing | BOM, Work Order | Manufacturing |

NEVER recreate what ERPNext already provides. ALWAYS extend with Custom Fields or hooks.

## Step 2: Decide App Boundaries

### Domain Boundary Analysis

Group related DocTypes by asking:

1. Do these DocTypes share the same user roles?
2. Do these DocTypes reference each other frequently?
3. Would these DocTypes be useful independently?
4. Does one team own all of these DocTypes?
5. Do these DocTypes have the same release cycle?

If YES to all 5 → same app. If NO to 2+ → consider separate apps.

### Dependency Direction Rule

Draw a dependency diagram BEFORE finalizing app boundaries:

```
RULE: All arrows must point in ONE direction (toward base/shared)

VALID:
  app_reporting --> app_core --> frappe

INVALID (circular):
  app_a --> app_b --> app_a
```

If you find circular dependencies during design, restructure:
- Extract shared DocTypes into a base app
- Use hooks/events instead of direct imports for cross-app communication

### Module Organization Within Apps

Even within a single app, organize DocTypes into modules:

```
myapp/
├── myapp/
│   ├── core_module/          # Shared DocTypes (Settings, Configuration)
│   │   └── doctype/
│   ├── sales_module/         # Sales-related DocTypes
│   │   └── doctype/
│   ├── inventory_module/     # Inventory-related DocTypes
│   │   └── doctype/
│   └── hooks.py
```

## Step 3: Design Cross-App Dependencies

### Hook Contract Design

When App B needs to react to App A's documents:

```python
# App B's hooks.py — subscribing to App A's events
doc_events = {
    "Sales Invoice": {  # App A's DocType
        "on_submit": "app_b.handlers.on_invoice_submit",
        "on_cancel": "app_b.handlers.on_invoice_cancel"
    }
}
```

Rules for hook contracts:
- App B depends on App A (add to `required_apps`)
- App A does NOT know about App B (no reverse dependency)
- Hook functions MUST handle missing data gracefully
- Hook functions MUST NOT modify the source document unless explicitly designed to

### Shared DocType Strategy

When multiple apps need the same reference data:

| Strategy | Implementation | Use When |
|----------|---------------|----------|
| **Owner app** | One app owns the DocType, others Link to it | Clear ownership |
| **Base app** | Shared DocTypes in a base/utilities app | Multiple consumers, no clear owner |
| **ERPNext native** | Use existing ERPNext DocType | ERPNext already has it |

### Custom Fields for Extension

When extending another app's DocType without modifying it:

```python
# In your app's fixtures or setup
custom_fields = {
    "Sales Invoice": [
        {
            "fieldname": "custom_approval_status",
            "fieldtype": "Select",
            "options": "Pending\nApproved\nRejected",
            "insert_after": "status"
        }
    ]
}
```

ALWAYS prefix custom fields with `custom_` to avoid conflicts.

## Step 4: Design Data Model

### DocType Design Checklist

For each DocType in the architecture:

1. **Name**: Title Case with spaces, descriptive
2. **Module**: Which module does it belong to?
3. **Naming**: autoname rule (hash, series, field-based, or UUID for v16)
4. **Fields**: List all fields with types
5. **Child Tables**: Identify repeating row data
6. **Links**: All references to other DocTypes
7. **Permissions**: Which roles can CRUD?
8. **Workflow**: Does it need approval states?
9. **Is Submittable**: Does it need submit/cancel lifecycle?

### Relationship Design Rules

- One-to-Many: ALWAYS use Child Table (parent DocType has the table)
- Many-to-One: ALWAYS use Link field (child points to parent)
- Many-to-Many: Create an intermediary DocType with two Link fields
- Self-referential: Link field pointing to same DocType (add validation to prevent cycles)

### Field Type Selection Guide

| Data Type | Frappe Fieldtype | Notes |
|-----------|-----------------|-------|
| Short text (< 140 chars) | Data | Single line |
| Long text | Text | Multi-line, no formatting |
| Rich text | Text Editor | HTML content |
| Number (integer) | Int | Whole numbers only |
| Number (decimal) | Float or Currency | Currency for money |
| Date | Date | Date only |
| Date + time | Datetime | Date and time |
| Yes/No | Check | Boolean checkbox |
| Dropdown | Select | Predefined options |
| Reference to DocType | Link | Foreign key |
| File | Attach | Single file |
| Multiple files | Attach Image or Table | Use child table for multiple |

## Step 5: Generate Implementation Roadmap

### Build Order Rules

1. ALWAYS build base/shared apps first
2. ALWAYS build DocTypes before their dependents
3. ALWAYS build settings/configuration DocTypes before transaction DocTypes
4. ALWAYS build and test one app fully before starting the next
5. NEVER build frontend (Client Scripts, pages) before backend is stable

### Phase Template

```
Phase 1: Foundation (Week 1)
- Create app scaffolding: bench new-app {name}
- Define all DocTypes (JSON only, no logic yet)
- Set up permissions for all roles
- Create fixtures for master data

Phase 2: Core Logic (Week 2-3)
- Implement controllers for transaction DocTypes
- Add Server Scripts for validations
- Build workflows for approval processes
- Implement hooks for cross-app events

Phase 3: User Experience (Week 3-4)
- Add Client Scripts for form behavior
- Build custom pages/dashboards
- Create print formats
- Build Script Reports

Phase 4: Integration (Week 4-5)
- External system connectors
- Scheduled sync jobs
- API endpoints for third parties

Phase 5: Testing and Deployment (Week 5-6)
- Unit tests for all controllers
- Integration tests for cross-app workflows
- Performance testing
- Production deployment
```

### Team Assignment Rules

- One app per team (clear ownership)
- Base/shared apps: most experienced team
- Integration layer: dedicated person or team
- NEVER have two teams modifying the same app simultaneously
