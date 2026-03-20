# CI/CD Anti-Patterns

## Anti-Pattern 1: Missing Service Health Checks

```yaml
# WRONG — tests start before MariaDB is ready
services:
  mariadb:
    image: mariadb:11.4
    ports:
      - 3306:3306
    env:
      MARIADB_ROOT_PASSWORD: db_root
    # No health check — bench new-site will fail with "Can't connect to MySQL server"
```

```yaml
# CORRECT — ALWAYS add health checks with sufficient retries
services:
  mariadb:
    image: mariadb:11.4
    ports:
      - 3306:3306
    env:
      MARIADB_ROOT_PASSWORD: db_root
    options: >-
      --health-cmd="healthcheck.sh --connect --innodb_initialized"
      --health-interval=5s
      --health-timeout=5s
      --health-retries=10
```

## Anti-Pattern 2: Using `sudo pip install`

```yaml
# WRONG — permission issues and global pip pollution
- name: Install bench
  run: sudo pip install frappe-bench
```

```yaml
# CORRECT — install in user space
- name: Install bench
  run: pip install frappe-bench
```

## Anti-Pattern 3: Hardcoded Redis Ports

```yaml
# WRONG — default Redis port 6379 conflicts when running multiple Redis services
services:
  redis-cache:
    image: redis:alpine
    ports:
      - 6379:6379  # Will conflict with redis-queue
  redis-queue:
    image: redis:alpine
    ports:
      - 6379:6379  # Port conflict!
```

```yaml
# CORRECT — ALWAYS use unique host ports for each Redis service
services:
  redis-cache:
    image: redis:alpine
    ports:
      - 13000:6379
  redis-queue:
    image: redis:alpine
    ports:
      - 11000:6379
```

And ALWAYS configure bench to match:
```yaml
- run: |
    bench set-config -g redis_cache redis://localhost:13000
    bench set-config -g redis_queue redis://localhost:11000
```

## Anti-Pattern 4: Missing --skip-assets on bench init

```yaml
# WRONG — builds all assets during init (slow, unnecessary before app install)
- name: Init bench
  run: bench init .
```

```yaml
# CORRECT — skip assets until after app installation
- name: Init bench
  run: bench init --skip-assets --skip-redis-config-generation .
```

## Anti-Pattern 5: Not Using Concurrency Groups

```yaml
# WRONG — multiple CI runs stack up for same PR
name: Tests
on: [push, pull_request]
# No concurrency control — wastes resources
```

```yaml
# CORRECT — cancel outdated runs
name: Tests
on: [push, pull_request]
concurrency:
  group: tests-${{ github.ref }}
  cancel-in-progress: true
```

## Anti-Pattern 6: fail-fast: true in Matrix

```yaml
# WRONG — one Python version failing cancels all other matrix entries
strategy:
  fail-fast: true  # Default is true!
  matrix:
    python-version: ["3.11", "3.12"]
```

```yaml
# CORRECT — let all matrix entries complete
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12"]
```

## Anti-Pattern 7: No Timeout on Jobs

```yaml
# WRONG — stuck test can run for 6 hours (GitHub Actions default)
jobs:
  test:
    runs-on: ubuntu-latest
    # No timeout — a hanging test blocks the runner indefinitely
```

```yaml
# CORRECT — ALWAYS set a reasonable timeout
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 60
```

## Anti-Pattern 8: Skipping Node Setup

```yaml
# WRONG — system Node version may be incompatible
- name: Build assets
  run: bench build --apps myapp
  # Fails because Node 16 is too old for Frappe v15
```

```yaml
# CORRECT — ALWAYS pin Node version
- name: Setup Node
  uses: actions/setup-node@v4
  with:
    node-version: 20  # NEVER use Node 16 for Frappe v15+
```

## Anti-Pattern 9: Running All App Tests Instead of Just Your App

```yaml
# WRONG — runs ALL tests including frappe core (slow, noisy)
- name: Run tests
  run: bench --site test_site run-tests
```

```yaml
# CORRECT — ALWAYS scope to your app
- name: Run tests
  run: bench --site test_site run-tests --app myapp
```

## Anti-Pattern 10: Not Checking Ruff Format in CI

```yaml
# WRONG — only checks linting, not formatting
- name: Lint
  run: ruff check .
  # Formatting issues slip through
```

```yaml
# CORRECT — check both linting AND formatting
- name: Lint
  run: |
    ruff check .
    ruff format --check .
```

## Anti-Pattern 11: Committing Directly to Main

```yaml
# WRONG — no branch protection, no CI validation before merge
on:
  push:
    branches: [main]
# Tests run AFTER code is already on main
```

```yaml
# CORRECT — require PR with passing checks
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]
# Combined with branch protection rules requiring status checks
```

## Anti-Pattern 12: Missing --no-mariadb-socket

```yaml
# WRONG — bench tries to use Unix socket (not available in CI container)
- run: bench new-site test_site --db-root-password db_root --admin-password admin
```

```yaml
# CORRECT — force TCP connection
- run: bench new-site test_site --db-root-password db_root --admin-password admin --no-mariadb-socket
```
