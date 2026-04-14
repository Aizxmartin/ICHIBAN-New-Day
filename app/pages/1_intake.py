
import streamlit as st
import pandas as pd

st.set_page_config(page_title="ICHIBAN - Intake", layout="wide")

st.title("Module 1 — Intake")

st.subheader("Upload Required Files")

mls_file = st.file_uploader("Upload MLS Market Data", type=["csv", "xlsx"])
subject_pdf = st.file_uploader("Upload Subject Property PDF", type=["pdf"])

# --- Store MLS ---
if mls_file is not None:
    st.session_state["mls_uploaded"] = True
    st.session_state["mls_filename"] = mls_file.name
    st.success("MLS Market Data uploaded")
else:
    st.session_state["mls_uploaded"] = False

# --- Store Subject PDF (UPDATED FIX) ---
if subject_pdf is not None:
    st.session_state["subject_pdf_uploaded"] = True
    st.session_state["subject_pdf_filename"] = subject_pdf.name
    st.session_state["subject_pdf_bytes"] = subject_pdf.getvalue()
    st.success("Subject Property PDF uploaded")
else:
    st.session_state["subject_pdf_uploaded"] = False


st.divider()

st.subheader("D. Intake Readiness")

ready = (
    st.session_state.get("mls_uploaded")
    and st.session_state.get("subject_pdf_uploaded")
)

if ready:
    st.success("Ready for next module")
    st.session_state["intake_ready"] = True
else:
    st.warning("Upload required files to continue")
    st.session_state["intake_ready"] = False


if st.button("Confirm Intake"):
    if st.session_state.get("intake_ready"):
        st.success("Intake confirmed. Module 1 is complete.")
        st.switch_page("pages/2_subject_extraction.py")
    else:
        st.error("Please upload required files first.")
