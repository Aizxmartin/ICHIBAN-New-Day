from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="ICHIBAN - New Day", page_icon="🏡", layout="wide")

st.title("ICHIBAN - New Day")
st.subheader("Home")
st.caption("AI + Realtor Experience + Market Data + Judgment")

st.markdown(
    """
Welcome to **ICHIBAN - New Day**.

This app is being rebuilt in smaller, testable sections so each part can be confirmed before moving to the next one.

### Workflow
**1. Intake**
- Upload the MLS comps file
- Upload the subject property PDF
- Enter Zillow / Redfin / AVM values if needed
- Add subject property notes when available

**2. Subject Extraction**
- Run Module 2 on the uploaded subject property PDF
- Review extracted subject facts
- Review missing items and data issues
- Confirm what may need manual verification

### Current Build Principle
This app is designed to:
- keep the front end simple
- keep the hidden logic structured
- support Realtor judgment rather than replace it
- show missing information clearly before final reporting
"""
)

st.info("Start with the Intake page in the left sidebar. The Subject Extraction page is separate and should no longer appear here.")
