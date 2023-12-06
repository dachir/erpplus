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
from erpnext.stock.doctype.serial_no.serial_no import (
	get_serial_nos,
	update_serial_nos_after_submit,
)
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
		self.update_subcontract_order_supplied_items()
		self.update_subcontracting_order_status()

		if self.work_order and self.purpose == "Material Consumption for Manufacture":
			self.validate_work_order_status()

		self.update_work_order()
		self.update_stock_ledger()

		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation")

		self.make_gl_entries_on_cancel()
		self.repost_future_sle_and_gle()
		self.update_cost_in_project()
		self.update_transferred_qty()
		self.update_quality_inspection()
		self.delete_auto_created_batches()
		self.delete_linked_stock_entry()

		if self.purpose == "Material Transfer" and self.add_to_transit:
			self.set_material_request_transfer_status("Not Started")
		if self.purpose == "Material Transfer" and self.outgoing_stock_entry:
			self.set_material_request_transfer_status("In Transit")


	def cancel_journal(self):
		nb = frappe.db.count("Journal Entry",  {"cheque_no" : self.name})
		if nb > 0:
			jv = frappe.get_doc("Journal Entry", {"cheque_no" : self.name})
			jv.cancel()

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
			#self.make_stock_branch_tranfert_jv_entry()
			self.make_gl_entries_2()


	def get_gl_entries_2(self):

		warehouse_account = get_warehouse_account_map(self.company)

		sle_map = self.get_stock_ledger_details()
		#voucher_details = self.get_voucher_details(default_expense_account, default_cost_center, sle_map)

		gl_list = []
		warehouse_with_no_account = []
		precision = self.get_debit_field_precision()
		for item_row in self.items:
			sle_list = sle_map.get(item_row.name)
			sle_rounding_diff = 0.0
			if sle_list:
				for sle in sle_list:
					if warehouse_account.get(sle.warehouse):
						# from warehouse account

						sle_rounding_diff += flt(sle.stock_value_difference)

						self.check_expense_account(item_row)

						# expense account/ target_warehouse / source_warehouse
						if item_row.get("target_warehouse"):
							warehouse = item_row.get("target_warehouse")
							expense_account = warehouse_account[warehouse]["account"]
						else:
							expense_account = item_row.expense_account
						
						s_branch = frappe.db.get_value("Warehouse", item_row.s_warehouse, "branch")
						t_branch = frappe.db.get_value("Warehouse", item_row.t_warehouse, "branch")

						if s_branch == t_branch :
							if self.add_to_transit:
								stock_transfert_account = frappe.db.get_value("Branch", s_branch, "stock_transfert_account")
								gl_list.append(
									self.get_gl_dict(
										{
											"account": warehouse_account[sle.warehouse]["account"],
											"against": stock_transfert_account,
											"cost_center": item_row.cost_center,
											"project": item_row.project or self.get("project"),
											"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
											"credit": flt(sle.stock_value_difference, precision),
											"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
										},
										warehouse_account[sle.warehouse]["account_currency"],
										item=item_row,
									)
								)

								gl_list.append(
									self.get_gl_dict(
										{
											"account": stock_transfert_account,
											"against": warehouse_account[sle.warehouse]["account"],
											"cost_center": item_row.cost_center,
											"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
											"debit":  flt(sle.stock_value_difference, precision),
											"project": item_row.get("project") or self.get("project"),
											"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
										},
										item=item_row,
									)
								)
						else:
							stock_transfert_account = frappe.db.get_value("Branch", t_branch, "stock_transfert_account")
							gl_list.append(
									self.get_gl_dict(
										{
											"account": warehouse_account[sle.warehouse]["account"],
											"against": stock_transfert_account,
											"cost_center": item_row.cost_center,
											"project": item_row.project or self.get("project"),
											"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
											"debit": flt(sle.stock_value_difference, precision),
											"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
										},
										warehouse_account[sle.warehouse]["account_currency"],
										item=item_row,
									)
								)

							gl_list.append(
								self.get_gl_dict(
									{
										"account": stock_transfert_account,
										"against": warehouse_account[sle.warehouse]["account"],
										"cost_center": item_row.cost_center,
										"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
										"credit":  flt(sle.stock_value_difference, precision),
										"project": item_row.get("project") or self.get("project"),
										"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
									},
									item=item_row,
								)
							)

					elif sle.warehouse not in warehouse_with_no_account:
						warehouse_with_no_account.append(sle.warehouse)

			if abs(sle_rounding_diff) > (1.0 / (10**precision)) and self.is_internal_transfer():
				warehouse_asset_account = ""
				if self.get("is_internal_customer"):
					warehouse_asset_account = warehouse_account[item_row.get("target_warehouse")]["account"]
				elif self.get("is_internal_supplier"):
					warehouse_asset_account = warehouse_account[item_row.get("warehouse")]["account"]

				expense_account = frappe.get_cached_value("Company", self.company, "default_expense_account")

				gl_list.append(
					self.get_gl_dict(
						{
							"account": expense_account,
							"against": warehouse_asset_account,
							"cost_center": item_row.cost_center,
							"project": item_row.project or self.get("project"),
							"remarks": _("Rounding gain/loss Entry for Stock Transfer"),
							"debit": sle_rounding_diff,
							"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
						},
						warehouse_account[sle.warehouse]["account_currency"],
						item=item_row,
					)
				)

				gl_list.append(
					self.get_gl_dict(
						{
							"account": warehouse_asset_account,
							"against": expense_account,
							"cost_center": item_row.cost_center,
							"remarks": _("Rounding gain/loss Entry for Stock Transfer"),
							"credit": sle_rounding_diff,
							"project": item_row.get("project") or self.get("project"),
							"is_opening": item_row.get("is_opening") or self.get("is_opening") or "No",
						},
						item=item_row,
					)
				)

		if warehouse_with_no_account:
			for wh in warehouse_with_no_account:
				if frappe.get_cached_value("Warehouse", wh, "company"):
					frappe.throw(
						_(
							"Warehouse {0} is not linked to any account, please mention the account in the warehouse record or set default inventory account in company {1}."
						).format(wh, self.company)
					)

		return process_gl_map(gl_list, precision=precision)

	def make_gl_entries_2(self, gl_entries=None, from_repost=False):
		if self.docstatus == 2:
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

		provisional_accounting_for_non_stock_items = cint(
			frappe.get_cached_value(
				"Company", self.company, "enable_provisional_accounting_for_non_stock_items"
			)
		)

		if (
			cint(erpnext.is_perpetual_inventory_enabled(self.company))
			or provisional_accounting_for_non_stock_items
		):
			warehouse_account = get_warehouse_account_map(self.company)

			if self.docstatus == 1:
				if not gl_entries:
					gl_entries = self.get_gl_entries_2()
				#make_gl_entries(gl_entries, from_repost=from_repost)
				#save_entries(gl_entries, False,"Yes", False)
				frappe.msgprint(str(gl_entries))
				for arg in gl_entries:
					#gle = frappe.new_doc("GL Entry", arg)
					#gle.update(arg)
					arg.update({"doctype": "GL Entry"})
					doc = frappe.get_doc(arg)
					frappe.msgprint(doc.account)
					doc.flags.ignore_permissions = 1
					doc.submit()
