# Client Script Implementation Workflows

## Workflow: Master-Detail Form (Auto-populate)

**Use case**: Customer selection auto-fills name, territory, credit limit.

```javascript
frappe.ui.form.on('Sales Order', {
    setup(frm) {
        frm.set_df_property('customer_name', 'read_only', 1);
        frm.set_df_property('territory', 'read_only', 1);
    },

    refresh(frm) {
        if (frm.doc.credit_limit) {
            frm.dashboard.add_indicator(
                __('Credit: {0}', [format_currency(frm.doc.credit_limit)]),
                'blue');
        }
    },

    async customer(frm) {
        if (!frm.doc.customer) {
            frm.set_value({ customer_name: '', territory: '', credit_limit: 0 });
            return;
        }
        try {
            let r = await frappe.db.get_value('Customer', frm.doc.customer,
                ['customer_name', 'territory', 'credit_limit']);
            if (r.message) frm.set_value(r.message);
        } catch (e) {
            frappe.show_alert({ message: __('Could not fetch customer details'), indicator: 'red' });
        }
    }
});
```

## Workflow: Conditional Form Sections

**Use case**: Show different sections based on document type.

```javascript
frappe.ui.form.on('Sales Order', {
    refresh(frm) { frm.trigger('order_type'); },

    order_type(frm) {
        const type = frm.doc.order_type;
        // Hide all type-specific sections
        ['standard_section', 'blanket_section', 'maintenance_section']
            .forEach(s => frm.toggle_display(s, false));

        // Show relevant section and set required fields
        if (type === 'Standard') {
            frm.toggle_display('standard_section', true);
        } else if (type === 'Blanket') {
            frm.toggle_display('blanket_section', true);
            frm.toggle_reqd('blanket_order', true);
        } else if (type === 'Maintenance') {
            frm.toggle_display('maintenance_section', true);
            frm.toggle_reqd(['maintenance_schedule', 'service_level'], true);
        }
    }
});
```

## Workflow: Tiered Price Calculation

**Use case**: Apply quantity-based discount tiers on child table.

```javascript
frappe.ui.form.on('Quotation Item', {
    async item_code(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (!row.item_code) return;
        let r = await frappe.db.get_value('Item Price',
            { item_code: row.item_code, selling: 1 }, 'price_list_rate');
        if (r.message) frappe.model.set_value(cdt, cdn, 'rate', r.message.price_list_rate);
    },

    qty(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let discount = row.qty >= 50 ? 10 : row.qty >= 10 ? 5 : 0;
        frappe.model.set_value(cdt, cdn, 'discount_percentage', discount);
        calculate_amount(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) { calculate_amount(frm, cdt, cdn); },
    discount_percentage(frm, cdt, cdn) { calculate_amount(frm, cdt, cdn); }
});

function calculate_amount(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    let factor = 1 - (flt(row.discount_percentage) / 100);
    frappe.model.set_value(cdt, cdn, 'amount', flt(row.qty) * flt(row.rate) * factor);
}
```

## Workflow: Document Creation Button

**Use case**: Sales Order → Sales Invoice with one click.

```javascript
frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.per_billed < 100) {
            frm.add_custom_button(__('Sales Invoice'), () => {
                create_invoice(frm);
            }, __('Create'));
        }
    }
});

async function create_invoice(frm) {
    let confirmed = await new Promise(resolve =>
        frappe.confirm(__('Create Sales Invoice?'), () => resolve(true), () => resolve(false)));
    if (!confirmed) return;

    try {
        let r = await frappe.call({
            method: 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice',
            args: { source_name: frm.doc.name },
            freeze: true,
            freeze_message: __('Creating Invoice...')
        });
        if (r.message) {
            frappe.model.sync(r.message);
            frappe.set_route('Form', 'Sales Invoice', r.message.name);
        }
    } catch (e) {
        frappe.msgprint({ title: __('Error'), message: e.message, indicator: 'red' });
    }
}
```

## Workflow: Multi-Step Validation

**Use case**: Complex validation with local + server checks.

```javascript
frappe.ui.form.on('Sales Order', {
    async validate(frm) {
        // Step 1: Local checks (fast)
        if (!frm.doc.items || frm.doc.items.length === 0)
            frappe.throw(__('At least one item required'));
        if (frm.doc.grand_total <= 0)
            frappe.throw(__('Total must be greater than zero'));

        // Step 2: Server validation (async)
        let r = await frappe.call({
            method: 'myapp.validations.validate_sales_order',
            args: { customer: frm.doc.customer, amount: frm.doc.grand_total }
        });
        if (r.message) {
            if (r.message.customer_disabled)
                frappe.throw(__('Customer {0} is disabled', [frm.doc.customer]));
            if (r.message.credit_exceeded)
                frappe.throw(__('Credit limit exceeded by {0}',
                    [format_currency(r.message.exceeded_by)]));
        }
    }
});
```

## Workflow: Auto-Populate Child Table from Template

```javascript
frappe.ui.form.on('Sales Order', {
    async order_template(frm) {
        if (!frm.doc.order_template) return;
        if (frm.doc.items && frm.doc.items.length > 0) {
            let ok = await new Promise(resolve =>
                frappe.confirm(__('Replace existing items?'),
                    () => resolve(true), () => resolve(false)));
            if (!ok) { frm.set_value('order_template', ''); return; }
        }

        let template = await frappe.db.get_doc('Order Template', frm.doc.order_template);
        frm.clear_table('items');
        for (let item of template.items) {
            frm.add_child('items', {
                item_code: item.item_code, qty: item.qty, rate: item.rate
            });
        }
        frm.refresh_field('items');
        frappe.show_alert({
            message: __('Added {0} items', [template.items.length]),
            indicator: 'green'
        });
    }
});
```

## Workflow: Bulk Actions on Child Table

```javascript
frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Mark Selected as Received'), () => {
                let selected = frm.get_selected();
                if (!selected.items || selected.items.length === 0) {
                    frappe.msgprint(__('Select items first'));
                    return;
                }
                frappe.confirm(__('Mark {0} items as received?', [selected.items.length]), () => {
                    selected.items.forEach(cdn => {
                        let row = frappe.get_doc('Purchase Order Item', cdn);
                        frappe.model.set_value('Purchase Order Item', cdn, {
                            received_qty: row.qty,
                            received_date: frappe.datetime.now_date()
                        });
                    });
                    frm.refresh_field('items');
                    frappe.show_alert({ message: __('Updated'), indicator: 'green' });
                });
            });
        }
    }
});
```

## Workflow: Role-Based Tab Visibility

```javascript
frappe.ui.form.on('Employee Record', {
    refresh(frm) {
        if (!frappe.user_roles.includes('HR Manager')) {
            frm.toggle_display('salary_tab', false);
            frm.toggle_display('documents_tab', false);
        }
    }
});
```

## Workflow: Real-time Dashboard in Form

```javascript
frappe.ui.form.on('Customer', {
    async refresh(frm) {
        if (frm.is_new()) return;
        let stats = await frappe.call({
            method: 'myapp.api.get_customer_stats',
            args: { customer: frm.doc.name }
        });
        if (stats.message) {
            frm.dashboard.clear_headline();
            frm.dashboard.add_indicator(
                __('Orders: {0}', [stats.message.total_orders]),
                stats.message.total_orders > 0 ? 'blue' : 'gray');
            frm.dashboard.add_indicator(
                __('Revenue: {0}', [format_currency(stats.message.total_revenue)]),
                'green');
        }
    }
});
```
