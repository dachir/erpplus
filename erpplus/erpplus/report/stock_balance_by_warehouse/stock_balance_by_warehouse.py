import frappe

def execute(filters=None):
    # Step 1: Fetch Default Company
    default_company = frappe.defaults.get_user_default("company")
    company_filter = filters.get("company", default_company)

    # Step 2: Fetch all unique warehouse names for the selected company
    warehouses = frappe.db.sql("""
        SELECT DISTINCT warehouse FROM `tabBin`
        WHERE warehouse IN (SELECT name FROM `tabWarehouse` WHERE company = %s)
        ORDER BY warehouse
    """, (company_filter,), as_list=True)

    warehouse_columns = [w[0] for w in warehouses]

    # Step 3: Create dynamic SQL for warehouse columns
    warehouse_query_parts = [
        f"SUM(CASE WHEN b.warehouse = '{warehouse}' THEN b.actual_qty ELSE 0 END) AS `{warehouse}`"
        for warehouse in warehouse_columns
    ]
    
    warehouse_query = ", ".join(warehouse_query_parts) if warehouse_columns else "0 AS `No Stock`"

    # Step 4: Construct final SQL query with Total Stock column
    sql_query = f"""
        SELECT 
            i.item_code AS "Item Code",
            i.item_name AS "Item Name",
            i.item_group AS "Item Group",
            i.brand AS "Brand",
            {warehouse_query},
            SUM(b.actual_qty) AS "Total Stock"
        FROM `tabItem` i
        LEFT JOIN `tabBin` b ON i.item_code = b.item_code
        LEFT JOIN `tabWarehouse` w ON b.warehouse = w.name
        WHERE 
            i.disabled = 0
            AND (%(company)s IS NULL OR w.company = %(company)s)
            AND (%(item_group)s IS NULL OR i.item_group = %(item_group)s)
            AND (%(brand)s IS NULL OR i.brand = %(brand)s)
        GROUP BY i.item_code, i.item_name, i.item_group, i.brand
        ORDER BY i.item_code;
    """

    # Step 5: Execute the query
    result = frappe.db.sql(sql_query, {
        "company": company_filter,
        "item_group": filters.get("item_group"),
        "brand": filters.get("brand"),
    }, as_dict=True)

    # Step 6: Prepare columns dynamically
    columns = [
        {"label": "Item Code", "fieldname": "Item Code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": "Item Name", "fieldname": "Item Name", "fieldtype": "Data", "width": 200},
        {"label": "Item Group", "fieldname": "Item Group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": "Brand", "fieldname": "Brand", "fieldtype": "Link", "options": "Brand", "width": 120},
    ]
    
    for warehouse in warehouse_columns:
        columns.append({
            "label": warehouse,
            "fieldname": warehouse,
            "fieldtype": "Float",
            "width": 120
        })
    
    # Add Total Stock column
    columns.append({
        "label": "Total Stock",
        "fieldname": "Total Stock",
        "fieldtype": "Float",
        "width": 150
    })

    return columns, result
