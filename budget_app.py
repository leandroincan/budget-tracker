import streamlit as st
from notion_client import Client
import pandas as pd

# 1. Setup
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.title("💰 Budget Debug Mode")

# 2. Add Expense
with st.form("add"):
    name = st.text_input("Item")
    cost = st.number_input("Cost")
    who = st.selectbox("Who?", ["Leandro", "Jonas"])
    if st.form_submit_button("Add"):
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": name}}]},
                "Cost": {"number": cost},
                "Who": {"select": {"name": who}}
            }
        )
        st.rerun()

# 3. Fetch Everything (No Filters)
try:
    response = notion.databases.query(database_id=DATABASE_ID)
    st.write(f"Connected! Found {len(response['results'])} items.")
    
    rows = []
    for page in response["results"]:
        p = page["properties"]
        # This part is super safe - it won't crash if a column is missing
        row_name = p.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "N/A")
        row_cost = p.get("Cost", {}).get("number", 0)
        row_who = p.get("Who", {}).get("select", {}).get("name", "N/A")
        
        rows.append({"Name": row_name, "Cost": row_cost, "Who": row_who})
    
    df = pd.DataFrame(rows)
    st.table(df)

except Exception as e:
    st.error(f"Total Failure: {e}")
