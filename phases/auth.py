import streamlit as st
from utils.db_manager import supabase
import time
import streamlit.components.v1 as components

def auth_page():
    if supabase is None:
        st.error("Database connection missing. Please configure Supabase environment variables.")
        st.stop()

    if "error" in st.query_params:
        err_msg = st.query_params.get("error_description", st.query_params["error"])
        st.error(f"Login Failed: {err_msg}")

    # --- COMPONENT BRIDGE FOR IMPLICIT FLOW ---
    import os
    
    # Load the custom component
    auth_bridge = components.declare_component("auth_bridge", path="auth_bridge")
    
    # Render component and get hash value
    hash_val = auth_bridge()
    
    if hash_val and isinstance(hash_val, str) and "access_token=" in hash_val:
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

    # --- PREMIUM SAAS AUTH UI ---
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Centered container for Auth
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem; margin-top: 5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔮</div>
                <h1 style="font-family: 'Outfit'; font-weight: 800; font-size: 2.5rem; margin-bottom: 0.5rem;">
                    Welcome to <span class="text-gradient">Insight AI</span>
                </h1>
                <p style="color: var(--text-dim); font-size: 1.1rem;">Secure access to your intelligent data workspace.</p>
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔐 Sign In", "✨ Create Account"])

        with tab_login:
            st.markdown('<div class="glass-card" style="padding: 2.5rem;">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom: 1.5rem;'>Sign In to Insight AI</h3>", unsafe_allow_html=True)
            email = st.text_input("Email Address", key="login_email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Access Workspace ➔", key="l_btn", type="primary", use_container_width=True):
                if email and password:
                    clean_email = email.strip()
                    with st.spinner("Authenticating..."):
                        try:
                            res = supabase.auth.sign_in_with_password({"email": clean_email, "password": password})
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

            st.markdown('</div>', unsafe_allow_html=True)

        with tab_signup:
            st.markdown('<div class="glass-card" style="padding: 2.5rem;">', unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom: 1.5rem;'>Start Your Free Trial</h3>", unsafe_allow_html=True)
            new_email = st.text_input("Work Email", key="reg_email", placeholder="name@company.com")
            new_pass = st.text_input("Create Password", type="password", key="reg_pass", placeholder="Min 6 characters", help="Password must be at least 6 characters long.")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_conf_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account ✨", key="s_btn", type="primary", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("❌ Passwords do not match.")
                elif len(new_pass) < 6:
                    st.error("❌ Password must be at least 6 characters.")
                else:
                    clean_new_email = new_email.strip()
                    with st.spinner("Provisioning your secure environment..."):
                        try:
                            res = supabase.auth.sign_up({"email": clean_new_email, "password": new_pass})
                            if res.session:
                                st.session_state.user = res.user
                                from utils.db_manager import sync_user_profile
                                sync_user_profile(res.user)
                                st.rerun()
                            else:
                                st.success("✅ Account created! Please check your inbox for the verification link.")
                        except Exception as e:
                            error_str = str(e).lower()
                            if "user already registered" in error_str:
                                st.warning("ℹ️ This email is already registered. Please switch to the Sign In tab.")
                            else:
                                st.error(f"⚠️ Signup failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
