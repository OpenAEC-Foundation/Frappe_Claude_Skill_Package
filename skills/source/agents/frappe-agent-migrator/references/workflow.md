# Migration Workflow — Detailed Steps

## Step 1: Identify Migration Path

### Input Requirements

ALWAYS collect this information before starting:

1. **Source version**: Exact Frappe and ERPNext versions (`bench version`)
2. **Target version**: Desired Frappe and ERPNext versions
3. **Custom apps**: List all installed custom apps (`bench --site {site} list-apps`)
4. **Environment**: Development, staging, or production
5. **Infrastructure**: OS, Python, Node.js, MariaDB, Redis versions

### Path Determination Rules

- NEVER skip major versions (v14 → v16 requires v14 → v15 → v16)
- ALWAYS migrate Frappe first, then ERPNext, then custom apps
- ALWAYS check if custom apps have version-specific branches
- For minor version jumps within same major (v15.20 → v15.30): direct upgrade is safe

### Version Branch Mapping

| Version | Frappe Branch | ERPNext Branch |
|---------|--------------|----------------|
| v14 | version-14 | version-14 |
| v15 | version-15 | version-15 |
| v16 | develop (or version-16) | develop (or version-16) |

## Step 2: Check Breaking Changes

### Process

For each version jump in the migration path:

1. Read the breaking changes table in SKILL.md for that version pair
2. Cross-reference with custom app functionality
3. Mark each breaking change as: AFFECTED / NOT AFFECTED / UNKNOWN
4. For UNKNOWN items: investigate further before proceeding

### Priority Classification

| Priority | Description | Action Required |
|----------|-------------|-----------------|
| CRITICAL | Will cause immediate failure | Fix BEFORE migration |
| HIGH | Will cause errors in specific workflows | Fix BEFORE or DURING migration |
| MEDIUM | May cause issues under certain conditions | Fix DURING or AFTER migration |
| LOW | Cosmetic or non-blocking | Fix AFTER migration |

## Step 3: Scan Custom Code

### Automated Scan Process

For EACH custom app, run the deprecated pattern grep commands from SKILL.md:

```bash
APP_PATH="apps/{app_name}/{app_name}"

# Run all pattern checks and save results
echo "=== Scanning $APP_PATH ==="

# Count total issues
ISSUES=0

# Run each grep pattern from SKILL.md Step 3
# Collect results into a report file
```

### Manual Review Items

After automated scan, ALWAYS manually check:

1. **hooks.py**: Read completely, check all function paths exist
2. **Custom DocType controllers**: Verify lifecycle method compatibility
3. **Custom reports**: Check query syntax and API usage
4. **Custom print formats**: Verify Jinja template compatibility
5. **Custom pages/workspace**: Check frontend API usage
6. **fixtures**: Verify fixture export format is compatible

## Step 4: Generate Migration Plan

### Plan Customization Rules

Adapt the template from SKILL.md based on:

| Factor | Impact on Plan |
|--------|----------------|
| Number of custom apps | More testing time needed per app |
| Data volume (>10GB) | Longer backup/restore, schedule accordingly |
| Active users (>100) | Longer maintenance window, more communication |
| Complex workflows | Dedicated workflow testing phase |
| External integrations | Integration testing phase |
| Multi-site setup | Per-site migration, staggered rollout |

### Timing Estimates

| Activity | Small Site (<1GB) | Medium Site (1-10GB) | Large Site (>10GB) |
|----------|-------------------|----------------------|--------------------|
| Full backup | 5 min | 30 min | 2+ hours |
| Migration command | 10 min | 30 min | 1+ hours |
| Build assets | 5 min | 5 min | 10 min |
| Basic verification | 15 min | 30 min | 1 hour |
| Full test suite | 1 hour | 2 hours | 4+ hours |

## Step 5: Generate Patch List

### Patch Generation Rules

For each issue found in Step 3:

1. Identify the exact file and line number
2. Show the current (broken) code
3. Show the corrected code for the target version
4. Note if the fix is backward-compatible (works on source version too)
5. Prioritize: CRITICAL fixes first, then HIGH, MEDIUM, LOW

### Backward-Compatible Fixes

ALWAYS prefer fixes that work on BOTH source and target versions:

```python
# Backward-compatible: works on v14, v15, and v16
import frappe
if hasattr(frappe, 'new_api'):
    frappe.new_api()
else:
    frappe.old_api()
```

### Version-Conditional Code

When backward compatibility is impossible:

```python
# hooks.py — version-conditional configuration
import frappe
frappe_version = int(frappe.__version__.split('.')[0])

if frappe_version >= 16:
    extend_doctype_class = {
        "Sales Invoice": "myapp.overrides.CustomSalesInvoice"
    }
else:
    doc_events = {
        "Sales Invoice": {
            "validate": "myapp.overrides.custom_validate"
        }
    }
```

## Rollback Procedures

### When to Rollback

ALWAYS rollback if ANY of these conditions are met:

- Critical business processes are broken
- Data integrity issues detected
- Performance degradation > 50%
- More than 3 CRITICAL errors found post-migration

### Rollback Steps

1. **Immediate**: Stop all services
2. **Restore**: Use the pre-migration backup (NEVER skip backup in Step 4)
3. **Revert**: Switch branches back to source version
4. **Migrate**: Run `bench migrate` on old version to ensure clean state
5. **Verify**: Run the same test checklist from Step 4 Phase 3
6. **Communicate**: Notify users of rollback and revised timeline

### Post-Rollback Analysis

After rollback, ALWAYS:

1. Document what went wrong
2. Identify which breaking change was missed
3. Update the patch list with additional fixes
4. Re-test on staging before next attempt
