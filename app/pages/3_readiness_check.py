import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

CURRENT_DIR = os.path.dirname(__file__)
APP_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
REPO_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from core.readiness_engine import (
        evaluate_readiness,
        load_market_data_from_bytes,
        normalize_market_dataframe,
    )
except Exception as e:
    st.set_page_config(page_title="Module 3 - Readiness Check", layout="wide")
    st.title("Module 3 — Readiness / Decision Engine")
    st.error("Could not import the readiness engine.")
    st.code(str(e))
    st.stop()

st.set_page_config(page_title="Module 3 - Readiness Check", layout="wide")
st.title("Module 3 — Readiness / Decision Engine")
st.caption("AI + Realtor Experience + Market Data + Judgment")

st.write(
    "This module decides whether the app can proceed with a full report, a limited-scope valuation, "
    "or must stop due to insufficient data."
)

subject_property = st.session_state.get("subject_property", {}) or {}
subject_data_issues = st.session_state.get("subject_data_issues", []) or []

if not subject_property:
    st.warning("No subject property extraction result is available yet.")
    if st.button("Go to Module 2"):
        st.switch_page("pages/2_subject_extraction.py")
    st.stop()

market_df = st.session_state.get("market_data")
if market_df is not None:
    market_df = normalize_market_dataframe(market_df)

zillow_value = st.session_state.get("zillow_value_num")
redfin_value = st.session_state.get("redfin_value_num")

st.subheader("Current Inputs")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Subject Address Found", "Yes" if subject_property.get("address") else "No")
with c2:
    st.metric("MLS Data Loaded", "Yes" if market_df is not None and len(market_df) > 0 else "No")
with c3:
    online_ready = any(v is not None for v in [subject_property.get("realist_avm"), zillow_value, redfin_value])
    st.metric("Online Estimate Support", "Yes" if online_ready else "No")

with st.expander("Subject Property Snapshot"):
    st.json(subject_property)

with st.expander("Subject Data Issues from Module 2"):
    if subject_data_issues:
        for item in subject_data_issues:
            st.write(f"- {item}")
    else:
        st.success("No subject data issues were passed from Module 2.")

result = evaluate_readiness(
    subject_property=subject_property,
    data_issues=subject_data_issues,
    market_df=market_df,
    zillow_value=zillow_value,
    redfin_value=redfin_value,
)
st.session_state["module3_readiness_result"] = result

st.divider()
st.subheader("Module 3 Decision")

status = result["status"]
if status == "full_report_ready":
    st.success("Status: full_report_ready")
elif status == "limited_scope_only":
    st.warning("Status: limited_scope_only")
else:
    st.error("Status: insufficient_data")

st.json(result)

st.subheader("Interpretation")
if status == "full_report_ready":
    st.write("The system has enough verified subject and market data to move into comp filtering and the full report path.")
elif status == "limited_scope_only":
    st.write(
        "The system does not have enough verified subject data for a full report, "
        "but it does have enough support to continue with a limited-scope valuation."
    )
else:
    st.write(
        "The system does not have enough reliable subject and support data to continue responsibly. "
        "A full summary report should not be produced yet."
    )

st.divider()
left, right = st.columns(2)
with left:
    if st.button("Back to Module 2"):
        st.switch_page("pages/2_subject_extraction.py")
with right:
    if status in {"full_report_ready", "limited_scope_only"}:
        st.button("Module 4 Next (placeholder)", disabled=True)
    else:
        st.button("Cannot Proceed", disabled=True)
