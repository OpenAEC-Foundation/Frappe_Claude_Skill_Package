# Client Script Complete Examples

## Example 1: Project Tracking Form

**Requirements**: Show completion_date on Completed status, calculate days, validate dates.

```javascript
frappe.ui.form.on('Project Task', {
    setup(frm) {
        frm.set_query('assigned_to', () => ({ filters: { enabled: 1 } }));
    },

    refresh(frm) {
        frm.trigger('status');
        if (frm.doc.start_date && !frm.is_new()) {
            let days = frappe.datetime.get_day_diff(
                frappe.datetime.now_date(),
                frappe.datetime.str_to_obj(frm.doc.start_date));
            frm.set_value('days_elapsed', days);
        }
    },

    status(frm) {
        let done = frm.doc.status === 'Completed';
        frm.toggle_display('completion_date', done);
        frm.toggle_reqd('completion_date', done);
        if (done && !frm.doc.completion_date)
            frm.set_value('completion_date', frappe.datetime.now_date());
    },

    validate(frm) {
        if (frm.doc.completion_date && frm.doc.start_date
            && frm.doc.completion_date < frm.doc.start_date)
            frappe.throw(__('Completion date cannot be before start date'));
    }
});
```

## Example 2: Invoice with Tax Calculation

```javascript
frappe.ui.form.on('Custom Invoice', {
    tax_rate(frm) {
        (frm.doc.items || []).forEach(row =>
            calculate_row_tax(frm, row.doctype, row.name));
    },
    items_remove(frm) { calculate_totals(frm); }
});

frappe.ui.form.on('Custom Invoice Item', {
    qty(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    rate(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    amount(frm, cdt, cdn) { calculate_row_tax(frm, cdt, cdn); },
    tax_amount(frm) { calculate_totals(frm); }
});

function calculate_row(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, 'amount', flt(flt(row.qty) * flt(row.rate), 2));
}

function calculate_row_tax(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    let rate = flt(frm.doc.tax_rate) || 21;
    frappe.model.set_value(cdt, cdn, 'tax_amount', flt(flt(row.amount) * rate / 100, 2));
}

function calculate_totals(frm) {
    let subtotal = 0, total_tax = 0;
    (frm.doc.items || []).forEach(row => {
        subtotal += flt(row.amount);
        total_tax += flt(row.tax_amount);
    });
    frm.set_value({
        subtotal: flt(subtotal, 2),
        total_tax: flt(total_tax, 2),
        grand_total: flt(subtotal + total_tax, 2)
    });
}
```

## Example 3: Wizard-Style Multi-Step Form

```javascript
frappe.ui.form.on('Onboarding Form', {
    refresh(frm) {
        update_step_visibility(frm);
        let current = frm.doc.current_step || 'step_1';
        if (current !== 'step_1')
            frm.add_custom_button(__('Previous'), () => navigate_step(frm, -1));
        if (current !== 'step_3')
            frm.add_custom_button(__('Next'), () => navigate_step(frm, 1), null, 'primary');
    }
});

const STEPS = ['step_1', 'step_2', 'step_3'];

function update_step_visibility(frm) {
    let current = frm.doc.current_step || 'step_1';
    STEPS.forEach(s => frm.toggle_display(`${s}_section`, s === current));
    frm.set_intro(__('Step {0} of 3', [STEPS.indexOf(current) + 1]), 'blue');
}

async function navigate_step(frm, direction) {
    let idx = STEPS.indexOf(frm.doc.current_step || 'step_1');
    if (direction > 0 && !await validate_step(frm)) return;
    let next = idx + direction;
    if (next >= 0 && next < STEPS.length) {
        await frm.set_value('current_step', STEPS[next]);
        frm.refresh();
    }
}

async function validate_step(frm) {
    let step = frm.doc.current_step || 'step_1';
    if (step === 'step_1' && (!frm.doc.full_name || !frm.doc.email)) {
        frappe.msgprint(__('Fill Name and Email'));
        return false;
    }
    if (step === 'step_2' && !frm.doc.department) {
        frappe.msgprint(__('Select a Department'));
        return false;
    }
    return true;
}
```

## Example 4: Cascading Filters with Custom Server Query

```javascript
frappe.ui.form.on('Customer Location', {
    setup(frm) {
        frm.set_query('city', () => {
            if (!frm.doc.country) return { filters: { name: '' } };
            return { filters: { country: frm.doc.country } };
        });
        frm.set_query('address', () => ({
            query: 'myapp.queries.get_addresses_for_city',
            filters: { city: frm.doc.city, address_type: 'Office' }
        }));
    },

    country(frm) {
        frm.set_value('city', '');
        frm.set_value('address', '');
    },

    city(frm) {
        frm.set_value('address', '');
    }
});
```

Server-side query (`myapp/queries.py`):
```python
@frappe.whitelist()
def get_addresses_for_city(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, address_line1, city FROM `tabAddress`
        WHERE city = %(city)s AND address_type = %(address_type)s
        AND (name LIKE %(txt)s OR address_line1 LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {"city": filters.get("city"), "address_type": filters.get("address_type"),
          "txt": f"%{txt}%", "start": start, "page_len": page_len})
```

## Example 5: File Upload with Custom Button

```javascript
frappe.ui.form.on('Product', {
    refresh(frm) {
        if (frm.doc.product_image) show_preview(frm);
        if (!frm.is_new()) {
            frm.add_custom_button(__('Upload Image'), () => {
                new frappe.ui.FileUploader({
                    doctype: frm.doc.doctype,
                    docname: frm.doc.name,
                    folder: 'Home/Products',
                    restrictions: {
                        allowed_file_types: ['image/*'],
                        max_file_size: 2 * 1024 * 1024
                    },
                    on_success: (file_doc) => {
                        frm.set_value('product_image', file_doc.file_url);
                        frm.save();
                    }
                });
            });
        }
    },
    product_image(frm) { show_preview(frm); }
});

function show_preview(frm) {
    if (!frm.doc.product_image) return;
    frm.$wrapper.find('.product-preview').remove();
    frm.get_field('product_image').$wrapper.append(`
        <div class="product-preview" style="margin:10px 0">
            <img src="${frm.doc.product_image}"
                 style="max-width:200px;max-height:200px;border:1px solid #d1d8dd">
        </div>`);
}
```

## Example 6: Keyboard Shortcuts

```javascript
frappe.ui.form.on('Quick Entry', {
    onload(frm) {
        frappe.ui.keys.add_shortcut({
            shortcut: 'ctrl+d',
            action: () => {
                if (frm.is_new()) { frappe.msgprint(__('Save first')); return; }
                let new_doc = frappe.model.copy_doc(frm.doc);
                new_doc.docstatus = 0;
                frappe.set_route('Form', frm.doc.doctype, new_doc.name);
            },
            description: __('Duplicate Document'),
            page: frm.page
        });
    }
});
```

## Example 7: Print and Export Actions

```javascript
frappe.ui.form.on('Report Document', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print Report'), () => {
                frm.print_doc('Custom Report Format');
            }, __('Actions'));

            frm.add_custom_button(__('Export to Excel'), () => {
                let data = [['Item', 'Quantity', 'Rate', 'Amount']];
                (frm.doc.items || []).forEach(row =>
                    data.push([row.item_code, row.qty, row.rate, row.amount]));
                data.push(['', '', 'Total:', frm.doc.grand_total]);
                frappe.tools.downloadify(data, null, frm.doc.name);
            }, __('Actions'));
        }
    }
});
```

## Example 8: Realtime Collaboration Indicator

```javascript
frappe.ui.form.on('Project', {
    onload(frm) {
        if (frm.is_new()) return;
        frappe.realtime.emit('viewing_document', {
            doctype: frm.doc.doctype, name: frm.doc.name, user: frappe.session.user
        });
        frappe.realtime.on('viewing_document', (data) => {
            if (data.doctype === frm.doc.doctype && data.name === frm.doc.name
                && data.user !== frappe.session.user) {
                frappe.show_alert({
                    message: __('User {0} is also viewing', [data.user]),
                    indicator: 'yellow'
                }, 10);
            }
        });
    }
});
```
