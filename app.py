"""
ERP Anomaly Detector — Supply Chain Analytics Platform
SAP MM-structured DuckDB database
NL→SQL via Claude API | 5 anomaly types | Downloadable audit report
"""

import os
import json
import re
import duckdb
import pandas as pd
import streamlit as st
from datetime import datetime
from anomaly_queries import ANOMALY_QUERIES, SCHEMA_CONTEXT

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERP Anomaly Detector",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 8px;
    padding: 1rem;
    border-left: 4px solid;
    margin-bottom: 0.5rem;
}
.anomaly-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    background: #FF6B6B22;
    color: #FF6B6B;
}
.stDataFrame { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── DB connection ─────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "erp_data.duckdb")

if not os.path.exists(DB_PATH):
    import generate_data
    generate_data.generate(DB_PATH)

@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_connection()

def run_query(sql: str) -> pd.DataFrame:
    return con.execute(sql).df()

# ── Claude NL→SQL ─────────────────────────────────────────────────────────────
def nl_to_sql(question: str) -> tuple[str, str]:
    """Returns (sql, error). Requires ANTHROPIC_API_KEY env var."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"{SCHEMA_CONTEXT}\n\nUser question: {question}\n\nReturn only the SQL query, no explanation, no markdown fences."
            }]
        )
        sql = msg.content[0].text.strip()
        # strip markdown fences if present
        sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\s*```$", "", sql)
        # safety: only allow SELECT
        if not sql.strip().upper().startswith("SELECT"):
            return "", "Only SELECT queries are allowed."
        return sql.strip(), ""
    except KeyError:
        return "", "ANTHROPIC_API_KEY not set. Add it in Settings → Secrets."
    except Exception as e:
        return "", str(e)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 ERP Anomaly Detector")
    st.markdown("**SAP MM Supply Chain Analytics**")
    st.divider()

    # DB stats
    st.markdown("### 📊 Database")
    tables = ["LFA1","MARA","EKKO","EKPO","MSEG","RBKP","PLAF","MARD"]
    for t in tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        st.markdown(f"- **{t}**: {n:,} rows")
    st.divider()

    st.markdown("### 🔍 Anomaly Summary")
    late = con.execute("SELECT COUNT(*) FROM EKPO WHERE LATE_FLAG=1").fetchone()[0]
    mismatch = con.execute("SELECT COUNT(*) FROM RBKP WHERE MISMATCH_FLAG=1").fetchone()[0]
    stockout = con.execute("SELECT COUNT(*) FROM MARD WHERE STOCKOUT_FLAG=1").fetchone()[0]
    spike = con.execute("SELECT COUNT(*) FROM PLAF WHERE SPIKE_FLAG=1").fetchone()[0]
    unconf = con.execute("SELECT COUNT(*) FROM EKKO WHERE BSTAE=''").fetchone()[0]

    st.markdown(f"⏰ **Late deliveries**: {late}")
    st.markdown(f"💰 **Invoice mismatches**: {mismatch}")
    st.markdown(f"📦 **Stockout risks**: {stockout}")
    st.markdown(f"📈 **Demand spikes**: {spike}")
    st.markdown(f"❓ **Unconfirmed POs**: {unconf}")

# ── main tabs ─────────────────────────────────────────────────────────────────
tab_dashboard, tab_nl, tab_report = st.tabs([
    "🚨 Anomaly Dashboard", "💬 Ask a Question (NL→SQL)", "📋 Audit Report"
])

# ── TAB 1: Anomaly Dashboard ──────────────────────────────────────────────────
with tab_dashboard:
    st.markdown("## Supply Chain Anomaly Dashboard")
    st.markdown("Automated detection across 5 anomaly types in SAP MM data.")

    # top KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    total_po_val = con.execute("SELECT ROUND(SUM(MENGE*NETPR),0) FROM EKPO").fetchone()[0]
    late_val = con.execute("SELECT ROUND(SUM(MENGE*NETPR),0) FROM EKPO WHERE LATE_FLAG=1").fetchone()[0]
    mismatch_val = con.execute("SELECT ROUND(SUM(WRBTR-PO_AMOUNT),0) FROM RBKP WHERE MISMATCH_FLAG=1").fetchone()[0]

    col1.metric("Total PO Value", f"${total_po_val/1e6:.1f}M")
    col2.metric("⏰ Late Deliveries", late, delta=f"{late/con.execute('SELECT COUNT(*) FROM EKPO').fetchone()[0]*100:.1f}% of lines", delta_color="inverse")
    col3.metric("💰 Invoice Overcharges", f"${mismatch_val/1e3:.0f}K", delta=f"{mismatch} invoices", delta_color="inverse")
    col4.metric("📦 Stockout Risks", stockout, delta=f"{stockout/360*100:.1f}% of SKU-plants", delta_color="inverse")
    col5.metric("❓ Unconfirmed POs", unconf, delta=f"{unconf/820*100:.1f}% of POs", delta_color="inverse")

    st.divider()

    # anomaly selector
    selected = st.selectbox(
        "Select anomaly type to explore:",
        list(ANOMALY_QUERIES.keys()),
        format_func=lambda k: f"{ANOMALY_QUERIES[k]['icon']} {ANOMALY_QUERIES[k]['title']}"
    )

    info = ANOMALY_QUERIES[selected]
    st.markdown(f"### {info['icon']} {info['title']}")
    st.caption(info["description"])

    with st.expander("View SQL query"):
        st.code(info["sql"].strip(), language="sql")

    df = run_query(info["sql"])
    st.markdown(f"**{len(df):,} anomalies detected**")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # download
    csv = df.to_csv(index=False)
    st.download_button(
        label=f"⬇️ Download {info['title']} CSV",
        data=csv,
        file_name=f"erp_{selected}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# ── TAB 2: NL→SQL ─────────────────────────────────────────────────────────────
with tab_nl:
    st.markdown("## Ask a Question")
    st.markdown("Type a plain-English supply chain question. Claude converts it to SQL and runs it against the ERP database.")

    example_questions = [
        "Which vendors have the most late deliveries?",
        "Show me all purchase orders over $100,000 with unconfirmed status",
        "What materials are most at risk of stockout in plant P001?",
        "Which vendors have the largest invoice overcharges this year?",
        "Show demand spikes by material group",
        "Top 10 materials by total PO value",
    ]

    with st.expander("💡 Example questions"):
        for q in example_questions:
            st.markdown(f"- {q}")

    question = st.text_input(
        "Your question:",
        placeholder="e.g. Which vendors have the most late deliveries?",
    )

    if st.button("🔍 Run Query", type="primary") and question:
        with st.spinner("Converting to SQL with Claude..."):
            sql, err = nl_to_sql(question)

        if err:
            st.error(f"Error: {err}")
        else:
            st.markdown("**Generated SQL:**")
            st.code(sql, language="sql")
            try:
                result_df = run_query(sql)
                st.markdown(f"**Results: {len(result_df):,} rows**")
                st.dataframe(result_df, use_container_width=True, hide_index=True)
                csv = result_df.to_csv(index=False)
                st.download_button("⬇️ Download results CSV", csv, "query_results.csv", "text/csv")
            except Exception as e:
                st.error(f"SQL execution error: {e}")

    # demo mode: run a canned example without API key
    st.divider()
    st.markdown("#### 🎮 Demo — try without API key")
    demo_q = st.selectbox("Pick an example:", example_questions)
    demo_sqls = {
        "Which vendors have the most late deliveries?": """
            SELECT v.NAME1 AS vendor, v.LAND1 AS country,
                   COUNT(*) AS late_deliveries,
                   ROUND(AVG(CAST(julian(e.ACTUAL_DELIVERY) - julian(e.EINDT) AS FLOAT)),1) AS avg_days_late,
                   ROUND(SUM(e.MENGE * e.NETPR),2) AS late_po_value_usd
            FROM EKPO e JOIN EKKO k ON e.EBELN=k.EBELN JOIN LFA1 v ON k.LIFNR=v.LIFNR
            WHERE e.LATE_FLAG=1
            GROUP BY v.NAME1, v.LAND1 ORDER BY late_deliveries DESC LIMIT 15
        """,
        "Show me all purchase orders over $100,000 with unconfirmed status": """
            SELECT k.EBELN AS po_number, v.NAME1 AS vendor, k.BEDAT AS po_date,
                   ROUND(SUM(e.MENGE*e.NETPR),2) AS po_value_usd
            FROM EKKO k JOIN LFA1 v ON k.LIFNR=v.LIFNR JOIN EKPO e ON k.EBELN=e.EBELN
            WHERE k.BSTAE='' GROUP BY k.EBELN, v.NAME1, k.BEDAT
            HAVING po_value_usd > 100000 ORDER BY po_value_usd DESC
        """,
        "What materials are most at risk of stockout in plant P001?": """
            SELECT d.MATNR, m.MAKTX AS material_desc, m.MATKL AS group,
                   d.LABST AS current_stock, d.EISBE AS safety_stock,
                   ROUND(d.LABST/NULLIF(d.EISBE,0)*100,1) AS pct_of_safety, d.DAYS_OF_SUPPLY
            FROM MARD d JOIN MARA m ON d.MATNR=m.MATNR
            WHERE d.WERKS='P001' AND d.STOCKOUT_FLAG=1 ORDER BY pct_of_safety ASC LIMIT 20
        """,
        "Which vendors have the largest invoice overcharges this year?": """
            SELECT v.NAME1 AS vendor, COUNT(*) AS mismatched_invoices,
                   ROUND(SUM(r.WRBTR-r.PO_AMOUNT),2) AS total_overcharge_usd,
                   ROUND(AVG(r.MISMATCH_PCT),1) AS avg_overcharge_pct
            FROM RBKP r JOIN LFA1 v ON r.LIFNR=v.LIFNR WHERE r.MISMATCH_FLAG=1
            GROUP BY v.NAME1 ORDER BY total_overcharge_usd DESC LIMIT 10
        """,
        "Show demand spikes by material group": """
            SELECT m.MATKL AS material_group, COUNT(*) AS spike_count,
                   ROUND(AVG((p.PBMNG-p.BASE_DEMAND)/NULLIF(p.BASE_DEMAND,0)*100),1) AS avg_spike_pct,
                   ROUND(SUM(p.PLWRT),2) AS total_planned_value_usd
            FROM PLAF p JOIN MARA m ON p.MATNR=m.MATNR WHERE p.SPIKE_FLAG=1
            GROUP BY m.MATKL ORDER BY spike_count DESC
        """,
        "Top 10 materials by total PO value": """
            SELECT e.MATNR, m.MAKTX AS description, m.MATKL AS group,
                   COUNT(DISTINCT e.EBELN) AS po_count,
                   ROUND(SUM(e.MENGE*e.NETPR),2) AS total_value_usd
            FROM EKPO e JOIN MARA m ON e.MATNR=m.MATNR
            GROUP BY e.MATNR, m.MAKTX, m.MATKL ORDER BY total_value_usd DESC LIMIT 10
        """,
    }
    if st.button("▶️ Run Demo Query"):
        sql = demo_sqls.get(demo_q, "SELECT 1")
        st.code(sql.strip(), language="sql")
        df = run_query(sql)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ── TAB 3: Audit Report ───────────────────────────────────────────────────────
with tab_report:
    st.markdown("## Audit Report")
    st.markdown("Full anomaly scan across all 5 categories. Download as JSON for audit trail.")

    if st.button("🔄 Generate Full Audit Report", type="primary"):
        report = {
            "generated_at": datetime.now().isoformat(),
            "database": DB_PATH,
            "summary": {
                "late_deliveries": int(late),
                "invoice_mismatches": int(mismatch),
                "stockout_risks": int(stockout),
                "demand_spikes": int(spike),
                "unconfirmed_pos": int(unconf),
                "total_anomalies": int(late + mismatch + stockout + spike + unconf),
            },
            "anomalies": {}
        }

        progress = st.progress(0)
        for i, (key, info) in enumerate(ANOMALY_QUERIES.items()):
            df = run_query(info["sql"])
            report["anomalies"][key] = {
                "title": info["title"],
                "count": len(df),
                "records": df.to_dict(orient="records")
            }
            st.markdown(f"{info['icon']} **{info['title']}**: {len(df)} anomalies")
            progress.progress((i + 1) / len(ANOMALY_QUERIES))

        json_str = json.dumps(report, indent=2, default=str)
        st.success(f"✅ Report complete — {report['summary']['total_anomalies']} total anomalies detected")
        st.download_button(
            label="⬇️ Download JSON Audit Report",
            data=json_str,
            file_name=f"erp_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
        with st.expander("Preview report JSON"):
            st.json(report["summary"])
