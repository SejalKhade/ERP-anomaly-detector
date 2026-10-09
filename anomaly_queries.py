"""
Pre-built anomaly detection SQL queries for the 5 anomaly types.
Each returns a DataFrame with detected anomalies.
"""

ANOMALY_QUERIES = {
    "late_deliveries": {
        "title": "Late Deliveries",
        "description": "PO line items where actual delivery exceeded scheduled delivery date.",
        "sql": """
            SELECT
                e.EBELN AS po_number,
                e.EBELP AS line_item,
                e.MATNR AS material,
                m.MAKTX AS material_desc,
                v.NAME1 AS vendor,
                v.LAND1 AS vendor_country,
                e.EINDT AS scheduled_delivery,
                e.ACTUAL_DELIVERY AS actual_delivery,
                CAST(julian(e.ACTUAL_DELIVERY::DATE) - julian(e.EINDT::DATE) AS INTEGER) AS days_late,
                e.MENGE AS qty,
                e.MEINS AS unit,
                ROUND(e.MENGE * e.NETPR, 2) AS po_line_value_usd
            FROM EKPO e
            JOIN EKKO k ON e.EBELN = k.EBELN
            JOIN MARA m ON e.MATNR = m.MATNR
            JOIN LFA1 v ON k.LIFNR = v.LIFNR
            WHERE e.LATE_FLAG = 1
            ORDER BY days_late DESC
        """,
        "icon": "⏰",
        "color": "#FF6B6B",
    },
    "invoice_mismatches": {
        "title": "Invoice Mismatches",
        "description": "Invoices where billed amount exceeds PO value by more than 5%.",
        "sql": """
            SELECT
                r.BELNR AS invoice_number,
                r.EBELN AS po_number,
                v.NAME1 AS vendor,
                r.BLDAT AS invoice_date,
                r.PO_AMOUNT AS po_amount_usd,
                r.WRBTR AS invoice_amount_usd,
                r.MISMATCH_PCT AS overcharge_pct,
                ROUND(r.WRBTR - r.PO_AMOUNT, 2) AS overcharge_usd
            FROM RBKP r
            JOIN LFA1 v ON r.LIFNR = v.LIFNR
            WHERE r.MISMATCH_FLAG = 1
            ORDER BY overcharge_usd DESC
        """,
        "icon": "💰",
        "color": "#FFB347",
    },
    "stockout_risks": {
        "title": "Stockout Risks",
        "description": "Materials where unrestricted stock is below safety stock level.",
        "sql": """
            SELECT
                d.MATNR AS material,
                m.MAKTX AS material_desc,
                m.MATKL AS material_group,
                d.WERKS AS plant,
                d.LABST AS current_stock,
                d.EISBE AS safety_stock,
                d.MEINS AS unit,
                ROUND((d.EISBE - d.LABST), 2) AS shortage,
                ROUND(d.LABST / NULLIF(d.EISBE, 0) * 100, 1) AS stock_pct_of_safety,
                d.DAYS_OF_SUPPLY AS days_of_supply
            FROM MARD d
            JOIN MARA m ON d.MATNR = m.MATNR
            WHERE d.STOCKOUT_FLAG = 1
            ORDER BY shortage DESC
        """,
        "icon": "📦",
        "color": "#FF4444",
    },
    "demand_spikes": {
        "title": "Demand Spikes",
        "description": "Planning records where demand exceeds baseline by more than 50%.",
        "sql": """
            SELECT
                p.MATNR AS material,
                m.MAKTX AS material_desc,
                m.MATKL AS material_group,
                p.WERKS AS plant,
                p.PERMO AS planning_month,
                p.BASE_DEMAND AS baseline_demand,
                p.PBMNG AS planned_demand,
                p.MEINS AS unit,
                ROUND((p.PBMNG - p.BASE_DEMAND) / NULLIF(p.BASE_DEMAND, 0) * 100, 1) AS spike_pct,
                ROUND(p.PLWRT, 2) AS planned_value_usd
            FROM PLAF p
            JOIN MARA m ON p.MATNR = m.MATNR
            WHERE p.SPIKE_FLAG = 1
            ORDER BY spike_pct DESC
        """,
        "icon": "📈",
        "color": "#9B59B6",
    },
    "unconfirmed_pos": {
        "title": "Unconfirmed Purchase Orders",
        "description": "PO headers missing vendor order acknowledgment (BSTAE empty).",
        "sql": """
            SELECT
                k.EBELN AS po_number,
                v.NAME1 AS vendor,
                v.LAND1 AS vendor_country,
                k.BEDAT AS po_date,
                CAST(julian(CURRENT_DATE) - julian(k.BEDAT::DATE) AS INTEGER) AS days_open,
                COUNT(e.EBELP) AS line_items,
                ROUND(SUM(e.MENGE * e.NETPR), 2) AS total_po_value_usd
            FROM EKKO k
            JOIN LFA1 v ON k.LIFNR = v.LIFNR
            LEFT JOIN EKPO e ON k.EBELN = e.EBELN
            WHERE k.BSTAE = ''
            GROUP BY k.EBELN, v.NAME1, v.LAND1, k.BEDAT
            ORDER BY total_po_value_usd DESC
        """,
        "icon": "❓",
        "color": "#3498DB",
    },
}

SCHEMA_CONTEXT = """
You are a supply chain data analyst working with an SAP MM-structured ERP database in DuckDB.

Database schema:

LFA1 (Vendor Master):
  LIFNR VARCHAR PRIMARY KEY  -- vendor number
  NAME1 VARCHAR              -- vendor name
  LAND1 VARCHAR              -- country code
  ORT01 VARCHAR              -- city
  STRAS VARCHAR              -- street address
  TELF1 VARCHAR              -- phone
  KTOKK VARCHAR              -- account group
  ERDAT DATE                 -- creation date

MARA (Material Master):
  MATNR VARCHAR PRIMARY KEY  -- material number
  MAKTX VARCHAR              -- material description
  MATKL VARCHAR              -- material group (RAW/SEMI/FINISH/PKG/MRO)
  MEINS VARCHAR              -- base unit of measure
  NETPR DECIMAL              -- net price
  WAERS VARCHAR              -- currency
  MTART VARCHAR              -- material type
  ERDAT DATE                 -- creation date

EKKO (Purchase Order Header):
  EBELN VARCHAR PRIMARY KEY  -- PO number
  LIFNR VARCHAR              -- vendor (FK→LFA1)
  BEDAT DATE                 -- PO date
  BUKRS VARCHAR              -- company code
  EKORG VARCHAR              -- purchasing org
  BSART VARCHAR              -- PO type
  BSTAE VARCHAR              -- order acknowledgment (empty = unconfirmed)
  WAERS VARCHAR              -- currency
  ERNAM VARCHAR              -- created by

EKPO (Purchase Order Line Items):
  EBELN VARCHAR              -- PO number (FK→EKKO)
  EBELP VARCHAR              -- line item number
  MATNR VARCHAR              -- material (FK→MARA)
  MENGE DECIMAL              -- ordered quantity
  MEINS VARCHAR              -- unit
  NETPR DECIMAL              -- net price per unit
  WERKS VARCHAR              -- plant
  LGORT VARCHAR              -- storage location
  EINDT DATE                 -- scheduled delivery date
  WEMNG DECIMAL              -- goods receipt quantity
  LATE_FLAG INTEGER          -- 1 = delivery was late
  ACTUAL_DELIVERY DATE       -- actual delivery date

MSEG (Goods Receipts):
  MBLNR VARCHAR              -- material document number
  ZEILE VARCHAR              -- line
  BWART VARCHAR              -- movement type (101=GR)
  EBELN VARCHAR              -- PO number (FK→EKKO)
  EBELP VARCHAR              -- PO line (FK→EKPO)
  MATNR VARCHAR              -- material (FK→MARA)
  WERKS VARCHAR              -- plant
  LGORT VARCHAR              -- storage location
  MENGE DECIMAL              -- quantity received
  MEINS VARCHAR              -- unit
  BUDAT DATE                 -- posting date

RBKP (Invoice Verification):
  BELNR VARCHAR PRIMARY KEY  -- invoice document
  EBELN VARCHAR              -- PO number (FK→EKKO)
  BLDAT DATE                 -- invoice date
  BUDAT DATE                 -- posting date
  WRBTR DECIMAL              -- invoice amount
  WAERS VARCHAR              -- currency
  LIFNR VARCHAR              -- vendor (FK→LFA1)
  PO_AMOUNT DECIMAL          -- original PO total value
  MISMATCH_FLAG INTEGER      -- 1 = invoice > PO by >5%
  MISMATCH_PCT DECIMAL       -- % overcharge

PLAF (Demand Planning):
  MATNR VARCHAR              -- material (FK→MARA)
  WERKS VARCHAR              -- plant
  PERMO VARCHAR              -- planning period (YYYYMM)
  PBMNG DECIMAL              -- planned demand quantity
  MEINS VARCHAR              -- unit
  PLWRT DECIMAL              -- planned value USD
  SPIKE_FLAG INTEGER         -- 1 = demand >50% above baseline
  BASE_DEMAND DECIMAL        -- baseline demand

MARD (Stock Levels):
  MATNR VARCHAR              -- material (FK→MARA)
  WERKS VARCHAR              -- plant
  LGORT VARCHAR              -- storage location
  LABST DECIMAL              -- unrestricted stock
  EISBE DECIMAL              -- safety stock
  MEINS VARCHAR              -- unit
  STOCKOUT_FLAG INTEGER      -- 1 = stock below safety level
  DAYS_OF_SUPPLY DECIMAL     -- days of inventory remaining

Rules:
- Return ONLY a valid DuckDB SQL SELECT statement
- No UPDATE, DELETE, DROP, INSERT, or DDL statements
- Always use column aliases for readability
- Limit results to 200 rows unless user asks for more
- Use ROUND() for monetary values (2 decimals)
- Join tables as needed using the FK relationships above
"""
