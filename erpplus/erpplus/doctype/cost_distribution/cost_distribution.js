// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Distribution', {
	// refresh: function(frm) {

	// }
	distribution: function(frm) {
		if (frm.doc.distribution){
			frm.call('fill_details');
		}
	}
});

frappe.ui.form.on('Cost Distribution Details', {
	details_add(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.document_type = frm.doc.dimension;
		frm.refresh();
	},
  });