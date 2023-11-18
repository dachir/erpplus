# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CostDistribution(Document):
	
	@frappe.whitelist()
	def fill_details(self):
		gl_doc = frappe.get_doc("GL Entry", self.document)
		names = frappe.db.get_list("GL Entry",["name"], {"voucher_no":gl_doc.voucher_no})
        doctype = gl_doc.get("doctype")
		for name in names:
			gl_doc = frappe.get_doc("GL Entry", name)
			parent_dimension = gl_doc.get(self.dimension.lower())
			if parent_dimension:
				tpl_doc = frappe.get_doc("Cost Distribution Template", {"name":self.distribution, "dimension": parent_dimension})
				if tpl_doc :
					self.append('details',{
							"document_type": self.dimension,
							"dimension": parent_dimension,
							"account": gl_doc.account,
							"debit_amount": self.credit if self.credit > 0 else 0,
							"credit_amount": self.debit if self.debit > 0 else 0,
							"type": "Parent",
						}
					)
					
					for l in tpl_doc.details:
						self.append('details',{
								"document_type": self.dimension,
								"dimension": l.dimension,
								"account": gl_doc.account,
								"debit_amount": self.debit if self.debit > 0 else 0 * l.rate / 100,
								"credit_amount": self.credit if self.credit > 0 else 0 * l.rate / 100,
								"type": "Child",
							}
						)
				
			
