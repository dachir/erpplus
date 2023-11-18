// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Distribution Template', {
	//refresh: function(frm) {

	//}
});

frappe.ui.form.on('Cost Distribution Template Details', {
  details_add(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
		row.document_type = frm.doc.document_type;
    frm.refresh();
  },
});