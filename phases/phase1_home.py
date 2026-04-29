import streamlit as st

def phase1_home():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Hero Section
    col1, col2, col3 = st.columns([0.5, 6, 0.5])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; margin-bottom: 3rem;">
            <p style="color: var(--accent); font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; font-size: 0.9rem;">
                Autonomous Data Intelligence Platform
            </p>
            <h1 class="hero-title">Welcome to <br/><span class="text-gradient">Insight AI.</span></h1>
            <p style="font-size: 1.3rem; color: var(--text-dim); margin: 0 auto 3rem auto; max-width: 700px; line-height: 1.6;">
                Unleash the full potential of your datasets with automated profiling, AI-powered cleaning, and conversational storytelling.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Phase Navigator
        st.markdown("<h3 style='text-align:center; margin-bottom:2rem;'>🗺️ The Insight AI Architecture</h3>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("""
            <div class="glass-card" style="min-height: 220px; margin-bottom: 2rem;">
                <div style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.8rem; color: var(--accent);">🔌 Phase 1: Connect</div>
                <p style="color: var(--text-dim); font-size: 1rem; line-height: 1.5;">
                    Seamlessly link your raw data. Our AI perform instant health diagnostics, identifying outliers and missing values in milliseconds.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="min-height: 220px;">
                <div style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.8rem; color: var(--secondary);">💬 Phase 3: Chat with Data</div>
                <p style="color: var(--text-dim); font-size: 1rem; line-height: 1.5;">
                    Don't just look at charts—talk to them. Ask complex questions and watch the AI generate interactive stories from your metrics.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
             st.markdown("""
            <div class="glass-card" style="min-height: 220px; margin-bottom: 2rem;">
                <div style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.8rem; color: var(--primary);">⚙️ Phase 2: Prepare</div>
                <p style="color: var(--text-dim); font-size: 1rem; line-height: 1.5;">
                    Automated data engineering at your fingertips. AI-driven imputation, scaling, and feature optimization with full transparency.
                </p>
            </div>
            """, unsafe_allow_html=True)
             
             st.markdown("""
            <div class="glass-card" style="min-height: 220px;">
                <div style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.8rem; color: var(--success);">🖼️ Phase 4: Dashboard</div>
                <p style="color: var(--text-dim); font-size: 1rem; line-height: 1.5;">
                    Your discoveries, preserved. Build permanent dashboards and export automated executive summaries for stakeholders.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Main CTA
        st.markdown("<div style='margin-top: 4rem;'>", unsafe_allow_html=True)
        if st.button("🚀 Enter the Workspace ➔", use_container_width=True, type="primary"):
            st.session_state.current_page = "1 Connect"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
