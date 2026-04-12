import streamlit as st
import pandas as pd

st.title("Module 1 - Intake")

mls_file = st.file_uploader("Upload MLS Data", type=["csv","xlsx"])
subject_pdf = st.file_uploader("Upload Subject Property PDF", type=["pdf"])
mc_pdf = st.file_uploader("Upload 1004MC Report", type=["pdf"])

zillow_file = st.file_uploader("Upload Zillow", type=["pdf","jpg","jpeg","png"])
redfin_file = st.file_uploader("Upload Redfin", type=["pdf","jpg","jpeg","png"])

zillow_val = st.text_input("Zillow Estimate")
redfin_val = st.text_input("Redfin Estimate")
realavm_val = st.text_input("Real AVM Estimate")

if mls_file:
    if mls_file.name.endswith(".csv"):
        df = pd.read_csv(mls_file)
    else:
        df = pd.read_excel(mls_file)

    st.dataframe(df.head())
    st.session_state["market_data"] = df

if st.button("Confirm Intake"):
    st.session_state["intake_ready"] = True
