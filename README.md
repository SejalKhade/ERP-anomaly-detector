# ERP Anomaly Detector — Supply Chain Analytics Platform

**AI-powered anomaly detection on a SAP MM-structured ERP database.**  
Natural language → SQL · 5 anomaly types · 820 purchase orders · Downloadable audit reports

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.10-yellow?style=flat-square)](https://duckdb.org)
[![Claude API](https://img.shields.io/badge/Claude-API-orange?style=flat-square)](https://anthropic.com)

---

## What This Project Demonstrates

| Skill | Details |
|---|---|
| **ERP / SAP MM domain knowledge** | Authentic table names (EKKO, EKPO, LFA1, MARA, MSEG, RBKP, PLAF, MARD) and procurement workflows |
| **Anomaly detection** | 5 rule-based detectors across 820 POs, flagging $1M+ in anomalous spend |
| **AI — Natural Language → SQL** | Claude API converts plain-English questions to validated DuckDB SQL in real time |
| **Data engineering** | Synthetic SAP dataset seeded at exact anomaly rates using Faker + NumPy |
| **Full-stack delivery** | Streamlit UI · DuckDB · Docker · cloud deployment |

---

## Anomaly Types Detected

| # | Anomaly | Count | Rate | Business Risk |
|---|---|---|---|---|
| 1 | ⏰ Late Deliveries | 407 | ~18% of PO lines | Production delays, SLA breaches |
| 2 | 💰 Invoice Mismatches | 110 | ~12% of invoices | Financial overcharges >5% |
| 3 | 📦 Stockout Risks | 75 | ~20% of SKU-plants | Supply disruption |
| 4 | 📈 Demand Spikes | 145 | ~10% of planning records | Procurement bottlenecks |
| 5 | ❓ Unconfirmed POs | 67 | ~8% of PO headers | Unacknowledged supplier orders |

---

## App Features

- **Anomaly Dashboard** — KPI tiles, drill-down tables, CSV export per anomaly type
- **NL→SQL Chat** — Ask any supply chain question in plain English; Claude writes and runs the SQL
- **Audit Report** — One-click JSON report across all 5 categories for audit trail
- **Demo Mode** — 6 pre-built queries run instantly without an API key

---

## Database Schema (SAP MM Structure)

| Table | SAP Description | Rows |
|---|---|---|
| LFA1 | Vendor Master | 50 |
| MARA | Material Master | 120 |
| EKKO | Purchase Order Headers | 820 |
| EKPO | Purchase Order Line Items | ~2,065 |
| MSEG | Goods Receipts | ~1,658 |
| RBKP | Invoice Verification | 820 |
| PLAF | Demand Planning | 1,440 |
| MARD | Stock / Inventory Levels | 360 |

---

## Sample NL→SQL Questions

```
"Which vendors have the most late deliveries?"
"Show all purchase orders over $100,000 with unconfirmed status"
"What materials are most at risk of stockout in plant P001?"
"Which vendors have the largest invoice overcharges this year?"
"Show demand spikes by material group"
```

---

## Run Locally

```bash
git clone https://github.com/SejalKhade/erp-anomaly-detector
cd erp-anomaly-detector
pip install -r requirements.txt
streamlit run app.py
```

> The database (`erp_data.duckdb`) is auto-generated on first run — no setup needed.  
> Set `ANTHROPIC_API_KEY` as an environment variable to enable the NL→SQL tab.

---

## Project Structure

```
erp_anomaly_detector/
├── app.py               # Streamlit UI — 3 tabs: Dashboard, NL→SQL, Audit Report
├── anomaly_queries.py   # 5 SQL detectors + full schema context for Claude
├── generate_data.py     # Synthetic SAP MM dataset generator (auto-runs on startup)
├── requirements.txt
└── Dockerfile
```

---

## Tech Stack

`Python` · `DuckDB` · `Streamlit` · `Anthropic Claude API` · `Faker` · `NumPy` · `Pandas` · `Docker`

---

*Built to demonstrate ERP data analytics and AI integration skills for Supply Chain and Data Analyst roles.*
