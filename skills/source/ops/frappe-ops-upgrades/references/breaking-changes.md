# Breaking Changes Reference

## v14 → v15 Complete Breaking Changes

### Removed Python APIs

| Removed | Replacement |
|---------|-------------|
| `frappe.db.set()` | `doc.db_set()` |
| `frappe.db.touch()` | No replacement needed |
| `frappe.db.clear_table()` | Direct SQL or custom logic |
| `frappe.db.update()` | `frappe.db.set_value()` |
| `frappe.db.set_temp()` / `get_temp()` | Use `frappe.cache` |
| `frappe.db.sql(as_utf8=True)` | Remove parameter |
| `frappe.db.sql(formatted=True)` | Remove parameter |
| `frappe.db.set_value()` for Singles | `frappe.db.set_single_value()` |
| `frappe.db.set_value(for_update=True)` | Remove parameter |
| `frappe.compare()` | `from frappe.utils import compare` |
| `frappe.local.rollback_observers` | DB transaction hooks |
| `frappe.db.add_before_commit` | DB transaction hooks |

### Changed Python APIs

| API | Change |
|-----|--------|
| `frappe.new_doc()` | `parent_doc`, `parentfield`, `as_dict` MUST be kwargs |
| `frappe.get_installed_apps()` | `sort`, `frappe_last` args removed |
| `enqueue(job_name=...)` | Use `job_id` parameter instead |
| `get_year_ending()` | Returns `datetime.date` instead of string |
| `get_timespan_date_range()` | Returns `datetime.date` tuples |
| `convert_utc_to_user_timezone()` | Renamed to `convert_utc_to_system_timezone()` |
| `get_time_zone()` | Renamed to `get_system_timezone()` |
| `validate_from_to_dates()` | Skips validation if either date is empty |
| Method override execution | Last override takes precedence (was first) |
| `search_link()` / `search_widget()` | Returns `message` key instead of custom keys |

### Removed Frontend APIs

| Removed | Replacement |
|---------|-------------|
| `window.get_today` | `frappe.datetime.get_today` |
| `window.show_alert` | `frappe.show_alert` |
| `window.user` | `frappe.session.user` |
| `window.roles` | `frappe.user_roles` |
| Query report globals | `frappe.query_report.get_filter_value()` |
| `this` in Client Scripts | Not supported; use `cur_frm` |
| `<div class="website-image-lazy">` | `<img loading="lazy">` |

### Vue Migration (v2 → v3)

| Package | v14 Version | v15 Version |
|---------|-------------|-------------|
| Vue | 2.x | **3.x** |
| Vuex | 3.x | **4.0.2** |
| vue-router | 2.x | **4.1.5** |
| vuedraggable | 2.24.3 | **4.1.0** |

### Configuration Changes

| Change | Details |
|--------|---------|
| Server Scripts | Disabled by default; enable with `server_script_enabled` |
| "Desk User" role | New catch-all role for desk users |
| `currentsite.txt` | No longer sets default site |
| Node.js minimum | v18 (was v14) |
| Python packaging | `pyproject.toml` (was `setup.py`) |
| Build flags | `--make_copy`, `--restore` removed; use `--hard-link` |
| SocketIO | Requires namespacing: `io('${url}/${frappe.local.site}')` |

### Removed Features

- Event Streaming (moved to separate app)
- Cordova support
- `/fixtures/custom_scripts` import
- "Error Snapshot" DocType (use Error Log)
- Session device differentiation

### Removed Python Dependencies

No longer available for indirect import: `googlemaps`, `urllib3`, `gitdb`, `pyasn1`, `pypng`, `google-auth-httplib2`, `schedule`, `pycryptodome`.

---

## v15 → v16 Complete Breaking Changes

### Removed/Separated Modules

| Module | New App Repository |
|--------|-------------------|
| Energy Points | `frappe/eps` |
| Newsletter | `frappe/newsletter` |
| Backup Integrations | `frappe/offsite_backups` |
| Blog | `frappe/blog` |

### Changed Python APIs

| API | Change |
|-----|--------|
| Default sort order | `creation` instead of `modified` for all list queries |
| `has_permission` hooks | MUST return explicit `True`; `None` not accepted |
| `frappe.get_doc(dt, name, field=val)` | No longer updates values |
| `frappe.sendmail(now=True)` | No longer commits transactions |
| `db.get_value()` for Singles | Returns proper types (not strings) |
| `db.value_cache` | Changed to nested defaultdict |
| `db.count(cache=True)` | Uses transaction cache instead of Redis |
| `!=None` condition | Correctly generates `IS NOT NULL` |
| `meta.get_valid_columns()` | Excludes virtual fields |
| `frappe.flags.in_test` | Deprecated; use `frappe.in_test` |
| `site_cache` decorator | No longer supports unhashable args (dicts) |
| Document hooks | DB commits not allowed (data integrity) |
| State-changing methods | MUST use POST (`/api/method/logout`, etc.) |
| `override_doctype` classes | MUST inherit from overridden class |

### Removed Translation APIs

| Removed | Details |
|---------|---------|
| `get_translated_dict` hook | Removed entirely |
| `frappe.get_lang_dict()` | Removed |
| `doc.meta.__messages` | No longer holds doc-specific translations |
| Currency/timezone translations | No longer translated |

### Frontend Changes

| Change | Details |
|--------|---------|
| Report/Dashboard/Page JS | Evaluated as IIFEs (no global scope) |
| Awesome Bar | Redesigned, moved to sidebar (`Cmd+K`) |
| List view sidebar | Removed; filters moved to top |
| Map view | Paginated (20 items, not all) |
| `/apps` endpoint | Deprecated; `/app` → `/desk` |

### Configuration Changes

| Change | Details |
|--------|---------|
| Site config caching | Cached up to 1 minute |
| Country field | Requires ISO 3166 ALPHA-2 code |
| Time field default | Removed; only "Now" option sets current time |
| `bench version` output | "plain" format default; use `-f legacy` |
| System Console | Restricted to Administrator |

### Removed DocTypes

- Transaction Log (was France/Germany compliance)

### Removed Features

- GeoIP MaxMind database features
