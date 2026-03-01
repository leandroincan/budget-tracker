import os
import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or st.secrets.get("NOTION_TOKEN")
DOG_DATABASE_ID = os.environ.get("DOG_DATABASE_ID") or st.secrets.get("DOG_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

GOAL = 4951.92
INDIVIDUAL_GOAL = GOAL / 2  # $2,475 each

# --- 2. UI STYLING ---
st.set_page_config(page_title="Wolfie's Fund", page_icon="🐾", layout="centered")
st.markdown("""
    <style>
    [data-testid="stToolbar"], footer, header {visibility: hidden !important;}
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    .main { background-color: #ffffff; }

    html, body, [class*="st-"], .stSelectbox, .stTextInput, .stNumberInput, label, button, td, th, p {
        font-size: 14px !important; 
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        font-size: 18px !important;
        font-weight: bold !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 16px !important;
    }

    /* All buttons blue by default */
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

    /* Green primary button */
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"]:focus,
    button[data-testid="stBaseButton-primary"]:active {
        background-color: #34C759 !important;
        border-color: #34C759 !important;
    }

    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #28A745 !important;
        border-color: #28A745 !important;
    }

    /* HTML nav buttons */
    .nav-button {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        transition: 0.2s;
        color: #333333 !important;
        text-decoration: none !important;
    }

    .nav-button:hover {
        background: #f0f0f0 !important;
    }

    .nav-button:active {
        background: #e0e0e0 !important;
    }

    a .nav-button, a:visited .nav-button, a:hover .nav-button {
        color: #333333 !important;
        text-decoration: none !important;
    }

    /* Green progress bar */
    .st-dc {
        background-color: #34C759 !important;
    }

    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #f8f9fb !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }

    table { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 Wolfie's Surgery Fund")

# --- NAVIGATION ---
st.markdown(
    '<div style="display:flex; gap:8px; margin-bottom:8px;">'
    '<a href="/" target="_self" style="text-decoration:none;">'
    '<button class="nav-button">💰 Budget Tracker</button>'
    '</a>'
    '<a href="/Tax_Receipts" target="_self" style="text-decoration:none;">'
    '<button class="nav-button">🧾 Tax Receipts</button>'
    '</a>'
    '</div>',
    unsafe_allow_html=True
)

st.write("")

# --- 3. SESSION STATE ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# --- 4. INPUT SECTION ---
fk = st.session_state.form_key
amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0.00", key=f"amount_{fk}")
who = st.selectbox("Who saved?", ["Leandro", "Jonas"], index=None, placeholder="Select person", key=f"who_{fk}")
note = st.text_input("Note (Optional)", placeholder="e.g. Birthday money", key=f"note_{fk}")

st.write("")

add_clicked = st.button("Add Contribution", type="primary", key="add_btn")

if add_clicked:
    if who and amount and amount > 0:
        today = datetime.now().strftime("%Y-%m-%d")
        notion.pages.create(
            parent={"database_id": DOG_DATABASE_ID},
            properties={
                "Note": {"title": [{"text": {"content": note if note else "Contribution"}}]},
                "Amount": {"number": amount},
                "Who": {"select": {"name": who}},
                "Date": {"date": {"start": today}},
            }
        )
        st.success("Contribution added!")
        st.session_state.form_key += 1
        st.rerun()
    else:
        st.error("Please fill out Amount and Who.")

# --- 5. DATA FETCHING ---
try:
    response = notion.databases.query(database_id=DOG_DATABASE_ID)
    results = response.get("results")

    rows = []
    for page in results:
        p = page["properties"]
        title_list = p.get("Note", {}).get("title", [])
        note_val = title_list[0]["text"]["content"] if title_list else ""
        date_val = p.get("Date", {}).get("date", {})
        date_str = date_val.get("start", "No Date") if date_val else "No Date"

        rows.append({
            "Date": date_str,
            "Note": note_val,
            "Amount": p.get("Amount", {}).get("number") or 0.0,
            "Who": p.get("Who", {}).get("select", {}).get("name", "Unknown")
        })

    df = pd.DataFrame(rows)

    # --- 6. DASHBOARD ---
    if not df.empty:
        st.divider()

        total_saved = df["Amount"].sum()
        remaining = max(0.0, GOAL - total_saved)

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Saved", f"${total_saved:,.2f}")
        col2.metric("🎯 Goal", f"${GOAL:,.2f}")
        col3.metric("📋 Remaining", f"${remaining:,.2f}")

        st.divider()

        l_saved = df[df["Who"] == "Leandro"]["Amount"].sum()
        j_saved = df[df["Who"] == "Jonas"]["Amount"].sum()

        l_progress = min(l_saved / INDIVIDUAL_GOAL, 1.0)
        j_progress = min(j_saved / INDIVIDUAL_GOAL, 1.0)

        st.write("**🐾 Leandro**")
        st.progress(l_progress)
        st.caption(f"\${l_saved:,.2f} of \${INDIVIDUAL_GOAL:,.2f} — {l_progress * 100:.1f}% of goal reached")

        st.write("**🐾 Jonas**")
        st.progress(j_progress)
        st.caption(f"\${j_saved:,.2f} of \${INDIVIDUAL_GOAL:,.2f} — {j_progress * 100:.1f}% of goal reached")

        st.divider()

        st.subheader("Contributions")
        df_disp = df.copy()
        df_disp.index = range(1, len(df_disp) + 1)
        df_disp["Amount"] = df_disp["Amount"].map("${:,.2f}".format)
        st.table(df_disp[["Date", "Note", "Amount", "Who"]])

except Exception as e:
    st.error(f"Error: {e}")
