import streamlit as st

def phase1_home():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # --- HERO SECTION ---
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-top: 4rem; margin-bottom: 3rem; width: 100%;">
        <div style="margin-bottom: 1.5rem;">
            <span class="feature-badge">✨ AI Analytics</span>
            <span class="feature-badge">📊 Dashboard Builder</span>
            <span class="feature-badge">💬 Chat With Data</span>
            <span class="feature-badge">🔮 Predictive Analytics</span>
            <span class="feature-badge">📈 Auto Visualizations</span>
        </div>
        <h1 class="hero-title" style="text-align: center; width: 100%;">Insight AI<br/><span class="text-gradient">AI Powered Data Intelligence Platform</span></h1>
        <p class="hero-subtitle" style="text-align: center; max-width: 800px; margin: 0 auto 3rem auto;">
            Transform raw datasets into intelligent insights using AI-powered analytics, interactive dashboards, and smart visualizations. Your complete end-to-end data pipeline.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main CTAs
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("🚀 Get Started for Free", use_container_width=True, type="primary"):
            st.session_state.current_page = "1 Connect"
            st.rerun()

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # --- WORKFLOW SECTION ---
    st.markdown("<h2 style='text-align:center; margin-bottom:2rem;'>The Insight Workflow</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="glass-card" style="min-height: 250px;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">1️⃣</div>
            <h3 style="color: var(--accent); margin-bottom: 0.5rem;">Upload & Prepare</h3>
            <p style="color: var(--text-dim); line-height: 1.5; font-size: 0.95rem;">
                Drag and drop your datasets (CSV, Excel). Our engine automatically detects schemas, handles missing values, and suggests optimal preprocessing steps.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card" style="min-height: 250px;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">2️⃣</div>
            <h3 style="color: var(--primary); margin-bottom: 0.5rem;">Chat & Discover</h3>
            <p style="color: var(--text-dim); line-height: 1.5; font-size: 0.95rem;">
                Ask questions in plain English. The AI analytics engine powered by LangChain and Gemini translates your queries into deep statistical insights instantly.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="glass-card" style="min-height: 250px;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">3️⃣</div>
            <h3 style="color: var(--secondary); margin-bottom: 0.5rem;">Visualize & Export</h3>
            <p style="color: var(--text-dim); line-height: 1.5; font-size: 0.95rem;">
                Auto-generate the best charts for your data. Pin them to your customizable dashboard and export comprehensive reports with one click.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- DEMO PREVIEW SECTION ---
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <h2 style="margin-bottom: 1rem;">Experience the Future of Analytics</h2>
        <div class="glass-card" style="padding: 3rem; margin-top: 2rem; border-color: rgba(45, 212, 191, 0.3);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔮</div>
            <h3 style="margin-bottom: 1rem;">AI-Powered Dashboard Preview</h3>
            <p style="color: var(--text-dim); max-width: 600px; margin: 0 auto;">
                Connect a dataset to unlock the full potential of your own personalized Insight AI workspace.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
