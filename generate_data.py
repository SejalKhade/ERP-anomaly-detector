"""
Generate SAP MM-structured synthetic ERP dataset.
8 tables: LFA1, MARA, EKKO, EKPO, MSEG, RBKP, PLAF, MARD
Seeded anomalies:
  - Late deliveries: 18% of PO line items
  - Invoice mismatches: 12% of invoices
  - Stockout risks: 20% of materials
  - Demand spikes: 10% of demand planning records
  - Unconfirmed POs: 8% of PO headers
"""

import random
import duckdb
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

def generate(db_path: str = "erp_data.duckdb"):
    fake = Faker()
    random.seed(42)
    np.random.seed(42)

    def rand_date(start, end):
        return start + timedelta(days=random.randint(0, (end - start).days))

    START = datetime(2024, 1, 1)
    END   = datetime(2024, 12, 31)

    VENDORS = 50
    MATERIALS = 120
    PO_HEADERS = 820
    LINES_PER_PO_MAX = 4

    MATERIAL_GROUPS = ["RAW", "SEMI", "FINISH", "PKG", "MRO"]
    PLANTS = ["P001", "P002", "P003"]
    STORAGE_LOCS = ["SL01", "SL02", "SL03"]
    UNITS = ["EA", "KG", "L", "M", "BOX"]
    COMPANY_CODE = "1000"
    PURCH_ORG = "PO01"

    print("Generating LFA1 (vendors)...")
    lfa1_rows = []
    for i in range(1, VENDORS + 1):
        lfa1_rows.append({
            "LIFNR": f"V{i:04d}",
            "NAME1": fake.company(),
            "LAND1": random.choice(["US", "CN", "DE", "JP", "MX", "IN"]),
            "ORT01": fake.city(),
            "STRAS": fake.street_address(),
            "TELF1": fake.phone_number()[:20],
            "KTOKK": "0001",
            "ERDAT": rand_date(datetime(2018,1,1), datetime(2022,12,31)).strftime("%Y-%m-%d"),
        })
    lfa1 = pd.DataFrame(lfa1_rows)

    print("Generating MARA (materials)...")
    mara_rows = []
    for i in range(1, MATERIALS + 1):
        unit = random.choice(UNITS)
        price = round(random.uniform(5, 5000), 2)
        mara_rows.append({
            "MATNR": f"MAT{i:05d}",
            "MAKTX": fake.bs().title()[:40],
            "MATKL": random.choice(MATERIAL_GROUPS),
            "MEINS": unit,
            "NETPR": price,
            "WAERS": "USD",
            "MTART": random.choice(["ROH","HALB","FERT","VERP","HIBE"]),
            "ERDAT": rand_date(datetime(2018,1,1), datetime(2022,12,31)).strftime("%Y-%m-%d"),
        })
    mara = pd.DataFrame(mara_rows)

    print("Generating EKKO (PO headers)...")
    ekko_rows = []
    for i in range(1, PO_HEADERS + 1):
        doc_date = rand_date(START, END - timedelta(days=30))
        confirmed = random.random() > 0.08
        ekko_rows.append({
            "EBELN": f"45{i:07d}",
            "LIFNR": f"V{random.randint(1, VENDORS):04d}",
            "BEDAT": doc_date.strftime("%Y-%m-%d"),
            "BUKRS": COMPANY_CODE,
            "EKORG": PURCH_ORG,
            "BSART": "NB",
            "BSTAE": "AB" if confirmed else "",
            "WAERS": "USD",
            "ERNAM": fake.first_name(),
        })
    ekko = pd.DataFrame(ekko_rows)

    print("Generating EKPO (PO lines)...")
    ekpo_rows = []
    for _, po in ekko.iterrows():
        n_lines = random.randint(1, LINES_PER_PO_MAX)
        for ln in range(1, n_lines + 1):
            mat = mara.sample(1).iloc[0]
            qty = round(random.uniform(10, 500), 0)
            net_price = round(mat["NETPR"] * random.uniform(0.9, 1.1), 2)
            delivery_date = pd.to_datetime(po["BEDAT"]) + timedelta(days=random.randint(7, 60))
            is_late = random.random() < 0.18
            actual_delivery = delivery_date + timedelta(days=random.randint(5,30)) if is_late else delivery_date - timedelta(days=random.randint(0,3))
            ekpo_rows.append({
                "EBELN": po["EBELN"],
                "EBELP": f"{ln*10:04d}",
                "MATNR": mat["MATNR"],
                "MENGE": qty,
                "MEINS": mat["MEINS"],
                "NETPR": net_price,
                "PEINH": 1,
                "WERKS": random.choice(PLANTS),
                "LGORT": random.choice(STORAGE_LOCS),
                "EINDT": delivery_date.strftime("%Y-%m-%d"),
                "WEMNG": qty if not is_late else 0,
                "LATE_FLAG": int(is_late),
                "ACTUAL_DELIVERY": actual_delivery.strftime("%Y-%m-%d"),
            })
    ekpo = pd.DataFrame(ekpo_rows)

    print("Generating MSEG (goods receipts)...")
    mseg_rows = []
    for _, line in ekpo.iterrows():
        if line["WEMNG"] > 0:
            gr_date = pd.to_datetime(line["ACTUAL_DELIVERY"])
            mseg_rows.append({
                "MBLNR": f"50{len(mseg_rows)+1:08d}",
                "ZEILE": "0001",
                "BWART": "101",
                "EBELN": line["EBELN"],
                "EBELP": line["EBELP"],
                "MATNR": line["MATNR"],
                "WERKS": line["WERKS"],
                "LGORT": line["LGORT"],
                "MENGE": line["WEMNG"],
                "MEINS": line["MEINS"],
                "BUDAT": gr_date.strftime("%Y-%m-%d"),
            })
    mseg = pd.DataFrame(mseg_rows)

    print("Generating RBKP (invoices)...")
    rbkp_rows = []
    inv_id = 1
    for _, po in ekko.iterrows():
        po_lines = ekpo[ekpo["EBELN"] == po["EBELN"]]
        if po_lines.empty:
            continue
        total_po = (po_lines["MENGE"] * po_lines["NETPR"]).sum()
        is_mismatch = random.random() < 0.12
        inv_amount = round(total_po * random.uniform(1.06, 1.20), 2) if is_mismatch else round(total_po * random.uniform(0.98, 1.02), 2)
        inv_date = pd.to_datetime(po["BEDAT"]) + timedelta(days=random.randint(15, 75))
        rbkp_rows.append({
            "BELNR": f"51{inv_id:08d}",
            "EBELN": po["EBELN"],
            "BLDAT": inv_date.strftime("%Y-%m-%d"),
            "BUDAT": inv_date.strftime("%Y-%m-%d"),
            "WRBTR": inv_amount,
            "WAERS": "USD",
            "LIFNR": po["LIFNR"],
            "PO_AMOUNT": round(total_po, 2),
            "MISMATCH_FLAG": int(is_mismatch),
            "MISMATCH_PCT": round((inv_amount - total_po) / total_po * 100, 2) if is_mismatch else 0.0,
        })
        inv_id += 1
    rbkp = pd.DataFrame(rbkp_rows)

    print("Generating PLAF (demand planning)...")
    plaf_rows = []
    for _, mat in mara.iterrows():
        for month in range(1, 13):
            base_demand = random.uniform(100, 2000)
            is_spike = random.random() < 0.10
            planned = round(base_demand * random.uniform(1.6, 2.5), 0) if is_spike else round(base_demand * random.uniform(0.85, 1.15), 0)
            plaf_rows.append({
                "MATNR": mat["MATNR"],
                "WERKS": random.choice(PLANTS),
                "PERMO": f"2024{month:02d}",
                "PBMNG": planned,
                "MEINS": mat["MEINS"],
                "PLWRT": round(planned * mat["NETPR"], 2),
                "SPIKE_FLAG": int(is_spike),
                "BASE_DEMAND": round(base_demand, 0),
            })
    plaf = pd.DataFrame(plaf_rows)

    print("Generating MARD (stock levels)...")
    mard_rows = []
    for _, mat in mara.iterrows():
        for plant in PLANTS:
            unrestricted = round(random.uniform(0, 1000), 0)
            safety_stock = round(random.uniform(50, 300), 0)
            is_stockout = random.random() < 0.20
            if is_stockout:
                unrestricted = round(random.uniform(0, safety_stock * 0.4), 0)
            mard_rows.append({
                "MATNR": mat["MATNR"],
                "WERKS": plant,
                "LGORT": random.choice(STORAGE_LOCS),
                "LABST": unrestricted,
                "EISBE": safety_stock,
                "MEINS": mat["MEINS"],
                "STOCKOUT_FLAG": int(is_stockout),
                "DAYS_OF_SUPPLY": round(unrestricted / max(safety_stock * 0.1, 1), 1),
            })
    mard = pd.DataFrame(mard_rows)

    print("Writing to DuckDB...")
    con = duckdb.connect(db_path)
    tables = {
        "LFA1": lfa1, "MARA": mara, "EKKO": ekko, "EKPO": ekpo,
        "MSEG": mseg, "RBKP": rbkp, "PLAF": plaf, "MARD": mard,
    }
    for tname, df in tables.items():
        con.execute(f"DROP TABLE IF EXISTS {tname}")
        con.execute(f"CREATE TABLE {tname} AS SELECT * FROM df")
        print(f"  {tname}: {len(df):,} rows")
    con.close()
    print(f"\nDone — {db_path} written.")


if __name__ == "__main__":
    generate()
