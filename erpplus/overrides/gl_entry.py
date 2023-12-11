import frappe

from erpnext.accounts.doctype.gl_entry.gl_entry import GLEntry

class CustomGLEntry(GLEntry):

    def after_insert(self):
        if self.to_be_paid:
            if self.credit > 0:
                frappe.db.update("GL Entry", self.name, "remaining_amount",self.credit)