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
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007AFF;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

# --- 3. INPUT SECTION (NO FORM) ---
categories = ["Superstore", "Safeway", "Dollarama", "Walmart", "Others"]

# We use columns to keep it tight
category = st.selectbox("Category", options=categories, index=None, placeholder="Select store")
details = st.text_input("Details (Optional)", placeholder="e.g. Groceries")
cost = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0.00")
who = st.selectbox("Who paid?", ["Leandro", "Jonas"], index=None, placeholder="Select person")

# Regular button (No form = No "Press Enter" message)
if st.button("Add Expense"):
    if category and who and cost:
        final_item_name = f"{category}: {details}" if details else category
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
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
        except Exception as e:
            st.error(f"Error saving to Notion: {e}")
    else:
        st.warning("Please fill out all fields.")

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

    # --- 5. DASHBOARD & MATH ---
    if not df.empty:
        total = df["Cost"].sum()
        st.metric("Total", f"${total:,.2f}")
        
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        leandro_owes = max(0.0, (j_spent - l_spent) / 2)
        jonas_owes = max(0.0, (l_spent - j_spent) / 2)

        st.markdown("### ⚖️ Balance")
        st.write(f"💳 **Leandro owes Jonas:** `${leandro_owes:,.2f}`")
        st.write(f"💳 **Jonas owes Leandro:** `${jonas_owes:,.2f}`")

        # Table Display
        st.subheader("Current Expenses")
        df_display = df.copy()
        df_display["Cost"] = df_display["Cost"].map("${:,.2f}".format)
        
        st.dataframe(
            df_display[["Date", "Item", "Cost", "Who"]], 
            use_container_width=True, 
            hide_index=True
        )

        st.divider()
        if st.button("Clear & Start New Round"):
            for page_id in df["id"]:
                notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
            st.rerun()
    else:
        st.info("No active expenses.")

except Exception as e:
    st.error(f"Connection Error: {e}")
