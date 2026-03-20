# GitHub Actions Reference for Frappe Apps

## Required Services

Every Frappe CI workflow MUST include these services:

### MariaDB (Primary Database)

```yaml
services:
  mariadb:
    image: mariadb:11.4  # v15+: use 11.x; v14: use 10.x
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

### PostgreSQL (Optional, Dual-DB)

```yaml
  postgres:
    image: postgres:16
    ports:
      - 5432:5432
    env:
      POSTGRES_PASSWORD: db_root
    options: >-
      --health-cmd pg_isready
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

### Redis (Cache + Queue)

```yaml
  redis-cache:
    image: redis:alpine
    ports:
      - 13000:6379
  redis-queue:
    image: redis:alpine
    ports:
      - 11000:6379
```

ALWAYS use separate Redis instances for cache and queue. NEVER share a single Redis for both.

## Bench Setup Steps

### Step 1: Initialize Bench

```yaml
- name: Init bench
  working-directory: frappe-bench
  run: |
    bench init --skip-assets --skip-redis-config-generation .
    bench set-config -g db_root_password db_root
    bench set-config -g redis_cache redis://localhost:13000
    bench set-config -g redis_queue redis://localhost:11000
```

### Step 2: Install App

```yaml
- name: Install app
  working-directory: frappe-bench
  run: |
    bench get-app --skip-assets myapp ./apps/myapp
    bench setup requirements --dev
```

### Step 3: Create Site

```yaml
# MariaDB site
- name: Create site (MariaDB)
  working-directory: frappe-bench
  run: |
    bench new-site test_site \
      --db-root-password db_root \
      --admin-password admin \
      --no-mariadb-socket

# PostgreSQL site
- name: Create site (PostgreSQL)
  working-directory: frappe-bench
  run: |
    bench new-site test_site \
      --db-type postgres \
      --db-root-password db_root \
      --admin-password admin
```

### Step 4: Install App on Site

```yaml
- name: Install app on site
  working-directory: frappe-bench
  run: |
    bench --site test_site install-app myapp
    bench build --apps myapp
```

## Test Matrix Configuration

### Python Version Matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12"]
```

**Version compatibility**:
- Frappe v14: Python 3.10, 3.11
- Frappe v15: Python 3.11, 3.12
- Frappe v16: Python 3.12, 3.13+

### Database Matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - python-version: "3.11"
        db: mariadb
      - python-version: "3.12"
        db: mariadb
      - python-version: "3.12"
        db: postgres
```

## Environment Variables

```yaml
env:
  NODE_ENV: production
  CI: true
```

## Useful Actions

| Action | Version | Purpose |
|--------|---------|---------|
| `actions/checkout@v4` | v4 | Clone repository |
| `actions/setup-python@v5` | v5 | Install Python version |
| `actions/setup-node@v4` | v4 | Install Node version |
| `actions/upload-artifact@v4` | v4 | Upload test artifacts |
| `actions/download-artifact@v4` | v4 | Download artifacts between jobs |
| `codecov/codecov-action@v4` | v4 | Upload coverage to Codecov |
| `pre-commit/action@v3.0.1` | v3 | Run pre-commit checks |
| `returntocorp/semgrep-action@v1` | v1 | Run Semgrep security scans |
| `softprops/action-gh-release@v2` | v2 | Create GitHub releases |

## Caching (Optional Performance Boost)

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt', '**/pyproject.toml') }}

- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: ~/.cache/yarn
    key: ${{ runner.os }}-node-${{ hashFiles('**/yarn.lock') }}
```

## Debugging Failed CI

### Enable SSH Debug Session

```yaml
- name: Debug via SSH
  if: failure()
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 15
```

### Upload Logs on Failure

```yaml
- name: Upload bench logs
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: bench-logs
    path: |
      frappe-bench/logs/
      frappe-bench/sites/test_site/logs/
```

## Branch Protection via GitHub CLI

```bash
# Require status checks before merging
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test (3.11, mariadb)", "test (3.12, mariadb)", "lint"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF
```
