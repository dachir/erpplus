# Copyright (c) 2023, Kossivi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils import flt
from frappe.model.document import Document

class CostDistribution(Document):
	def on_submit(self):
		self.make_accrual_jv_entry()

	def validate(self):
		for d in self.get("details"):
			if d.type == "Parent":
				if (d.debit != d.debit_amount) or (d.credit != d.credit_amount):
					frappe.throw(_("Ligne {0}: Parent Lines should not be changed").format(d.idx))

	def on_cancel(self):
		nb = frappe.db.count("Journal Entry",  {"cheque_no" : self.name})
		if nb > 0:
			jv = frappe.get_doc("Journal Entry", {"cheque_no" : self.name})
			jv.cancel()
	
	@frappe.whitelist()
	def fill_details(self):
		self.details.clear()
		gl_doc = frappe.get_doc("GL Entry", self.document)
		names = frappe.db.get_list("GL Entry",["name"], {"voucher_no":gl_doc.voucher_no})
		doctype = gl_doc.get("doctype")
		for name in names:
			gl_doc = frappe.get_doc("GL Entry", name)
			expense_account = frappe.get_value("Account", {"name": gl_doc.account, "root_type": "Expense", "account_type": ["!=", "Round Off"]}, "name")
			if expense_account:
				parent_dimension = gl_doc.get(self.dimension.lower())
				if parent_dimension:
					tpl_doc = frappe.get_doc("Cost Distribution Template", {"name":self.distribution, "parent1": parent_dimension})
					if tpl_doc :	
						self.append('details',{
								"document_type": self.dimension,
								"dimension": parent_dimension,
								"account": expense_account,
								"debit_amount": gl_doc.credit if gl_doc.credit > 0 else 0,
								"credit_amount": gl_doc.debit if gl_doc.debit > 0 else 0,
								"debit": gl_doc.credit if gl_doc.credit > 0 else 0,
								"credit": gl_doc.debit if gl_doc.debit > 0 else 0,
								"type": "Parent",
								"gl_entry": gl_doc.name,
							}
						)
						
						for l in tpl_doc.details:
							self.append('details',{
									"document_type": self.dimension,
									"dimension": l.dimension,
									"account": expense_account,
									"debit_amount": (gl_doc.debit if gl_doc.debit > 0 else 0) * l.rate / 100,
									"credit_amount": (gl_doc.credit if gl_doc.credit > 0 else 0) * l.rate / 100,
									"debit": (gl_doc.debit if gl_doc.debit > 0 else 0) * l.rate / 100,
									"credit": (gl_doc.credit if gl_doc.credit > 0 else 0) * l.rate / 100,
									"type": "Child",
									"gl_entry": gl_doc.name,
								}
							)


	def create_row(self,r, current_account=None):
		row = {}
		if not current_account:
			row = {
				"account": r.account,
				"debit_in_account_currency": r.debit_amount,
				"credit_in_account_currency": r.credit_amount,
			}
		else: 
			row = {
				"account": current_account,
				"debit_in_account_currency": r.credit_amount,
				"credit_in_account_currency": r.debit_amount,
			}
			
		gle = frappe.get_doc("GL Entry", r.gl_entry)
		doctype = gle.get("doctype")
		fieldnames = frappe.get_meta(doctype).get_valid_columns()
		idx = fieldnames.index("is_cancelled")
		nb = len(fieldnames)
		dimensions = fieldnames[idx + 1:nb]
		for d in dimensions:
			if gle.get(d) :
				if d == self.dimension.lower() :
					row.update(
						{
							d: r.dimension,
						}
					)
				else :
					row.update(
						{
							d: gle.get(d),
						}
					)
		
		return row


	def make_accrual_jv_entry(self):
		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = "Journal Entry"
		gle = frappe.get_doc("GL Entry", self.document)
		journal_entry.user_remark = _("Cost Distribution on  {0} for dimension {1}").format(gle.voucher_no, self.dimension) 
		journal_entry.company = self.company 
		journal_entry.posting_date = gle.posting_date
		journal_entry.cheque_no = self.name
		journal_entry.cheque_date = self.date
		accounts = []
		payable_amount = 0
		row = {}

		current_account = frappe.db.get_value("Branch", self.details[0].dimension, "current_account")
		for d in self.details:
			amount = flt(d.debit_amount - d.credit_amount, precision)
			payable_amount += amount

			accounting_entry = self.create_row(d)
			accounts.append(accounting_entry)
			
			accounting_entry = self.create_row(d,current_account)
			accounts.append(accounting_entry)


		if flt(payable_amount, precision) != 0 :
			round_off_account = frappe.db.get_value("Company", self.company,"round_off_account")
			row = {
				"account": round_off_account,
				"debit_in_account_currency": (flt(payable_amount, precision) if flt(payable_amount, precision) < 0 else 0) * -1,
				"credit_in_account_currency": flt(payable_amount, precision) if flt(payable_amount, precision) >= 0 else 0,
			}
		
			doctype = gle.get("doctype")
			fieldnames = frappe.get_meta(doctype).get_valid_columns()
			idx = fieldnames.index("is_cancelled")
			nb = len(fieldnames)
			dimensions = fieldnames[idx + 1:nb]
			for d in dimensions:
				if gle.get(d) :
					if d == self.dimension :
						row.update(
							{
								d: r.dimension,
							}
						)
					else :
						row.update(
							{
								d: gle.get(d),
							}
						)
			accounts.append(row)
			
		journal_entry.title = _("Cost Distribution on  {0} for dimension {1}").format(gle.voucher_no, self.dimension)
		journal_entry.set("accounts", accounts)
		journal_entry.submit()
				
			
