import streamlit as st
import json

from sami_processor import process_document
from faizan_analysis import analyze_documents


st.set_page_config(
    page_title="TenderWise AI",
    page_icon="📄",
    layout="wide"
)


st.title("TenderWise AI")
st.write("Tender + Company Analysis")


col1,col2=st.columns(2)

with col1:
    tender_file=st.file_uploader(
        "Upload Tender PDF",
        type=["pdf"]
    )

with col2:
    company_file=st.file_uploader(
        "Upload Company Profile PDF",
        type=["pdf"]
    )


if tender_file and company_file:

    if st.button("Analyze Documents",use_container_width=True):

        try:

            with st.spinner("Sami: Processing PDFs..."):

                tender_data=process_document(
                    tender_file,
                    tender_file.name
                )

                company_data=process_document(
                    company_file,
                    company_file.name
                )

            st.success("PDF processing completed.")

            with st.spinner("Analyzing documents..."):

                result=analyze_documents(
                    tender_data,
                    company_data
                )

            st.success("Tender and company analysis completed.")

            st.divider()

            st.header("Tender Analysis")

            st.json(result["tender_analysis"])

            st.divider()

            st.header("Company Analysis")

            st.json(result["company_analysis"])

            st.divider()

            final_json=json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )

            st.download_button(
                "Download JSON",
                final_json,
                "faizan_analysis.json",
                "application/json"
            )

        except Exception as e:
            st.error(f"Error: {e}")