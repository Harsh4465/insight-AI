import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load components
from utils.db_manager import supabase
from phases.auth import auth_page
from phases.phase1_home import phase1_home
from phases.phase2_connect import phase2_connect
from phases.phase2_prepare import phase2_prepare
from phases.phase3_chat import phase3_chat
from phases.phase4_dashboard import phase4_dashboard

# Load secrets
load_dotenv()

st.set_page_config(
    page_title="Insight AI | 3D Analytics Hub",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/style.css")

# Session State Initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'df' not in st.session_state:
    st.session_state.df = None

# --- AUTO SESSION RECOVERY ---
if st.session_state.user is None and supabase:
    try:
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session.user
    except:
        pass

# --- AUTH GATE ---
if st.session_state.user is None:
    auth_page()
    st.stop()

# --- MAIN APP NAVIGATION ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0;">
            <h1 style="font-family: 'Outfit'; color: var(--primary); margin: 0;">🔮 Insight AI</h1>
            <p style="font-size: 0.8rem; color: var(--text-dim);">{st.session_state.user.email if hasattr(st.session_state.user, 'email') else 'Verified User'}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation Buttons
    if st.button("🏠 Hub Home", use_container_width=True, type="primary" if st.session_state.current_page == "Home" else "secondary"):
        st.session_state.current_page = "Home"
        st.rerun()
    
    st.markdown("<p style='font-size:0.7rem; color:var(--text-dim); margin-top:1rem;'>DATA PIPELINE</p>", unsafe_allow_html=True)
    
    if st.button("🔌 1: Connect", use_container_width=True, type="primary" if st.session_state.current_page == "1 Connect" else "secondary"):
        st.session_state.current_page = "1 Connect"
        st.rerun()

    if st.button("⚙️ 2: Prepare", use_container_width=True, disabled=st.session_state.df is None, type="primary" if st.session_state.current_page == "2 Prepare" else "secondary"):
        st.session_state.current_page = "2 Prepare"
        st.rerun()

    if st.button("💬 3: Chat Hub", use_container_width=True, disabled=st.session_state.df is None, type="primary" if st.session_state.current_page == "3 Chat" else "secondary"):
        st.session_state.current_page = "3 Chat"
        st.rerun()

    if st.button("📈 4: Dashboards", use_container_width=True, disabled=st.session_state.df is None, type="primary" if st.session_state.current_page == "4 Dashboards" else "secondary"):
        st.session_state.current_page = "4 Dashboards"
        st.rerun()

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        if supabase: supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.df = None
        st.rerun()

# --- PAGE ROUTING ---
from utils.ui_components import scroll_to_top

if 'last_page' not in st.session_state:
    st.session_state.last_page = st.session_state.current_page

if st.session_state.last_page != st.session_state.current_page:
    scroll_to_top()
    st.session_state.last_page = st.session_state.current_page

if st.session_state.current_page == "Home":
    phase1_home()
elif st.session_state.current_page == "1 Connect":
    phase2_connect()
elif st.session_state.current_page == "2 Prepare":
    phase2_prepare()
elif st.session_state.current_page == "3 Chat":
    phase3_chat()
elif st.session_state.current_page == "4 Dashboards":
    phase4_dashboard()
