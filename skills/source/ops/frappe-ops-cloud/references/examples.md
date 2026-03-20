# Frappe Cloud Examples

## Example 1: Setting Up a New Production Site on Frappe Cloud

### Step-by-Step Workflow

1. **Create account** at `frappecloud.com`
2. **Add your app** (if custom):
   - Go to Apps → Add App
   - Enter GitHub repo URL and branch
   - Wait for initial build to complete
3. **Create a bench** (or use shared):
   - Go to Benches → New Bench
   - Select Frappe version (e.g., version-15)
   - Add apps: frappe, erpnext, your-custom-app
   - Choose region closest to your users
4. **Create a site**:
   - Go to Sites → New Site
   - Select the bench
   - Choose a plan
   - Set subdomain (e.g., `mycompany.frappe.cloud`)
   - Select apps to install
   - Click Create
5. **Configure custom domain**:
   - Site → Domains → Add Domain
   - Enter `erp.mycompany.com`
   - Add CNAME record in your DNS provider:
     ```
     erp.mycompany.com  CNAME  mycompany.frappe.cloud
     ```
   - Wait for DNS propagation and SSL provisioning

---

## Example 2: Deploying a Custom App Update

### Via GitHub Integration

```
1. Push code to your app's GitHub repository (configured branch)
2. Frappe Cloud detects the push
3. Navigate to Benches → Your Bench → Updates
4. Click "Deploy" to trigger rebuild
5. Wait for build to complete
6. Sites on the bench are automatically migrated
```

### Manual Trigger

```
1. Navigate to Benches → Your Bench
2. Click "Update Available" indicator
3. Review changes
4. Click "Deploy" to start update
5. Monitor build progress in the dashboard
```

---

## Example 3: Staging → Production Workflow

```
1. Create a staging site on the same bench:
   - Sites → New Site → "staging.mycompany.frappe.cloud"
   - Install same apps as production

2. Test updates on staging first:
   - Deploy app update to bench
   - Staging site receives the update
   - Test critical workflows

3. If staging passes:
   - Production site is already updated (same bench)

4. For isolated testing (different app versions):
   - Create a separate private bench for staging
   - Deploy new version to staging bench only
   - After testing, update production bench
```

---

## Example 4: Restoring a Site from Backup

```
1. Navigate to Sites → Your Site → Backups
2. Find the backup you want to restore
3. Click "Restore" on the desired backup
4. Confirm the restore operation
5. Wait for restore to complete (site is offline during restore)
6. Verify site functionality after restore
```

### Restoring to a New Site

```
1. Download backup files from the old site's Backups section
2. Create a new site on Frappe Cloud
3. Use the "Restore" option during site creation
4. Upload the backup files
5. Wait for provisioning and restore
```

---

## Example 5: Setting Up Environment Variables (Private Bench)

```
1. Navigate to Benches → Your Private Bench
2. Go to Configuration → Environment Variables
3. Add variables:
   - STRIPE_SECRET_KEY = sk_live_xxx
   - SENTRY_DSN = https://xxx@sentry.io/123
   - CUSTOM_API_ENDPOINT = https://api.example.com
4. Save and restart bench
```

**For shared benches**: Use `site_config.json` via the dashboard instead:
```
1. Navigate to Sites → Your Site → Site Config
2. Add key-value pairs
3. Save (takes effect after next request)
```

---

## Example 6: Monitoring and Debugging

### Viewing Application Logs

```
1. Navigate to Sites → Your Site → Logs
2. Select log type:
   - frappe.log — Application logs
   - worker.log — Background job logs
   - scheduler.log — Scheduler event logs
3. Filter by date range and severity
```

### Debugging via SSH (Private Bench Only)

```
1. Navigate to Benches → Your Private Bench → SSH
2. Click "Enable SSH Access"
3. Add your SSH public key
4. Connect:
   ssh frappe@your-bench-server.frappe.cloud

5. Inside SSH session:
   cd frappe-bench
   bench --site yoursite console
   >>> frappe.get_doc("Error Log", {"error": ("like", "%specific error%")})
```

### Database Analysis

```
1. Navigate to DevOps → Database Analyzer
2. Select your site
3. Run queries:
   - Slow query analysis
   - Index usage statistics
   - Table size breakdown
```

---

## Example 7: Migrating from Self-Hosted to Frappe Cloud

```bash
# On self-hosted server:
# 1. Create full backup
bench --site mysite backup --with-files

# 2. Download backup files:
#    - database.sql.gz
#    - files.tar
#    - private-files.tar

# On Frappe Cloud:
# 3. Create new site (same Frappe/ERPNext version)
# 4. Go to Sites → New Site → "Restore from backup"
# 5. Upload the three backup files
# 6. Wait for restore to complete
# 7. Verify data and functionality
# 8. Configure custom domain
# 9. Switch DNS from old server to Frappe Cloud
```

---

## Example 8: Frappe Cloud API Usage

### Accessing Frappe Cloud API

Frappe Cloud exposes a REST API for programmatic management:

```bash
# List your sites
curl -H "Authorization: token api_key:api_secret" \
  https://frappecloud.com/api/method/press.api.site.all

# Get site details
curl -H "Authorization: token api_key:api_secret" \
  https://frappecloud.com/api/method/press.api.site.get \
  -d "name=mysite.frappe.cloud"

# Create a backup
curl -X POST \
  -H "Authorization: token api_key:api_secret" \
  https://frappecloud.com/api/method/press.api.site.backup \
  -d "name=mysite.frappe.cloud"
```

**Note**: API availability and endpoints may change. ALWAYS check the latest Frappe Cloud documentation for current API reference.
