import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DOG_DATABASE_ID = st.secrets["DOG_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

GOAL = 4500.00

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
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 16px !important;
    }

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

    /* Small gray nav button */
    div[data-testid="stButton"].nav-btn > button {
        background-color: #e0e0e0 !important;
        color: #333333 !important;
        height: 2em !important;
        font-size: 12px !important;
        font-weight: normal !important;
        border-radius: 8px !important;
    }

    div[data-testid="stButton"].nav-btn > button:hover {
        background-color: #c8c8c8 !important;
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
st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
if st.button("💰 Budget Tracker", key="nav_budget"):
    st.switch_page("budget_app.py")
st.markdown('</div>', unsafe_allow_html=True)

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
        progress = min(total_saved / GOAL, 1.0)

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Saved", f"${total_saved:,.2f}")
        col2.metric("🎯 Goal", f"${GOAL:,.2f}")
        col3.metric("📋 Remaining", f"${remaining:,.2f}")

        st.progress(progress)
        st.caption(f"{progress * 100:.1f}% of goal reached")

        l_saved = df[df["Who"] == "Leandro"]["Amount"].sum()
        j_saved = df[df["Who"] == "Jonas"]["Amount"].sum()

        col1, col2 = st.columns(2)
        col1.write(f"🐾 **Leandro saved:** `${l_saved:,.2f}`")
        col2.write(f"🐾 **Jonas saved:** `${j_saved:,.2f}`")

        st.subheader("Contributions")
        df_disp = df.copy()
        df_disp.index = range(1, len(df_disp) + 1)
        df_disp["Amount"] = df_disp["Amount"].map("${:,.2f}".format)
        st.table(df_disp[["Date", "Note", "Amount", "Who"]])

except Exception as e:
    st.error(f"Error: {e}")
