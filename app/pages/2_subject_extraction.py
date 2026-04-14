import sys
from pathlib import Path
import time

import pandas as pd
import streamlit as st

# Make repo root importable when app entrypoint is app/main.py
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.subject_extractor import build_subject_profile


st.set_page_config(page_title="ICHIBAN - New Day | Module 2", page_icon="🏡", layout="wide")

st.title("Module 2 — Subject Property Extraction")
st.subheader("ICHIBAN Intelligence Engine")


def fmt_currency(value):
    if value is None or value == "":
        return "Not found"
    try:
        return f"${value:,.0f}"
    except Exception:
        return str(value)


def fmt_number(value):
    if value is None or value == "":
        return "Not found"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


pdf_name = st.session_state.get("subject_pdf_filename")
pdf_bytes = st.session_state.get("subject_pdf_bytes")

if not pdf_bytes:
    st.error("No Subject Property PDF was found in session. Please return to Module 1 and upload the PDF again.")
    if st.button("Back to Module 1"):
        st.switch_page("pages/1_intake.py")
    st.stop()

st.info(f"Loaded Subject Property PDF: {pdf_name or 'Unnamed PDF'}")

with st.container(border=True):
    st.markdown("### 🧠 Elevating Property Data to Market Intelligence")
    st.write("Please wait while ICHIBAN analyzes your subject property and prepares valuation intelligence.")

    status_area = st.empty()
    progress = st.progress(0)

    steps = [
        "⚙️ Reading Subject Property Report",
        "📊 Extracting RealAVM and valuation signals",
        "🧠 Identifying subject property characteristics",
        "📈 Normalizing data for market comparison",
        "🏗️ Building valuation intelligence",
    ]

    for idx, step in enumerate(steps, start=1):
        status_area.markdown(f"**{step}**")
        progress.progress(int(idx / len(steps) * 100))
        time.sleep(0.25)

subject_profile = build_subject_profile(pdf_bytes)
st.session_state["subject_profile"] = subject_profile
st.session_state["module_2_complete"] = True

st.success("Moving into Real Valuation Intelligence Phase")
st.caption("Module 2 extraction is complete. Review the extracted subject profile below.")

summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("RealAVM", fmt_currency(subject_profile.get("real_avm")))
summary_col2.metric(
    "RealAVM Range",
    (
        f"{fmt_currency(subject_profile.get('real_avm_range_low'))} to "
        f"{fmt_currency(subject_profile.get('real_avm_range_high'))}"
        if subject_profile.get("real_avm_range_low") is not None or subject_profile.get("real_avm_range_high") is not None
        else "Not found"
    ),
)
summary_col3.metric("Address Found", "Yes" if subject_profile.get("subject_address") else "No")

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### Extracted Subject Profile")
    profile_rows = [
        ["Subject Address", subject_profile.get("subject_address") or "Not found"],
        ["RealAVM", fmt_currency(subject_profile.get("real_avm"))],
        ["RealAVM Range Low", fmt_currency(subject_profile.get("real_avm_range_low"))],
        ["RealAVM Range High", fmt_currency(subject_profile.get("real_avm_range_high"))],
        ["Above Grade SF", fmt_number(subject_profile.get("above_grade_sqft"))],
        ["Beds", fmt_number(subject_profile.get("beds"))],
        ["Baths", fmt_number(subject_profile.get("baths"))],
        ["Year Built", fmt_number(subject_profile.get("year_built"))],
        ["Lot Size SF", fmt_number(subject_profile.get("lot_size_sqft"))],
    ]
    df = pd.DataFrame(profile_rows, columns=["Field", "Extracted Value"])
    st.dataframe(df, width="stretch", hide_index=True)

with right:
    st.markdown("### Extraction Status")
    checks = [
        ("PDF text extracted", subject_profile.get("extracted_text_available")),
        ("RealAVM found", subject_profile.get("real_avm") is not None),
        ("RealAVM range found", subject_profile.get("real_avm_range_raw") is not None),
        ("Address found", subject_profile.get("subject_address") is not None),
        ("Subject profile saved", st.session_state.get("module_2_complete")),
    ]
    for label, passed in checks:
        st.write(f"{'✅' if passed else '➖'} {label}")

    if subject_profile.get("real_avm") is None:
        st.warning(
            "RealAVM was not found automatically in this PDF. That may mean the layout differs from the expected pattern. "
            "We can refine the parser with a sample PDF later."
        )

st.divider()
st.markdown("### Extracted Text Preview")
preview = subject_profile.get("extracted_text_preview") or "No extractable text was found in the PDF."
st.text_area("Preview", value=preview, height=280, disabled=False)

nav1, nav2 = st.columns(2)
with nav1:
    if st.button("Back to Module 1"):
        st.switch_page("pages/1_intake.py")

with nav2:
    st.info("Module 2 is now complete. Next step: build Module 3.")
