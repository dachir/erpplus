import frappe
from frappe import _
from frappe.query_builder.functions import CombineDatetime, CurDate, Sum

import json

@frappe.whitelist()
def get_batch_qty_2(
	batch_no=None, warehouse=None, item_code=None, posting_date=None, posting_time=None
):
	"""Returns batch actual qty if warehouse is passed,
	        or returns dict of qty by warehouse if warehouse is None

	The user must pass either batch_no or batch_no + warehouse or item_code + warehouse

	:param batch_no: Optional - give qty for this batch no
	:param warehouse: Optional - give qty for this warehouse
	:param item_code: Optional - give qty for this item"""

	sle = frappe.qb.DocType("Stock Ledger Entry")

	out = 0
	if batch_no and warehouse:
		query = (
			frappe.qb.from_(sle)
			.select(Sum(sle.actual_qty))
			.where((sle.is_cancelled == 0) & (sle.warehouse == warehouse) & (sle.batch_no == batch_no))
		)

		if posting_date:
			if posting_time is None:
				posting_time = nowtime()

			query = query.where(
				CombineDatetime(sle.posting_date, sle.posting_time)
				<= CombineDatetime(posting_date, posting_time)
			)

		out = query.run(as_list=True)[0][0] or 0

	elif batch_no and not warehouse:
		query = (
			frappe.qb.from_(sle)
			.select(sle.warehouse, Sum(sle.actual_qty).as_("qty"))
			.where((sle.is_cancelled == 0) & (sle.batch_no == batch_no))
			.groupby(sle.warehouse)
		)

		if posting_date:
			if posting_time is None:
				posting_time = nowtime()

			query = query.where(
				CombineDatetime(sle.posting_date, sle.posting_time)
				<= CombineDatetime(posting_date, posting_time)
			)

		out = query.run(as_dict=True)

	elif not batch_no and item_code and warehouse:
		query = (
			frappe.qb.from_(sle)
			.select(sle.batch_no, Sum(sle.actual_qty).as_("qty"))
			.where((sle.is_cancelled == 0) & (sle.item_code == item_code) & (sle.warehouse == warehouse))
			.groupby(sle.batch_no)
		)

		if posting_date:
			if posting_time is None:
				posting_time = nowtime()

			query = query.where(
				CombineDatetime(sle.posting_date, sle.posting_time)
				<= CombineDatetime(posting_date, posting_time)
			)

		out = query.run(as_dict=True)

	return out


@frappe.whitelist()
def get_provisions_from_gl(params=None):
	if not params:
		return []
	
	#params = frappe._dict(params)
	conditions = []

	#for key, value in params.items():
	#	if key == "start_date":
	#		conditions.append(f"posting_date >= '{frappe.db.escape(value)}'")
	#	elif key == "end_date":
	#		conditions.append(f"posting_date <= '{frappe.db.escape(value)}'")
	#	else:
	#		conditions.append(f"{d.fieldname} = '{frappe.db.escape(value)}'")
	params = json.loads(params)
	for p in params:
		if  p['value']:
			if p['key'] == "start_date":		
				conditions.append(f"posting_date >= {frappe.db.escape(p['value'])}")
			elif p['key'] == "end_date":
				conditions.append(f"posting_date <= {frappe.db.escape(p['value'])}")
			else:
				conditions.append(f"{p['key']} = {frappe.db.escape(p['value'])}")

	conditions.append("credit > 0 AND to_be_paid = 1 AND remaining_amount > 0 AND is_cancelled = 0")

	condition_str = " AND ".join(conditions)

	query = f"""
		SELECT name,voucher_no, account, credit AS amount, remaining_amount, posting_date
		FROM `tabGL Entry`
		WHERE {condition_str}
	"""

	#query = f"""
	#	SELECT name, account, credit AS amount, remaining_amount
	#	FROM `tabGL Entry`
	#	WHERE to_be_paid = 1 AND remaining_amount > 0
	#"""

	#frappe.msgprint(query)	

	return frappe.db.sql(query, as_dict=1)