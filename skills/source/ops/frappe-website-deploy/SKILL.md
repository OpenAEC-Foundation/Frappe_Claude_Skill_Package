---
name: frappe-website-deploy
description: >
  Deploy HTML/CSS websites to ERPNext/Frappe (v15/v16) as Web Pages via the REST API.
  Use this skill whenever a user wants to host a website on ERPNext, deploy HTML mockups
  to Frappe, create Web Pages programmatically, configure Website Settings, or integrate
  Frappe's Discussion system as a forum. Also use when the user mentions "website on ERPNext",
  "Web Page API", "Page Builder", "Web Template", or wants to serve custom HTML from Frappe.
  Covers: Web Pages with Page Builder, custom Web Templates, Website Settings (navbar, footer),
  CSS management, Frappe Discussion integration, and deployment scripting.
license: MIT
compatibility: "Claude Code, Claude.ai Projects, Claude API. Frappe v15-v16, ERPNext v15-v16."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# Deploy Websites on ERPNext/Frappe

> Patterns for deploying static HTML/CSS websites to ERPNext v15/v16 using Web Pages, Page Builder, and the REST API.

---

## Critical: ERPNext v16 Does NOT Render main_section

In Frappe v16, the `main_section` field on a Web Page is stored but **not rendered** in the browser — even with `content_type: "HTML"` or `dynamic_template: 1`. The Page Builder (`page_blocks`) is the primary rendering mechanism.

**You must use `page_blocks` with a custom Web Template to render HTML content.**

---

## Decision Tree

```
What do you need?
├── Deploy HTML pages to ERPNext
│   ├── Step 1: Create "Raw HTML Section" Web Template (one-time)
│   ├── Step 2: Create Web Pages with page_blocks
│   └── Step 3: Configure Website Settings
│
├── Add a forum / discussion system
│   └── Use Frappe's built-in Discussion Topic/Reply + Discussions Web Template
│
├── Manage CSS
│   ├── Per-page CSS → Web Page `css` field
│   ├── Global CSS → Website Settings `head_html`
│   └── WARNING: Never stack !important overrides (see CSS Management)
│
└── Configure navigation
    └── Website Settings: top_bar_items, footer_items, brand_html, home_page
```

---

## Step 1: Create the Raw HTML Section Web Template

This is a one-time setup. The template accepts raw HTML and renders it as-is.

```
POST /api/resource/Web%20Template
```

```json
{
  "name": "Raw HTML Section",
  "type": "Section",
  "template": "{{ values.html_content }}",
  "fields": [
    {
      "fieldname": "html_content",
      "fieldtype": "Text",
      "label": "HTML Content"
    }
  ]
}
```

**Important constraints:**
- The `fieldtype` must be `"Text"` — Frappe rejects `"Code"` for Web Template fields
- Allowed fieldtypes: `Attach Image`, `Check`, `Data`, `Int`, `Link`, `Select`, `Small Text`, `Text`, `Markdown Editor`, `Section Break`, `Column Break`, `Table Break`
- The template uses `{{ values.html_content }}` (with `values.` prefix) to access field data

---

## Step 2: Create Web Pages with Page Builder

Each page needs `content_type: "Page Builder"` and its HTML in `page_blocks`.

```
POST /api/resource/Web%20Page
```

```json
{
  "title": "Page Title",
  "route": "my-page",
  "published": 1,
  "show_title": 0,
  "full_width": 1,
  "content_type": "Page Builder",
  "css": "<per-page CSS here>",
  "page_blocks": [
    {
      "web_template": "Raw HTML Section",
      "web_template_values": "{\"html_content\": \"<div>Your HTML here</div>\"}"
    }
  ]
}
```

**Critical: `web_template_values` is a JSON string, not an object.** Serialize it with `json.dumps()` before sending.

### Updating an existing page

```
PUT /api/resource/Web%20Page/{url_encoded_name}
```

To find a page by route:
```
GET /api/resource/Web%20Page?filters=[["route","=","my-page"]]&fields=["name"]
```

---

## Step 3: Configure Website Settings

```
PUT /api/resource/Website%20Settings/Website%20Settings
```

```json
{
  "home_page": "home",
  "brand_html": "<span style=\"...\">NL</span> My Brand",
  "head_html": "<link href=\"fonts.css\" rel=\"stylesheet\">\n<style>/* global CSS */</style>",
  "top_bar_items": [
    {"label": "About", "url": "/about", "right": 0}
  ],
  "footer_items": [
    {"label": "About", "url": "/about"}
  ]
}
```

### head_html: Frappe Wrapper Fixes

Frappe wraps page content in several divs that add unwanted whitespace. Add these fixes to `head_html`:

```html
<style>
.page-header-wrapper { display: none !important; }
.page-breadcrumbs { display: none !important; }
.page-content-wrapper { padding: 0 !important; margin: 0 !important; }
.page_content { padding: 0 !important; margin: 0 !important; }
.webpage-content { padding: 0 !important; margin: 0 !important; }
.web-page-content { padding: 0 !important; margin: 0 !important; max-width: none !important; }
.section.section-padding-top { padding-top: 0 !important; }
.section.section-padding-bottom { padding-bottom: 0 !important; }
.web-template-section { padding: 0 !important; margin: 0 !important; }
main { padding: 0 !important; margin: 0 !important; }
</style>
```

These are the **only** `!important` overrides you should use — they target Frappe's own wrapper elements, not your content.

---

## CSS Management

### The golden rule: keep your mockup CSS intact

Use the original mockup CSS in each page's `css` field. Only add Frappe wrapper fixes in `head_html`. Do not layer `!important` overrides on top of your content CSS — this leads to cascading conflicts and unpredictable layouts.

### Where CSS goes

| CSS Type | Where | Field |
|----------|-------|-------|
| Mockup/page CSS | Per Web Page | `css` |
| Google Fonts, Frappe fixes | Website Settings | `head_html` |
| CSS variables (:root) | Website Settings | `head_html` |

### What NOT to do

Never add broad `!important` overrides for content elements like `.card`, `section`, `h2`, etc. If spacing looks wrong, the cause is almost always a Frappe wrapper div — fix that specifically rather than overriding all your content styles.

---

## Deploying from HTML Mockups

When converting a static HTML mockup to ERPNext Web Pages, follow this process:

### 1. Extract the body content

Strip everything outside the main content area — typically between `</header>` and `<footer>`. Remove the mockup's own nav and footer since Frappe provides its own via Website Settings.

### 2. Rewrite links

Replace `.html` file references with Frappe routes:
```
href="about.html"  →  href="/about"
href="index.html"  →  href="/"
```

### 3. Handle images

Local `img/` references won't work on ERPNext. Options:
- Upload images via Frappe File Manager and use the returned URL
- Use the File API: `POST /api/method/upload_file`
- Reference external image URLs

### 4. Deploy script pattern

See `scripts/deploy.py` for a complete deployment script. The key pattern:

```python
import requests, json

def deploy_page(title, route, html_content, css):
    data = {
        "title": title,
        "route": route,
        "published": 1,
        "show_title": 0,
        "full_width": 1,
        "content_type": "Page Builder",
        "css": css,
        "page_blocks": [{
            "web_template": "Raw HTML Section",
            "web_template_values": json.dumps({"html_content": html_content})
        }]
    }
    # Create or update (check 409 conflict for existing pages)
    resp = requests.post(f"{BASE_URL}/api/resource/Web%20Page",
                         headers=HEADERS, json=data)
    if resp.status_code == 409:
        # Find and update existing
        ...
```

---

## Forum Integration with Frappe Discussions

Frappe has built-in DocTypes for discussions that can be embedded on any Web Page.

### Available DocTypes

- **Discussion Topic** — a thread/topic linked to a reference document
- **Discussion Reply** — a reply within a topic

### Creating a forum page

Use the built-in "Discussions" Web Template as a page block:

```json
{
  "page_blocks": [
    {
      "web_template": "Raw HTML Section",
      "web_template_values": "{\"html_content\": \"<section><div class=\\\"container\\\"><h1>Forum</h1></div></section>\"}"
    },
    {
      "web_template": "Discussions",
      "web_template_values": "{\"title\": \"Discussies\", \"cta_title\": \"Nieuw onderwerp\", \"docname\": \"forum\", \"single_thread\": 0}"
    }
  ]
}
```

### Discussions Web Template fields

| Field | Type | Purpose |
|-------|------|---------|
| `title` | Data | Section heading |
| `cta_title` | Data | Button text for new topic |
| `docname` | Link | Web Page to attach discussions to |
| `single_thread` | Check | 0 = multiple topics, 1 = single thread |

### Managing topics via API

```
POST /api/resource/Discussion%20Topic
{"subject": "My topic", "reference_doctype": "Web Page", "reference_docname": "forum"}

POST /api/resource/Discussion%20Reply
{"topic": "TOPIC0001", "reply": "My reply text"}
```

---

## Authentication

All API calls require authentication via token header:

```
Authorization: token {api_key}:{api_secret}
```

Generate API keys in ERPNext: User Settings → API Access → Generate Keys.

**Never store API keys in skill files, SKILL.md, or commit them to git.** Pass them as environment variables or read from a secure config.

---

## Troubleshooting

### Page is blank / main_section not rendering
You're hitting the v16 Page Builder issue. Switch to `content_type: "Page Builder"` with `page_blocks`. See Step 2.

### White bar above content
Frappe's `.page-header-wrapper` and `.page-breadcrumbs` add empty space. Hide them via `head_html`. See Step 3.

### Web Template creation fails with fieldtype error
Use `"Text"` not `"Code"` for the fieldtype. Frappe Web Templates only allow a subset of fieldtypes.

### CSS looks wrong / spacing is off
Check if Frappe's `.section.section-padding-top` or `.page-content-wrapper` are adding padding. Fix those specifically — don't override your content CSS with `!important`.

### Grid layouts collapse to single column
If your mockup CSS has media queries that override grid columns, those will apply on ERPNext too. Check the rendered CSS for conflicting media query rules.

### Images don't show
Local `img/` paths from mockups won't resolve. Upload files to ERPNext or use absolute URLs.
