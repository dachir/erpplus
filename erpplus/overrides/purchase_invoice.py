import frappe

from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice

class CustomPurchaseInvoice(PurchaseInvoice):

    def on_submit(self):
        super(CustomPurchaseInvoice, self).on_submit()
        for i in self.items:
            if i.gl_entry :
                remaining_amount = frappe.db.get_value("GL Entry", i.gl_entry, "remaining_amount")
                if remaining_amount < i.amount:
                    frappe.throw("The amount enter is more than the remaining amount")

                frappe.db.update("GL Entry", i.gl_entry, "remaining_amount",(remaining_amount or 0.0) - (i.amount or 0.0))

    def on_cancel(self):
        super(CustomPurchaseInvoice, self).on_cancel()
        for i in self.items:
            if i.gl_entry :
                remaining_amount = frappe.db.get_value("GL Entry", i.gl_entry, "remaining_amount")
                frappe.db.update("GL Entry", i.gl_entry, "remaining_amount",(remaining_amount or 0.0) + (i.amount or 0.0))