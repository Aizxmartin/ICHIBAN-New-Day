
import sys
from pathlib import Path
import time
import streamlit as st
import pandas as pd

# Make repo root importable when app entrypoint is app/main.py
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.subject_extractor import build_subject_profile

st.set_page_config(page_title="ICHIBAN - Module 2", layout="wide")

REQUIRED_FIELDS = [
    "subject_address",
    "above_grade_sqft",
    "beds",
    "baths",
    "year_built",
]

OPTIONAL_FIELDS = [
    "real_avm",
    "real_avm_range_low",
    "real_avm_range_high",
    "lot_size_sqft",
]

FIELD_LABELS = {
    "subject_address": "Subject Address",
    "real_avm": "RealAVM",
    "real_avm_range_low": "RealAVM Range Low",
    "real_avm_range_high": "RealAVM Range High",
    "above_grade_sqft": "Above Grade SqFt",
    "beds": "Bedrooms",
    "baths": "Bathrooms",
    "year_built": "Year Built",
    "lot_size_sqft": "Lot Size SqFt",
    "style": "Style",
    "stories": "Stories",
}


def is_missing(value):
    return value is None or value == "" or value == 0


def fmt_value(value):
    if value is None or value == "":
        return ""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def field_status(value, required=False):
    if is_missing(value):
        return "Missing" if required else "Not found"
    return "Found"


def build_verified_profile(extracted, verified_inputs):
    final = dict(extracted)
    field_sources = {}

    for field in list(FIELD_LABELS.keys()):
        verified_value = verified_inputs.get(field)
        extracted_value = extracted.get(field)

        if not is_missing(verified_value):
            final[field] = verified_value
            field_sources[field] = "verified_lookup_or_manual"
        elif not is_missing(extracted_value):
            final[field] = extracted_value
            field_sources[field] = "pdf_extraction"
        else:
            final[field] = None
            field_sources[field] = "missing"

    final["field_sources"] = field_sources
    final["subject_profile_ready"] = all(not is_missing(final.get(f)) for f in REQUIRED_FIELDS)
    return final


st.title("Module 2 — Subject Property Extraction & Verification")
st.subheader("ICHIBAN Intelligence Engine")

pdf_bytes = st.session_state.get("subject_pdf_bytes")
pdf_name = st.session_state.get("subject_pdf_filename", "Uploaded PDF")

if not pdf_bytes:
    st.error("No Subject Property PDF found in session. Please return to Module 1 and upload the subject property report.")
    st.stop()

with st.container():
    st.markdown("### 🧠 Elevating Property Data to Market Intelligence")
    status = st.empty()
    progress = st.progress(0)

    steps = [
        "Reading Subject Property Report...",
        "Extracting valuation signals...",
        "Identifying property characteristics...",
        "Preparing subject profile...",
        "Opening verification layer..."
    ]

    for i, step in enumerate(steps):
        status.write(step)
        progress.progress((i + 1) * 20)
        time.sleep(0.15)

extracted = build_subject_profile(pdf_bytes)
st.session_state["subject_profile_extracted"] = extracted

verified_defaults = st.session_state.get("subject_profile_verified_inputs", {})

st.success("Initial extraction complete")
st.caption(f"Source file: {pdf_name}")

warnings = extracted.get("warnings", [])
critical_missing = any(is_missing(extracted.get(f)) for f in REQUIRED_FIELDS)

if not extracted.get("extracted_text_available"):
    st.error("⚠️ ICHIBAN could not read this PDF format clearly enough for dependable extraction.")
elif critical_missing:
    st.error("❗ Critical subject data is incomplete. Please verify or enter the missing fields below before valuation.")
elif warnings:
    st.warning("⚠️ Some property details were found, but a few fields still need review.")
else:
    st.success("✅ Subject property successfully analyzed from the PDF.")

st.markdown("""
### Verification Layer
Use this section to confirm or correct the subject property using a backup source such as:
- county assessor / public record
- Redfin
- Zillow
- Realtor / MLS public page
- your own verified notes

ICHIBAN will compare the PDF extraction with the verified values and build one final subject profile.
""")

left, right = st.columns([1.15, 1])

with left:
    st.markdown("#### PDF-Extracted Values")
    extracted_rows = []
    for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
        extracted_rows.append([
            FIELD_LABELS.get(field, field),
            fmt_value(extracted.get(field)),
            field_status(extracted.get(field), required=field in REQUIRED_FIELDS)
        ])
    extracted_df = pd.DataFrame(extracted_rows, columns=["Field", "PDF Extracted", "Status"])
    st.dataframe(extracted_df, width="stretch", hide_index=True)

    if warnings:
        st.markdown("#### Extraction Notes")
        for w in warnings:
            st.write(f"- {w}")

with right:
    st.markdown("#### Backup Verification / Manual Confirmation")
    st.caption("Enter only the values you want to confirm or override.")

    verify_source = st.selectbox(
        "Verification Source",
        [
            "",
            "County / Public Record",
            "Redfin",
            "Zillow",
            "MLS Public Page",
            "Agent Verified Notes",
            "Other",
        ],
        index=0,
        key="verify_source",
    )

    verified_address = st.text_input(
        "Verified Address",
        value=verified_defaults.get("subject_address", ""),
        key="verified_address",
    )

    verified_real_avm = st.number_input(
        "Verified RealAVM",
        min_value=0,
        step=1000,
        value=int(verified_defaults.get("real_avm") or 0),
        key="verified_real_avm",
    )
    verified_real_avm_low = st.number_input(
        "Verified RealAVM Range Low",
        min_value=0,
        step=1000,
        value=int(verified_defaults.get("real_avm_range_low") or 0),
        key="verified_real_avm_low",
    )
    verified_real_avm_high = st.number_input(
        "Verified RealAVM Range High",
        min_value=0,
        step=1000,
        value=int(verified_defaults.get("real_avm_range_high") or 0),
        key="verified_real_avm_high",
    )

    verified_sqft = st.number_input(
        "Verified Above Grade SqFt",
        min_value=0,
        step=1,
        value=int(verified_defaults.get("above_grade_sqft") or 0),
        key="verified_sqft",
    )
    verified_beds = st.number_input(
        "Verified Bedrooms",
        min_value=0.0,
        step=1.0,
        value=float(verified_defaults.get("beds") or 0.0),
        key="verified_beds",
    )
    verified_baths = st.number_input(
        "Verified Bathrooms",
        min_value=0.0,
        step=0.5,
        value=float(verified_defaults.get("baths") or 0.0),
        key="verified_baths",
    )
    verified_year = st.number_input(
        "Verified Year Built",
        min_value=0,
        step=1,
        value=int(verified_defaults.get("year_built") or 0),
        key="verified_year",
    )
    verified_lot = st.number_input(
        "Verified Lot Size SqFt",
        min_value=0,
        step=1,
        value=int(verified_defaults.get("lot_size_sqft") or 0),
        key="verified_lot",
    )
    verified_style = st.text_input(
        "Verified Style",
        value=verified_defaults.get("style", ""),
        key="verified_style",
    )
    verified_stories = st.text_input(
        "Verified Stories",
        value=verified_defaults.get("stories", ""),
        key="verified_stories",
    )

verified_inputs = {
    "subject_address": verified_address.strip(),
    "real_avm": None if verified_real_avm == 0 else verified_real_avm,
    "real_avm_range_low": None if verified_real_avm_low == 0 else verified_real_avm_low,
    "real_avm_range_high": None if verified_real_avm_high == 0 else verified_real_avm_high,
    "above_grade_sqft": None if verified_sqft == 0 else verified_sqft,
    "beds": None if verified_beds == 0 else verified_beds,
    "baths": None if verified_baths == 0 else verified_baths,
    "year_built": None if verified_year == 0 else verified_year,
    "lot_size_sqft": None if verified_lot == 0 else verified_lot,
    "style": verified_style.strip(),
    "stories": verified_stories.strip(),
    "verification_source": verify_source,
}

st.session_state["subject_profile_verified_inputs"] = verified_inputs

verified_profile = build_verified_profile(extracted, verified_inputs)
verified_profile["verification_source"] = verify_source
st.session_state["subject_profile"] = verified_profile

st.divider()
st.markdown("### Final Subject Profile Preview")

compare_rows = []
for field in REQUIRED_FIELDS + OPTIONAL_FIELDS + ["style", "stories"]:
    compare_rows.append([
        FIELD_LABELS.get(field, field),
        fmt_value(extracted.get(field)),
        fmt_value(verified_inputs.get(field)),
        fmt_value(verified_profile.get(field)),
        verified_profile.get("field_sources", {}).get(field, ""),
    ])

compare_df = pd.DataFrame(
    compare_rows,
    columns=["Field", "PDF Extracted", "Verified Input", "Final Value Used", "Final Source"]
)
st.dataframe(compare_df, width="stretch", hide_index=True)

missing_required = [FIELD_LABELS.get(f, f) for f in REQUIRED_FIELDS if is_missing(verified_profile.get(f))]

if missing_required:
    st.error("❗ Subject profile is not ready yet. Missing required fields: " + ", ".join(missing_required))
else:
    st.success("✅ Subject profile is ready for downstream valuation logic.")

st.session_state["subject_profile_ready"] = len(missing_required) == 0

st.info(
    "Current build note: this version supports a verification layer for county / Redfin / other backup data, "
    "but it does not yet perform live web lookups automatically."
)

nav1, nav2 = st.columns(2)
with nav1:
    if st.button("Back to Module 1"):
        st.switch_page("pages/1_intake.py")

with nav2:
    if st.session_state.get("subject_profile_ready"):
        st.success("Module 2 ready. Subject profile can hand off to the next module.")
    else:
        st.warning("Complete the missing required subject fields before handoff.")
