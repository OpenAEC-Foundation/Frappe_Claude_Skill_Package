# Performance Tuning Workflows

## Workflow 1: Initial Production Tuning

```
1. Assess server resources
   $ free -h           (total RAM)
   $ nproc             (CPU cores)
   $ df -h             (disk space and type — SSD vs HDD)
   |
2. Calculate resource allocation
   Gunicorn workers = (2 * CPU) + 1
   MariaDB buffer pool = 25-40% of RAM (shared server)
   Redis maxmemory = 256MB-1GB (depending on dataset)
   Remaining = OS + headroom
   |
3. Configure MariaDB
   Edit /etc/mysql/mariadb.conf.d/99-frappe-tuning.cnf
   Set innodb_buffer_pool_size, slow_query_log, character set
   $ sudo systemctl restart mariadb
   |
4. Configure Redis
   Edit bench config/redis_cache.conf
   Set maxmemory and maxmemory-policy allkeys-lru
   $ sudo supervisorctl restart frappe-bench-redis-cache
   |
5. Configure Gunicorn
   Edit supervisor config: set -w [workers] --timeout 120
   Add --max-requests 5000 --max-requests-jitter 500
   $ sudo supervisorctl restart frappe-bench-frappe-web
   |
6. Verify
   $ bench doctor
   $ curl -o /dev/null -s -w '%{time_total}\n' https://mysite.com
   Compare response times before/after
```

## Workflow 2: Diagnose Slow Page Loads

```
1. Identify the slow page
   Note URL, time of day, frequency
   |
2. Check server-side response time
   Browser DevTools > Network tab > check TTFB (Time To First Byte)
   |
   +-- TTFB > 2s? → Server-side bottleneck
   |   |
   |   +-- Check MariaDB slow query log
   |       $ mysqldumpslow -t 5 -s t /var/log/mysql/slow.log
   |       |
   |       +-- Slow queries found?
   |           +-- Run EXPLAIN on slow query
   |           +-- Add missing indexes
   |           +-- Optimize Python code (N+1 patterns)
   |
   +-- TTFB < 500ms but page still slow?
       → Client-side bottleneck (JS, CSS, large assets)
       |
       +-- Enable CDN for static assets
       +-- Check for unminified custom JavaScript
       +-- Use browser DevTools Performance tab
   |
3. Check Gunicorn worker saturation
   $ sudo supervisorctl status
   Are all workers busy? If yes → increase worker count
   |
4. Check Redis cache effectiveness
   $ redis-cli -p 13000 INFO stats | grep keyspace_hits
   $ redis-cli -p 13000 INFO stats | grep keyspace_misses
   Hit ratio should be > 90%
   |
5. Monitor over time
   Log response times, identify patterns (peak hours, specific pages)
```

## Workflow 3: Diagnose Background Job Delays

```
1. Check scheduler health
   $ bench doctor
   Expected: scheduler running, workers online, no pending jobs
   |
2. Check pending jobs
   $ bench --site mysite.com show-pending-jobs
   |
   +-- Many pending short/default jobs?
   |   → Increase short/default workers in supervisor config
   |
   +-- Many pending long jobs?
   |   → Increase long workers OR optimize long-running job code
   |
   +-- Jobs stuck (same jobs for hours)?
       → $ bench purge-jobs (clears all pending)
       → Investigate why jobs are failing (check worker logs)
   |
3. Check worker logs
   $ tail -100 logs/worker.log
   Look for: exceptions, timeouts, memory errors
   |
4. If RQ workers crash repeatedly
   Check available memory (workers may be OOM killed)
   $ dmesg | grep -i "out of memory"
   → Reduce Gunicorn workers to free RAM
   → Or add more server RAM
```

## Workflow 4: Database Performance Audit

```
1. Enable monitoring
   SET GLOBAL slow_query_log = 1;
   SET GLOBAL long_query_time = 1;
   SET GLOBAL log_queries_not_using_indexes = 1;
   |
2. Collect data for 24 hours (including peak)
   |
3. Analyze slow queries
   $ mysqldumpslow -t 20 -s c /var/log/mysql/slow.log  (by count)
   $ mysqldumpslow -t 20 -s t /var/log/mysql/slow.log  (by time)
   |
4. For each top slow query:
   a. Run EXPLAIN
   b. Check if index exists on filtered columns
   c. Check if query uses SELECT *
   d. Check for N+1 patterns in calling Python code
   |
5. Fix identified issues
   - Add indexes: ALTER TABLE `tabXxx` ADD INDEX idx_name (col1, col2)
   - Optimize queries: specify fields, add filters, use limit
   - Add caching: get_cached_value, frappe.cache.set_value
   |
6. Measure improvement
   Compare slow query count before/after
   Compare page load times
   |
7. Document findings
   Update LESSONS.md with discovered patterns
```

## Workflow 5: Scale from Single Server to Multi-Server

```
Stage 1: Vertical scaling (exhaust single server first)
  - Upgrade RAM → increase buffer pool + Redis
  - Upgrade CPU → increase Gunicorn + RQ workers
  - Move to SSD → immediate I/O improvement
  |
Stage 2: Separate database
  - Move MariaDB to dedicated server
  - Update common_site_config.json: db_host
  - Give DB server 70% RAM as buffer pool
  - Benchmark: usually 30-50% improvement
  |
Stage 3: Separate Redis
  - Move Redis to dedicated server (or managed service)
  - Update common_site_config.json: redis_cache, redis_queue
  - Low effort, moderate improvement
  |
Stage 4: Multiple app servers
  - Two or more Frappe app servers behind load balancer
  - Shared NFS/GlusterFS for sites/ directory
  - Sticky sessions for WebSocket connections
  - Significant complexity increase
  |
Stage 5: Read replicas (for reporting)
  - MariaDB read replica for heavy reports
  - Custom code routes report queries to replica
  - Complex but enables massive read scalability
```

## Workflow 6: Emergency Performance Triage

```
SCENARIO: Production site unresponsive

1. Check server is alive
   $ uptime (load average > CPU count = overloaded)
   $ free -h (no free memory = OOM risk)
   |
2. Check processes
   $ sudo supervisorctl status (any FATAL/STOPPED?)
   $ sudo systemctl status nginx
   $ sudo systemctl status mariadb
   |
   +-- Processes down? → Restart them
       $ sudo supervisorctl restart all
       $ sudo systemctl restart nginx
   |
3. Check for OOM kills
   $ dmesg | tail -50 | grep -i "oom\|killed"
   → Reduce workers, increase RAM
   |
4. Check disk space
   $ df -h (any filesystem > 95%?)
   → Clean old backups, logs, tmp files
   → $ bench --site mysite.com clear-cache
   |
5. Check MariaDB
   $ mysql -e "SHOW PROCESSLIST;"
   → Many sleeping connections? Increase wait_timeout
   → Long running query? KILL [process_id]
   |
6. Check Redis
   $ redis-cli -p 13000 ping (should return PONG)
   $ redis-cli -p 13000 INFO memory | grep used_memory_human
   → Memory full? Flush cache: redis-cli -p 13000 FLUSHDB
   |
7. Temporary relief
   $ bench --site mysite.com set-maintenance-mode on
   Fix root cause, then disable maintenance mode
```
