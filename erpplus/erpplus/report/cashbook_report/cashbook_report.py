import frappe
from frappe import _, _dict
from frappe.utils import cint, flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 150},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 120},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 200},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 120}
    ]

def get_data(filters):
    # Get the selected accounts (Bank and Cash)
    accounts = filters.get("accounts")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    if not accounts:
        frappe.throw(_("Please select at least one account."))

    # Initialize variables
    opening_balance = get_opening_balance(accounts, from_date)
    balance = opening_balance
    data = []

    # Add Opening Balance Row
    data.append({
        "posting_date": "",
        "account": "Opening Balance",
        "debit": 0,
        "credit": 0,
        "remarks": "",
        "balance": balance
    })

    # Fetch GL Entries for the selected accounts and date range
    gl_entries = frappe.db.sql("""
        SELECT posting_date, account, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE against IN %(accounts)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY posting_date, account
    """, {
        "accounts": accounts,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)

    # Process GL Entries
    for entry in gl_entries:
        balance += flt(entry.credit) - flt(entry.debit)
        data.append({
            "posting_date": entry.posting_date,
            "account": entry.account,
            "debit": entry.credit,
            "credit": entry.debit,
            "remarks": entry.remarks,
            "balance": balance
        })

    # Add Closing Balance Row
    data.append({
        "posting_date": "",
        "account": "Closing Balance",
        "debit": 0,
        "credit": 0,
        "remarks": "",
        "balance": balance
    })

    return data

def get_opening_balance(accounts, from_date):
    # Calculate the opening balance for the selected accounts
    opening_balance = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit) AS balance
        FROM `tabGL Entry`
        WHERE account IN %(accounts)s
            AND posting_date < %(from_date)s
    """, {
        "accounts": accounts,
        "from_date": from_date
    }, as_dict=True)

    return flt(opening_balance[0].balance) if opening_balance else 0