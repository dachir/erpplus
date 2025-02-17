frappe.query_reports["Cashbook Report"] = {
    filters: [
        {
            "fieldname": "accounts",
            "label": __("Accounts"),
            "fieldtype": "MultiSelectList",
            "options": "Account",
            "reqd": 1,
            get_data: function(txt) {
                return frappe.db.get_link_options("Account", txt);
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1
        }
    ]
};
