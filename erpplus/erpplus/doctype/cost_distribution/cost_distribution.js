// Copyright (c) 2023, Kossivi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Distribution', {
	onload: function (frm) {
        // Make the first row of the child table readonly
        frm.fields_dict['details'].grid.get_field('type').read_only = function(doc, cdt, cdn) {
            // Check if the current row is the first row
            return locals[cdt][cdn].idx === 1;
        };
    },
	distribution: function(frm) {
		if (frm.doc.distribution){
			frm.call('fill_details');
		}
	},
});

frappe.ui.form.on('Cost Distribution Details', {
	details_add(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.document_type = frm.doc.dimension;
		frm.refresh();
	},
  });