import streamlit as st

st.set_page_config(page_title="ICHIBAN - New Day | Subject Extraction", page_icon="🏡", layout="wide")

st.title("Module 2 — Subject Property Extraction")
st.subheader("Subject PDF intake check and extraction placeholder")

st.markdown(
    """
This page confirms Module 2 is connected.

### What this module will do
- Read the uploaded Subject Property PDF
- Extract RealAVM and RealAVM Range
- Capture subject property details for later valuation steps
- Prepare normalized subject data for downstream modules
"""
)

pdf_name = st.session_state.get("subject_pdf_filename")
pdf_bytes = st.session_state.get("subject_pdf_bytes")

if pdf_name:
    st.success(f"Subject PDF linked from Module 1: {pdf_name}")
else:
    st.warning("No Subject Property PDF name was found in session state.")

if pdf_bytes:
    st.info(f"PDF bytes available for extraction: {len(pdf_bytes):,} bytes")
    st.success("Module 2 is ready for extraction logic.")
else:
    st.error(
        "The Subject Property PDF file bytes were not saved by Module 1, so extraction cannot run yet. "
        "Module 2 is now connected, but Module 1 still needs one small update to store the uploaded PDF bytes in session state."
    )

    st.code(
        """if subject_pdf is not None:
    st.session_state[\"subject_pdf_uploaded\"] = True
    st.session_state[\"subject_pdf_filename\"] = subject_pdf.name
    st.session_state[\"subject_pdf_bytes\"] = subject_pdf.getvalue()
else:
    st.session_state[\"subject_pdf_uploaded\"] = False""",
        language="python",
    )

st.divider()

left, right = st.columns(2)

with left:
    if st.button("Back to Module 1"):
        st.switch_page("pages/1_intake.py")

with right:
    if st.button("Continue"):
        st.info("Module 2 page is installed. Next step is wiring extraction logic.")
