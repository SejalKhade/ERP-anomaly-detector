# ERP Anomaly Detector — Supply Chain Analytics Platform

> **AI-powered anomaly detection on a SAP MM-structured ERP database.**  
> Natural language → SQL · 5 anomaly types · 820 POs · Downloadable audit reports

---

## Live Demo

[![HuggingFace Spaces](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-yellow?style=for-the-badge)](https://huggingface.co/spaces/Sejjjallll/erp-anomaly-detector)

---

## What This Project Demonstrates

| Skill | Details |
|---|---|
| **ERP / SAP MM domain knowledge** | Authentic table names (EKKO, EKPO, LFA1, MARA, MSEG, RBKP, PLAF, MARD) and procurement workflows |
| **Anomaly detection at scale** | 5 rule-based detectors across 820 POs, catching $1M+ in anomalous spend |
| **Natural Language → SQL (AI)** | Claude API converts plain-English questions to read-only DuckDB SQL in real time |
| **Data engineering** | Synthetic SAP dataset seeded at precise anomaly rates using Faker + NumPy |
| **Full-stack app delivery** | Streamlit UI + DuckDB + Docker + HuggingFace Spaces deployment |

---

## Anomaly Types Detected

| Anomaly | Count | Rate | Business Risk |
|---|---|---|---|
| ⏰ Late Deliveries | 407 | ~18% of PO lines | Production delays, SLA breaches |
| 💰 Invoice Mismatches | 110 | ~12% of invoices | Financial loss, >5% overcharge |
| 📦 Stockout Risks | 75 | ~20% of SKU-plants | Supply disruption, lost sales |
| 📈 Demand Spikes | 145 | ~10% of planning records | Procurement bottlenecks |
| ❓ Unconfirmed POs | 67 | ~8% of PO headers | Unacknowledged supplier orders |

---

## App Features

- **Anomaly Dashboard** — KPI tiles + drill-down table per anomaly type, CSV export
- **NL→SQL Chat** — Type any supply chain question in plain English; Claude writes and executes the SQL
- **Audit Report** — One-click JSON report across all 5 anomaly categories for audit trail
- **Demo Mode** — 6 pre-built queries work without an API key

---

## Database Schema (SAP MM Structure)

| Table | Description | Rows |
|---|---|---|
| LFA1 | Vendor Master | 50 |
| MARA | Material Master | 120 |
| EKKO | PO Headers | 820 |
| EKPO | PO Line Items | ~2,065 |
| MSEG | Goods Receipts | ~1,658 |
| RBKP | Invoice Verification | 820 |
| PLAF | Demand Planning | 1,440 |
| MARD | Stock Levels | 360 |

---

## Tech Stack

`Python` · `DuckDB` · `Streamlit` · `Anthropic Claude API` · `Docker` · `Faker` · `NumPy` · `Pandas`

---

## Run Locally

```bash
git clone https://github.com/Sejjjallll/erp-anomaly-detector
cd erp-anomaly-detector
pip install -r requirements.txt
python generate_data.py        # creates erp_data.duckdb (~2 sec)
streamlit run app.py
```

Set `ANTHROPIC_API_KEY` in your environment to enable the NL→SQL tab.

---

## Deploy to HuggingFace Spaces

1. Create a new Space → SDK: **Streamlit**
2. Upload all files (or connect this repo)
3. Settings → Repository Secrets → add `ANTHROPIC_API_KEY`
4. Space auto-builds and deploys

---

## Project Structure

```
erp_anomaly_detector/
├── app.py               # Streamlit UI (3 tabs)
├── anomaly_queries.py   # 5 SQL detectors + schema context for Claude
├── generate_data.py     # Synthetic SAP MM dataset generator
├── requirements.txt
└── Dockerfile
```

---

## Sample NL→SQL Queries

```
"Which vendors have the most late deliveries?"
"Show purchase orders over $100,000 with unconfirmed status"
"What materials are most at risk of stockout in plant P001?"
"Which vendors have the largest invoice overcharges this year?"
```

---

*Built to demonstrate practical AI integration with ERP/supply chain data for data analyst and supply chain engineer roles.*
