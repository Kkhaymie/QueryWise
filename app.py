import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
import re
import json
import requests

st.set_page_config(page_title="QueryWise", page_icon="🔍", layout="wide")

# ── Session state ──────────────────────────────────────────────────────────────
if "db_conn"     not in st.session_state: st.session_state.db_conn     = None
if "schema_info" not in st.session_state: st.session_state.schema_info = ""
if "api_key"     not in st.session_state: st.session_state.api_key     = ""
if "history"     not in st.session_state: st.session_state.history     = []

MISTRAL_MODEL = "mistral-large-latest"
MISTRAL_URL   = "https://api.mistral.ai/v1/chat/completions"

# ── Mistral call ───────────────────────────────────────────────────────────────
def call_mistral(system_msg, user_msg):
    key = st.session_state.api_key
    r = requests.post(
        MISTRAL_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": MISTRAL_MODEL,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Mistral {r.status_code}: {r.text}")
    return r.json()["choices"][0]["message"]["content"].strip()

# ── Load dataset ───────────────────────────────────────────────────────────────
def load_dataset(f):
    ext = f.name.rsplit(".", 1)[-1].lower()
    df  = pd.read_csv(f) if ext == "csv" else pd.read_excel(f)
    df.columns = [re.sub(r"[^\w]", "_", c).lower().strip("_") for c in df.columns]
    tname = re.sub(r"[^\w]", "_", os.path.splitext(f.name)[0]).lower()[:40]
    conn  = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(tname, conn, index=False, if_exists="replace")
    cols   = conn.execute(f"PRAGMA table_info({tname})").fetchall()
    schema = f"Table: {tname}\nColumns:\n" + "".join(f"  - {c[1]} ({c[2]})\n" for c in cols)
    sample = pd.read_sql(f"SELECT * FROM {tname} LIMIT 5", conn)
    schema += f"\nSample rows:\n{sample.to_string(index=False)}"
    return conn, tname, schema

# ── Auto chart ─────────────────────────────────────────────────────────────────
def make_chart(df):
    num = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(exclude="number").columns.tolist()
    time_kw = ["month","year","date","quarter","week","period","time"]
    time_cols = [c for c in df.columns if any(k in c.lower() for k in time_kw)]
    if time_cols and num:
        return px.line(df, x=time_cols[0], y=num[0], markers=True, color_discrete_sequence=["#c97d4e"])
    if cat and num:
        return px.bar(df.sort_values(num[0], ascending=False).head(15),
                      x=cat[0], y=num[0], text_auto=".2s", color_discrete_sequence=["#c97d4e"])
    if len(num) >= 2:
        return px.scatter(df, x=num[0], y=num[1], color_discrete_sequence=["#c97d4e"])
    return None

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🔍 QueryWise")
    st.caption("Text-to-SQL · Mistral AI")
    st.divider()

    st.subheader("Step 1 — API Key")
    key_in = st.text_input("Mistral API Key", type="password", placeholder="paste key here")
    if key_in:
        st.session_state.api_key = key_in
        st.success("Key saved for this session")

    st.subheader("Step 2 — Upload Dataset")
    uploaded = st.file_uploader("CSV or Excel", type=["csv","xlsx","xls"])
    if uploaded:
        try:
            conn, tname, schema = load_dataset(uploaded)
            st.session_state.db_conn     = conn
            st.session_state.table_name  = tname
            st.session_state.schema_info = schema
            nrows = pd.read_sql(f"SELECT COUNT(*) as n FROM {tname}", conn).iloc[0,0]
            ncols = len(conn.execute(f"PRAGMA table_info({tname})").fetchall())
            st.success(f"Loaded: {nrows} rows × {ncols} cols")
        except Exception as e:
            st.error(f"Load error: {e}")

    st.divider()
    st.caption("Only SELECT queries run. Raw data never leaves your machine.")
    if st.button("Clear history"):
        st.session_state.history = []
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.title("QueryWise — Text-to-SQL")
st.caption("Ask a business question in plain English. Get SQL, a chart, and a business insight.")
st.divider()

# Guard
if not st.session_state.api_key:
    st.warning("👈 Enter your Mistral API key in the sidebar to get started.")
    st.stop()
if st.session_state.db_conn is None:
    st.warning("👈 Upload a CSV or Excel dataset in the sidebar.")
    st.stop()

# Schema
with st.expander("View dataset schema"):
    st.code(st.session_state.schema_info)

# Suggested questions
st.subheader("💡 Suggested Questions")
if st.button("Generate 6 business questions from my dataset"):
    with st.spinner("Thinking..."):
        try:
            raw = call_mistral(
                "Return ONLY a JSON array of exactly 6 business question strings. No markdown, no explanation.",
                f"Schema:\n{st.session_state.schema_info}\n\nReturn JSON array:"
            )
            raw = re.sub(r"```(?:json)?|```", "", raw).strip()
            st.session_state["suggestions"] = json.loads(raw)
        except Exception as e:
            st.error(f"Could not generate questions: {e}")

if st.session_state.get("suggestions"):
    c1, c2 = st.columns(2)
    for i, q in enumerate(st.session_state["suggestions"]):
        col = c1 if i % 2 == 0 else c2
        if col.button(q, key=f"sq_{i}"):
            st.session_state["pending_q"] = q
            st.rerun()

st.divider()

# Question box
st.subheader("🗣️ Ask Your Question")

# Seed text area when a suggested question button is clicked
if "pending_q" in st.session_state and st.session_state["pending_q"]:
    st.session_state["question_input"] = st.session_state.pop("pending_q")
elif "question_input" not in st.session_state:
    st.session_state["question_input"] = ""

st.text_area(
    "Business question",
    key="question_input",
    height=80,
    placeholder="Which region generated the highest revenue?",
    label_visibility="collapsed",
)

run = st.button("▶ Run Query", type="primary", use_container_width=False)

# ── Pipeline ───────────────────────────────────────────────────────────────────
if run:
    question = st.session_state.get("question_input", "").strip()
    if not question:
        st.warning("Please type a question first.")
        st.stop()

    # 1. Generate SQL
    with st.spinner("Step 1/3 — Generating SQL..."):
        try:
            sql_raw = call_mistral(
                (
                    "You are an expert SQLite analyst. "
                    "Return ONLY the raw SQL SELECT query — no markdown, no backticks, no explanation. "
                    "Never use DROP, DELETE, UPDATE, INSERT, CREATE, ALTER. "
                    "If unanswerable with this schema, return exactly: CANNOT_ANSWER"
                ),
                f"Schema:\n{st.session_state.schema_info}\n\nQuestion: {question}\n\nSQL:"
            )
            sql = re.sub(r"```(?:sql)?|```", "", sql_raw, flags=re.IGNORECASE).strip()
        except Exception as e:
            st.error(f"❌ Mistral error while generating SQL: {e}")
            st.stop()

    if sql.upper().strip() == "CANNOT_ANSWER":
        st.warning("⚠️ This question cannot be answered from the available data. Try rephrasing.")
        st.stop()

    bad = re.findall(r"\b(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)\b", sql, re.IGNORECASE)
    if bad:
        st.error(f"🚫 Blocked — query contained unsafe keyword(s): {bad}")
        st.stop()

    st.markdown("**Generated SQL:**")
    st.code(sql, language="sql")

    # 2. Execute
    with st.spinner("Step 2/3 — Running query..."):
        try:
            df = pd.read_sql(sql, st.session_state.db_conn).head(500)
        except Exception as e:
            st.error(f"❌ Query failed: {e}")
            st.stop()

    if df.empty:
        st.info("Query returned no rows.")
        st.stop()

    st.success(f"✅ Query returned {len(df)} row(s)")

    # 3. Insight
    with st.spinner("Step 3/3 — Generating insight & recommendation..."):
        try:
            insight = call_mistral(
                (
                    "You are a senior business analyst writing for a non-technical executive. "
                    "Given the business question and query results below, write a concise report with exactly three paragraphs:\n"
                    "Paragraph 1 — KEY FINDING: what the data directly shows.\n"
                    "Paragraph 2 — BUSINESS IMPLICATION: what this means for the business.\n"
                    "Paragraph 3 — RECOMMENDATION: one concrete action to take.\n"
                    "Plain English only. No bullet points. No markdown."
                ),
                f"Question: {question}\n\nResults (top 15 rows):\n{df.head(15).to_string(index=False)}"
            )
        except Exception as e:
            insight = None
            st.warning(f"Could not generate insight: {e}")

    # 4. Display tabs
    tab_chart, tab_table, tab_insight = st.tabs(["📊 Chart", "📋 Table", "💬 Insight & Recommendation"])

    with tab_chart:
        fig = make_chart(df)
        if fig:
            fig.update_layout(plot_bgcolor="#ffffff", paper_bgcolor="#ffffff")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No chart could be auto-generated for this result shape.")
            st.dataframe(df, use_container_width=True)

    with tab_table:
        st.dataframe(df, use_container_width=True, height=340)
        st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(),
                           "results.csv", "text/csv")

    with tab_insight:
        if insight:
            parts  = [p.strip() for p in insight.split("\n\n") if p.strip()]
            labels = ["🔍 Key Finding", "📈 Business Implication", "✅ Recommendation"]
            for idx, para in enumerate(parts):
                st.markdown(f"**{labels[idx] if idx < len(labels) else ''}**")
                st.info(para)
        else:
            st.warning("No insight was generated.")

    # Save to history
    st.session_state.history.append({
        "question": question, "sql": sql,
        "rows": len(df), "insight": insight or ""
    })

# ── History ────────────────────────────────────────────────────────────────────
st.divider()
with st.expander("⚖️ Accuracy, Limitations & Safeguards"):
    st.markdown("""
**Accuracy** — SQL quality depends on clear column names. Always review the generated query.  
**Limitations** — Single-table datasets only. Results capped at 500 rows.  
**Safeguards** — Only SELECT runs. Only your question and schema are sent to Mistral. Raw data never leaves your machine.
    """)

if st.session_state.history:
    st.subheader("🕓 Query History")
    for i, h in enumerate(reversed(st.session_state.history)):
        with st.expander(f"Q{len(st.session_state.history)-i}: {h['question'][:80]}"):
            st.markdown(f"**Rows:** {h['rows']}")
            st.code(h["sql"], language="sql")
            if h.get("insight"):
                st.markdown("**Insight:**")
                st.info(h["insight"])