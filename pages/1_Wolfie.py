import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- SETUP ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="centered")

st.markdown("""
<style>
[data-testid="stToolbar"], footer, header {visibility: hidden !important;}
[data-testid="stSidebar"] {display: none !important;}
[data-testid="collapsedControl"] {display: none !important;}
.main { background-color: #ffffff; }

html, body, [class*="st-"], .stSelectbox, .stTextInput, .stNumberInput, label, button, td, th, p {
    font-size: 14px !important;
}

/* Default blue */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    height: 3.2em;
    background-color: #007AFF !important;
    color: white !important;
    font-weight: bold;
    border: none !important;
    transition: 0.2s;
}

.stButton > button:hover {
    background-color: #0056b3 !important;
}

/* Green Add button */
button[data-testid="baseButton-add_btn"],
button[data-testid="baseButton-add_btn"]:focus,
button[data-testid="baseButton-add_btn"]:active {
    background-color: #34C759 !important;
}

button[data-testid="baseButton-add_btn"]:hover {
    background-color: #28A745 !important;
}

/* Gray navigation button */
button[data-testid="baseButton-nav_wolfie"] {
    background-color: #e0e0e0 !important;
    color: #333333 !important;
    font-weight: normal !important;
    height: 2.5em !important;
}

button[data-testid="baseButton-nav_wolfie"]:hover {
    background-color: #d0d0d0 !important;
}

button[data-testid="baseButton-nav_wolfie"]:active {
    background-color: #bfbfbf !important;
}
</style>
""", unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

if st.button("🐾 Wolfie's Fund", key="nav_wolfie"):
    st.switch_page("pages/1_Wolfie.py")

st.write("")

# (rest of your original logic continues unchanged)
