# Leandro Pereira
import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
# This looks for the keys in the cloud's secure vault
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

# Initialize connection
try:
    notion = Client(auth=NOTION_TOKEN)
except Exception as e:
    st.error(f"Connection Error: {e}")

st.title("💸 Couple's Budget Tracker")

# --- INPUT FORM ---
with st.form("budget_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    item = col1.text_input("Item Name (e.g., Groceries)")
    cost = col2.number_input("Cost ($)", min_value=0.0, step=0.01)

    # These options must match the 'Select' options in Notion exactly
    who = st.selectbox("Who Paid?", ["Leandro", "Partner"])

    submitted = st.form_submit_button("Add Expense")

    if submitted and item and cost > 0:
        try:
            # Send data to Notion
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": item}}]},
                    "Cost": {"number": cost},
                    "Who": {"select": {"name": who}},
                    "Date": {"date": {"start": datetime.now().isoformat()}}
                }
            )
            st.success(f"✅ Saved: {item} (${cost})")
        except Exception as e:
            st.error(f"❌ Error saving to Notion. Check your column names! Details: {e}")

# --- VIEW DATA ---
st.divider()
st.subheader("Recent Expenses")

# Get data from Notion
try:
    response = notion.databases.query(database_id=DATABASE_ID)

    rows = []
    # Loop through results and extract data
    for page in response["results"]:
        props = page["properties"]
        try:
            # Extracting values safely
            row = {
                "Date": props["Date"]["date"]["start"][:10],  # Get just YYYY-MM-DD
                "Item": props["Name"]["title"][0]["text"]["content"],
                "Cost": props["Cost"]["number"],
                "Who": props["Who"]["select"]["name"]
            }
            rows.append(row)
        except (KeyError, IndexError):
            continue  # Skip empty or malformed rows

    if rows:
        df = pd.DataFrame(rows)
        # Sort by date (newest first)
        df = df.sort_values(by="Date", ascending=False)
        st.dataframe(df, use_container_width=True)

        # Simple Chart
        st.bar_chart(df.groupby("Who")["Cost"].sum())
    else:
        st.info("No expenses found yet. Add one above!")

except Exception as e:
    st.warning("Could not load data. Make sure you connected the integration to the page.")