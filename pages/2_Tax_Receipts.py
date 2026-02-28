import os
import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime
import cloudinary
import cloudinary.uploader

# --- 1. SETUP & CONFIG ---
NOTION_TOKEN = os.environ.get("NOTION_TOKEN") or st.secrets.get("NOTION_TOKEN")
TAX_DATABASE_ID = os.environ.get("TAX_DATABASE_ID") or st.secrets.get("TAX_DATABASE_ID")
notion = Client(auth=NOTION_TOKEN)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# --- 2. UI STYLING ---
st.set_page_config(page_title="Tax Receipts", page_icon="🧾", layout="centered")
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
    button[data-testid="stBaseButton-primary"]:active {
        background-color: #34C759 !important;
        border-color: #34C759 !important;
    }

    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #28A745 !important;
        border-color: #28A745 !important;
    }

    /* White nav button */
    button.st-emotion-cache-jc12jo,
    button.st-emotion-cache-jc12jo:focus,
    button.st-emotion-cache-jc12jo:active {
        background-color: #ffffff !important;
        color: #333333 !important;
        font-weight: normal !important;
        white-space: nowrap !important;
        height: auto !important;
        padding: 0.4em 0.8em !important;
        font-size: 12px !important;
        border: 1px solid #e0e0e0 !important;
    }

    button.st-emotion-cache-jc12jo:hover {
        background-color: #f0f0f0 !important;
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

st.title("🧾 Tax Receipts")

# --- NAVIGATION ---
st.markdown(
    '<div style="display:flex; gap:8px; margin-bottom:8px;">'
    '<a href="/" target="_self" style="text-decoration:none;">'
    '<button style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:6px 12px;font-size:12px;cursor:pointer;">💰 Budget Tracker</button>'
    '</a>'
    '<a href="/1_Wolfie" target="_self" style="text-decoration:none;">'
    '<button style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:6px 12px;font-size:12px;cursor:pointer;">🐾 Wolfie\'s Fund</button>'
    '</a>'
    '</div>',
    unsafe_allow_html=True
)

st.write("")

# --- 3. SESSION STATE ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# --- 4. INPUT SECTION ---
fk = st.session_state.form_key
categories = ["Health", "Business", "Home Office", "Vehicle/Transportation"]
years = ["2025"]

description = st.text_input("Description", placeholder="e.g. Medical Appointment", key=f"description_{fk}")
amount = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="0.00", key=f"amount_{fk}")
category = st.selectbox("Category", options=categories, index=None, placeholder="Select category", key=f"category_{fk}")
who = st.selectbox("Who?", ["Leandro", "Jonas"], index=None, placeholder="Select person", key=f"who_{fk}")
year = st.selectbox("Tax Year", options=years, index=None, placeholder="Select year", key=f"year_{fk}")
receipt_photos = st.file_uploader("Receipt Photos", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True, key=f"photo_{fk}")

st.write("")

add_clicked = st.button("Add Receipt", type="primary", key="add_btn")

if add_clicked:
    if description and amount and amount > 0 and category and who and year:
        today = datetime.now().strftime("%Y-%m-%d")

        # Upload photos to Cloudinary if provided
        photo_urls = []
        if receipt_photos:
            for photo in receipt_photos:
                upload_result = cloudinary.uploader.upload(photo, folder="tax_receipts")
                url = upload_result.get("secure_url", "")
                if url:
                    photo_urls.append(url)

        photo_url_string = " | ".join(photo_urls)

        notion.pages.create(
            parent={"database_id": TAX_DATABASE_ID},
            properties={
                "Description": {"title": [{"text": {"content": description}}]},
                "Amount": {"number": amount},
                "Category": {"select": {"name": category}},
                "Who": {"select": {"name": who}},
                "Date": {"date": {"start": today}},
                "Year": {"select": {"name": year}},
                "Receipt": {"url": photo_url_string if photo_url_string else None},
            }
        )
        st.success("Receipt added!" + (f" 📸 {len(photo_urls)} photo(s) uploaded!" if photo_urls else ""))
        st.session_state.form_key += 1
        st.rerun()
    else:
        st.error("Please fill out all fields.")

# --- 5. DATA FETCHING ---
try:
    response = notion.databases.query(database_id=TAX_DATABASE_ID)
    results = response.get("results")

    rows = []
    for page in results:
        p = page["properties"]
        title_list = p.get("Description", {}).get("title", [])
        desc_val = title_list[0]["text"]["content"] if title_list else ""
        date_val = p.get("Date", {}).get("date", {})
        date_str = date_val.get("start", "No Date") if date_val else "No Date"
        category_val = p.get("Category", {}).get("select") or {}
        who_val = p.get("Who", {}).get("select") or {}
        year_val = p.get("Year", {}).get("select") or {}
        receipt_url = p.get("Receipt", {}).get("url", "") or ""

        rows.append({
            "Date": date_str,
            "Description": desc_val,
            "Amount": p.get("Amount", {}).get("number") or 0.0,
            "Category": category_val.get("name", "Unknown"),
            "Who": who_val.get("name", "Unknown"),
            "Year": year_val.get("name", "Unknown"),
            "Receipt URL": receipt_url,
        })

    df = pd.DataFrame(rows)

    # --- 6. DASHBOARD ---
    if not df.empty:
        st.divider()

        selected_year = st.selectbox("Filter by Tax Year", options=["All"] + years, index=0, key="year_filter")
        if selected_year != "All":
            df = df[df["Year"] == selected_year]

        if not df.empty:
            total = df["Amount"].sum()
            st.metric("🧾 Total", f"${total:,.2f}")

            col1, col2 = st.columns(2)
            l_total = df[df["Who"] == "Leandro"]["Amount"].sum()
            j_total = df[df["Who"] == "Jonas"]["Amount"].sum()
            col1.write(f"🧾 **Leandro:** `${l_total:,.2f}`")
            col2.write(f"🧾 **Jonas:** `${j_total:,.2f}`")

            st.subheader("By Category")
            cat_summary = df.groupby("Category")["Amount"].sum().reset_index()
            cat_summary.index = range(1, len(cat_summary) + 1)
            cat_summary["Amount"] = cat_summary["Amount"].map("${:,.2f}".format)
            st.table(cat_summary)

            st.subheader("All Receipts")
            for i, row in df.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['Description']}** — ${row['Amount']:,.2f} | {row['Category']} | {row['Who']} | {row['Date']}")
                if row["Receipt URL"]:
                    urls = row["Receipt URL"].split(" | ")
                    for idx, url in enumerate(urls):
                        col2.markdown(f"📸 [View]({url})", unsafe_allow_html=True)
                else:
                    col2.write("No photo")
        else:
            st.info(f"No receipts found for {selected_year}.")

except Exception as e:
    st.error(f"Error: {e}")
