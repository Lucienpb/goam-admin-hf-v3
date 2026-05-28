#-------------------------------
# GOAM ADMIN APP (Final Clean Version, Patched)
#-------------------------------
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime, timedelta
import requests

# AUTH MODULES
from auth.auth import (
    verify_token,
    verify_user_email,
    reset_password,
    get_user_role,
    migrate_users_to_lowercase,   # <-- NEW import
    load_users
)
from auth.login_page import show_login_page
from auth.profile_page import show_profile_page
from auth.admin_page import show_admin_page

# GOAM MODULES
from apps.pairing_app import run as run_pairing_app
from apps.handicap_app import run as run_handicap_app
from apps.scores_app import run_scores_app
from apps.goam_dashboard import run as run_goam_dashboard
from utils.handicap_calculator import load_course_data
from admin.data_manager_page import show_data_manager_page
from utils.github_storage import sync_all_from_github   # <-- already imported
from apps.ai_chat import run as run_ai_chat

SESSION_TIMEOUT = 3600  # 1 hour

# ============================================================
# SCRAPER STATUS CHECK
# ============================================================
def scraper_is_awake(base_url: str) -> bool:
    try:
        r = requests.get(base_url, timeout=3)
        return r.headers.get("content-type", "").startswith("application/json")
    except:
        return False

# ========================================================================
# PAGE CONFIG
# ========================================================================
st.set_page_config(
    page_title="GOAM Admin",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================================================
# THEME
# ========================================================================
def inject_theme():
    st.markdown("""
        <style>
        html, body, [class*="css"]  {
            font-family: 'Segoe UI', sans-serif;
        }
        .main {
            background-color: #f7f9fc;
        }

        section[data-testid="stSidebar"] {
            background-color: #D6ECFF;
            color: #003366;
        }

        .stButton>button {
            background-color: #0b3d91;
            color: white;
            border-radius: 6px;
            padding: 0.6rem 1rem;
            border: none;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #0a357f;
            color: #e6e6e6;
        }
        .streamlit-expanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
            color: #0b3d91;
        }
        </style>
    """, unsafe_allow_html=True)

inject_theme()

# ========================================================================
# SESSION INITIALIZATION
# ========================================================================
def init_session():
    defaults = {
        "authenticated": False,
        "email": None,
        "role": None,
        "login_time": None,
        "last_activity": datetime.now(),
        "course_df": None,
        "page": "profile",
        "handicap_mode": "single",
        "scraper_refresh_count": 0,
        # 🔥 REQUIRED FOR HANDICAP LOGIN
        "hcp_logged_in": False,
        "hcp_username": None,
        "hcp_password": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ========================================================================
# GITHUB SYNC + USER MIGRATION
# ========================================================================
if "github_synced" not in st.session_state:
    sync_all_from_github()
    migrate_users_to_lowercase()   # <-- extra line
     # DEBUG: show immediately what was loaded from user.json
    users = load_users()
    
    st.session_state.github_synced = True

# ========================================================================
# SESSION TIMEOUT
# ========================================================================
def check_timeout():
    if not st.session_state.get("authenticated"):
        return

    last = st.session_state.get("last_activity")

    if isinstance(last, str):
        try:
            last = datetime.fromisoformat(last)
        except:
            last = datetime.now()

    if datetime.now() - last > timedelta(seconds=SESSION_TIMEOUT):
        st.warning("Session expired. Please login again.")
        st.session_state.authenticated = False
        st.session_state.email = None
        st.session_state.role = None
        st.session_state.login_time = None
        st.session_state.last_activity = None
        st.rerun()

    st.session_state.last_activity = datetime.now()

check_timeout()

# ========================================================================
# EMAIL VERIFICATION
# ========================================================================
def handle_email_verification():
    params = st.query_params
    if "token" in params:
        email = verify_token(params["token"], "email_verification")
        if email:
            verify_user_email(email)
            st.success("Email verified successfully! You can now login.")
        else:
            st.error("Invalid or expired verification link.")

handle_email_verification()

# ========================================================================
# PASSWORD RESET
# ========================================================================
def handle_password_reset():
    params = st.query_params
    if "reset-password" in params:
        token = params["token"]
        email = verify_token(token, "password_reset")

        if not email:
            st.error("Invalid or expired reset link.")
            return

        st.header("🔐 Reset Password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")

        if st.button("Set New Password", use_container_width=True):
            if not new_pw:
                st.error("Password required")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match")
            elif len(new_pw) < 8:
                st.error("Password must be at least 8 characters")
            else:
                ok, msg = reset_password(email, new_pw)
                if ok:
                    st.success("Password reset successful!")
                else:
                    st.error(msg)

        st.stop()

handle_password_reset()

# ========================================================================
# LOGIN GATE
# ========================================================================
if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# ========================================================================
# SCRAPER CHECK (AUTO REFRESH)
# ========================================================================
SCRAPER_URL = "https://lucienpb-handicap-scraper.hf.space"

status_placeholder = st.empty()
scraper_awake = scraper_is_awake(SCRAPER_URL)

with status_placeholder.container():
    col1, = st.columns([0.06])
    if scraper_awake:
        col1.markdown("🟢", unsafe_allow_html=True)
    else:
        col1.markdown("🔴", unsafe_allow_html=True)

# Auto-refresh every 10 seconds, up to 6 times
if not scraper_awake and st.session_state.scraper_refresh_count < 6:
    st.session_state.scraper_refresh_count += 1
    st.experimental_rerun(delay=10)

# ========================================================================
# SIDEBAR NAVIGATION
# ========================================================================
st.sidebar.image("assets/goam_logo.png", width='stretch')
st.sidebar.markdown("---")

if st.sidebar.button("👤 My Profile"):
    st.session_state.page = "profile"

st.sidebar.markdown("---")

role = st.session_state.get("role", "member")

# SCORES GROUP
with st.sidebar.expander("📘 Scores", expanded=False):
    if st.button("Leaderboards"):
        st.session_state.page = "scores_leaderboards"
    if st.button("Scorecards"):
        st.session_state.page = "scores_cards"

# HANDICAP GROUP
with st.sidebar.expander("🏌️ Handicap", expanded=False):
    if not scraper_awake:
        st.button("Single Player", disabled=True)
        st.button("Batch", disabled=True)
    else:
        if st.button("Single Player"):
            st.session_state.page = "handicap"
            st.session_state.handicap_mode = "single"
        if st.button("Batch"):
            st.session_state.page = "handicap"
            st.session_state.handicap_mode = "batch"
    if st.button("Calculator"):
        st.session_state.page = "handicap"
        st.session_state.handicap_mode = "calculator"

# PAIRINGS GROUP
with st.sidebar.expander("⛳ Pairings", expanded=False):
    if st.button("Matrix"):
        st.session_state.page = "pairings_matrix"
    if st.button("4‑Ball Generation"):
        st.session_state.page = "pairings_gen"

# ADMIN GROUP
with st.sidebar.expander("🛠️ Admin", expanded=False):
    if st.button("User Management"):
        st.session_state.page = "admin_users"
    if st.button("Data Manager"):
        st.session_state.page = "admin_data"



# AI CHAT GROUP
with st.sidebar.expander("🤖 AI", expanded=False):
    if st.button("AI Chat (Free)"):
        st.session_state.page = "ai_chat"

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.email = None
    st.session_state.role = None
    st.session_state.login_time = None
    st.session_state.last_activity = None
    st.rerun()

# ========================================================================
# PAGE ROUTING
# ========================================================================
page = st.session_state.page

if page == "profile":
    show_profile_page(st.session_state.email)
elif page == "dashboard":
    run_goam_dashboard()
elif page == "pairings_matrix":
    run_pairing_app("matrix")
elif page == "pairings_gen":
    run_pairing_app("generator")
elif page == "scores_leaderboards":
    run_scores_app("leaderboards")
elif page == "scores_cards":
    run_scores_app("scorecards")
elif page == "handicap":
    # NEW: No sidebar login — login handled inside handicap_app.py
    st.session_state.course_df = load_course_data()
    mode = st.session_state.handicap_mode
    run_handicap_app(mode, None, st.session_state.course_df)

elif page == "admin_users":
    show_admin_page(st.session_state.email)

elif page == "admin_data":
    show_data_manager_page()

elif page == "ai_chat":
    run_ai_chat()
