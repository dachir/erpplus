// Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Trial Balance for Party All Party"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "reqd": 0
        },
        {
            "fieldname": "fiscal_year",
            "label": __("Fiscal Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "default": frappe.defaults.get_user_default("fiscal_year"),
            "reqd": 1,
            "on_change": function(query_report) {
                var fiscal_year = query_report.get_values().fiscal_year;
                if (!fiscal_year) {
                    return;
                }
                frappe.model.with_doc("Fiscal Year", fiscal_year, function(r) {
                    var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
                    frappe.query_report.set_filter_value({
                        from_date: fy.year_start_date,
                        to_date: fy.year_end_date
                    });
                });
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.defaults.get_user_default("year_start_date"),
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.defaults.get_user_default("year_end_date"),
        },
        {
            "fieldname": "account",
            "label": __("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    "doctype": "Account",
                    "filters": {
                        "company": company,
                    }
                }
            }
        },
        {
            "fieldname": "show_zero_values",
            "label": __("Show zero values"),
            "fieldtype": "Check"
        }
    ]
};
