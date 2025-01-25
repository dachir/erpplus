# Copyright (c) 2013, Frappe Technologies Pvt. Ltd.
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt

from erpnext.accounts.report.trial_balance.trial_balance import validate_filters


def execute(filters=None):
    validate_filters(filters)

    show_party_name = True  # Always show the party name for better visibility
    columns = get_columns(filters, show_party_name)
    data = get_data(filters, show_party_name)

    return columns, data


def get_parties():
    # Fetch parties from Customer, Supplier, and Employee DocTypes
    party_types = ["Customer", "Supplier", "Employee"]
    parties = []

    for p_type in party_types:
        # Determine the party name field dynamically
        party_name_field = f"{frappe.scrub(p_type)}_name"
        party_records = frappe.get_all(
            p_type,
            fields=["name", party_name_field],
            order_by="name",
        )

        # Add party type to each record for better distinction
        for record in party_records:
            record["party_type"] = p_type
            parties.append(record)

    return parties


def get_data(filters, show_party_name):
    # Fetch all parties
    parties = get_parties()
    company_currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    opening_balances = get_opening_balances(filters)
    balances_within_period = get_balances_within_period(filters)

    data = []
    total_row = frappe._dict(
        {
            "opening_debit": 0,
            "opening_credit": 0,
            "debit": 0,
            "credit": 0,
            "closing_debit": 0,
            "closing_credit": 0,
        }
    )

    for party in parties:
        row = {"party": party["name"], "party_type": party["party_type"]}
        if show_party_name:
            row["party_name"] = party.get(f"{frappe.scrub(party['party_type'])}_name", "")

        # Opening balances
        opening_debit, opening_credit = opening_balances.get((party["party_type"], party["name"]), [0, 0])
        row.update({"opening_debit": opening_debit, "opening_credit": opening_credit})

        # Balances within period
        debit, credit = balances_within_period.get((party["party_type"], party["name"]), [0, 0])
        row.update({"debit": debit, "credit": credit})

        # Calculate closing balances
        closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)
        row.update({"closing_debit": closing_debit, "closing_credit": closing_credit})

        # Totals
        for col in total_row:
            total_row[col] += row.get(col, 0)

        row.update({"currency": company_currency})

        # Add row if it has values or show_zero_values is checked
        has_value = any([opening_debit, opening_credit, debit, credit, closing_debit, closing_credit])
        if cint(filters.show_zero_values) or has_value:
            data.append(row)

    # Add total row
    total_row.update({"party": "'" + _("Totals") + "'", "currency": company_currency})
    data.append(total_row)

    return data


def get_opening_balances(filters):
    account_filter = ""
    if filters.get("account"):
        account_filter = "AND account = %s" % frappe.db.escape(filters.get("account"))

    gle = frappe.db.sql(
        f"""
        SELECT 
            party_type, party, SUM(debit) AS opening_debit, SUM(credit) AS opening_credit
        FROM 
            `tabGL Entry`
        WHERE 
            company = %(company)s
            AND (branch = %(branch)s OR %(branch)s IS NULL)
            AND is_cancelled = 0
            AND IFNULL(party, '') != ''
            AND (posting_date < %(from_date)s OR (IFNULL(is_opening, 'No') = 'Yes' AND posting_date <= %(to_date)s))
            {account_filter}
        GROUP BY 
            party_type, party
        """,
        {
            "company": filters.company,
            "branch": filters.branch,
            "from_date": filters.from_date,
            "to_date": filters.to_date,
        },
        as_dict=True,
    )

    opening = frappe._dict()
    for d in gle:
        opening_debit, opening_credit = toggle_debit_credit(d.opening_debit, d.opening_credit)
        opening[(d.party_type, d.party)] = [opening_debit, opening_credit]

    return opening


def get_balances_within_period(filters):
    account_filter = ""
    if filters.get("account"):
        account_filter = "AND account = %s" % frappe.db.escape(filters.get("account"))

    gle = frappe.db.sql(
        f"""
        SELECT 
            party_type, party, SUM(debit) AS debit, SUM(credit) AS credit
        FROM 
            `tabGL Entry`
        WHERE 
            company = %(company)s
            AND (branch = %(branch)s OR %(branch)s IS NULL)
            AND is_cancelled = 0
            AND IFNULL(party, '') != ''
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND IFNULL(is_opening, 'No') = 'No'
            {account_filter}
        GROUP BY 
            party_type, party
        """,
        {
            "company": filters.company,
            "branch": filters.branch,
            "from_date": filters.from_date,
            "to_date": filters.to_date,
        },
        as_dict=True,
    )

    balances_within_period = frappe._dict()
    for d in gle:
        balances_within_period[(d.party_type, d.party)] = [d.debit, d.credit]

    return balances_within_period


def toggle_debit_credit(debit, credit):
    if flt(debit) > flt(credit):
        debit = flt(debit) - flt(credit)
        credit = 0.0
    else:
        credit = flt(credit) - flt(debit)
        debit = 0.0

    return debit, credit


def get_columns(filters, show_party_name):
    columns = [
        {
            "fieldname": "party",
            "label": _("Party"),
            "fieldtype": "Link",
            "options": "Customer",  # Default link; works for all party types
            "width": 200,
        },
        {
            "fieldname": "party_type",
            "label": _("Party Type"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "opening_debit",
            "label": _("Opening (Dr)"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "opening_credit",
            "label": _("Opening (Cr)"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "debit",
            "label": _("Debit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "credit",
            "label": _("Credit"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "closing_debit",
            "label": _("Closing (Dr)"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "closing_credit",
            "label": _("Closing (Cr)"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 120,
        },
        {
            "fieldname": "currency",
            "label": _("Currency"),
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
        },
    ]

    if show_party_name:
        columns.insert(
            1,
            {
                "fieldname": "party_name",
                "label": _("Party Name"),
                "fieldtype": "Data",
                "width": 200,
            },
        )

    return columns
