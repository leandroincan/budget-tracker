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

    /* Default blue buttons */
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

    /* Green primary button */
    button[data-testid="baseButton-add_btn"],
    button[data-testid="baseButton-add_btn"]:focus,
    button[data-testid="baseButton-add_btn"]:active {
        background-color: #34C759 !important;
        border-color: #34C759 !important;
    }

    button[data-testid="baseButton-add_btn"]:hover {
        background-color: #28A745 !important;
        border-color: #28A745 !important;
    }

    /* Gray nav button (Budget Tracker) */
    button[data-testid="baseButton-nav_budget"] {
        background-color: #e0e0e0 !important;
        color: #333333 !important;
        font-weight: normal !important;
        height: 2.5em !important;
    }

    button[data-testid="baseButton-nav_budget"]:hover {
        background-color: #d0d0d0 !important;
    }

    button[data-testid="baseButton-nav_budget"]:active {
        background-color: #bfbfbf !important;
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
