import streamlit as st
import json

from sami_processor import process_document
from faizan_analysis import analyze_documents
from muteeba_matching import run_full_analysis, adapt_analysis_output

st.set_page_config(
    page_title="TenderWise AI - Full Pipeline",
    page_icon="📄",
    layout="wide"
)

st.title("📄 TenderWise AI")
st.markdown("#### End-to-End Bid Readiness Analysis")
st.markdown(
    "Upload a tender PDF and a company profile PDF. This app will process the "
    "documents, extract structured requirements and company capabilities, run "
    "requirement matching and risk analysis, and produce a final bid recommendation "
    "— all in a single step."
)

st.divider()

# ---------------- Upload ----------------
col1, col2 = st.columns(2)

with col1:
    tender_file = st.file_uploader("Upload Tender PDF", type=["pdf"])

with col2:
    company_file = st.file_uploader("Upload Company Profile PDF", type=["pdf"])

if tender_file and company_file:

    if st.button("🚀 Analyze Full Pipeline", use_container_width=True, type="primary"):

        try:
            # ---- Stage 1: PDF Processing ----
            with st.spinner("Stage 1/3: Processing PDFs..."):
                tender_data = process_document(tender_file, tender_file.name)
                company_data = process_document(company_file, company_file.name)

            st.success("Stage 1 complete: PDF processing finished.")

            # ---- Stage 2: Tender + Company Analysis ----
            with st.spinner("Stage 2/3: Analyzing tender and company documents..."):
                analysis_result = analyze_documents(tender_data, company_data)

            st.success("Stage 2 complete: Tender and company analysis finished.")

            # ---- Stage 3: Matching + Risk + Decision + Report + Checklist ----
            with st.spinner("Stage 3/3: Running matching, risk analysis, and decision engine..."):
                adapted_input = adapt_analysis_output(analysis_result)
                final_result = run_full_analysis(adapted_input)

            st.success("Stage 3 complete: Bid-readiness analysis finished.")
            st.divider()

            # ---------------- Summary Metrics ----------------
            compliance = final_result["compliance"]
            decision = final_result["decision"]

            st.subheader("📈 Compliance Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Compliance", f"{compliance['compliance_percentage']}%")
            c2.metric("Matched", compliance["matched"])
            c3.metric("Missing", compliance["missing"])
            c4.metric("Unclear", compliance["unclear"])

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
            for r in final_result["matched_results"]:
                icon = status_icons.get(r.get("status"), "•")
                with st.expander(f"{icon} [{r.get('priority')}] {r.get('requirement')}"):
                    st.write(f"**Category:** {r.get('category')}")
                    st.write(f"**Status:** {r.get('status')}")
                    st.write(f"**Evidence:** {r.get('company_evidence')}")
                    st.write(f"**Reason:** {r.get('reason')}")

            st.divider()

            # ---------------- Risk Analysis ----------------
            st.subheader("⚠️ Risk Analysis")
            risks = final_result["risks"]
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
            report = final_result["report"]
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
            checklist = final_result["checklist"]
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
            full_output = {
                "tender_analysis": analysis_result["tender_analysis"],
                "company_analysis": analysis_result["company_analysis"],
                "bid_readiness_analysis": final_result
            }
            final_json = json.dumps(full_output, indent=2, ensure_ascii=False)
            st.download_button(
                "⬇️ Download Full Result (JSON)",
                final_json,
                "tenderwise_full_analysis.json",
                "application/json",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Error: {e}")

else:
    st.info("Please upload both a Tender PDF and a Company Profile PDF to begin.")
