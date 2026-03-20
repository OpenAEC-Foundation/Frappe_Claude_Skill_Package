# CI/CD Examples

## Complete GitHub Actions Workflow: MariaDB Only

```yaml
name: Server Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: server-tests-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

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

      redis-cache:
        image: redis:alpine
        ports:
          - 13000:6379
      redis-queue:
        image: redis:alpine
        ports:
          - 11000:6379

    steps:
      - name: Checkout frappe
        uses: actions/checkout@v4
        with:
          repository: frappe/frappe
          path: frappe-bench/apps/frappe

      - name: Checkout app
        uses: actions/checkout@v4
        with:
          path: frappe-bench/apps/myapp

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install bench
        run: pip install frappe-bench

      - name: Init bench
        working-directory: frappe-bench
        run: |
          bench init --skip-assets --skip-redis-config-generation .
          bench set-config -g db_root_password db_root
          bench set-config -g redis_cache redis://localhost:13000
          bench set-config -g redis_queue redis://localhost:11000

      - name: Create site and install app
        working-directory: frappe-bench
        run: |
          bench get-app --skip-assets myapp ./apps/myapp
          bench setup requirements --dev
          bench new-site test_site \
            --db-root-password db_root \
            --admin-password admin \
            --no-mariadb-socket
          bench --site test_site install-app myapp
          bench build --apps myapp

      - name: Run tests
        working-directory: frappe-bench
        run: bench --site test_site run-tests --app myapp --failfast
```

## Dual Database Workflow (MariaDB + PostgreSQL)

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

      redis-cache:
        image: redis:alpine
        ports:
          - 13000:6379
      redis-queue:
        image: redis:alpine
        ports:
          - 11000:6379

    steps:
      # ... (checkout, setup Python/Node, install bench, init bench same as above)

      - name: Create site (MariaDB)
        if: matrix.db == 'mariadb'
        working-directory: frappe-bench
        run: |
          bench new-site test_site \
            --db-root-password db_root \
            --admin-password admin \
            --no-mariadb-socket

      - name: Create site (PostgreSQL)
        if: matrix.db == 'postgres'
        working-directory: frappe-bench
        run: |
          bench new-site test_site \
            --db-type postgres \
            --db-root-password db_root \
            --admin-password admin
```

## Parallel Test Workflow

```yaml
    strategy:
      matrix:
        build-number: [0, 1]

    steps:
      # ... (setup steps same as above)

      - name: Run parallel tests
        working-directory: frappe-bench
        run: |
          bench --site test_site run-parallel-tests \
            --app myapp \
            --total-builds 2 \
            --build-number ${{ matrix.build-number }}
```

## Linting Workflow (Separate Job)

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ruff
        run: pip install ruff

      - name: Ruff check
        run: ruff check .

      - name: Ruff format check
        run: ruff format --check .
```

## Pre-Commit CI Check

```yaml
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Run pre-commit
        uses: pre-commit/action@v3.0.1
```

## Release Workflow with Changelog

```yaml
name: Release
on:
  push:
    tags:
      - "v*"

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        uses: mikepenz/release-changelog-builder-action@v4
        with:
          configuration: ".github/changelog-config.json"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body: ${{ steps.changelog.outputs.changelog }}
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Coverage Upload with Codecov

```yaml
      - name: Run tests with coverage
        working-directory: frappe-bench
        run: |
          cd apps/myapp
          coverage run -m pytest
          coverage xml -o ../../sites/coverage.xml
          coverage report --show-missing

      - name: Upload coverage to Codecov
        if: always()
        uses: codecov/codecov-action@v4
        with:
          file: frappe-bench/sites/coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}
          flags: server
```

## Semgrep Security Scan Job

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: .semgrep/
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
```
