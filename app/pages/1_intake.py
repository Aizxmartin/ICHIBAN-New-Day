import io
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

CURRENT_DIR = os.path.dirname(__file__)
APP_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
REPO_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.readiness_engine import load_market_data_from_bytes, normalize_market_dataframe

st.set_page_config(page_title="ICHIBAN - New Day | Intake", page_icon="🏡", layout="wide")

st.title("Module 1 — Intake")
st.subheader("Guided drag-and-drop intake for a stronger ICHIBAN report")

st.markdown(
    """
To produce the strongest ICHIBAN report, upload as many of the following as available.

### Required
- **MLS Market Data** (`.csv` or `.xlsx`)
- **Subject Property Report** (`.pdf`)

### Recommended
- **Zillow support file** (`.jpg`, `.jpeg`, `.png`, `.pdf`)
- **Redfin support file** (`.jpg`, `.jpeg`, `.png`, `.pdf`)
- **1004MC report** (`.pdf`)
- **Agent / property notes** (`.txt`, `.docx`) or pasted text

### Notes
- **RealAVM and RealAVM Range** are expected to be extracted later from the uploaded **Subject Property PDF**
- **Zillow** and **Redfin** may be entered manually and/or supported with screenshots or PDFs
- Additional support files improve market context, property interpretation, and final narrative quality
"""
)

st.divider()


def parse_currency_input(value: str):
    if not value:
        return None
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def safe_preview_dataframe(df: pd.DataFrame, rows: int = 10) -> pd.DataFrame:
    preview = df.head(rows).copy()
    preview.columns = [str(c) for c in preview.columns]
    for col in preview.columns:
        preview[col] = preview[col].astype(str)
    return preview


left, right = st.columns([1.2, 1])

with left:
    st.markdown("### Upload source files")

    mls_file = st.file_uploader(
        "MLS Market Data",
        type=["csv", "xlsx"],
        help="Upload the MLS comps export used for comp filtering and adjustment analysis.",
    )

    subject_pdf = st.file_uploader(
        "Subject Property Report",
        type=["pdf"],
        help="Upload the property information / Realist / CoreLogic PDF for the subject property.",
    )

    zillow_support = st.file_uploader(
        "Zillow support file (optional)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Optional screenshot or PDF support for Zestimate review.",
    )

    redfin_support = st.file_uploader(
        "Redfin support file (optional)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Optional screenshot or PDF support for Redfin estimate review.",
    )

    report_1004mc = st.file_uploader(
        "1004MC report (optional)",
        type=["pdf"],
        help="Optional market-trend support file for later module use.",
    )

    notes_file = st.file_uploader(
        "Agent / property notes file (optional)",
        type=["txt", "docx"],
        help="Optional notes file for property-specific observations and later narrative use.",
    )

with right:
    st.markdown("### Manual support values")

    zillow_value_text = st.text_input("Zillow estimate (optional)", placeholder="$850,000")
    redfin_value_text = st.text_input("Redfin estimate (optional)", placeholder="$845,000")

    st.markdown("### Optional pasted notes")
    pasted_notes = st.text_area(
        "Property / agent notes",
        placeholder="Add notes about updates, deferred maintenance, location strengths, condition, amenities, or anything else worth preserving.",
        height=220,
    )

st.divider()

st.markdown("### Process intake")

can_process = mls_file is not None and subject_pdf is not None

if not can_process:
    st.info("Upload both the MLS Market Data file and Subject Property PDF to continue.")

if st.button("Save Intake and Preview", type="primary", disabled=not can_process):
    try:
        market_df = load_market_data_from_bytes(mls_file.getvalue(), mls_file.name)
        market_df = normalize_market_dataframe(market_df)
        st.session_state["market_data"] = market_df
        st.session_state["market_data_filename"] = mls_file.name
        st.session_state["market_data_bytes"] = mls_file.getvalue()

        st.session_state["subject_pdf_bytes"] = subject_pdf.getvalue()
        st.session_state["subject_pdf_filename"] = subject_pdf.name

        if zillow_support is not None:
            st.session_state["zillow_support_bytes"] = zillow_support.getvalue()
            st.session_state["zillow_support_filename"] = zillow_support.name
        else:
            st.session_state.pop("zillow_support_bytes", None)
            st.session_state.pop("zillow_support_filename", None)

        if redfin_support is not None:
            st.session_state["redfin_support_bytes"] = redfin_support.getvalue()
            st.session_state["redfin_support_filename"] = redfin_support.name
        else:
            st.session_state.pop("redfin_support_bytes", None)
            st.session_state.pop("redfin_support_filename", None)

        if report_1004mc is not None:
            st.session_state["report_1004mc_bytes"] = report_1004mc.getvalue()
            st.session_state["report_1004mc_filename"] = report_1004mc.name
        else:
            st.session_state.pop("report_1004mc_bytes", None)
            st.session_state.pop("report_1004mc_filename", None)

        if notes_file is not None:
            st.session_state["notes_file_bytes"] = notes_file.getvalue()
            st.session_state["notes_file_filename"] = notes_file.name
        else:
            st.session_state.pop("notes_file_bytes", None)
            st.session_state.pop("notes_file_filename", None)

        st.session_state["zillow_value_num"] = parse_currency_input(zillow_value_text)
        st.session_state["redfin_value_num"] = parse_currency_input(redfin_value_text)
        st.session_state["pasted_notes"] = pasted_notes

        st.success("Intake saved to session state.")
    except Exception as e:
        st.error("Intake processing failed.")
        st.code(str(e))

if "market_data" in st.session_state:
    st.markdown("### Intake Preview")

    preview_left, preview_right = st.columns([1.2, 1])

    with preview_left:
        st.markdown("**MLS Market Data Preview**")
        try:
            preview_df = safe_preview_dataframe(st.session_state["market_data"])
            st.dataframe(preview_df, width="stretch")
        except Exception as e:
            st.warning("Could not preview market data.")
            st.code(str(e))

    with preview_right:
        st.markdown("**Saved Inputs**")
        st.write(f"MLS file: `{st.session_state.get('market_data_filename', 'N/A')}`")
        st.write(f"Subject PDF: `{st.session_state.get('subject_pdf_filename', 'N/A')}`")
        st.write(f"Zillow estimate: `{st.session_state.get('zillow_value_num')}`")
        st.write(f"Redfin estimate: `{st.session_state.get('redfin_value_num')}`")
        st.write(
            "1004MC file: "
            f"`{st.session_state.get('report_1004mc_filename', 'None uploaded')}`"
        )
        st.write(
            "Notes file: "
            f"`{st.session_state.get('notes_file_filename', 'None uploaded')}`"
        )

        if st.session_state.get("pasted_notes"):
            st.markdown("**Pasted Notes**")
            st.write(st.session_state["pasted_notes"][:1200])

    st.divider()
    if st.button("Continue to Subject Extraction"):
        st.switch_page("pages/2_subject_extraction.py")
