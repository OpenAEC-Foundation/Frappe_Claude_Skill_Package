# Frappe Page Wrapper Elements

When Frappe renders a Web Page, it wraps the content in several nested divs. These are the elements between the navbar and your actual content, and they often add unwanted padding/margin.

## Element hierarchy (outside → inside)

```html
<div id="page-{name}" data-path="{route}" data-doctype="Web Page">
  <div class="page-content-wrapper">
    <div class="page-breadcrumbs">
      <!-- empty if no breadcrumbs configured -->
    </div>
    <main class="">
      <div class="page-header-wrapper">
        <div class="page-header">
          <!-- page title if show_title=1, padding: 56px 0 36px by default -->
        </div>
      </div>
      <div class="page_content">
        <section class="section section-padding-top section-padding-bottom"
                 data-section-template="Raw HTML Section">
          <div class="container">
            <!-- YOUR CONTENT HERE -->
          </div>
        </section>
      </div>
    </main>
  </div>
</div>
```

## Elements to hide/reset

| Element | Default behavior | Fix |
|---------|-----------------|-----|
| `.page-header-wrapper` | 56px top padding, border | `display: none` |
| `.page-breadcrumbs` | Empty space | `display: none` |
| `.page-content-wrapper` | May have padding | `padding: 0; margin: 0` |
| `.page_content` | May have padding | `padding: 0; margin: 0` |
| `.section.section-padding-top` | Adds top padding | `padding-top: 0` |
| `.section.section-padding-bottom` | Adds bottom padding | `padding-bottom: 0` |
| `.web-template-section` | May add spacing | `padding: 0; margin: 0` |

## Where to apply fixes

Put these in Website Settings → `head_html` as a `<style>` block. This applies globally to all Web Pages. Do NOT put them in per-page CSS — they're Frappe structural fixes, not content styles.
