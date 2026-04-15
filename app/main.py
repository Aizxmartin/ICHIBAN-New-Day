import streamlit as st

st.set_page_config(page_title="ICHIBAN - New Day", layout="wide")

st.title("ICHIBAN - New Day")
st.subheader("Home")

st.markdown(
    """
**AI + Realtor Experience + Market Data + Judgment**

Use the pages in the left sidebar in this order:

**1. Intake**
- Upload the MLS comps file
- Upload the subject property PDF
- Enter Zillow / Redfin / AVM values if needed
- Add property notes when available

**2. Subject Extraction**
- Run Module 2 on the uploaded subject property PDF
- Review extracted subject facts
- Review missing items and data issues
- Confirm what may need manual verification
"""
)

st.info("Start with Intake, then move to Subject Extraction.")
