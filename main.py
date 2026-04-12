import streamlit as st

st.set_page_config(page_title="Ichiban Valuation App", layout="wide")
st.title("🏠 Ichiban Modular Valuation App")

st.markdown("""
Welcome to the **Ichiban Modular Valuation App**.

Use the sidebar to navigate through each module:
1. 📂 Upload and clean your CSV comps (Module 1)
2. 🏡 Upload subject property PDF or enter manually (Module 2)
3. 💻 Enter online estimates (Module 3)
4. 📏 Filter comps by Above Grade SF (Module 4)
5. 📐 Apply adjustments (Module 5)
6. 📊 View the final valuation summary (Module 6)
""")
