# Frontend Build Anti-Patterns

## Anti-Pattern 1: Using build.json in v15+

```json
// WRONG in v15+:
{
    "js/myapp.min.js": ["public/js/file1.js", "public/js/file2.js"]
}
```

**Why it breaks**: v15+ ignores `build.json` entirely. The esbuild pipeline only discovers `*.bundle.*` files.

**Correct approach**: Create bundle entry points using the `*.bundle.*` convention:
```javascript
// public/js/myapp.bundle.js
import "./file1.js";
import "./file2.js";
```

---

## Anti-Pattern 2: Including Full Paths in hooks.py (v15+)

```python
# WRONG in v15+:
app_include_js = "assets/myapp/js/myapp.min.js"
app_include_css = "assets/myapp/css/myapp.min.css"
```

**Why it breaks**: v15+ uses hashed filenames. The full path will not resolve.

**Correct approach**: Use the bundle name only — Frappe resolves the hashed path automatically:
```python
app_include_js = "myapp.bundle.js"
app_include_css = "myapp.bundle.css"
```

---

## Anti-Pattern 3: Including Hash in hooks.py

```python
# WRONG:
app_include_js = "myapp.bundle.abc123.js"
```

**Why it breaks**: The hash changes on every build. Hardcoding it means assets break after the next build.

**Correct approach**: NEVER include the hash. Use the base bundle name:
```python
app_include_js = "myapp.bundle.js"
```

---

## Anti-Pattern 4: Forgetting to Rebuild After hooks.py Changes

```python
# Changed hooks.py but didn't rebuild
app_include_js = "new-feature.bundle.js"  # Added this line
# But forgot: bench build --app myapp
```

**Why it breaks**: hooks.py changes require a rebuild to register new asset mappings.

**Correct approach**: ALWAYS run `bench build --app myapp` after changing hooks.py.

---

## Anti-Pattern 5: Naming Partials with .bundle.

```
public/css/
├── myapp.bundle.scss
└── _helpers.bundle.scss    # WRONG — this becomes a separate entry point
```

**Why it breaks**: Any file with `.bundle.` in the name is treated as an entry point and compiled separately.

**Correct approach**: Partials MUST NOT have `.bundle.` in their name:
```
public/css/
├── myapp.bundle.scss       # Entry point
└── _helpers.scss           # Partial — imported only
```

---

## Anti-Pattern 6: Loading All Assets on Every Page

```python
# WRONG — huge bundle loaded on every Desk page
app_include_js = [
    "myapp.bundle.js",
    "charts.bundle.js",
    "reports.bundle.js",
    "dashboard.bundle.js",
    "print-tools.bundle.js"
]
```

**Why it breaks**: Every page load downloads all these bundles, even when not needed.

**Correct approach**: Only include essential assets in hooks. Lazy-load the rest:
```python
app_include_js = "myapp.bundle.js"  # Core only
```

```javascript
// Lazy load when needed
frappe.require("charts.bundle.js", () => {
    renderChart();
});
```

---

## Anti-Pattern 7: Not Using --production for Deployment

```bash
# WRONG for production:
bench build
```

**Why it breaks**: Development builds include source maps and are not minified, resulting in larger downloads and slower page loads.

**Correct approach**: ALWAYS use `--production` for deployment:
```bash
bench build --production
```

---

## Anti-Pattern 8: Editing Files in assets/dist/

```
# WRONG: Editing compiled output directly
vim sites/assets/dist/myapp/js/myapp.bundle.abc123.js
```

**Why it breaks**: Changes are overwritten on the next `bench build`. The `dist/` directory is auto-generated.

**Correct approach**: ALWAYS edit source files in `apps/myapp/public/` and rebuild.

---

## Anti-Pattern 9: Mixing ES6 and CommonJS Imports

```javascript
// WRONG — mixing module systems
const dayjs = require("dayjs");     // CommonJS
import { Chart } from "chart.js";   // ES6
```

**Why it breaks**: esbuild handles both but mixing can cause unexpected bundling behavior and duplicate dependencies.

**Correct approach**: ALWAYS use ES6 imports consistently:
```javascript
import dayjs from "dayjs";
import { Chart } from "chart.js";
```

---

## Anti-Pattern 10: Not Clearing Cache After Production Build

```bash
bench build --production
# Forgot: bench clear-cache
# Users still see old assets due to cached asset paths
```

**Why it breaks**: Frappe caches asset URL mappings. Old hashed filenames are served until cache is cleared.

**Correct approach**: ALWAYS clear cache after production builds:
```bash
bench build --production
bench clear-cache
```
