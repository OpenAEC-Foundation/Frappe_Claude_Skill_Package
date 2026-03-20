# Decision Tree: Client Script Events

## Level 1: Client or Server?

```
WHERE SHOULD THE LOGIC RUN?
│
├── Only when user opens/edits the form in browser?
│   └── CLIENT SCRIPT
│
├── Also on API calls, imports, Data Import Tool?
│   └── SERVER SCRIPT or CONTROLLER
│
├── Critical business rule that must NEVER be skipped?
│   └── SERVER (controller validate / before_save)
│
└── UX improvement (speed, visual feedback)?
    └── CLIENT SCRIPT (+ optional server backup)
```

## Level 2: Which Client Event?

```
WHAT IS THE GOAL?

INITIALIZATION
├── One-time setup (link filters)?
│   └── setup — ALWAYS use for set_query
├── UI initialization on form load?
│   └── onload — fires once per form load
└── Actions after complete DOM render?
    └── onload_post_render — DOM fully available

UI MANIPULATION
├── Add custom buttons?
│   └── refresh — re-added after each render cycle
├── Show/hide fields?
│   └── refresh + {fieldname} — ALWAYS use both
├── Set indicator/intro text?
│   └── refresh
└── Adjust field properties (read_only, label)?
    └── refresh

DATA VALIDATION
├── Sync validation (data already available)?
│   └── validate — frappe.throw() stops save
├── Async validation (server check needed)?
│   └── validate with async/await
└── Pre-submit check?
    └── before_submit

POST-SAVE ACTIONS
├── UI update after save?
│   └── after_save
├── Redirect to another document?
│   └── after_save
└── Create follow-up document?
    └── after_save or on_submit

FIELD CHANGES
├── Respond to field change?
│   └── {fieldname}
├── Cascading changes (A → B → C)?
│   └── {fieldname} for each link in chain
└── Trigger calculation?
    └── {fieldname} for all input fields

CHILD TABLE
├── Row added?
│   └── {tablename}_add
├── Row removed?
│   └── {tablename}_remove
├── Before row removed (v15+)?
│   └── before_{tablename}_remove
├── Field in row changed?
│   └── ChildDocType: {fieldname}(frm, cdt, cdn)
└── Row reordered?
    └── {tablename}_move
```

## Event Timing Matrix

| Event | When | Can Stop Save? | Access To |
|-------|------|----------------|-----------|
| `setup` | Once on first form creation | No | frm (doc may be empty) |
| `before_load` | Before data loads from server | No | frm |
| `onload` | After data loaded, before render | No | frm, doc |
| `refresh` | After each render cycle | No | frm, doc, full UI |
| `onload_post_render` | After complete DOM render | No | frm, doc, DOM |
| `validate` | Before save request | YES (`frappe.throw`) | frm, doc |
| `before_save` | Just before save | YES (`frappe.throw`) | frm, doc |
| `after_save` | After successful save | No | frm, doc (saved) |
| `before_submit` | Before submit | YES (`frappe.throw`) | frm, doc (docstatus=0) |
| `on_submit` | After submit | No | frm, doc (docstatus=1) |
| `before_cancel` | Before cancel | YES (`frappe.throw`) | frm, doc |
| `after_cancel` | After cancel | No | frm, doc (docstatus=2) |
| `{fieldname}` | On field value change | No | frm, doc |
| `{table}_add` | Row added to child table | No | frm, cdt, cdn |
| `{table}_remove` | Row removed from child table | No | frm |
| `{table}_move` | Row reordered in child table | No | frm |

## Event Combination Patterns

### Pattern: Visibility Toggle
ALWAYS use both `refresh` and `{fieldname}`:
```
refresh(frm) → frm.trigger('controlling_field')
controlling_field(frm) → frm.toggle_display(...)
```

### Pattern: Cascading Filters
ALWAYS use `setup` + `{parent_field}`:
```
setup(frm) → frm.set_query('child_field', ...)
parent_field(frm) → frm.set_value('child_field', '')
```

### Pattern: Calculated Fields
ALWAYS use all input field handlers:
```
field_a(frm) → calculate(frm)
field_b(frm) → calculate(frm)
```

### Pattern: Child Table Totals
ALWAYS handle both change and remove:
```
ChildDocType.qty → calculate_row → calculate_totals
ChildDocType.rate → calculate_row → calculate_totals
ParentDocType.items_remove → calculate_totals
```

## Quick Reference

| I want to... | Event(s) |
|--------------|----------|
| Filter link field | `setup` |
| Add button | `refresh` |
| Hide field on condition | `refresh` + `{fieldname}` |
| Calculate value | `{input_fields}` |
| Validate before save | `validate` |
| Server check before save | `validate` (async) |
| Redirect after save | `after_save` |
| Calculate child table total | Child `{fieldname}` + Parent `{table}_remove` |
| Set default for new doc | `onload` (check `frm.is_new()`) |
| Custom keyboard shortcut | `onload` |
