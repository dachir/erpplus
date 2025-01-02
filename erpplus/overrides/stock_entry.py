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
from erpnext.accounts.general_ledger import process_gl_map
from erpnext.accounts.general_ledger import (
	make_gl_entries,
	make_reverse_gl_entries,
	process_gl_map,
	save_entries,
)

class CustomStockEntry(StockEntry):
	def on_cancel(self):
		self.cancel_journal()
		super().on_cancel()
		#self.update_subcontract_order_supplied_items()
		#self.update_subcontracting_order_status()

		#if self.work_order and self.purpose == "Material Consumption for Manufacture":
		#	self.validate_work_order_status()

		#self.update_work_order()
		#self.update_stock_ledger()

		#self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation")

		#self.make_gl_entries_on_cancel()
		#self.repost_future_sle_and_gle()
		#self.update_cost_in_project()
		#self.update_transferred_qty()
		#self.update_quality_inspection()
		#self.delete_auto_created_batches()
		#self.delete_linked_stock_entry()

		#if self.purpose == "Material Transfer" and self.add_to_transit:
		#	self.set_material_request_transfer_status("Not Started")
		#if self.purpose == "Material Transfer" and self.outgoing_stock_entry:
		#	self.set_material_request_transfer_status("In Transit")


	def cancel_journal(self):
		nb = frappe.db.count("Journal Entry",  {"cheque_no" : self.name})
		if nb > 0:
			jv = frappe.get_doc("Journal Entry", {"cheque_no" : self.name})
			jv.cancel()

	def on_submit(self):
		super().on_submit()
		#self.update_stock_ledger()

		#update_serial_nos_after_submit(self, "items")
		#self.update_work_order()
		#self.validate_subcontract_order()
		#self.update_subcontract_order_supplied_items()
		#self.update_subcontracting_order_status()
		#self.update_pick_list_status()

		#self.make_gl_entries()

		#self.repost_future_sle_and_gle()
		#self.update_cost_in_project()
		#self.validate_reserved_serial_no_consumption()
		#self.update_transferred_qty()
		#self.update_quality_inspection()

		#if self.work_order and self.purpose == "Manufacture":
		#	self.update_so_in_serial_number()

		#if self.purpose == "Material Transfer" and self.add_to_transit:
		#	self.set_material_request_transfer_status("In Transit")

		#if self.purpose == "Material Transfer" and self.outgoing_stock_entry:
		#	self.set_material_request_transfer_status("Completed")

		if self.purpose == "Material Transfer":
			self.make_stock_branch_tranfert_jv_entry()
			#self.make_gl_entries_2()

	def make_stock_branch_tranfert_jv_entry(self):
		gl_entries = []
		posting_date = self.posting_date
		remarks = _("Stock Transfer {0}").format(self.name)
		company = self.company

		for d in self.items:
			# Get source and target branch for warehouses
			s_branch = frappe.db.get_value("Warehouse", d.s_warehouse, "branch")
			t_branch = frappe.db.get_value("Warehouse", d.t_warehouse, "branch")

			if s_branch == t_branch:
				if self.add_to_transit:
					# Fetch credit account and append GL entries
					credit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					credit_account_currency = frappe.db.get_value("Account", credit_account, "account_currency")
					credit_exchange_rate = get_exchange_rate(self.currency, credit_account_currency)

					# Fetch debit account and append GL entries
					debit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					debit_account_currency = frappe.db.get_value("Account", debit_account, "account_currency")
					debit_exchange_rate = get_exchange_rate(self.currency, debit_account_currency)

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
					debit_exchange_rate = get_exchange_rate(self.currency, debit_account_currency)

					credit_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					credit_account_currency = frappe.db.get_value("Account", credit_account, "account_currency")
					credit_exchange_rate = get_exchange_rate(self.currency, credit_account_currency)

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



