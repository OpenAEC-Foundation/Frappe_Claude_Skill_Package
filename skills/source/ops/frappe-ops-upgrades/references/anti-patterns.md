# Upgrade Anti-Patterns

## Anti-Pattern 1: Skipping Multiple Major Versions

```
WRONG: Upgrading directly from v13 → v15
```

**Why it breaks**: Each major version has patches that depend on the previous version's schema. Skipping versions causes missing patches and schema mismatches.

**Correct approach**: ALWAYS upgrade one major version at a time: v13 → v14 → v15 → v16.

---

## Anti-Pattern 2: Upgrading Production Without Staging Test

```
WRONG: bench switch-to-branch version-15 frappe erpnext  # on production
       bench update
```

**Why it breaks**: Custom apps may use deprecated APIs, custom scripts may fail, data patches may encounter unexpected data states.

**Correct approach**: ALWAYS clone production to staging, test the full upgrade there, then apply to production.

---

## Anti-Pattern 3: Forgetting to Enable Server Scripts After v15

```
WRONG: Upgrade to v15, wonder why Server Scripts stopped working
```

**Why it breaks**: v15 disables Server Scripts by default for security.

**Correct approach**: After v15 upgrade, explicitly enable if needed:
```bash
bench set-config -g server_script_enabled 1
```

---

## Anti-Pattern 4: Not Checking Python/Node Versions

```
WRONG: Upgrade to v16 while running Node 18 and Python 3.10
```

**Why it breaks**: v16 requires Node 24+ and Python 3.14+. Build and runtime failures occur.

**Correct approach**: ALWAYS upgrade system dependencies BEFORE switching app branches.

---

## Anti-Pattern 5: Running `bench migrate` After Rollback

```
WRONG: Restore old backup → bench migrate
```

**Why it breaks**: The restored database already has the correct schema for the old version. Running migrate with new code expectations corrupts data.

**Correct approach**: After restoring a backup and switching to the old branch, run `bench build` and `bench setup requirements` only. NEVER run `bench migrate`.

---

## Anti-Pattern 6: Ignoring patches.txt Section Order

```
WRONG: Putting schema-dependent patches in [pre_model_sync]
```

**Why it breaks**: `[pre_model_sync]` patches run BEFORE schema sync. If your patch references new fields, they do not exist yet.

**Correct approach**: Use `[pre_model_sync]` for data preparation and `[post_model_sync]` for data that needs the new schema.

---

## Anti-Pattern 7: Not Backing Up Files With Database

```
WRONG: bench --site mysite backup  # database only
```

**Why it breaks**: File references in the database point to files on disk. Restoring database without files creates broken links.

**Correct approach**: ALWAYS use `--with-files` for pre-upgrade backups:
```bash
bench --site mysite backup --with-files
```

---

## Anti-Pattern 8: Using `bench update --reset` in Production

```
WRONG: bench update --reset  # on production with local patches
```

**Why it breaks**: `--reset` runs `git reset --hard`, destroying ALL local changes including custom patches and hotfixes.

**Correct approach**: NEVER use `--reset` in production. Resolve git conflicts manually or maintain changes in a proper branch.

---

## Anti-Pattern 9: Not Reloading DocType in Patches

```python
# WRONG:
def execute():
    # Trying to use new field without reload
    for doc in frappe.get_all("Sales Invoice", fields=["new_field"]):
        pass  # Fails: new_field doesn't exist in old schema
```

**Correct approach**: ALWAYS reload the DocType before accessing new fields:
```python
def execute():
    frappe.reload_doc("accounts", "doctype", "sales_invoice")
    for doc in frappe.get_all("Sales Invoice", fields=["new_field"]):
        pass
```

---

## Anti-Pattern 10: Upgrading Without Checking Custom App Compatibility

```
WRONG: Switch branch → bench update → discover custom app breaks
```

**Why it breaks**: Custom apps may use deprecated APIs, removed hooks, or incompatible Vue 2 components.

**Correct approach**: ALWAYS audit custom apps BEFORE switching branches. Search for deprecated APIs listed in breaking changes, fix them, commit, then upgrade.
