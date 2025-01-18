import frappe
from frappe import _
from frappe.utils import (
	cint,
	comma_or,
	cstr,
	flt,
	format_time,
	formatdate,
	getdate,
	month_diff,
	nowdate,
)

import erpnext
from erpnext.stock import get_warehouse_account_map
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
#from erpnext.stock.doctype.serial_no.serial_no import (
#	get_serial_nos,
#	update_serial_nos_after_submit,
#)
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.general_ledger import process_gl_map
from erpnext.accounts.general_ledger import (
	make_gl_entries,
	make_reverse_gl_entries,
	process_gl_map,
	save_entries,
)

class CustomStockEntry(StockEntry):
	def on_cancel_function(self):
		#self.cancel_journal()
		super().on_cancel()

	def cancel_journal(self):
		nb = frappe.db.count("Journal Entry",  {"cheque_no" : self.name})
		if nb > 0:
			jv = frappe.get_doc("Journal Entry", {"cheque_no" : self.name})
			jv.cancel()

	def on_submit_function(self):
		#super().on_submit()
		if self.purpose == "Material Transfer":
			self.make_stock_branch_tranfert_jv_entry()

	def make_stock_branch_tranfert_jv_entry(self):
		gl_entries = []
		posting_date = self.posting_date
		remarks = _("Stock Transfer {0}").format(self.name)
		company = self.company
		currency=erpnext.get_company_currency(self.company)

		for d in self.items:
			# Get source and target branch for warehouses
			s_branch = frappe.db.get_value("Warehouse", d.s_warehouse, "branch")
			t_branch = frappe.db.get_value("Warehouse", d.t_warehouse, "branch")

			if s_branch == t_branch:
				if self.add_to_transit:
					# Fetch credit account and append GL entries
					credit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					credit_account_currency = frappe.db.get_value("Account", credit_account, "account_currency")
					credit_exchange_rate = get_exchange_rate(currency, credit_account_currency)

					# Fetch debit account and append GL entries
					debit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					debit_account_currency = frappe.db.get_value("Account", debit_account, "account_currency")
					debit_exchange_rate = get_exchange_rate(currency, debit_account_currency)

					self.append_gl_entry(
						gl_entries, credit_account, 0, d.amount, d.cost_center,
						credit_exchange_rate, s_branch, credit_account_currency, remarks, debit_account
					)

					
					self.append_gl_entry(
						gl_entries, debit_account, d.amount, 0, d.cost_center,
						debit_exchange_rate, s_branch, debit_account_currency, remarks, credit_account
					)

				else:
					# Append GL entries for direct transfer
					debit_account = frappe.db.get_value("Branch", t_branch, "stock_transfert_account")
					debit_account_currency = frappe.db.get_value("Account", debit_account, "account_currency")
					debit_exchange_rate = get_exchange_rate(currency, debit_account_currency)

					credit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					credit_account_currency = frappe.db.get_value("Account", credit_account, "account_currency")
					credit_exchange_rate = get_exchange_rate(currency, credit_account_currency)

					self.append_gl_entry(
						gl_entries, debit_account, d.amount, 0, d.cost_center,
						debit_exchange_rate, t_branch, debit_account_currency, remarks, credit_account
					)

					
					self.append_gl_entry(
						gl_entries, credit_account, 0, d.amount, d.cost_center,
						credit_exchange_rate, s_branch, credit_account_currency, remarks, debit_account
					)

	def append_gl_entry(self, gl_entries, account, debit_amount, credit_amount, cost_center, ex_rate, branch, currency, remarks, against_account=None):
		arg = frappe._dict({
			"posting_date": self.posting_date,
			"account": account,
			"debit": flt(debit_amount, 2),
			"credit": flt(credit_amount, 2),
			"exchange_rate": ex_rate,
			"branch": branch,
			"currency": currency,
			"remarks": remarks,
			"cost_center": cost_center,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"company": self.company
		})

		if against_account:
			arg.update({"against": against_account})

		gl_entries.append(arg)


	
	"""
	def make_stock_branch_tranfert_jv_entry(self):
		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = "Journal Entry"
		journal_entry.user_remark = _("Stock Transfert {0} ").format(self.name) 
		journal_entry.company = self.company 
		journal_entry.posting_date = self.posting_date
		journal_entry.cheque_no = self.name
		journal_entry.cheque_date = self.posting_date
		accounts = []
		row = {}
		warehouses = get_warehouse_account_map(self.company)

		for d in self.items:
			s_branch = frappe.db.get_value("Warehouse", d.s_warehouse, "branch")
			t_branch = frappe.db.get_value("Warehouse", d.t_warehouse, "branch")
			if s_branch == t_branch :
				if self.add_to_transit:
					row = {
						"account": warehouses[d.s_warehouse].account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": d.basic_amount,
						"branch": s_branch,
					}
					accounts.append(row)
					stock_transfert_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					row = {
						"account": stock_transfert_account,
						"debit_in_account_currency": d.basic_amount,
						"credit_in_account_currency": 0,
						"branch": s_branch,
					}
					accounts.append(row)
			else:
				row = {
					"account": warehouses[d.t_warehouse].account,
					"debit_in_account_currency": d.basic_amount,
					"credit_in_account_currency": 0,
					"branch": t_branch,
				}
				accounts.append(row)
				stock_transfert_account = frappe.db.get_value("Branch", t_branch, "stock_transfert_account")
				row = {
					"account": stock_transfert_account,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": d.basic_amount,
					"branch": t_branch,
				}
				accounts.append(row)
	
		if row :	
			journal_entry.title = _("Stock Transfert {0} ").format(self.name) 
			journal_entry.set("accounts", accounts)
			journal_entry.flags.ignore_permissions = 1
			journal_entry.submit()
	"""



	def correction_jv_entry(self):
		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = "Journal Entry"
		journal_entry.user_remark = _("Stock Transfert {0} ").format(self.name) 
		journal_entry.company = self.company 
		journal_entry.posting_date = self.posting_date
		journal_entry.cheque_no = self.name
		journal_entry.cheque_date = self.posting_date
		accounts = []
		row = {}
		warehouses = get_warehouse_account_map(self.company)

		for d in self.items:
			s_branch = frappe.db.get_value("Warehouse", d.s_warehouse, "branch")
			t_branch = frappe.db.get_value("Warehouse", d.t_warehouse, "branch")
			if s_branch == t_branch :
				if self.add_to_transit:
					row = {
						"account": warehouses[d.s_warehouse].account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": -d.additional_cost,
						"branch": s_branch,
					}
					accounts.append(row)
					stock_transfert_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					row = {
						"account": stock_transfert_account,
						"debit_in_account_currency": -d.additional_cost,
						"credit_in_account_currency": 0,
						"branch": s_branch,
					}
					accounts.append(row)
			else:
				row = {
					"account": warehouses[d.t_warehouse].account,
					"debit_in_account_currency": -d.additional_cost,
					"credit_in_account_currency": 0,
					"branch": t_branch,
				}
				accounts.append(row)
				stock_transfert_account = frappe.db.get_value("Branch", t_branch, "stock_transfert_account")
				row = {
					"account": stock_transfert_account,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": -d.additional_cost,
					"branch": t_branch,
				}
				accounts.append(row)
	
		if row :	
			journal_entry.title = _("Stock Transfert {0} ").format(self.name) 
			journal_entry.set("accounts", accounts)
			journal_entry.flags.ignore_permissions = 1
			journal_entry.submit()



