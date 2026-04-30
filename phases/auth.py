import streamlit as st
from utils.db_manager import supabase
import time
import streamlit.components.v1 as components

def auth_page():
    import os
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    groq = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not supabase:
        st.error(f"Database connection missing. URL: {'Found' if url else 'Missing'}, KEY: {'Found' if key else 'Missing'}, GROQ: {'Found' if groq else 'Missing'}")
        st.stop()

    if "error" in st.query_params:
        err_msg = st.query_params.get("error_description", st.query_params["error"])
        st.error(f"Google Login Failed: {err_msg}")
        st.info("Tip: Please check your Google Cloud Client ID & Secret in the Supabase Dashboard.")

    # (Old JS bridge removed)

    # --- COMPONENT BRIDGE FOR IMPLICIT FLOW ---
    import streamlit.components.v1 as components
    import os
    
    # Load the custom component
    auth_bridge = components.declare_component("auth_bridge", path="auth_bridge")
    
    # Render component and get hash value
    hash_val = auth_bridge()
    
    if hash_val and isinstance(hash_val, str) and "access_token=" in hash_val:
        # Parse the hash string (#access_token=...&refresh_token=...)
        from urllib.parse import parse_qs
        params = parse_qs(hash_val.lstrip("#"))
        token = params.get("access_token", [None])[0]
        refresh = params.get("refresh_token", [None])[0]
        
        if token:
            try:
                res = supabase.auth.set_session(token, refresh)
                st.session_state.user = res.user
                from utils.db_manager import sync_user_profile
                sync_user_profile(res.user)
                st.rerun()
            except Exception as e:
                st.error("⚠️ Login session expired or invalid. Please try logging in again.")
                components.html("<script>window.parent.history.replaceState(null, null, window.parent.location.pathname);</script>", height=0)
    elif hash_val and isinstance(hash_val, str) and hash_val.startswith("ERROR:"):
        st.error(f"Bridge Error: {hash_val}")

    # --- UI LAYOUT ---
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem; margin-top: 2rem;">
                <h1 class="hero-title"><span class="text-gradient">Insight AI</span></h1>
                <p style="color: var(--text-dim); font-size: 1.1rem;">The Future of Intelligent Data Analytics</p>
            </div>
        """, unsafe_allow_html=True)

        # Tabs for Login/Signup
        tab_login, tab_signup = st.tabs(["🔐 Login", "✨ Create Account"])

        with tab_login:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Welcome Back")
            email = st.text_input("Email", key="login_email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            
            if st.button("Sign In ➔", key="l_btn", type="primary", use_container_width=True):
                if email and password:
                    with st.spinner("Authenticating..."):
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = res.user
                            from utils.db_manager import sync_user_profile
                            sync_user_profile(res.user)
                            st.rerun()
                        except Exception as e:
                            error_str = str(e).lower()
                            if "email not confirmed" in error_str:
                                st.error("⚠️ Please check your inbox and verify your email before logging in.")
                            elif "invalid login credentials" in error_str:
                                st.error("❌ Incorrect email or password. Please try again.")
                            else:
                                st.error(f"⚠️ Login failed: {e}")
                else:
                    st.warning("Please enter both email and password.")

            st.markdown("<div style='text-align:center; margin:1rem 0; color:var(--text-dim);'>OR</div>", unsafe_allow_html=True)
            
            # Social Login Buttons
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🌐 Continue with Google", use_container_width=True):
                with st.spinner("Connecting to Google..."):
                    try:
                        redirect_url = st.secrets.get("SITE_URL", "http://localhost:8501")
                        auth_res = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_url}})
                        if auth_res: 
                            st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_res.url}">', unsafe_allow_html=True)
                            components.html(f'<script>window.parent.location.href="{auth_res.url}";</script>', height=0)
                    except Exception as e:
                        st.error("⚠️ Google login unavailable. Please check configuration.")
            
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_signup:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("Join the Hub")
            new_email = st.text_input("Email Address", key="reg_email", placeholder="name@company.com")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass", placeholder="Min 6 characters", help="Password must be at least 6 characters long.")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_conf_pass")
            
            if st.button("Create Free Account ✨", key="s_btn", type="primary", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("❌ Passwords do not match.")
                elif len(new_pass) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    with st.spinner("Setting up your secure workspace..."):
                        try:
                            res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
                            if res.session:
                                st.session_state.user = res.user
                                from utils.db_manager import sync_user_profile
                                sync_user_profile(res.user)
                                st.rerun()
                            else:
                                st.success("✅ Account created successfully! Please check your inbox for a verification link.")
                        except Exception as e:
                            error_str = str(e).lower()
                            if "user already registered" in error_str:
                                st.warning("ℹ️ This email is already registered. Please switch to the Login tab.")
                            else:
                                st.error(f"⚠️ Signup failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

