// Copyright (c) 2025, Kossivi and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance by Warehouse"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_default("company"),
            reqd: 1
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
            reqd: 0
        },
        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand",
            reqd: 0
        }
    ]
};
