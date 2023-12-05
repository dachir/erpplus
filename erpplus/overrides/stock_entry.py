import frappe
from frappe import _

from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

class CustomStockEntry(StockEntry):
	def on_submit(self):
		self.update_stock_ledger()

		update_serial_nos_after_submit(self, "items")
		self.update_work_order()
		self.validate_subcontract_order()
		self.update_subcontract_order_supplied_items()
		self.update_subcontracting_order_status()
		self.update_pick_list_status()

		self.make_gl_entries()

		self.repost_future_sle_and_gle()
		self.update_cost_in_project()
		self.validate_reserved_serial_no_consumption()
		self.update_transferred_qty()
		self.update_quality_inspection()

		if self.work_order and self.purpose == "Manufacture":
			self.update_so_in_serial_number()

		if self.purpose == "Material Transfer" and self.add_to_transit:
			self.set_material_request_transfer_status("In Transit")

		if self.purpose == "Material Transfer" and self.outgoing_stock_entry:
			self.set_material_request_transfer_status("Completed")

		if self.purpose == "Material Transfer":
			self.make_stock_branch_tranfert_jv_entry()

	
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
						"credit_in_account_currency": d.amount,
						"branch": s_branch,
					}
					accounts.append(row)
					stock_transfert_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
					row = {
						"account": stock_transfert_account,
						"debit_in_account_currency": d.amount,
						"credit_in_account_currency": 0,
						"branch": s_branch,
					}
					accounts.append(row)
			else:
				row = {
					"account": warehouses[d.t_warehouse].account,
					"debit_in_account_currency": d.amount,
					"credit_in_account_currency": 0,
					"branch": t_branch,
				}
				accounts.append(row)
				stock_transfert_account = frappe.db.get_value("Branch", t_branch, "stock_transfert_account")
				row = {
					"account": stock_transfert_account,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": d.amount,
					"branch": t_branch,
				}
				accounts.append(row)
				
		if row :	
			journal_entry.title = _("Stock Transfert {0} ").format(self.name) 
			journal_entry.set("accounts", accounts)
			journal_entry.submit()
