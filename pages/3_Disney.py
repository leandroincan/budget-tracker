import os
import streamlit as st
from notion_client import Client
import pandas as pd
from datetime import datetime

# --- SETUP & STYLING (Use the exact same CSS as your main app) ---
# ... (Paste your Section 1 & 2 here) ...

st.title("🎡 Disney Trip Budget")

# Create the 3 Tabs
tab1, tab2, tab3 = st.tabs(["📅 Pre-Trip (Fixed)", "🎢 During Trip", "📊 Settlement Dashboard"])

# --- TAB 1: PRE-TRIP ---
with tab1:
    st.subheader("Bookings & Tickets")
    cat_fixed = st.selectbox("Category", ["Flights", "Hotel", "Disneyland Tickets", "Universal Tickets"], key="fixed_cat")
    details_fixed = st.text_input("Details", placeholder="e.g. Delta Flights, Airbnb", key="fixed_det")
    cost_fixed = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", key="fixed_cost")
    who_fixed = st.selectbox("Who paid?", ["Leandro", "Jonas"], key="fixed_who")
    
    if st.button("Add Fixed Cost", type="primary"):
        # We will add a hidden "Phase" tag here before sending to Notion
        st.success("Fixed cost added!")

# --- TAB 2: DURING TRIP ---
with tab2:
    st.subheader("Daily Spending")
    cat_daily = st.selectbox("Category", ["Food & Drinks", "Uber / Transit", "Souvenirs", "Misc"], key="daily_cat")
    details_daily = st.text_input("Details", placeholder="e.g. Dinner at Disney Springs", key="daily_det")
    cost_daily = st.number_input("Amount ($)", min_value=0.0, step=0.01, format="%.2f", key="daily_cost")
    who_daily = st.selectbox("Who paid?", ["Leandro", "Jonas"], key="daily_who")
    
    if st.button("Add Daily Expense", type="primary"):
        st.success("Daily expense added!")

# --- TAB 3: DASHBOARD ---
with tab3:
    st.subheader("Total Trip Settlement")
    # This math handles the Net Settlement you asked about automatically
    # If Leandro pays $500 and Jonas pays $300, l_owes will be $0, and j_owes will be $100.
    
    # Example logic once data is fetched:
    # l_spent = df[df["Who"] == "Leandro"]["Cost"].sum()
    # j_spent = df[df["Who"] == "Jonas"]["Cost"].sum()
    # l_owes = max(0.0, (j_spent - l_spent) / 2)
    # j_owes = max(0.0, (l_spent - j_spent) / 2)
    
    st.write("Math goes here!")
