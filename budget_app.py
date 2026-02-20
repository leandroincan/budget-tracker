import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# --- 2. UI STYLING ---
st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="centered")
st.markdown("""
    <style>
    [data-testid="stToolbar"], footer, header {visibility: hidden !important;}
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
    button[data-testid="stBaseButton-primary"]:active,
    .st-emotion-cache-16rr57l {
        background-color: #34C759 !important;
        border-color: #34C759 !important;
    }

    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #28A745 !important;
        border-color: #28A745 !important;
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

st.title("💰 Our Budget Tracker")

# --- NAVIGATION ---
col1, col2 = st.columns(2)
with col1:
    if st.button("💰 Budget Tracker", key="nav_budget"):
        st.switch_page("budget_app.py")
with col2:
    if st.button("🐾 Wolfie's Fund", key="nav_wolfie"):
        st.switch_page("pages/1_Wolfie.py")

st.write("")

# --- 3. SESSION STATE INIT ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# --- 4. INPUT SECTION ---
categories = ["Superstore", "Safeway", "Dollarama", "Walmart", "Others"]

fk = st.session_state.form_key
category = st.selectbox("Category", options=categories, index=None, placeholder="Select store", key=f"category_{fk}")
details = st.text_input("Details (Optional)", placeholder="e.g. Groceries", key=f"details_{fk}")
cost = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0.00", key=f"cost_{fk}")
who = st.selectbox("Who paid?", ["Leandro", "Jonas"], index=None, placeholder="Select person", key=f"who_{fk}")

st.write("")

add_clicked = st.button("Add Expense", type="primary", key="add_btn")

if add_clicked:
    if category and who and cost and cost > 0:
        final_item_name = f"{category}: {details}" if details else category
        today = datetime.now().strftime("%Y-%m-%d")
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Item": {"title": [{"text": {"content": final_item_name}}]},
                "Cost": {"number": cost},
                "Who": {"select": {"name": who}},
                "Date": {"date": {"start": today}},
                "Archived": {"checkbox": False}
            }
        )
        st.success("Added!")
        st.session_state.form_key += 1
        st.rerun()
    else:
        st.error("Please fill out Category, Amount, and Who paid.")

# --- 5. DATA FETCHING ---
try:
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results")
    
    rows = []
    for page in results:
        p = page["properties"]
        if not p.get("Archived", {}).get("checkbox", False):
            title_list = p.get("Item", {}).get("title", [])
            item_val = title_list[0]["text"]["content"] if title_list else "Untitled"
            date_val = p.get("Date", {}).get("date", {})
            date_str = date_val.get("start", "No Date") if date_val else "No Date"
            
            rows.append({
                "id": page["id"],
                "Date": date_str,
                "Item": item_val,
                "Cost": p.get("Cost", {}).get("number") or 0.0,
                "Who": p.get("Who", {}).get("select", {}).get("name", "Unknown")
            })
    
    df = pd.DataFrame(rows)

    # --- 6. DASHBOARD ---
    if not df.empty:
        st.divider()
        total = df["Cost"].sum()
        st.metric("**Total**", f"${total:,.2f}")
        
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        l_owes = max(0.0, (j_spent - l_spent) / 2)
        j_owes = max(0.0, (l_spent - j_spent) / 2)

        col1, col2 = st.columns(2)
        col1.write(f"💳 **Leandro owes:** `${l_owes:,.2f}`")
        col2.write(f"💳 **Jonas owes:** `${j_owes:,.2f}`")

        st.subheader("Current Expenses")
        df_disp = df.copy()
        df_disp.index = range(1, len(df_disp) + 1)
        df_disp["Cost"] = df_disp["Cost"].map("${:,.2f}".format)
        st.table(df_disp[["Date", "Item", "Cost", "Who"]])

        st.divider()
        if st.button("Clear & Start New Round", key="clear_btn"):
            for page_id in df["id"]:
                notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
            st.rerun()

except Exception as e:
    st.error(f"Error: {e}")
