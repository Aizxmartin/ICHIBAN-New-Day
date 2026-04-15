import io
import json
import os
import sys
from typing import Any, Dict

import streamlit as st

CURRENT_DIR = os.path.dirname(__file__)
APP_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
REPO_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from core.subject_extractor import extract_subject_property
except Exception as e:
    extract_subject_property = None
    IMPORT_ERROR = str(e)
else:
    IMPORT_ERROR = None

st.set_page_config(page_title="Module 2 - Subject Extraction", layout="wide")

st.title("Module 2 — Subject Property Extraction Engine")
st.caption("AI + Realtor Experience + Market Data + Judgment")

st.write(
    "Upload a subject property PDF to extract core facts, identify missing items, "
    "and generate issue notes that will later feed Data Verification Notes."
)

uploaded = st.file_uploader("Upload subject property PDF", type=["pdf"])

def render_results(result: Dict[str, Any]) -> None:
    subject = result.get("subject_property", {}) or {}
    data_issues = result.get("data_issues", []) or []
    field_sources = result.get("field_sources", {}) or {}
    document_meta = result.get("document_meta", {}) or {}
    raw_text = result.get("raw_text_preview", "") or ""

    st.subheader("Extracted Subject Property")
    st.json(subject)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Data Issues")
        if data_issues:
            for issue in data_issues:
                st.write(f"- {issue}")
        else:
            st.success("No data issues were flagged from the extracted text.")

    with c2:
        st.subheader("Document Meta")
        if document_meta:
            st.json(document_meta)
        else:
            st.info("No document metadata returned.")

    st.subheader("Field Sources")
    if field_sources:
        st.json(field_sources)
    else:
        st.info("No field source details returned.")

    with st.expander("Raw Text Preview"):
        if raw_text:
            st.text(raw_text[:12000])
        else:
            st.info("No text preview available.")

if IMPORT_ERROR:
    st.error("Could not import the subject extractor.")
    st.code(IMPORT_ERROR)
elif uploaded is None:
    st.info("Upload a subject property PDF to run Module 2.")
else:
    pdf_bytes = uploaded.read()
    if not pdf_bytes:
        st.error("The uploaded PDF appears to be empty.")
    else:
        with st.spinner("Extracting subject property details..."):
            try:
                result = extract_subject_property(pdf_bytes, filename=uploaded.name)
            except TypeError:
                # Fallback in case the function only accepts bytes
                result = extract_subject_property(pdf_bytes)
            except Exception as e:
                st.error("The extractor ran into an error.")
                st.code(str(e))
            else:
                if not isinstance(result, dict):
                    st.error("Extractor did not return a dictionary result.")
                    st.write(result)
                else:
                    render_results(result)
