import os
import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime
import requests

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or st.secrets.get("NOTION_TOKEN")
DISNEY_DATABASE_ID = os.environ.get("DISNEY_DATABASE_ID") or st.secrets.get("DISNEY_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

# Pull live exchange rate and cache it for 1 hour so it doesn't slow down the app
@st.cache_data(ttl=3600)
def get_live_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        return float(response.json()["rates"]["CAD"])
    except:
        return 1.41  # Fallback if the API is ever down

live_usd_cad = get_live_rate()

# --- 2. UI STYLING ---
st.set_page_config(page_title="Disney Trip", page_icon="🎡", layout="centered")
st.markdown("""
    <style>
    [data-testid="stToolbar"], footer, header {visibility: hidden !important;}
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    .main { background-color: #ffffff; }

    html, body, [class*="st-"], .stSelectbox, .stTextInput, .stNumberInput, label, button, td, th, p {
        font-size: 14px !important; 
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        font-size: 18px !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 16px !important;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3.2em;
        background-color: #007AFF !important;
        color: white !important;
        font-weight: bold;
        border: none !important;
        transition: 0.2s;
    }

    .stButton > button:hover {
        background-color: #0056b3 !important;
    }

    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"]:focus,
    button[data-testid="stBaseButton-primary"]:active,
    .st-emotion-cache-16rr57l {
        background-color: #34C759 !important;
        border-color: #34C759 !important;
    }

    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #28A745 !important;
        border-color: #28A745 !important;
    }

    .nav-button {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        transition: 0.2s;
        color: #333333 !important;
        text-decoration: none !important;
    }

    .nav-button:hover {
        background: #f0f0f0 !important;
    }

    .nav-button:active {
        background: #e0e0e0 !important;
    }

    a .nav-button, a:visited .nav-button, a:hover .nav-button {
        color: #333333 !important;
        text-decoration: none !important;
    }

    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #f8f9fb !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }

    table { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎡 Disney Trip Budget")

# --- NAVIGATION ---
st.markdown(
    '<div style="display:flex; gap:8px; margin-bottom:8px; flex-wrap: wrap;">'
    '<a href="/" target="_self" style="text-decoration:none;"><button class="nav-button">💰 Main Tracker</button></a>'
    '<a href="/Wolfie" target="_self" style="text-decoration:none;"><button class="nav-button">🐾 Wolfie\'s Fund</button></a>'
    '<a href="/Tax_Receipts" target="_self" style="text-decoration:none;"><button class="nav-button">🧾 Tax Receipts</button></a>'
    '</div>',
    unsafe_allow_html=True
)
st.write("")

# --- TABS ---
tab1, tab2 = st.tabs(["📅 Pre-Trip", "🎢 During Trip"])

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
fk = st.session_state.form_key

def add_expense(cat, det, amount, currency, rate, payer, date, phase):
    if cat and payer and amount and amount > 0:
        final_amount = amount * rate if currency == "USD" else amount
        display_det = f"{det} (USD {amount:,.2f} @ {rate:.2f})" if currency == "USD" else det
        final_name = f"{cat}: {display_det}" if display_det else cat
        
        notion.pages.create(
            parent={"database_id": DISNEY_DATABASE_ID},
            properties={
                "Item": {"title": [{"text": {"content": final_name}}]},
                "Cost": {"number": final_amount},
                "Who": {"select": {"name": payer}},
                "Date": {"date": {"start": str(date) if date else datetime.now().strftime("%Y-%m-%d")}},
                "Phase": {"select": {"name": phase}},
                "Archived": {"checkbox": False}
            }
        )
        st.success("Added!")
        st.session_state.form_key += 1
        st.rerun()
    else:
        st.error("Please fill out Category, Amount, and Who paid.")

with tab1:
    st.subheader("Bookings & Tickets")
    cat_pre = st.selectbox("Category", ["Flights", "Hotel", "Disneyland Tickets", "Universal Tickets", "Other"], key=f"cat_pre_{fk}")
    det_pre = st.text_input("Details", placeholder="e.g. Airbnb", key=f"det_pre_{fk}")
    
    currency_pre = st.selectbox("Currency", ["CAD", "USD"], key=f"curr_pre_{fk}")
    rate_pre = 1.0
    if currency_pre == "USD":
        # Uses the live rate as the default, but lets you type over it
        rate_pre = st.number_input("USD to CAD Exchange Rate", min_value=1.0, value=live_usd_cad, step=0.01, format="%.2f", key=f"rate_pre_{fk}")
    
    cost_pre = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", value=None, key=f"cost_pre_{fk}")
    who_pre = st.selectbox("Who paid?", ["Leandro", "Jonas"], index=None, key=f"who_pre_{fk}")
    date_pre = st.date_input("Date", value=None, key=f"date_pre_{fk}")
    
    if st.button("Add Fixed Cost", type="primary", key="btn_pre"):
        add_expense(cat_pre, det_pre, cost_pre, currency_pre, rate_pre, who_pre, date_pre, "Pre-Trip")

    st.divider()
    
    # --- DASHBOARD ---
    try:
        results = notion.databases.query(database_id=DISNEY_DATABASE_ID).get("results", [])
        rows = []
        for p in results:
            prop = p["properties"]
            if not prop.get("Archived", {}).get("checkbox", False):
                t_list = prop.get("Item", {}).get("title", [])
                item_val = t_list[0]["text"]["content"] if t_list else "Untitled"
                date_val = prop.get("Date", {}).get("date", {})
                d_str = date_val.get("start", "No Date") if date_val else "No Date"
                phase_val = prop.get("Phase", {}).get("select", {})
                p_str = phase_val.get("name", "Unknown") if phase_val else "Unknown"
                
                rows.append({
                    "id": p["id"], "Date": d_str, "Item": item_val,
                    "Cost": prop.get("Cost", {}).get("number") or 0.0,
                    "Who": prop.get("Who", {}).get("select", {}).get("name", "Unknown"),
                    "Phase": p_str
                })
        
        df = pd.DataFrame(rows)
        if not df.empty:
            total = df["Cost"].sum()
            st.metric("**Total Trip Cost**", f"${total:,.2f}")
            
            l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
            j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
            
            l_owes = max(0.0, (j_spent - l_spent) / 2)
            j_owes = max(0.0, (l_spent - j_spent) / 2)
            
            col1, col2 = st.columns(2)
            col1.write(f"💳 **Leandro owes:** `${l_owes:,.2f}`")
            col2.write(f"💳 **Jonas owes:** `${j_owes:,.2f}`")
            
            st.subheader("All Expenses")
            df_disp = df.copy()
            df_disp["Cost"] = df_disp["Cost"].map("${:,.2f}".format)
            st.table(df_disp[["Date", "Item", "Cost", "Who", "Phase"]])
            
            st.divider()
            if st.button("Archive All Trip Expenses"):
                for page_id in df["id"]:
                    notion.pages.update(page_id=page_id, properties={"Archived": {"checkbox": True}})
                st.rerun()
    except Exception as e:
        st.error(f"Error loading data: {e}")

with tab2:
    st.subheader("Daily Spending")
    cat_daily = st.selectbox("Category", ["Food & Drinks", "Uber/Transit", "Souvenirs", "Misc"], key=f"cat_day_{fk}")
    det_daily = st.text_input("Details", placeholder="e.g. Dinner at Disney Springs", key=f"det_day_{fk}")
    
    currency_daily = st.selectbox("Currency", ["CAD", "USD"], key=f"curr_day_{fk}")
    rate_daily = 1.0
    if currency_daily == "USD":
        # Uses the live rate as the default, but lets you type over it
        rate_daily = st.number_input("USD to CAD Exchange Rate", min_value=1.0, value=live_usd_cad, step=0.01, format="%.2f", key=f"rate_day_{fk}")
        
    cost_daily = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", value=None, key=f"cost_day_{fk}")
    who_daily = st.selectbox("Who paid?", ["Leandro", "Jonas"], index=None, key=f"who_daily_{fk}")
    date_daily = st.date_input("Date", value=None, key=f"date_daily_{fk}")
    
    if st.button("Add Daily Expense", type="primary", key="btn_daily"):
        add_expense(cat_daily, det_daily, cost_daily, currency_daily, rate_daily, who_daily, date_daily, "Daily")
