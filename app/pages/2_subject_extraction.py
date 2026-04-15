
import sys
from pathlib import Path
import time
import streamlit as st
import pandas as pd

# Fix import path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.subject_extractor import build_subject_profile

st.set_page_config(page_title="ICHIBAN - Module 2", layout="wide")

st.title("Module 2 — Subject Property Extraction")
st.subheader("ICHIBAN Intelligence Engine")

pdf_bytes = st.session_state.get("subject_pdf_bytes")

if not pdf_bytes:
    st.error("No Subject Property PDF found. Please return to Module 1.")
    st.stop()

# Intelligence animation
with st.container():
    st.markdown("### 🧠 Elevating Property Data to Market Intelligence")
    status = st.empty()
    progress = st.progress(0)

    steps = [
        "Reading Subject Property Report...",
        "Extracting valuation signals...",
        "Identifying property characteristics...",
        "Normalizing data...",
        "Building valuation intelligence..."
    ]

    for i, step in enumerate(steps):
        status.write(step)
        progress.progress((i+1)*20)
        time.sleep(0.2)

# Run extraction
profile = build_subject_profile(pdf_bytes)
st.session_state["subject_profile"] = profile

st.success("Analysis Complete")

# --- FAILURE MESSAGES ---
warnings = profile.get("warnings", [])

critical_missing = (
    profile.get("real_avm") is None or
    profile.get("above_grade_sqft") is None or
    profile.get("beds") is None or
    profile.get("baths") is None
)

if not profile.get("extracted_text_available"):
    st.error("⚠️ ICHIBAN could not read this PDF format. Please enter data manually.")

elif critical_missing:
    st.error("❗ Critical property data is missing. Please complete the fields below.")

elif warnings:
    st.warning("⚠️ Some property details could not be fully extracted. Please review below.")

else:
    st.success("✅ Subject property successfully analyzed")

# --- DISPLAY DATA ---
st.subheader("Extracted Subject Profile")

df = pd.DataFrame([
    ["Address", profile.get("subject_address")],
    ["RealAVM", profile.get("real_avm")],
    ["SqFt", profile.get("above_grade_sqft")],
    ["Beds", profile.get("beds")],
    ["Baths", profile.get("baths")],
    ["Year Built", profile.get("year_built")]
], columns=["Field", "Value"])

st.dataframe(df, use_container_width=True)

# --- MANUAL ENTRY ---
if critical_missing:
    st.subheader("Manual Entry Required")

    profile["real_avm"] = st.number_input("RealAVM", value=profile.get("real_avm") or 0)
    profile["above_grade_sqft"] = st.number_input("SqFt", value=profile.get("above_grade_sqft") or 0)
    profile["beds"] = st.number_input("Beds", value=profile.get("beds") or 0)
    profile["baths"] = st.number_input("Baths", value=profile.get("baths") or 0)

    st.session_state["subject_profile"] = profile

st.info("Module 2 complete. Ready for Module 3.")
