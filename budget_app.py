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

st.title("💰 Leonas Budget Tracker")

# --- 3. INPUT FORM ---
with st.form("expense_form", clear_on_submit=True):
    item_name = st.text_input("What did you buy?", placeholder="e.g. Groceries")
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
        st.metric("Total", f"${total:,.2f}")
        
        # Calculate individual totals
        l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
        j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
        
        # Settlement Logic (50/50 Split)
        if l_spent > j_spent:
            leandro_owes = 0.00
            jonas_owes = (l_spent - j_spent) / 2
        elif j_spent > l_spent:
            leandro_owes = (j_spent - l_spent) / 2
            jonas_owes = 0.00
        else:
            leandro_owes = 0.00
            jonas_owes = 0.00

        # Display the specific owing lines
        st.markdown("### ⚖️ Balance")
        st.write(f"💳 **Leandro owes Jonas:** `${leandro_owes:,.2f}`")
        st.write(f"💳 **Jonas owes Leandro:** `${jonas_owes:,.2f}`")

        # Display list of items
        st.subheader("Current Expenses")
        st.dataframe(df[["Item", "Cost", "Who"]], use_container_width=True, hide_index=True)

        # Archive Button
        st.divider()
        if st.button("Clear & Start New Round"):
            for page_id in df["id"]:
                notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
            st.rerun()
    else:
        st.info("No active expenses. Start logging!")

except Exception as e:
    st.error(f"Connection Error: {e}")
