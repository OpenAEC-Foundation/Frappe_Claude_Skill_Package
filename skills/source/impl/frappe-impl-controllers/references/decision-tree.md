# Controller Hook Decision Tree

## Master Decision: Which Hook?

```
WHAT DO YOU WANT TO ACHIEVE?

 VALIDATION & CALCULATIONS
 ├── Validate field values?                          → validate
 ├── Auto-calculate totals/percentages?              → validate (changes saved)
 ├── Set default values before validation?           → before_validate
 └── Pre-validation setup (rarely needed)?           → before_validate

 POST-SAVE ACTIONS
 ├── Send email notifications?                       → on_update
 ├── Update linked/related documents?                → on_update
 ├── Create audit log?                               → on_update
 └── Trigger webhook / external API?                 → on_update (or enqueue)

 NEW DOCUMENT ONLY
 ├── Action only on creation (not updates)?          → after_insert
 ├── Create related document on first save?          → after_insert
 ├── Generate custom document name?                  → autoname
 ├── Modify naming parameters?                       → before_naming
 └── Setup before any validation (new only)?         → before_insert

 SUBMITTABLE DOCUMENTS
 ├── Additional validation before submit?            → before_submit
 ├── Create ledger entries / update stock?           → on_submit
 ├── Prevent cancel under conditions?                → before_cancel
 ├── Reverse ledger entries / restore stock?         → on_cancel
 └── Action when submitted doc updated?              → on_update_after_submit

 DELETE / RENAME
 ├── Prevent delete under conditions?                → on_trash (throw)
 ├── Cleanup before delete?                          → on_trash
 ├── Post-delete actions?                            → after_delete
 ├── Before rename validation?                       → before_rename
 └── Update references after rename?                 → after_rename

 SPECIAL CASES
 ├── Detect ANY change (including db_set)?           → on_change
 ├── Modify print output?                            → before_print
 └── Draft discard (v15+)?                           → before_discard / on_discard
```

## Complete Hook Reference

### Standard Hooks (All DocTypes)

| Hook | Timing | Changes Saved? | Primary Use |
|------|--------|----------------|-------------|
| `before_insert` | Before new doc processing | Yes | Setup for new docs |
| `before_naming` | Before name generated | Yes | Modify naming_series |
| `autoname` | Generate document name | Yes (name) | Custom naming logic |
| `before_validate` | Before validation | Yes | Pre-validation defaults |
| `validate` | Main validation | **Yes** | Validation + calculations |
| `before_save` | After validate, before DB | Yes | Final adjustments |
| `after_insert` | After first DB insert | **No** | Creation-only actions |
| `on_update` | After every DB save | **No** | Post-save actions |
| `on_change` | After any change | No | Universal change detection |
| `before_rename` | Before name change | N/A | Rename validation |
| `after_rename` | After name changed | No | Update references |
| `on_trash` | Before delete | N/A | Cleanup, prevent delete |
| `after_delete` | After deleted | N/A | Post-delete cleanup |
| `before_print` | Before print render | N/A | Modify print data |

### Submittable Document Hooks

| Hook | Timing | Primary Use |
|------|--------|-------------|
| `before_submit` | Before docstatus=1 | Submit validation |
| `on_submit` | After docstatus=1 | Ledger entries, stock |
| `before_cancel` | Before docstatus=2 | Cancel validation |
| `on_cancel` | After docstatus=2 | Reverse entries |
| `before_update_after_submit` | Before submitted doc update | Validate changes |
| `on_update_after_submit` | After submitted doc update | Post-update actions |

### v15+ Hooks

| Hook | Timing | Primary Use |
|------|--------|-------------|
| `before_discard` | Before draft discard | Prevent discard |
| `on_discard` | After draft discarded | Cleanup |

## Execution Order Diagrams

### INSERT (New Document)
```
doc.insert()
    ▼
before_insert    ← Setup for new doc
    ▼
before_naming    ← Modify naming params
    ▼
autoname         ← Generate doc name
    ▼
before_validate  ← Pre-validation setup
    ▼
validate         ← Main validation + calc [changes SAVED]
    ▼
before_save      ← Final adjustments
    ▼
[DB INSERT]
    ▼
after_insert     ← Creation-only actions [changes NOT saved]
    ▼
on_update        ← Post-save actions [changes NOT saved]
    ▼
on_change        ← Universal change hook
```

### SAVE (Existing Document)
```
doc.save()
    ▼
before_validate  [changes SAVED]
    ▼
validate         [changes SAVED]
    ▼
before_save      [changes SAVED]
    ▼
[DB UPDATE]
    ▼
on_update        [changes NOT saved — use db_set]
    ▼
on_change
```

### SUBMIT
```
doc.submit()
    ▼
validate         ← Standard validation
    ▼
before_submit    ← Submit-specific checks (throw to abort)
    ▼
[DB: docstatus=1]
    ▼
on_update
    ▼
on_submit        ← Ledger entries, stock updates
    ▼
on_change
```

### CANCEL
```
doc.cancel()
    ▼
before_cancel    ← Prevent cancel (throw)
    ▼
[DB: docstatus=2]
    ▼
on_cancel        ← Reverse entries
    ▼
[check_no_back_links]
    ▼
on_change
```

### DELETE
```
doc.delete()
    ▼
on_trash         ← Cleanup / prevent (throw)
    ▼
[DB DELETE]
    ▼
after_delete     ← Post-delete cleanup
```

## Quick Selection Guide

| I want to... | Use hook |
|--------------|----------|
| Prevent save if invalid | `validate` + `frappe.throw()` |
| Auto-fill a field | `validate` |
| Send email after save | `on_update` |
| Create linked doc on first save | `after_insert` |
| Custom document naming | `autoname` |
| Prevent delete | `on_trash` + `frappe.throw()` |
| Detect changes via db_set | `on_change` |
| Prevent submit | `before_submit` + `frappe.throw()` |
| Create GL entries on submit | `on_submit` |
| Reverse GL on cancel | `on_cancel` |
| Modify print data | `before_print` |
