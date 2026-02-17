import streamlit as st
from notion_client import Client
import pandas as pd

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
with st.form("expense_form", clear_on_submit=True):
    # Changed from 'Name' to 'Item' for your Notion column
    item_name = st.text_input("What did you buy?", placeholder="e.g. Groceries")
    
    # Currency input styling
    cost = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f")
    
    who = st.selectbox("Who paid?", ["Leandro", "Jonas"])
    submitted = st.form_submit_button("Add Expense")

    if submitted and item_name and cost > 0:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Item": {"title": [{"text": {"content": item_name}}]},
                "Cost": {"number": cost},
                "Who": {"select": {"name": who}},
                "Archived": {"checkbox": False}
            }
        )
        st.success(f"Added ${cost:.2f} for {item_name}!")
        st.rerun()

# --- 4. DATA FETCHING ---
try:
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results")
    
    rows = []
    for page in results:
        p = page["properties"]
        # Check if item is archived
        is_archived = p.get("Archived", {}).get("checkbox", False)
        
        if not is_archived:
            # Safely grab the Item name
            title_list = p.get("Item", {}).get("title", [])
            item_val = title_list[0]["text"]["content"] if title_list else "Untitled"
            
            rows.append({
                "id": page["id"],
                "Item": item_val,
                "Cost": p.get("Cost", {}).get("number") or 0.0,
                "Who": p.get("Who", {}).get("select", {}).get("name", "Unknown")
            })
    
    df = pd.DataFrame(rows)

    # --- 5. DASHBOARD & MATH ---
    if not df.empty:
        total = df["Cost"].sum()
        st.metric("Total Shared Spend", f"${total:,.2f}")
        
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        col1, col2 = st.columns(2)
        col1.write(f"**Leandro:** ${l_spent:,.2f}")
        col2.write(f"**Jonas:** ${j_spent:,.2f}")

        # Settlement Logic
        if l_spent > j_spent:
            diff = (l_spent - j_spent) / 2
            st.info(f"💡 **Jonas owes Leandro: ${diff:,.2f}**")
        elif j_spent > l_spent:
            diff = (j_spent - l_spent) / 2
            st.info(f"💡 **Leandro owes Jonas: ${diff:,.2f}**")
        else:
            st.success("✅ You are perfectly even!")

        # Display list of items
        st.subheader("Current Expenses")
        st.dataframe(df[["Item", "Cost", "Who"]], use_container_width=True, hide_index=True)

        # Archive Button
        st.divider()
        if st.button("Clear & Start New Round"):
            with st.spinner("Cleaning up..."):
                for page_id in df["id"]:
                    notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
            st.rerun()
    else:
        st.info("No active expenses. Start logging!")

except Exception as e:
    st.error(f"Connection Error: {e}")
