"""
Deploy HTML mockup pages to ERPNext v16 as Web Pages using Page Builder.

Usage:
    python deploy.py --base-url https://your-site.com --api-key "key:secret" --mockup-dir ./mockup

This script:
1. Creates a "Raw HTML Section" Web Template (if it doesn't exist)
2. Reads HTML files from the mockup directory
3. Extracts the body content (between </header> and <footer>)
4. Rewrites .html links to Frappe routes
5. Creates/updates Web Pages with page_blocks
6. Configures Website Settings (navbar, footer, homepage)
"""

import json
import re
import os
import sys
import argparse
import urllib.parse

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Install with: pip install requests")
    sys.exit(1)


def make_headers(api_key):
    return {
        "Authorization": f"token {api_key}",
        "Content-Type": "application/json"
    }


def ensure_web_template(base_url, headers):
    """Create the Raw HTML Section Web Template if it doesn't exist."""
    resp = requests.get(
        f"{base_url}/api/resource/Web%20Template/Raw HTML Section",
        headers=headers, timeout=10
    )
    if resp.status_code == 200:
        print("Web Template 'Raw HTML Section' already exists")
        return True

    resp = requests.post(
        f"{base_url}/api/resource/Web%20Template",
        headers=headers,
        json={
            "name": "Raw HTML Section",
            "type": "Section",
            "template": "{{ values.html_content }}",
            "fields": [{
                "fieldname": "html_content",
                "fieldtype": "Text",
                "label": "HTML Content"
            }]
        },
        timeout=15
    )
    if resp.status_code == 200:
        print("Created Web Template 'Raw HTML Section'")
        return True
    else:
        print(f"Failed to create Web Template: {resp.status_code} {resp.text[:200]}")
        return False


def extract_body(html):
    """Extract content between </header> and <footer>."""
    match = re.search(r'</header>\s*', html, re.DOTALL)
    if match:
        html = html[match.end():]
    else:
        match = re.search(r'<body[^>]*>\s*', html, re.DOTALL)
        if match:
            html = html[match.end():]

    match = re.search(r'<footer', html, re.DOTALL)
    if match:
        html = html[:match.start()]

    html = re.sub(r'</body>\s*</html>\s*$', '', html, flags=re.DOTALL)
    return html.strip()


def rewrite_links(html, link_map):
    """Replace .html references with Frappe routes."""
    for old, new in link_map.items():
        html = html.replace(f'href="{old}"', f'href="{new}"')
        html = html.replace(f"href='{old}'", f"href='{new}'")
    return html


def extract_inline_styles(html):
    """Extract <style> tags from the HTML."""
    styles = re.findall(r'<style>(.*?)</style>', html, re.DOTALL)
    return '\n'.join(styles)


def find_page_by_route(base_url, headers, route):
    """Find a Web Page by its route."""
    resp = requests.get(
        f'{base_url}/api/resource/Web%20Page?filters=[["route","=","{route}"]]&fields=["name"]',
        headers=headers, timeout=10
    )
    if resp.status_code == 200 and resp.json().get("data"):
        return resp.json()["data"][0]["name"]
    return None


def deploy_page(base_url, headers, title, route, html_content, css):
    """Create or update a Web Page."""
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

    existing = find_page_by_route(base_url, headers, route)
    if existing:
        resp = requests.put(
            f"{base_url}/api/resource/Web%20Page/{urllib.parse.quote(existing)}",
            headers=headers, json=data, timeout=30
        )
        if resp.status_code == 200:
            print(f"  Updated: {title} -> /{route}")
            return True
    else:
        resp = requests.post(
            f"{base_url}/api/resource/Web%20Page",
            headers=headers, json=data, timeout=30
        )
        if resp.status_code == 200:
            print(f"  Created: {title} -> /{route}")
            return True

    print(f"  FAILED: {title} -> /{route}: {resp.status_code} {resp.text[:200]}")
    return False


def update_website_settings(base_url, headers, home_page, brand_html, nav_items, footer_items):
    """Configure Website Settings."""
    head_html = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
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
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
</style>'''

    data = {
        "home_page": home_page,
        "brand_html": brand_html,
        "head_html": head_html,
        "top_bar_items": nav_items,
        "footer_items": footer_items,
    }

    resp = requests.put(
        f"{base_url}/api/resource/Website%20Settings/Website%20Settings",
        headers=headers, json=data, timeout=15
    )
    if resp.status_code == 200:
        print("Website Settings updated")
    else:
        print(f"Website Settings FAILED: {resp.status_code} {resp.text[:200]}")


def main():
    parser = argparse.ArgumentParser(description="Deploy HTML mockup to ERPNext")
    parser.add_argument("--base-url", required=True, help="ERPNext instance URL")
    parser.add_argument("--api-key", required=True, help="API key in format key:secret")
    parser.add_argument("--mockup-dir", required=True, help="Path to mockup directory")
    parser.add_argument("--css-file", help="Path to CSS file (default: mockup-dir/css/style.css)")
    parser.add_argument("--pages-json", help="Path to pages config JSON")
    args = parser.parse_args()

    headers = make_headers(args.api_key)
    css_path = args.css_file or os.path.join(args.mockup_dir, "css", "style.css")

    # Read CSS
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    print(f"CSS loaded: {len(css)} chars")

    # Ensure Web Template exists
    if not ensure_web_template(args.base_url, headers):
        sys.exit(1)

    # Load pages config or auto-discover
    if args.pages_json:
        with open(args.pages_json, "r") as f:
            pages = json.load(f)
    else:
        # Auto-discover HTML files
        pages = []
        for fname in sorted(os.listdir(args.mockup_dir)):
            if fname.endswith(".html"):
                route = fname.replace(".html", "")
                if route == "index":
                    route = "home"
                title = route.replace("-", " ").title()
                pages.append({"file": fname, "title": title, "route": route})

    # Build link map
    link_map = {}
    for page in pages:
        old = page["file"]
        new = "/" if page["route"] == "home" else f"/{page['route']}"
        link_map[old] = new

    # Deploy pages
    print(f"\nDeploying {len(pages)} pages...")
    success = 0
    for page in pages:
        filepath = os.path.join(args.mockup_dir, page["file"])
        if not os.path.exists(filepath):
            print(f"  SKIP: {page['file']} not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            html_full = f.read()

        body = extract_body(html_full)
        body = rewrite_links(body, link_map)
        inline_styles = extract_inline_styles(html_full)
        if inline_styles:
            body = f"<style>{inline_styles}</style>\n{body}"

        if deploy_page(args.base_url, headers, page["title"], page["route"], body, css):
            success += 1

    print(f"\n{success}/{len(pages)} pages deployed")


if __name__ == "__main__":
    main()
