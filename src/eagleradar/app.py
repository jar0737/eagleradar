"""EagleRadar web app (Streamlit).

uv run streamlit run src/eagleradar/app.py
"""

import streamlit as st

st.set_page_config(page_title="EagleRadar", page_icon="🦅", layout="wide")

st.title("🦅 EagleRadar")
st.caption("Ortshinweise aus Social-Media-Beiträgen – Stromausfall Berlin, Januar 2026")
st.info("Setup works! The app is still empty – let's build it.")
