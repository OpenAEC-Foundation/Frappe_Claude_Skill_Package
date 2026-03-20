# Performance Anti-Patterns

## 1. Using default MariaDB settings in production

```ini
# WRONG — default innodb_buffer_pool_size is 128MB
# This causes excessive disk I/O on any non-trivial dataset

# CORRECT — set to 50-70% of RAM on dedicated DB server
[mysqld]
innodb_buffer_pool_size = 2G  # For 4GB RAM server
```

**Why**: The default 128MB buffer pool means MariaDB constantly reads from disk. This is the single biggest performance improvement for most Frappe installations.

## 2. No maxmemory on Redis cache

```conf
# WRONG — Redis grows unbounded, eventually triggers OOM killer
# (default: no memory limit)

# CORRECT — ALWAYS set maxmemory with eviction policy
maxmemory 512mb
maxmemory-policy allkeys-lru
```

**Why**: Without a limit, Redis cache consumes all available memory during heavy usage. The OOM killer then kills random processes, often taking down the entire application.

## 3. Too many Gunicorn workers for available RAM

```bash
# WRONG — 32 workers on a 4GB server
gunicorn -w 32 frappe.app:application
# 32 * 300MB = 9.6GB > 4GB → server swaps → everything slow

# CORRECT — calculate based on available RAM
# workers = min((2 * CPU + 1), (available_ram - db - redis - os) / 300MB)
gunicorn -w 5 frappe.app:application
```

**Why**: Each Gunicorn worker uses 150-300MB RAM. Overprovisioning causes swapping, which is orders of magnitude slower than RAM access.

## 4. N+1 query patterns in custom code

```python
# WRONG — N+1 queries (1 query + N queries in loop)
items = frappe.get_all("Item", fields=["name"])
for item in items:
    warehouse_qty = frappe.db.get_value("Bin",
        {"item_code": item.name, "warehouse": "Main"}, "actual_qty")
# 1001 queries for 1000 items!

# CORRECT — single query with join or get_all with filters
bins = frappe.get_all("Bin",
    filters={"warehouse": "Main"},
    fields=["item_code", "actual_qty"]
)
qty_map = {b.item_code: b.actual_qty for b in bins}
```

**Why**: Database roundtrip latency multiplied by N rows creates massive slowdowns. ALWAYS batch database calls.

## 5. Using get_value in loops instead of get_cached_value

```python
# WRONG — database hit every call
for invoice in invoices:
    customer_name = frappe.db.get_value("Customer", invoice.customer, "customer_name")

# CORRECT — cached lookup (Redis first, DB fallback)
for invoice in invoices:
    customer_name = frappe.db.get_cached_value("Customer", invoice.customer, "customer_name")
```

**Why**: `get_cached_value` checks Redis cache first. For repeated lookups of the same records, this eliminates redundant database queries.

## 6. Running bench clear-cache in production without understanding impact

```bash
# WRONG — clearing all caches during business hours
bench --site mysite.com clear-cache
# Every subsequent request is slow until cache rebuilds

# CORRECT — clear specific caches, or clear during off-peak
frappe.cache.delete_value("specific_key")  # Targeted
# OR schedule clear-cache during maintenance window
```

**Why**: `clear-cache` empties all Redis caches. Every page load, every API call must rebuild its cache from database. This causes a "thundering herd" effect.

## 7. Not using database indexes on filtered columns

```sql
-- WRONG — custom report filtering on unindexed columns
SELECT * FROM `tabSales Invoice`
WHERE custom_region = 'Europe' AND posting_date > '2024-01-01';
-- Full table scan on millions of rows

-- CORRECT — add composite index
ALTER TABLE `tabSales Invoice` ADD INDEX idx_region_date (custom_region, posting_date);
```

**Why**: Without indexes, MariaDB scans every row in the table. With proper indexes, the same query reads only matching rows.

## 8. Ignoring slow query log

```bash
# WRONG — slow queries accumulating silently
# No slow_query_log configured
# Users complain about "slow system" with no diagnostic data

# CORRECT — ALWAYS enable in production
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
```

**Why**: The slow query log is your primary tool for identifying database bottlenecks. Without it, you are debugging blind.

## 9. Scaling workers without scaling database connections

```bash
# WRONG — 20 Gunicorn workers + 6 RQ workers but max_connections = 50
# Random "Too many connections" errors under load

# CORRECT — ensure max_connections accommodates all workers
# Formula: max_connections >= gunicorn_workers + rq_workers + admin_connections + buffer
[mysqld]
max_connections = 200  # Safe for most deployments
```

## 10. SELECT * instead of specifying fields

```python
# WRONG — fetching all 50+ columns when you need 3
docs = frappe.get_all("Sales Invoice")  # SELECT `tabSales Invoice`.*

# CORRECT — specify only needed fields
docs = frappe.get_all("Sales Invoice",
    fields=["name", "customer", "grand_total"],
    filters={"docstatus": 1},
    limit_page_length=100
)
```

**Why**: Fetching unnecessary columns wastes memory, network bandwidth, and MariaDB buffer pool space. ALWAYS specify the fields you need.
