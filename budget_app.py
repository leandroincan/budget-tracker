import streamlit as st
from notion_client import Client
import pandas as pd

# --- CONFIGURATION ---
# These are pulled from your Streamlit Cloud Secrets
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

# --- UI STYLING (Hides Streamlit Branding) ---
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

# --- INPUT FORM ---
with st.form("expense_form", clear_on_submit=True):
    name = st.text_input("What did you buy?")
    cost = st.number_input("How much?", min_value=0.0, format="%.2f")
    who = st.selectbox("Who paid?", ["Leandro", "Jonas"])
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
        st.success("Expense added!")
        st.rerun()

# --- FETCH DATA ---
# We only pull items where 'Archived' is UNCHECKED
results = notion.databases.query(
    database_id=DATABASE_ID,
    filter={"property": "Archived", "checkbox": {"equals": False}}
).get("results")

data = []
for row in results:
    # Safely get properties (handles potential empty rows)
    props = row["properties"]
    try:
        data.append({
            "id": row["id"],
            "Name": props["Name"]["title"][0]["text"]["content"],
            "Cost": props["Cost"]["number"] or 0.0,
            "Who": props["Who"]["select"]["name"],
        })
    except (IndexError, KeyError, TypeError):
        continue

df = pd.DataFrame(data)

# --- TOTALS & SETTLEMENT MATH ---
if not df.empty:
    total = df["Cost"].sum()
    st.metric("Total This Round", f"${total:,.2f}")
    
    # Calculate individual totals
    leandro_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
    jonas_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Leandro Spent", f"${leandro_spent:,.2f}")
    col2.metric("Jonas Spent", f"${jonas_spent:,.2f}")

    # Settlement Calculation (The "Who owes who" logic)
    if leandro_spent > jonas_spent:
        diff = (leandro_spent - jonas_spent) / 2
        st.info(f"💡 **Jonas owes Leandro: ${diff:,.2f}** to even out.")
    elif jonas_spent > leandro_spent:
        diff = (jonas_spent - leandro_spent) / 2
        st.info(f"💡 **Leandro owes Jonas: ${diff:,.2f}** to even out.")
    else:
        st.success("✅ You are perfectly even!")

    # Display Table
    st.subheader("Current Expenses")
    st.dataframe(df[["Name", "Cost", "Who"]], use_container_width=True, hide_index=True)

    # --- ARCHIVE BUTTON ---
    st.divider()
    if st.button("Clear & Start New Round"):
        with st.spinner("Archiving..."):
            for page_id in df["id"]:
                notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
        st.success("Round cleared!")
        st.rerun()
else:
    st.info("No active expenses. Start adding some above!")
