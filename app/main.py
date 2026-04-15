from __future__ import annotations

import json

import streamlit as st

from core.subject_extractor import build_subject_profile

st.set_page_config(page_title="ICHIBAN - New Day", page_icon="🏡", layout="wide")

st.title("ICHIBAN - New Day")
st.subheader("Module 2 — Subject Property Extraction Engine")
st.caption("AI + Realtor Experience + Market Data + Judgment")

st.markdown(
    """
This screen tests the current Module 2 parser against a subject property PDF.
The goal is to extract key facts, identify missing items, and generate the issue notes that later feed **Data Verification Notes**.
"""
)

uploaded_pdf = st.file_uploader("Upload subject property PDF", type=["pdf"])

if uploaded_pdf is not None:
    pdf_bytes = uploaded_pdf.read()
    result = build_subject_profile(pdf_bytes)

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### Extracted Subject Property")
        st.json(result["subject_property"], expanded=True)

        st.markdown("### Data Issues")
        if result["data_issues"]:
            for issue in result["data_issues"]:
                st.write(f"- {issue}")
        else:
            st.success("No extraction issues were flagged.")

    with right:
        st.markdown("### Document Meta")
        st.json(result["document_meta"], expanded=True)

        st.markdown("### Field Sources")
        st.json(result["field_sources"], expanded=False)

    with st.expander("Extraction JSON Output", expanded=False):
        st.code(json.dumps(result, indent=2), language="json")

    with st.expander("Extracted Text Preview", expanded=False):
        preview = result["debug"].get("extracted_text_preview") or "No text preview available."
        st.text(preview)
else:
    st.info("Upload a subject property PDF to test Module 2.")
