# Frappe Hook Selection Decision Trees

Complete flowcharts for selecting the right hook type.

---

## Master Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WHAT ARE YOU TRYING TO DO?                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ DOCUMENT      │         │ SCHEDULED     │         │ MODIFY        │
│ LIFECYCLE     │         │ TASKS         │         │ EXISTING      │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
   doc_events              scheduler_events            Override hooks
   (Section 1)              (Section 2)                (Section 3)
        
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ PERMISSIONS   │         │ CLIENT DATA   │         │ ASSETS &      │
│               │         │               │         │ CONFIG        │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
   Permission hooks         extend_bootinfo           fixtures,
   (Section 4)              (Section 5)               asset includes
                                                      (Section 6)
```

---

## Section 1: Document Lifecycle (doc_events)

### When to Use doc_events vs Controller

```
IS THE DOCTYPE YOURS OR EXTERNAL?
│
├─► YOUR app's DocType
│   │
│   │ Do you need...
│   ├─► Full control, imports, complex logic?
│   │   └─► Controller methods in doctype/xxx/xxx.py
│   │
│   └─► Quick hook alongside controller?
│       └─► Can use doc_events (runs after controller)
│
├─► EXTERNAL app's DocType (ERPNext, Frappe)
│   └─► doc_events in hooks.py (ONLY option)
│
└─► ALL DocTypes (logging, audit trail)
    └─► doc_events with wildcard "*"
```

### Which doc_event to Use

```
WHEN DOES YOUR CODE NEED TO RUN?
│
├─► BEFORE the document is saved
│   │
│   ├─► Validate or calculate on EVERY save?
│   │   └─► validate
│   │       - Called on insert AND update
│   │       - Changes to doc ARE saved
│   │       - Use frappe.throw() to block save
│   │
│   ├─► Only on NEW documents?
│   │   └─► before_insert
│   │       - Only first save
│   │       - Good for: auto-naming, defaults
│   │
│   └─► Before validation starts?
│       └─► before_validate
│           - Rarely needed
│           - Runs before validate
│
├─► AFTER the document is saved
│   │
│   ├─► Only after FIRST save (new doc)?
│   │   └─► after_insert
│   │       - Document has name now
│   │       - Good for: notifications, linked docs
│   │
│   ├─► After EVERY save?
│   │   └─► on_update
│   │       - Most common "after save" hook
│   │       - Changes need db_set_value
│   │
│   └─► After ANY change (including db_set)?
│       └─► on_change
│           - Also fires on db_set_value
│           - Use carefully (can loop)
│
├─► SUBMITTABLE document workflow
│   │
│   ├─► Before submit button?
│   │   └─► before_submit
│   │       - Last chance to validate
│   │       - Can block with frappe.throw()
│   │
│   ├─► After submit?
│   │   └─► on_submit
│   │       - Create GL entries here
│   │       - Create linked docs
│   │
│   ├─► Before cancel?
│   │   └─► before_cancel
│   │       - Validate cancel allowed
│   │
│   ├─► After cancel?
│   │   └─► on_cancel
│   │       - Reverse GL entries here
│   │       - Update linked docs
│   │
│   ├─► Before amend?
│   │   └─► before_update_after_submit
│   │
│   └─► After amend?
│       └─► on_update_after_submit
│
├─► DELETION
│   │
│   ├─► Before delete (can prevent)?
│   │   └─► on_trash
│   │       - frappe.throw() blocks delete
│   │       - Cleanup linked data
│   │
│   └─► After delete (cleanup)?
│       └─► after_delete
│           - Document already gone
│           - External cleanup only
│
└─► RENAME
    │
    ├─► Before rename?
    │   └─► before_rename(doc, method, old, new, merge)
    │
    └─► After rename?
        └─► after_rename(doc, method, old, new, merge)
```

### Execution Order

```
DOCUMENT SAVE FLOW:
1. before_validate
2. validate
3. before_insert (new docs only)
4. [Database INSERT/UPDATE]
5. after_insert (new docs only)
6. on_update
7. on_change

SUBMIT FLOW:
1. before_submit
2. [Status → Submitted]
3. on_submit
4. on_change

CANCEL FLOW:
1. before_cancel
2. [Status → Cancelled]
3. on_cancel
4. on_change
```

---

## Section 2: Scheduler Events

### Frequency Selection

```
HOW OFTEN SHOULD THE TASK RUN?
│
├─► Every ~60 seconds (V16) / ~4 min (V14/V15)
│   └─► all
│       ⚠️ Very frequent - use sparingly
│
├─► Every hour
│   ├─► Task < 5 min → hourly
│   └─► Task 5-25 min → hourly_long
│
├─► Every day
│   ├─► Task < 5 min → daily
│   └─► Task 5-25 min → daily_long
│
├─► Every week
│   ├─► Task < 5 min → weekly
│   └─► Task 5-25 min → weekly_long
│
├─► Every month
│   ├─► Task < 5 min → monthly
│   └─► Task 5-25 min → monthly_long
│
└─► Specific time (cron syntax)
    └─► cron: {"0 9 * * 1-5": [...]}
        Examples:
        - "*/15 * * * *"  → Every 15 minutes
        - "0 9 * * *"     → Daily at 9 AM
        - "0 9 * * 1-5"   → Weekdays at 9 AM
        - "0 0 1 * *"     → First of month midnight
        - "30 17 * * 5"   → Friday 5:30 PM
```

### Queue Selection

```
HOW LONG DOES YOUR TASK TAKE?
│
├─► Under 5 minutes
│   └─► Standard events (hourly, daily, cron, etc.)
│       Queue: default
│       Timeout: 5 minutes
│
├─► 5-25 minutes
│   └─► Long events (hourly_long, daily_long, etc.)
│       Queue: long
│       Timeout: 25 minutes
│
└─► Over 25 minutes
    └─► Split into smaller tasks OR
        Use frappe.enqueue() with custom timeout
```

---

## Section 3: Override Hooks

### Controller Override Selection (Critical for V16)

```
FRAPPE VERSION?
│
├─► V16 or later
│   │
│   │ WHAT DO YOU NEED?
│   │
│   ├─► ADD functionality (properties, methods)?
│   │   └─► extend_doctype_class ✅ RECOMMENDED
│   │       - Multiple apps can extend same DocType
│   │       - All extensions active simultaneously
│   │       - Safer upgrades
│   │
│   ├─► REPLACE functionality completely?
│   │   └─► override_doctype_class
│   │       - Last app wins (others ignored)
│   │       - Risky on updates
│   │       - Use only when necessary
│   │
│   └─► Not sure?
│       └─► Start with extend_doctype_class
│           Fall back to override if needed
│
└─► V14 or V15
    └─► override_doctype_class (only option)
        ⚠️ Last installed app wins
        ⚠️ Multiple apps = conflicts
```

### API Override Selection

```
WHAT ARE YOU MODIFYING?
│
├─► Existing whitelisted API method?
│   └─► override_whitelisted_methods
│       - Must match EXACT signature
│       - Last app wins
│
├─► Form UI behavior?
│   └─► doctype_js
│       - Add JS to specific forms
│       - Extends, doesn't replace
│
└─► Need completely new API?
    └─► Create new whitelisted method
        (Not an override)
```

---

## Section 4: Permission Hooks

```
WHAT PERMISSION LOGIC DO YOU NEED?
│
├─► Filter LIST views (who sees what records)?
│   └─► permission_query_conditions
│       - Returns SQL WHERE clause
│       - Only affects get_list, NOT get_all
│       - Good for: territory-based, role-based filtering
│
├─► Control individual DOCUMENT access?
│   └─► has_permission
│       - Called for each document access
│       - Return True/False/None
│       - Can only DENY, not grant extra permissions
│       - Good for: status-based, dynamic conditions
│
└─► Both?
    └─► Use both hooks
        - permission_query for lists
        - has_permission for documents
```

---

## Section 5: Client Data (extend_bootinfo)

```
DO YOU NEED TO SEND DATA TO CLIENT ON PAGE LOAD?
│
├─► Yes - Configuration/settings
│   └─► extend_bootinfo
│       - Adds to frappe.boot object
│       - Available in all JS
│       ⚠️ Never send sensitive data
│
└─► Yes - But only for specific forms
    └─► Fetch via frappe.call instead
        - More secure
        - On-demand loading
```

---

## Section 6: Assets & Configuration

### Asset Includes

```
WHERE DO YOU NEED JS/CSS?
│
├─► Desk (backend/admin interface)
│   ├─► Global JS → app_include_js
│   ├─► Global CSS → app_include_css
│   └─► Specific form → doctype_js
│
└─► Portal (website/frontend)
    ├─► Global JS → web_include_js
    └─► Global CSS → web_include_css
```

### Fixtures

```
WHAT DO YOU NEED TO EXPORT/IMPORT?
│
├─► Custom Fields you created?
│   └─► fixtures: [{"dt": "Custom Field", "filters": [...]}]
│
├─► Property Setters (field modifications)?
│   └─► fixtures: [{"dt": "Property Setter", "filters": [...]}]
│
├─► Custom Roles?
│   └─► fixtures: [{"dt": "Role", "filters": [...]}]
│
├─► Custom DocTypes?
│   └─► fixtures: [{"dt": "DocType", "filters": [...]}]
│
└─► Other configuration data?
    └─► fixtures: [{"dt": "Your DocType", "filters": [...]}]

⚠️ Always use filters to scope to your app
```

---

## Quick Selection Matrix

| Need | Hook |
|------|------|
| Validate before save | `doc_events.validate` |
| After save notification | `doc_events.on_update` |
| Daily cleanup | `scheduler_events.daily` |
| Heavy daily task | `scheduler_events.daily_long` |
| 9 AM weekday report | `scheduler_events.cron` |
| Extend Sales Invoice (V16) | `extend_doctype_class` |
| Override Sales Invoice (V14/15) | `override_doctype_class` |
| Custom API behavior | `override_whitelisted_methods` |
| Filter list by user | `permission_query_conditions` |
| Block edit on status | `has_permission` |
| Client-side config | `extend_bootinfo` |
| Export Custom Fields | `fixtures` |
| Add global JS | `app_include_js` |
| Extend form JS | `doctype_js` |
