# Migration Checklists

## Pre-Migration Checklist

ALWAYS complete ALL items before starting any migration:

### Infrastructure Requirements

#### v14 → v15
- [ ] Python >= 3.10 installed
- [ ] Node.js >= 16 installed
- [ ] MariaDB >= 10.6 installed
- [ ] Redis >= 6 installed
- [ ] pip packages updated: `bench pip install --upgrade pip setuptools`
- [ ] Disk space: minimum 2x database size free

#### v15 → v16
- [ ] Python >= 3.11 installed
- [ ] Node.js >= 18 installed
- [ ] MariaDB >= 10.6 installed
- [ ] Redis >= 7 installed
- [ ] pip packages updated: `bench pip install --upgrade pip setuptools`
- [ ] Disk space: minimum 2x database size free

### Backup Verification
- [ ] Full database backup completed: `bench --site {site} backup`
- [ ] File backup completed: `bench --site {site} backup --with-files`
- [ ] Backup file verified (not corrupt): test restore on separate instance
- [ ] Backup stored in separate location (not on same server)
- [ ] Backup timestamp recorded in migration log

### Code Freeze
- [ ] All custom app changes committed and pushed
- [ ] No in-progress features in custom apps
- [ ] All pull requests merged or deferred
- [ ] Git tags created for current version of each custom app

### Communication
- [ ] Maintenance window scheduled with stakeholders
- [ ] Users notified of downtime
- [ ] Rollback plan documented and reviewed

## Custom App Scan Checklist

For EACH custom app, complete this scan:

### Python Code Scan
- [ ] `grep -rn "import" hooks.py` — verify all imports resolve
- [ ] `grep -rn "doc_events" hooks.py` — check for method overrides
- [ ] `grep -rn "scheduler_events" hooks.py` — review timing
- [ ] `grep -rn "frappe.enqueue" --include="*.py"` — check job patterns
- [ ] `grep -rn "frappe.db.sql" --include="*.py"` — check raw SQL compatibility
- [ ] `grep -rn "frappe.whitelist" --include="*.py"` — verify decorators
- [ ] `grep -rn "frappe.throw\|frappe.msgprint" --include="*.py"` — check error handling

### JavaScript Code Scan
- [ ] `grep -rn "cur_frm" --include="*.js"` — deprecated, use `frm`
- [ ] `grep -rn "cur_page" --include="*.js"` — deprecated in v15+
- [ ] `grep -rn "frappe.set_route" --include="*.js"` — check signature
- [ ] `grep -rn "frappe.call" --include="*.js"` — verify async patterns
- [ ] `grep -rn "frappe.db\." --include="*.js"` — should not exist in Client Scripts

### Configuration Scan
- [ ] `hooks.py` syntax is valid Python
- [ ] All function paths in `hooks.py` point to existing functions
- [ ] `required_apps` lists all dependencies
- [ ] `fixtures` export format is compatible
- [ ] `patches.txt` or `patches/` directory structure is correct

## Migration Execution Checklist

### Phase 1: Staging Migration
- [ ] Staging environment created (separate from production)
- [ ] Production backup restored on staging
- [ ] Branch switched: `bench switch-to-branch version-{target} frappe erpnext`
- [ ] Custom apps updated to compatible branches
- [ ] Dependencies installed: `bench setup requirements`
- [ ] Migration executed: `bench --site {site} migrate`
- [ ] Assets rebuilt: `bench build`
- [ ] No errors in migration output

### Phase 2: Staging Testing
- [ ] All DocTypes open without errors
- [ ] Create, read, update, delete operations work for key DocTypes
- [ ] All print formats render correctly (visual check)
- [ ] All workflows transition correctly
- [ ] All scheduled jobs execute (check scheduler.log)
- [ ] All custom reports generate without errors
- [ ] All API endpoints respond (test with curl/Postman)
- [ ] User permissions work correctly (test with different roles)
- [ ] File upload/download works
- [ ] Email sending works (test with test email)
- [ ] Page load time acceptable (< 3 seconds for main forms)
- [ ] Background jobs complete successfully

### Phase 3: Production Migration
- [ ] Maintenance mode enabled: `bench --site {site} set-maintenance-mode on`
- [ ] Final backup taken (with files)
- [ ] All services stopped (workers, scheduler)
- [ ] Branch switched on production
- [ ] `bench setup requirements` completed
- [ ] `bench --site {site} migrate` completed without errors
- [ ] `bench build --production` completed
- [ ] Services restarted
- [ ] Maintenance mode disabled
- [ ] Quick smoke test passed (login, open key DocTypes)

## Post-Migration Checklist

### Immediate (First Hour)
- [ ] Login works for admin user
- [ ] Login works for regular users (test 2-3 different roles)
- [ ] Key business DocTypes open correctly
- [ ] No new entries in Error Log DocType
- [ ] Scheduler is running: `bench doctor`
- [ ] Workers are processing jobs

### First Day
- [ ] All daily scheduled tasks executed
- [ ] No user-reported errors
- [ ] Email notifications sending correctly
- [ ] Print formats generating correctly
- [ ] API integrations working
- [ ] Performance baseline acceptable

### First Week
- [ ] All weekly scheduled tasks executed
- [ ] Error Log reviewed — no recurring patterns
- [ ] User feedback collected
- [ ] Performance monitored — no degradation
- [ ] Backup schedule confirmed working on new version

## Rollback Decision Checklist

Rollback IMMEDIATELY if ANY of these are true:

- [ ] Users cannot log in
- [ ] Key business processes are blocked (invoicing, ordering, etc.)
- [ ] Data corruption detected
- [ ] More than 3 CRITICAL errors in Error Log within first hour
- [ ] Performance degradation > 50% (page loads > 6 seconds)
- [ ] Scheduled jobs failing repeatedly
- [ ] External integrations broken with no quick fix

Rollback is NOT needed if:

- [ ] Only cosmetic issues (CSS, layout)
- [ ] Single non-critical report failing
- [ ] Warning messages (not errors) in logs
- [ ] Minor performance difference (< 20%)
