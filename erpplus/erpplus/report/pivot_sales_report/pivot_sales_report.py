import frappe
import pandas as pd

def execute(filters=None):
    filters = filters or {}

    # **Step 1: Fetch Sales Data**
    query = """
        SELECT 
            si.customer AS "Customer",
            it.item_group AS "Item Group",
            sii.item_code AS "Item Code",
            sii.item_name AS "Item Name",
            SUM(sii.qty) AS "Total Quantity",
            SUM(sii.net_amount) AS "Total Sales"
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabItem` it ON sii.item_code = it.item_code
        WHERE si.docstatus = 1
        {conditions}
        GROUP BY si.customer, it.item_group, sii.item_code, sii.item_name
    """

    conditions = []
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(f"AND si.posting_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'")

    if filters.get("customer"):
        conditions.append(f"AND si.customer = '{filters['customer']}'")

    if filters.get("item_group"):
        conditions.append(f"AND it.item_group = '{filters['item_group']}'")

    query = query.format(conditions=" ".join(conditions))
    sales_data = frappe.db.sql(query, as_dict=True)

    # **Step 2: Debugging - Log Data**
    frappe.log_error(f"Sales Data Count: {len(sales_data)}", "Pivot Sales Report")
    if sales_data:
        frappe.log_error("First Record Exists", "Pivot Sales Report")
        frappe.log_error(str(sales_data[0])[:100], "Pivot Sales Report")  # Truncate to 100 characters


    # **Step 3: Ensure Data Exists**
    if not sales_data or len(sales_data) == 0:
        return [], []  # No data, return empty

    df = pd.DataFrame.from_records(sales_data)

    # **Step 4: Debugging - Print DataFrame**
    frappe.log_error(f"DataFrame Columns: {df.columns.tolist()}", "Pivot Sales Report")
    frappe.log_error(f"DataFrame Head: {df.head()}", "Pivot Sales Report")

    # ✅ Ensure required columns exist
    required_columns = ["Customer", "Item Group", "Item Code", "Item Name", "Total Quantity", "Total Sales"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None  # Ensure missing columns are added with default value

    df.fillna(0, inplace=True)  # Handle missing values

    # ✅ **Step 5: Create Pivot Table (Two-Level - Item Group & Item)**
    pivot_table = df.pivot_table(
        values="Total Sales",
        index=["Customer"],  # Customers in Rows
        columns=["Item Group", "Item Code"],  # Item Group & Item in Columns
        aggfunc="sum",
        fill_value=0
    )

    # ✅ **Step 6: Debugging - Log Pivot Table**
    frappe.log_error(f"Pivot Table Shape: {pivot_table.shape}", "Pivot Sales Report")
    frappe.log_error(f"Pivot Table Data:\n{pivot_table.head()}", "Pivot Sales Report")

    pivot_table.reset_index(inplace=True)
    pivot_table.columns = [' '.join(col).strip() if isinstance(col, tuple) else col for col in pivot_table.columns]

    # ✅ **Step 7: Convert to ERPNext Format**
    columns = [{"label": "Customer", "fieldname": "Customer", "fieldtype": "Data", "width": 200}]
    for col in pivot_table.columns[1:]:  # Skip "Customer"
        columns.append({
            "label": col,
            "fieldname": col,
            "fieldtype": "Currency",
            "width": 150
        })

    data = pivot_table.to_dict(orient="records")

    # **Step 8: Final Debugging - Log Final Data**
    frappe.log_error(f"Final Data Count: {len(data)}", "Pivot Sales Report")
    #frappe.log_error(f"Final Data Preview: {data[:5]}", "Pivot Sales Report")

    return columns, data
