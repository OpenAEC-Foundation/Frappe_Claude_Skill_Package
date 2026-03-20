# Architecture Decision Trees

## Decision Tree 1: Single App vs Multiple Apps

```
START: How many custom DocTypes are planned?
|
+-- 1-5 DocTypes
|   +-- All in same business domain? --> SINGLE APP
|   +-- Different domains? --> SINGLE APP with separate modules
|
+-- 6-15 DocTypes
|   +-- Single team maintains all? --> SINGLE APP with modules
|   +-- Multiple teams?
|       +-- Clear domain boundaries? --> 2-3 APPS
|       +-- Overlapping domains? --> SINGLE APP with modules
|
+-- 16-30 DocTypes
|   +-- All tightly coupled? --> SINGLE APP (rare — verify coupling is real)
|   +-- Can group into 2-4 domains? --> 2-4 APPS
|   +-- Many independent components? --> 3-5 APPS
|
+-- 30+ DocTypes
|   --> ALWAYS SPLIT
|       Group by: domain > team > release cycle
|       Target: 10-15 DocTypes per app maximum
```

## Decision Tree 2: Extend ERPNext vs Build Custom

```
START: Does ERPNext have a DocType for this entity?
|
+-- YES, exact match
|   +-- Need < 10 extra fields? --> CUSTOM FIELDS (no custom app)
|   +-- Need > 10 extra fields? --> CUSTOM FIELDS + consider child table
|   +-- Need custom business logic?
|       +-- Simple validation? --> SERVER SCRIPT (no custom app)
|       +-- Complex logic with imports? --> CONTROLLER OVERRIDE (custom app)
|   +-- Need UI changes?
|       +-- Hide/show fields? --> CLIENT SCRIPT (no custom app)
|       +-- New buttons/sections? --> CLIENT SCRIPT (no custom app)
|       +-- Complete form redesign? --> Custom Page (custom app)
|
+-- YES, close match (similar but not exact)
|   +-- Can adapt with Custom Fields + logic? --> EXTEND existing DocType
|   +-- Fundamentally different data model? --> NEW CUSTOM DOCTYPE
|
+-- NO, nothing similar exists
|   --> NEW CUSTOM DOCTYPE in custom app
|       +-- Will it link to ERPNext DocTypes? --> Custom app with erpnext dependency
|       +-- Standalone? --> Custom app with frappe-only dependency
```

## Decision Tree 3: Controller Override Strategy

```
START: Need to modify ERPNext DocType behavior?
|
+-- Simple validation (< 20 lines)?
|   --> SERVER SCRIPT (no custom app needed)
|       Event: validate, before_save, on_submit, etc.
|
+-- Need Python imports or complex logic?
|   +-- Running v16?
|   |   --> extend_doctype_class in hooks.py
|   |       ALWAYS call super() in every method
|   |
|   +-- Running v14 or v15?
|       --> doc_events in hooks.py
|           Point to function in custom app
|
+-- Need to change core method behavior?
|   +-- Can you achieve it with before/after hooks?
|   |   --> Use doc_events (before_validate, after_insert, etc.)
|   |
|   +-- Must replace the method entirely?
|       --> extend_doctype_class (v16) or monkey-patch (v14/v15)
|           WARNING: Fragile, test on every ERPNext upgrade
```

## Decision Tree 4: Cross-App Communication

```
START: App A needs to know about App B's events?
|
+-- App A is UPSTREAM (base), App B is DOWNSTREAM
|   --> App B hooks into App A's doc_events
|       App B declares App A in required_apps
|       App A knows NOTHING about App B
|
+-- App A and App B are PEERS (same level)
|   +-- Can one depend on the other?
|   |   --> Make one upstream, one downstream (choose wisely)
|   |
|   +-- Neither should depend on the other?
|       --> Extract shared concern into BASE APP
|           Both A and B depend on base app
|           Use hooks for event communication
|
+-- Real-time communication needed?
|   --> frappe.publish_realtime() from source
|       frappe.realtime.on() in client of target
|       No app dependency required (event-based)
|
+-- Loose coupling preferred?
|   --> API-based communication
|       App B calls App A's whitelisted methods
|       App B handles App A being absent gracefully
```

## Decision Tree 5: Data Model — Child Table vs Link

```
START: Entity B "belongs to" Entity A?
|
+-- B has NO independent existence (always part of A)
|   +-- B appears as rows in A's form? --> CHILD TABLE
|   |   Examples: Invoice Items, BOM Materials, Task Checklist
|   |
|   +-- B is a sub-record but not rows? --> Separate DocType with Link
|       Examples: Multiple addresses for Customer
|
+-- B exists independently but relates to A
|   +-- One B relates to one A? --> LINK field on B pointing to A
|   +-- One B relates to many A's? --> LINK field on each A pointing to B
|   +-- Many B's relate to many A's? --> INTERMEDIARY DocType
|       Intermediary has Link to A and Link to B
```

## Decision Tree 6: Permission Architecture

```
START: Who should access this DocType?
|
+-- All logged-in users --> Role: All, perm_level 0
|
+-- Specific department/function
|   +-- Existing ERPNext role fits? --> Use that role
|   +-- Need custom role?
|       --> Create Role, assign permissions per DocType
|       --> Set perm_level for field-level access
|
+-- Users see only their own records?
|   +-- By owner? --> "if_owner" permission rule
|   +-- By company? --> User Permission on Company
|   +-- By territory/department? --> User Permission on Territory/Department
|   +-- Complex logic? --> Permission Query (Server Script)
|
+-- External users (portal/API)?
|   +-- Portal pages --> Website User role + portal settings
|   +-- API access --> API Key + Role for API user
|   +-- Guest access --> allow_guest=True on whitelisted methods
```

## Decision Tree 7: When to Create a Custom App

```
START: Do I need a custom Frappe app?
|
+-- Only adding fields to existing DocTypes?
|   --> NO — use Custom Fields via Setup
|
+-- Only adding simple validation logic?
|   --> NO — use Server Scripts
|
+-- Only adding UI behavior?
|   --> NO — use Client Scripts
|
+-- Only adding a workflow?
|   --> NO — use built-in Workflow Builder
|
+-- Need Python imports (requests, etc.)?
|   --> YES — custom app required
|
+-- Need scheduled background tasks?
|   --> YES — custom app required (hooks.py scheduler_events)
|
+-- Need new DocTypes?
|   --> YES — custom app required
|
+-- Need to override ERPNext controller logic?
|   --> YES — custom app required
|
+-- Need custom REST API endpoints?
|   +-- Simple? --> Server Script (API type) — NO app needed
|   +-- Complex with imports? --> YES — custom app required
```
