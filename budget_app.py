import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# --- 2. UI STYLING ---
st.set_page_config(page_title="Budget Tracker", layout="centered")
st.markdown("""
    <style>
    [data-testid="stToolbar"], footer, header {visibility: hidden !important;}
    .main { background-color: #ffffff; }

    /* Force 16px on EVERYTHING including the static table */
    html, body, [class*="st-"], .stSelectbox, .stTextInput, .stNumberInput, label, button, td, th, p {
        font-size: 16px !important; 
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.2em;
        color: white !important;
        font-weight: bold;
        border: none;
        transition: 0.2s;
    }

    /* ADD EXPENSE BUTTON (Green) */
    div.stButton > button:not([kind="secondary"]) {
        background-color: #34C759 !important;
    }

    /* CLEAR BUTTON (Original Blue) */
    div.stButton > button[kind="secondary"] {
        background-color: #007AFF !important;
    }

    /* Input styling */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #f8f9fb !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }

    /* Table styling to ensure it uses the full width */
    table {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

# --- 3. INPUT SECTION ---
categories = ["Superstore", "Safeway", "Dollarama", "Walmart", "Others"]

category = st.selectbox("Category", options=categories, index=None, placeholder="Select store")
details = st.text_input("Details (Optional)", placeholder="e.g. Groceries")
cost = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0.00")
who = st.selectbox("Who paid?", ["Leandro", "Jonas"], index=None, placeholder="Select person")

st.write("")

if st.button("Add Expense"):
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
        st.rerun()
    else:
        st.error("Please fill out Category, Amount, and Who paid.")

# --- 4. DATA FETCHING ---
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

    # --- 5. DASHBOARD ---
    if not df.empty:
        st.divider()
        total = df["Cost"].sum()
        st.metric("**Total Shared**", f"${total:,.2f}")
        
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        l_owes = max(0.0, (j_spent - l_spent) / 2)
        j_owes = max(0.0, (l_spent - j_spent) / 2)

        col1, col2 = st.columns(2)
        col1.write(f"💳 **Leandro owes:** `${l_owes:,.2f}`")
        col2.write(f"💳 **Jonas owes:** `${j_owes:,.2f}`")

        st.subheader("Current Expenses")
        df_disp = df.copy()
        df_disp["Cost"] = df_disp["Cost"].map("${:,.2f}".format)
        
        # CHANGED: Swapped st.dataframe to st.table for font control
        st.table(df_disp[["Date", "Item", "Cost", "Who"]])

        st.divider()
        if st.button("Clear & Start New Round", type="secondary"):
            for page_id in df["id"]:
                notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
            st.rerun()
except Exception as e:
    st.error(f"Error: {e}")
