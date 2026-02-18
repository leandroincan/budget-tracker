import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# --- 2. HIDE BRANDING & UI ---
st.set_page_config(page_title="Budget Tracker", layout="centered")
hide_st_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            header {visibility: hidden !important;}
            #stDecoration {display:none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

# --- 3. INPUT FORM ---
categories = ["Superstore", "Safeway", "Dollarama", "Walmart", "Others"]

with st.form("expense_form", clear_on_submit=True):
    # Dropdown for category
    category = st.selectbox("Category", options=categories, placeholder="Select", index=None)  # This allows the placeholder to show
    
    # Optional text for specifics (e.g., "Sushi" or "Costco")
    details = st.text_input("Details (Optional)", placeholder="e.g. Groceries")
    
    # Currency input
    cost = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f")
    
    who = st.selectbox("Who paid?", ["Leandro", "Jonas"],placeholder="Select", index=None)
    submitted = st.form_submit_button("Add Expense")

    if submitted and cost > 0:
        # Combine category and details for the 'Item' column
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
        st.success(f"Added!")
        st.rerun()

# --- 4. DATA FETCHING ---
try:
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results")
    
    rows = []
    for page in results:
        p = page["properties"]
        is_archived = p.get("Archived", {}).get("checkbox", False)
        
        if not is_archived:
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
        
        # 50/50 Split Logic
        if l_spent > j_spent:
            leandro_owes, jonas_owes = 0.0, (l_spent - j_spent) / 2
        elif j_spent > l_spent:
            leandro_owes, jonas_owes = (j_spent - l_spent) / 2, 0.0
        else:
            leandro_owes, jonas_owes = 0.0, 0.0

        st.markdown("### ⚖️ Balance")
        st.write(f"💳 **Leandro owes Jonas:** `${leandro_owes:,.2f}`")
        st.write(f"💳 **Jonas owes Leandro:** `${jonas_owes:,.2f}`")

        # Display list of items
        st.subheader("Current Expenses")
        
        df_display = df.copy()
        # Format Cost column for the table
        df_display["Cost"] = df_display["Cost"].map("${:,.2f}".format)
        
        # Display table with Date first
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
        st.info("No active expenses. Start logging!")

except Exception as e:
    st.error(f"Connection Error: {e}")
