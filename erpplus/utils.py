import frappe
from frappe import _

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

		out = query.run(as_list=True)

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

		out = query.run(as_list=True)

	return out