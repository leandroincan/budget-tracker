import streamlit as st
from notion_client import Client
import pandas as pd

# 1. Setup
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# 2. Hide Branding
st.set_page_config(page_title="Budget Tracker", layout="centered")
st.markdown("<style>footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

st.title("💰 Our Budget Tracker")

# 3. Input Form
with st.form("add_expense", clear_on_submit=True):
    name = st.text_input("Item Name")
    cost = st.number_input("Cost", min_value=0.0, step=0.01)
    who = st.selectbox("Who paid?", ["Leandro", "Jonas"])
    if st.form_submit_button("Add Expense"):
        if name and cost > 0:
            notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Cost": {"number": cost},
                    "Who": {"select": {"name": who}},
                    "Archived": {"checkbox": False}
                }
            )
            st.success("Added!")
            st.rerun()

# 4. Data Fetching
try:
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={"property": "Archived", "checkbox": {"equals": False}}
    )
    
    rows = []
    for page in response["results"]:
        p = page["properties"]
        rows.append({
            "id": page["id"],
            "Name": p["Name"]["title"][0]["text"]["content"] if p["Name"]["title"] else "Untitled",
            "Cost": p["Cost"]["number"] or 0,
            "Who": p["Who"]["select"]["name"] if p["Who"]["select"] else "Unknown"
        })
    df = pd.DataFrame(rows)

    # 5. Math & Display
    if not df.empty:
        total = df["Cost"].sum()
        st.metric("Total Bill", f"${total:,.2f}")
        
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        c1, c2 = st.columns(2)
        c1.write(f"**Leandro:** ${l_spent:,.2f}")
        c2.write(f"**Jonas:** ${j_spent:,.2f}")

        if l_spent > j_spent:
            st.info(f"💡 Jonas owes Leandro: **${(l_spent - j_spent)/2:,.2f}**")
        elif j_spent > l_spent:
            st.info(f"💡 Leandro owes Jonas: **${(j_spent - l_spent)/2:,.2f}**")

        st.dataframe(df[["Name", "Cost", "Who"]], use_container_width=True, hide_index=True)

        if st.button("Clear / New Round"):
            for pid in df["id"]:
                notion.pages.update(page_id=pid, properties={"Archived": {"checkbox": True}})
            st.rerun()
except Exception as e:
    st.error("Notion Connection Error. Please check if the 'Archived' checkbox exists in Notion.")
