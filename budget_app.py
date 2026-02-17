import streamlit as st
from notion_client import Client
import pandas as pd

# Setup
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.title("💰 Budget Tracker")

# 1. Add Expense
with st.form("add_expense", clear_on_submit=True):
    name = st.text_input("What did you buy?")
    cost = st.number_input("How much?", min_value=0.0)
    who = st.selectbox("Who paid?", ["Leandro", "Jonas"])
    if st.form_submit_button("Add Expense"):
        if name and cost > 0:
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Item": {"title": [{"text": {"content": name}}]},
                    "Cost": {"number": cost},
                    "Who": {"select": {"name": who}},
                    "Archived": {"checkbox": False}
                }
            )
            st.rerun()

# 2. Fetch Data (The syntax fix)
try:
    # This is the modern way to query
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results")
    
    rows = []
    for page in results:
        p = page["properties"]
        # Only show if NOT archived
        is_archived = p.get("Archived", {}).get("checkbox", False)
        
        if not is_archived:
            rows.append({
                "id": page["id"],
                "Item": p["Item"]["title"][0]["text"]["content"] if p["Item"]["title"] else "Untitled",
                "Cost": p["Cost"]["number"] or 0,
                "Who": p["Who"]["select"]["name"] if p["Who"]["select"] else "Unknown"
            })
    
    df = pd.DataFrame(rows)

    if not df.empty:
        total = df["Cost"].sum()
        st.metric("Total", f"${total:,.2f}")
        st.table(df[["Item", "Cost", "Who"]])
        
        if st.button("Clear Round"):
            for pid in df["id"]:
                notion.pages.update(page_id=pid, properties={"Archived": {"checkbox": True}})
            st.rerun()
    else:
        st.info("No active expenses.")

except Exception as e:
    st.error(f"Error: {e}")
