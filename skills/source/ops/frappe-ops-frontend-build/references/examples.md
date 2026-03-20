# Frontend Build Examples

## Example 1: Minimal App with Custom JS and CSS

### Directory Structure

```
myapp/
├── hooks.py
└── public/
    ├── js/
    │   └── myapp.bundle.js
    └── css/
        └── myapp.bundle.scss
```

### hooks.py

```python
app_include_js = "myapp.bundle.js"
app_include_css = "myapp.bundle.css"
```

### myapp.bundle.js

```javascript
// Simple Desk customization
frappe.provide("myapp");

myapp.init = function() {
    console.log("MyApp loaded");
};

// Auto-initialize
$(document).ready(() => myapp.init());
```

### myapp.bundle.scss

```scss
.myapp-highlight {
    background-color: var(--yellow-100);
    padding: var(--padding-sm);
    border-radius: var(--border-radius);
}
```

### Build

```bash
bench build --app myapp
```

---

## Example 2: Vue Component Page [v15+]

### Directory Structure

```
myapp/
├── hooks.py
└── public/
    ├── js/
    │   ├── myapp.bundle.js        # Core bundle (hooks)
    │   └── dashboard.bundle.js    # Lazy-loaded Vue dashboard
    └── css/
        └── myapp.bundle.scss
```

### dashboard.bundle.js

```javascript
import { createApp } from "vue";
import Dashboard from "./components/Dashboard.vue";

// Mount when called
window.myapp_dashboard = {
    mount(el) {
        const app = createApp(Dashboard);
        app.mount(el);
        return app;
    }
};
```

### Loading the Dashboard Lazily

```javascript
// In a Page or Client Script
frappe.require("dashboard.bundle.js", () => {
    const container = document.getElementById("dashboard-container");
    window.myapp_dashboard.mount(container);
});
```

---

## Example 3: Migrating from build.json (v14) to esbuild (v15+)

### Before (v14 — build.json)

```json
{
    "js/myapp.min.js": [
        "public/js/utils.js",
        "public/js/forms.js",
        "public/js/reports.js"
    ],
    "css/myapp.min.css": [
        "public/css/base.css",
        "public/css/forms.css"
    ]
}
```

### After (v15+ — bundle files)

```javascript
// public/js/myapp.bundle.js
import "./utils.js";
import "./forms.js";
import "./reports.js";
```

```scss
// public/css/myapp.bundle.scss
@import "./base";
@import "./forms";
```

### Update hooks.py

```python
# Before (v14):
app_include_js = "assets/myapp/js/myapp.min.js"
app_include_css = "assets/myapp/css/myapp.min.css"

# After (v15+):
app_include_js = "myapp.bundle.js"
app_include_css = "myapp.bundle.css"
```

### Delete build.json

```bash
rm apps/myapp/build.json
bench build --app myapp
```

---

## Example 4: Portal (Website) Assets

### hooks.py

```python
# Web-only assets (load on public pages, NOT in Desk)
web_include_js = "myapp-web.bundle.js"
web_include_css = "myapp-web.bundle.css"
```

### public/js/myapp-web.bundle.js

```javascript
// Portal-specific JavaScript
document.addEventListener("DOMContentLoaded", () => {
    // Initialize web components
    document.querySelectorAll(".myapp-accordion").forEach(el => {
        el.addEventListener("click", toggleAccordion);
    });
});

function toggleAccordion(e) {
    e.currentTarget.classList.toggle("active");
}
```

---

## Example 5: Using npm Packages

```bash
# Install dependencies
cd apps/myapp
yarn add chart.js dayjs
```

```javascript
// public/js/charts.bundle.js
import { Chart } from "chart.js/auto";
import dayjs from "dayjs";

export function renderChart(canvas, data) {
    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => dayjs(d.date).format("MMM DD")),
            datasets: [{
                label: "Revenue",
                data: data.map(d => d.amount)
            }]
        }
    });
}
```

---

## Example 6: SCSS with Frappe Variables

```scss
// public/css/myapp.bundle.scss

// Use Frappe's built-in CSS variables (no import needed for CSS vars)
.myapp-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    padding: var(--padding-lg);
    margin-bottom: var(--margin-md);

    &__title {
        font-size: var(--text-lg);
        font-weight: var(--weight-semibold);
        color: var(--heading-color);
    }

    &__body {
        color: var(--text-color);
        font-size: var(--text-base);
    }

    &--highlighted {
        border-color: var(--primary);
        box-shadow: var(--shadow-sm);
    }
}

// Dark mode support (automatic via Frappe's theme system)
// CSS variables automatically switch values in dark mode
```

---

## Example 7: Production Build and Deploy

```bash
# 1. Build for production (minified, no source maps)
bench build --production

# 2. Verify output
ls -la sites/assets/dist/myapp/js/
# myapp.bundle.abc123.js  (minified)

ls -la sites/assets/dist/myapp/css/
# myapp.bundle.def456.css  (minified)

# 3. Clear cache to serve new assets
bench clear-cache

# 4. Restart to pick up changes
sudo bench restart
```
