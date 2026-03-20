# Performance Tuning Examples

## Complete MariaDB Configuration for Frappe

```ini
# /etc/mysql/mariadb.conf.d/99-frappe-tuning.cnf
# For 8GB RAM server, shared with Frappe application

[mysqld]
# === InnoDB Settings ===
innodb_buffer_pool_size = 2G
innodb_buffer_pool_instances = 2
innodb_log_file_size = 256M
innodb_flush_method = O_DIRECT
innodb_flush_log_at_trx_commit = 2
innodb_file_per_table = ON

# === Character Set ===
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# === Connection Management ===
max_connections = 200
wait_timeout = 600
interactive_timeout = 600

# === MyISAM (minimal, Frappe uses InnoDB) ===
key_buffer_size = 32M

# === Query Cache (DISABLE for MariaDB 10.4+) ===
query_cache_type = 0
query_cache_size = 0

# === Temp Tables ===
tmp_table_size = 64M
max_heap_table_size = 64M

# === Slow Query Log ===
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = 1

# === Binary Log (for point-in-time recovery) ===
# log_bin = /var/log/mysql/mariadb-bin
# expire_logs_days = 7
# binlog_format = ROW

[mysql]
default-character-set = utf8mb4
```

## Redis Cache Configuration

```conf
# config/redis_cache.conf (managed by bench)
# Override in common_site_config.json or custom Redis config

port 13000
bind 127.0.0.1

# Memory limit — ALWAYS set for cache instance
maxmemory 512mb
maxmemory-policy allkeys-lru

# Disable persistence for cache (performance)
save ""
appendonly no

# Connection limits
maxclients 1000
timeout 300
```

## Gunicorn Production Configuration

```python
# config/gunicorn_config.py (create if not exists)
import multiprocessing

# Worker count: (2 * CPU) + 1
workers = (2 * multiprocessing.cpu_count()) + 1
bind = "127.0.0.1:8000"

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 2

# Worker recycling (prevents memory leaks)
max_requests = 5000
max_requests_jitter = 500

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker class
worker_class = "gthread"
threads = 2
```

## Frappe Caching Patterns

```python
import frappe

# Pattern 1: Use get_cached_value for frequent lookups
# WRONG — hits database every time
def get_company_currency(company):
    return frappe.db.get_value("Company", company, "default_currency")

# CORRECT — cached in Redis, dramatically faster
def get_company_currency(company):
    return frappe.db.get_cached_value("Company", company, "default_currency")


# Pattern 2: Custom cache with expiry
def get_exchange_rate(from_currency, to_currency):
    cache_key = f"exchange_rate:{from_currency}:{to_currency}"
    rate = frappe.cache.get_value(cache_key)
    if rate is None:
        rate = fetch_exchange_rate(from_currency, to_currency)
        frappe.cache.set_value(cache_key, rate, expires_in_sec=3600)  # 1 hour
    return rate


# Pattern 3: Bulk data caching
def get_item_prices():
    cache_key = "all_item_prices"
    prices = frappe.cache.get_value(cache_key)
    if prices is None:
        prices = frappe.db.get_all("Item Price",
            fields=["item_code", "price_list", "price_list_rate"],
            filters={"selling": 1}
        )
        frappe.cache.set_value(cache_key, prices, expires_in_sec=300)
    return prices


# Pattern 4: Hash-based cache for grouped data
def get_user_settings(user):
    settings = frappe.cache.hget("user_settings", user)
    if settings is None:
        settings = frappe.db.get_value("User", user,
            ["language", "time_zone", "desk_theme"], as_dict=True)
        frappe.cache.hset("user_settings", user, settings)
    return settings


# Pattern 5: Cache invalidation on document change
class ItemPrice(Document):
    def on_update(self):
        frappe.cache.delete_value("all_item_prices")

    def on_trash(self):
        frappe.cache.delete_value("all_item_prices")
```

## Database Query Optimization

```python
# WRONG — N+1 query pattern
items = frappe.get_all("Item", fields=["name"])
for item in items:
    price = frappe.db.get_value("Item Price", {"item_code": item.name}, "price_list_rate")
    # This runs len(items) + 1 queries!

# CORRECT — single query with join
items_with_prices = frappe.db.sql("""
    SELECT i.name, i.item_name, ip.price_list_rate
    FROM `tabItem` i
    LEFT JOIN `tabItem Price` ip ON ip.item_code = i.name
    WHERE ip.selling = 1
""", as_dict=True)


# WRONG — fetching all fields when you need only a few
invoices = frappe.get_all("Sales Invoice")  # SELECT * — slow for large tables

# CORRECT — specify only needed fields
invoices = frappe.get_all("Sales Invoice",
    fields=["name", "customer", "grand_total", "status"],
    filters={"docstatus": 1},
    limit_page_length=100
)


# Adding indexes for common query patterns
# In custom app hooks.py:
# after_migrate = ["myapp.patches.add_indexes"]

# myapp/patches/add_indexes.py
def execute():
    import frappe
    frappe.db.add_index("Sales Invoice", ["customer", "posting_date"])
    frappe.db.add_index("Sales Invoice Item", ["item_code"])
```

## Monitoring Script

```bash
#!/bin/bash
# frappe-health-check.sh — Quick system health overview
set -e

BENCH_DIR="/home/frappe/frappe-bench"
cd "$BENCH_DIR"

echo "=== Frappe Health Check ==="
echo ""

# 1. Bench doctor
echo "--- Scheduler & Workers ---"
bench doctor 2>/dev/null || echo "bench doctor failed"
echo ""

# 2. MariaDB stats
echo "--- MariaDB ---"
mysql -e "SHOW GLOBAL STATUS LIKE 'Threads_connected';"
mysql -e "SHOW GLOBAL STATUS LIKE 'Slow_queries';"
mysql -e "SELECT ROUND(@@innodb_buffer_pool_size/1024/1024) AS 'Buffer Pool (MB)';"
echo ""

# 3. Redis memory
echo "--- Redis Cache ---"
redis-cli -p 13000 INFO memory | grep used_memory_human
redis-cli -p 13000 INFO memory | grep maxmemory_human
echo ""

# 4. Disk usage
echo "--- Disk Usage ---"
du -sh sites/*/private/backups/ 2>/dev/null
du -sh sites/*/public/files/ 2>/dev/null
echo ""

# 5. System resources
echo "--- System ---"
free -h | head -2
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "CPU cores: $(nproc)"
```

## Slow Query Analysis Workflow

```bash
# 1. Enable slow query log (if not already)
mysql -e "SET GLOBAL slow_query_log = 1;"
mysql -e "SET GLOBAL long_query_time = 1;"
mysql -e "SET GLOBAL log_queries_not_using_indexes = 1;"

# 2. Wait for data collection (run during peak hours)

# 3. Analyze top slow queries by frequency
mysqldumpslow -t 10 -s c /var/log/mysql/slow.log

# 4. Analyze top slow queries by total time
mysqldumpslow -t 10 -s t /var/log/mysql/slow.log

# 5. For specific slow query, run EXPLAIN
mysql -e "EXPLAIN SELECT * FROM \`tabSales Invoice\` WHERE customer = 'ABC' AND posting_date > '2024-01-01';"
# Look for:
#   type = ALL → needs index
#   rows > 10000 → needs optimization
#   Extra: Using filesort → consider index on ORDER BY column
#   Extra: Using temporary → consider restructuring query

# 6. Add index if needed
mysql -e "ALTER TABLE \`tabSales Invoice\` ADD INDEX idx_customer_date (customer, posting_date);"
```
