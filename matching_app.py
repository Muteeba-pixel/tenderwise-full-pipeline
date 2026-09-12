import streamlit as st
import json
from muteeba_matching import (
    run_full_analysis,
    adapt_analysis_output,
    SAMPLE_INPUT
)

st.set_page_config(
    page_title="TenderWise AI - Bid Readiness Analysis",
    page_icon="📊",
    layout="wide"
)

# ---------------- Header ----------------
st.title("📊 TenderWise AI")
st.markdown("#### Bid Readiness Analysis — Matching, Risk & Decision Engine")
st.markdown(
    "This module takes the structured tender and company analysis produced by the "
    "**PDF Processing + Analysis** stage and generates a complete bid-readiness "
    "assessment: requirement matching, a compliance score, risk analysis, a bid "
    "recommendation, an AI-generated report, and a submission checklist."
)

st.divider()

# ---------------- Input Section ----------------
st.subheader("📥 Input: Tender & Company Analysis")

with st.expander("ℹ️ Where do I get this JSON from?", expanded=False):
    st.markdown(
        "- Run the **Tender + Company Analysis** step first (PDF upload and Analyze).\n"
        "- Click **Download JSON** on that page.\n"
        "- Paste the contents of that file below, or upload it directly."
    )

input_method = st.radio(
    "Choose an input method",
    ["Paste JSON", "Upload JSON file", "Use sample data (for testing)"],
    horizontal=True
)

analysis_output = None
input_error = None

if input_method == "Paste JSON":
    json_input = st.text_area(
        "Paste the analysis JSON here",
        height=250,
        placeholder='{"tender_analysis": {...}, "company_analysis": {...}}'
    )
    if json_input.strip():
        try:
            real_output = json.loads(json_input)
            analysis_output = adapt_analysis_output(real_output)
        except Exception as e:
            input_error = str(e)

elif input_method == "Upload JSON file":
    uploaded_file = st.file_uploader("Upload the analysis JSON file", type=["json"])
    if uploaded_file is not None:
        try:
            real_output = json.load(uploaded_file)
            analysis_output = adapt_analysis_output(real_output)
        except Exception as e:
            input_error = str(e)

else:
    st.info("Using built-in sample tender and company data for a quick demo.")
    analysis_output = SAMPLE_INPUT

if input_error:
    st.error(f"Could not read the JSON: {input_error}")

st.divider()

# ---------------- Run Analysis ----------------
run_clicked = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

if run_clicked:
    if analysis_output is None:
        st.warning("Please provide the input JSON (or select sample data) before running the analysis.")
        st.stop()

    with st.spinner("Matching requirements, assessing risk, and generating the bid decision..."):
        result = run_full_analysis(analysis_output)

    st.success("Analysis complete.")
    st.divider()

    # ---------------- Summary Metrics ----------------
    compliance = result["compliance"]
    decision = result["decision"]

    st.subheader("📈 Compliance Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Compliance", f"{compliance['compliance_percentage']}%")
    col2.metric("Matched", compliance["matched"])
    col3.metric("Missing", compliance["missing"])
    col4.metric("Unclear", compliance["unclear"])

    st.divider()

    # ---------------- Decision ----------------
    decision_icons = {"BID": "🟢", "CONDITIONAL BID": "🟡", "NO-BID": "🔴"}
    icon = decision_icons.get(decision["decision"], "⚪")

    st.subheader("🎯 Bid Recommendation")
    st.markdown(f"### {icon} {decision['decision']}")
    st.write(decision["reason"])

    st.divider()

    # ---------------- Requirement Matching ----------------
    st.subheader("🔍 Requirement Matching")
    status_icons = {"Matched": "✅", "Missing": "❌", "Unclear": "⚠️"}
    for r in result["matched_results"]:
        icon = status_icons.get(r.get("status"), "•")
        with st.expander(f"{icon} [{r.get('priority')}] {r.get('requirement')}"):
            st.write(f"**Category:** {r.get('category')}")
            st.write(f"**Status:** {r.get('status')}")
            st.write(f"**Evidence:** {r.get('company_evidence')}")
            st.write(f"**Reason:** {r.get('reason')}")

    st.divider()

    # ---------------- Risk Analysis ----------------
    st.subheader("⚠️ Risk Analysis")
    risks = result["risks"]

    risk_tabs = st.tabs(["🔴 High Risks", "🟠 Medium Risks", "🟢 Low Risks"])
    risk_levels = [
        ("high_risks", risk_tabs[0]),
        ("medium_risks", risk_tabs[1]),
        ("low_risks", risk_tabs[2]),
    ]
    for key, tab in risk_levels:
        with tab:
            items = risks.get(key, [])
            if not items:
                st.write("None identified.")
            for item in items:
                st.markdown(f"**{item.get('risk')}**")
                st.write(f"Impact: {item.get('impact')}")
                st.caption(f"Reason: {item.get('reason')}")
                st.markdown("---")

    st.divider()

    # ---------------- AI Report ----------------
    st.subheader("📄 AI-Generated Report")
    report = result["report"]
    report_sections = [
        ("Executive Summary", "executive_summary"),
        ("Tender Overview", "tender_overview"),
        ("Company Overview", "company_overview"),
        ("Compliance Summary", "compliance_summary"),
        ("Matched Requirements", "matched_requirements"),
        ("Missing Requirements", "missing_requirements"),
        ("Unclear Requirements", "unclear_requirements"),
        ("Risk Analysis", "risk_analysis"),
        ("Bid Recommendation", "bid_recommendation"),
        ("Key Reasons", "key_reasons"),
        ("Recommended Actions", "recommended_actions"),
    ]
    for title, key in report_sections:
        with st.expander(title):
            st.write(report.get(key, "Not available."))

    st.divider()

    # ---------------- Submission Checklist ----------------
    st.subheader("📋 Submission Checklist")
    checklist = result["checklist"]
    if not checklist:
        st.write("No document checklist items were generated.")
    for item in checklist:
        checked = item.get("status") == "checked"
        st.checkbox(
            f"{item.get('item')} — {item.get('priority')}",
            value=checked,
            disabled=True,
            key=item.get("item")
        )

    st.divider()

    # ---------------- Download ----------------
    final_json = json.dumps(result, indent=2, ensure_ascii=False)
    st.download_button(
        "⬇️ Download Full Result (JSON)",
        final_json,
        "tenderwise_bid_analysis.json",
        "application/json",
        use_container_width=True
    )
