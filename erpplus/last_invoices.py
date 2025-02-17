import frappe

@frappe.whitelist()
def get_last_three_invoices(item_code, customer):
    """
    Fetch the last 3 Sales Invoices for a given Item Code and Customer.
    """

    query = """
        SELECT 
            si.name AS invoice_no,
            si.posting_date,
            sii.rate,
            sii.qty,
            sii.amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE si.customer = %s
            AND sii.item_code = %s
            AND si.docstatus = 1  -- Only submitted invoices
        ORDER BY si.posting_date DESC
        LIMIT 3
    """

    invoices = frappe.db.sql(query, (customer, item_code), as_dict=True)

    return invoices
