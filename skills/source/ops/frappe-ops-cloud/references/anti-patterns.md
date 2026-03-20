# Frappe Cloud Anti-Patterns

## Anti-Pattern 1: Self-Hosting Press for a Single Site

```
WRONG: Setting up Press infrastructure to host one ERPNext instance
```

**Why it breaks**: Press requires multiple servers, Ansible, Docker, and ongoing maintenance. For a single site, this overhead is not justified.

**Correct approach**: Use `bench` directly for single-site self-hosting, or use Frappe Cloud shared bench.

---

## Anti-Pattern 2: Using A Records Instead of CNAME for Custom Domains

```
WRONG: erp.example.com  A  123.45.67.89
```

**Why it breaks**: Frappe Cloud's IP addresses can change. A records will break when infrastructure is migrated.

**Correct approach**: ALWAYS use CNAME records:
```
erp.example.com  CNAME  mysite.frappe.cloud
```

---

## Anti-Pattern 3: Editing Files via SSH on Frappe Cloud

```
WRONG: SSH into private bench → edit app source code directly
```

**Why it breaks**: Direct file edits are overwritten on the next deployment. Changes are not tracked in version control.

**Correct approach**: ALWAYS push changes to the GitHub repository. Frappe Cloud deploys from the repo.

---

## Anti-Pattern 4: Relying Solely on Frappe Cloud Backups

```
WRONG: Assuming Frappe Cloud backups are sufficient disaster recovery
```

**Why it breaks**: If your Frappe Cloud account is compromised, suspended, or experiences a billing issue, you may lose access to backups.

**Correct approach**: ALWAYS maintain off-platform backups:
- Download backups periodically from the dashboard
- Store in your own S3 bucket or local storage
- Test restore procedures regularly

---

## Anti-Pattern 5: Testing Updates on Production Directly

```
WRONG: Deploy new app version → production site updates → discover bugs
```

**Why it breaks**: On shared benches, all sites update together. A broken app affects all sites on the bench.

**Correct approach**: Use a staging site or separate staging bench to test updates before production.

---

## Anti-Pattern 6: Using Shared Bench for Sensitive Workloads

```
WRONG: Running medical/financial/legal ERPNext on a shared bench
```

**Why it breaks**: Shared benches share resources with other tenants. You have no SSH access, no control over updates, and limited isolation.

**Correct approach**: Use a private bench or dedicated server for sensitive workloads requiring compliance or performance guarantees.

---

## Anti-Pattern 7: Ignoring Frappe Cloud Plan Limits

```
WRONG: Running heavy background jobs on a basic plan → site becomes slow
```

**Why it breaks**: Each plan has CPU, memory, and storage limits. Exceeding them causes throttling or failures.

**Correct approach**: Monitor usage via the dashboard. Upgrade plans BEFORE hitting limits, not after performance degrades.

---

## Anti-Pattern 8: Disabling Scheduler on Frappe Cloud

```
WRONG: bench --site mysite scheduler disable  # via SSH
```

**Why it breaks**: Frappe Cloud manages the scheduler. Disabling it may interfere with Cloud's internal operations.

**Correct approach**: Use `pause_scheduler` via site config if you need to temporarily stop background jobs.

---

## Anti-Pattern 9: Not Setting Up Custom Domain Before Go-Live

```
WRONG: Launch on *.frappe.cloud domain → switch to custom domain later
```

**Why it breaks**: Changing the primary domain after go-live causes email delivery issues (SPF/DKIM), bookmark breakage, and OAuth redirect failures.

**Correct approach**: ALWAYS configure the custom domain and verify SSL BEFORE directing production traffic to the site.

---

## Anti-Pattern 10: Storing Secrets in site_config.json Without Private Bench

```
WRONG: Adding API keys to site_config.json on a shared bench
```

**Why it breaks**: On shared benches, site config is accessible to the hosting platform. For sensitive secrets, this may not meet security requirements.

**Correct approach**: For sensitive credentials, use a private bench with environment variables, or use an external secrets manager accessed via API.
