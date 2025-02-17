frappe.query_reports["Pivot Sales Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group"
        }
    ],

    onload: function (report) {
        report.page.add_inner_button(__("Expand All"), function () {
            $(".dt-tree-toggle").each(function () {
                $(this).click();
            });
        });

        report.page.add_inner_button(__("Collapse All"), function () {
            $(".dt-tree-toggle.expanded").each(function () {
                $(this).click();
            });
        });
    },

    get_datatable_options(options) {
        return {
            treeView: true,
            inlineFilters: true,
            cellHeight: 30,
            layout: "fluid"
        };
    }
};
