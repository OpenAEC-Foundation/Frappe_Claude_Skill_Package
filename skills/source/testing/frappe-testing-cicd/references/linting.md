# Linting and Formatting Reference

## Ruff (Python Linting + Formatting)

Ruff replaces flake8, isort, pyupgrade, and black for Frappe projects.

### Installation

```bash
pip install ruff
```

### Complete pyproject.toml Configuration

```toml
[tool.ruff]
line-length = 110
target-version = "py311"

[tool.ruff.lint]
select = [
    "F",   # Pyflakes — undefined names, unused imports
    "E",   # pycodestyle errors — syntax and style errors
    "W",   # pycodestyle warnings — style warnings
    "I",   # isort — import sorting
    "UP",  # pyupgrade — modernize Python syntax
    "B",   # flake8-bugbear — common bug patterns
    "RUF", # Ruff-specific — Ruff's own rules
]
ignore = [
    "E501",  # Line too long — handled by ruff format
    "F401",  # Unused import — Frappe uses __init__.py re-exports
    "F403",  # Wildcard import — Frappe convention in __init__.py
    "F405",  # Undefined from wildcard — consequence of F403
    "E402",  # Module-level import not at top — Frappe bootstrap pattern
]

[tool.ruff.format]
quote-style = "double"
indent-style = "tab"
docstring-code-format = true

[tool.ruff.lint.isort]
known-first-party = ["frappe", "erpnext", "myapp"]

[tool.ruff.lint.per-file-ignores]
"**/doctype/**/boilerplate/**" = ["ALL"]
"**/__init__.py" = ["F401", "F403"]
```

### CLI Commands

| Command | Purpose |
|---------|---------|
| `ruff check .` | Run linting checks |
| `ruff check . --fix` | Auto-fix linting issues |
| `ruff check . --select=I --fix` | Fix import sorting only |
| `ruff format .` | Format all files |
| `ruff format --check .` | Check formatting without changing files |
| `ruff format --diff .` | Show formatting diff |

### Frappe-Specific Rules

**ALWAYS ignore these rules** for Frappe projects:

| Rule | Why Ignore |
|------|-----------|
| `F401` | Frappe re-exports in `__init__.py` |
| `F403` | Frappe wildcard imports are conventional |
| `F405` | Side effect of F403 |
| `E402` | Frappe requires bootstrap imports before module imports |
| `E501` | Handled by formatter; Frappe uses 110 char lines |

**ALWAYS use these settings**:
- `indent-style = "tab"` — Frappe convention (NOT spaces)
- `line-length = 110` — Frappe standard
- `quote-style = "double"` — Frappe convention

## ESLint (JavaScript Linting)

### Installation

```bash
npm install --save-dev eslint
```

### .eslintrc.json for Frappe Apps

```json
{
    "env": {
        "browser": true,
        "node": true,
        "es2021": true
    },
    "extends": "eslint:recommended",
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "globals": {
        "frappe": "readonly",
        "cur_frm": "readonly",
        "cur_dialog": "readonly",
        "cur_page": "readonly",
        "cur_list": "readonly",
        "__": "readonly",
        "cint": "readonly",
        "cstr": "readonly",
        "flt": "readonly",
        "strip": "readonly"
    },
    "rules": {
        "no-unused-vars": ["warn", {
            "argsIgnorePattern": "^_",
            "varsIgnorePattern": "^_"
        }],
        "no-console": "warn",
        "no-undef": "error",
        "prefer-const": "warn"
    },
    "ignorePatterns": [
        "dist/",
        "node_modules/",
        "*.bundle.*",
        "*.min.js"
    ]
}
```

ALWAYS declare ALL Frappe globals — `frappe`, `cur_frm`, `__`, `cint`, `flt`, `cstr`, `cur_dialog`, `cur_page`, `cur_list`. Missing globals cause false-positive `no-undef` errors.

### CLI Commands

| Command | Purpose |
|---------|---------|
| `npx eslint "**/*.js"` | Lint all JS files |
| `npx eslint "**/*.js" --quiet` | Lint, suppress warnings |
| `npx eslint "**/*.js" --fix` | Auto-fix issues |

## Prettier (JavaScript/Vue/SCSS Formatting)

### .prettierrc

```json
{
    "semi": true,
    "singleQuote": false,
    "tabWidth": 4,
    "useTabs": true,
    "trailingComma": "es5"
}
```

### .prettierignore

```
dist/
node_modules/
*.min.js
*.bundle.*
```

## Semgrep (Security Scanning)

### Frappe-Specific Rules

Create `.semgrep/frappe-security.yml`:

```yaml
rules:
  - id: frappe-sql-injection-format
    pattern: frappe.db.sql($X.format(...))
    message: >
      SQL injection risk: NEVER use .format() in SQL queries.
      Use parameterized queries: frappe.db.sql("SELECT * FROM t WHERE x=%s", [value])
    severity: ERROR
    languages: [python]

  - id: frappe-sql-injection-concat
    pattern: frappe.db.sql($X + ...)
    message: >
      SQL injection risk: NEVER concatenate strings in SQL.
      Use parameterized queries: frappe.db.sql("SELECT * FROM t WHERE x=%s", [value])
    severity: ERROR
    languages: [python]

  - id: frappe-sql-injection-fstring
    pattern: frappe.db.sql(f"...")
    message: >
      SQL injection risk: NEVER use f-strings in SQL.
      Use parameterized queries: frappe.db.sql("SELECT * FROM t WHERE x=%s", [value])
    severity: ERROR
    languages: [python]

  - id: frappe-eval-usage
    pattern: eval(...)
    message: >
      Security risk: NEVER use eval(). Use frappe.safe_eval() for trusted expressions.
    severity: ERROR
    languages: [python]

  - id: frappe-exec-usage
    pattern: exec(...)
    message: >
      Security risk: NEVER use exec(). Use frappe.safe_eval() or Server Scripts.
    severity: ERROR
    languages: [python]

  - id: frappe-db-commit-in-test
    patterns:
      - pattern: frappe.db.commit()
      - pattern-inside: |
          class $CLASS(...):
              ...
    pattern-where-python: "'Test' in str(vars().get('$CLASS', ''))"
    message: >
      NEVER call frappe.db.commit() in test classes. The test framework handles transactions.
    severity: WARNING
    languages: [python]
```

### Running Semgrep Locally

```bash
# Install
pip install semgrep

# Run with local rules
semgrep --config .semgrep/ .

# Run with community rules
semgrep --config "p/python" --config .semgrep/ .
```

## Pre-Commit Hook Setup

### Installation

```bash
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### Running Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Update hook versions
pre-commit autoupdate
```

### Commitlint Configuration

Create `commitlint.config.js`:

```javascript
module.exports = {
    extends: ["@commitlint/config-conventional"],
    rules: {
        "type-enum": [2, "always", [
            "feat", "fix", "docs", "style", "refactor",
            "perf", "test", "chore", "revert", "ci"
        ]],
        "subject-case": [0],  // Allow any case
        "body-max-line-length": [0],  // No body line limit
    },
};
```

## Test Coverage Configuration

### .coveragerc

```ini
[run]
source = myapp
omit =
    */test_*.py
    */tests/*
    */setup.py
    */patches/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    if frappe.flags.in_test:
    if TYPE_CHECKING:
    raise NotImplementedError
    pass

show_missing = true
fail_under = 60

[html]
directory = coverage_html
```

### Running Coverage Locally

```bash
cd apps/myapp
coverage run -m pytest
coverage report --show-missing
coverage html  # Generate HTML report
coverage xml   # Generate XML for CI upload
```
