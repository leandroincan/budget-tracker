import streamlit as st
from notion_client import Client
import pandas as pd

# --- CONFIGURATION ---
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

# HIDE STREAMLIT BRANDING
hide_st_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            header {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

# --- INPUT FORM ---
with st.form("expense_form", clear_on_submit=True):
    name = st.text_input("What did you buy?")
    cost = st.number_input("How much?", min_value=0.0, format="%.2f")
    who = st.selectbox("Who paid?", ["Leandro", "Partner"]) # Change 'Partner' to real name
    submitted = st.form_submit_button("Add Expense")

    if submitted and name:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": name}}]},
                "Cost": {"number": cost},
                "Who": {"select": {"name": who}},
                "Date": {"date": {"start": pd.Timestamp.now().strftime("%Y-%m-%d")}},
                "Archived": {"checkbox": False}
            }
        )
        st.success("Added!")

# --- FETCH DATA ---
results = notion.databases.query(
    database_id=DATABASE_ID,
    filter={"property": "Archived", "checkbox": {"equals": False}} # Only show non-archived
).get("results")

data = []
for row in results:
    data.append({
        "id": row["id"],
        "Name": row["properties"]["Name"]["title"][0]["text"]["content"],
        "Cost": row["properties"]["Cost"]["number"],
        "Who": row["properties"]["Who"]["select"]["name"],
    })

df = pd.DataFrame(data)

# --- TOTALS & MATH ---
if not df.empty:
    total = df["Cost"].sum()
    st.metric("Total This Round", f"${total:,.2f}")
    
    # Show the table
    st.table(df[["Name", "Cost", "Who"]])

    # --- THE CLEAR BUTTON ---
    if st.button("Clear & Start New Round"):
        for page_id in df["id"]:
            notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
        st.rerun()
else:
    st.write("No active expenses. Start adding some!")
