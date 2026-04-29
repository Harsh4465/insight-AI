import streamlit as st
import pandas as pd
from utils.ai_agent import get_workspace_prime, get_dataset_summary, get_smart_suggestions, get_consultant_greeting
from utils.ui_components import safe_dataframe
from utils.db_manager import clear_user_charts

def phase2_connect():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    if 'ai_summary' not in st.session_state: st.session_state.ai_summary = None

    # --- 1. Connection Hub ---
    st.markdown('<div class="glass-card" style="margin-bottom: 2rem; border-left: 5px solid var(--primary);">', unsafe_allow_html=True)
    st.subheader("🔌 Data Connection Hub")
    st.write("Link your raw dataset to start the intelligent analytics sequence.")
    uploaded_file = st.file_uploader("Upload CSV, Excel, or Text", type=["csv", "xlsx", "xls", "xlsm", "xlsb", "txt"])
    
    if uploaded_file is not None:
        if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            st.session_state.last_uploaded = uploaded_file.name
            st.session_state.filename = uploaded_file.name
            st.session_state.df = None
            st.session_state.ai_summary = None
            
            # Clear Gallery on new upload
            user = st.session_state.get('user')
            if user:
                clear_user_charts(user.id)
                st.toast("♻️ Gallery reset for new dataset.")

        if st.session_state.df is None:
            try:
                with st.spinner("📥 Extracting data stream..."):
                    uploaded_file.seek(0)
                    fname = uploaded_file.name.lower()
                    
                    if fname.endswith(('.csv', '.txt')):
                        try:
                            df = pd.read_csv(uploaded_file)
                        except Exception:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
                    elif fname.endswith(('.xlsx', '.xlsm')):
                        df = pd.read_excel(uploaded_file, engine='openpyxl')
                    elif fname.endswith('.xls'):
                        df = pd.read_excel(uploaded_file, engine='xlrd')
                    elif fname.endswith('.xlsb'):
                        df = pd.read_excel(uploaded_file, engine='pyxlsb')
                    else:
                        st.error(f"Unsupported file format: {fname}")
                        return
                
                if not df.empty:
                    st.session_state.df = df
                    st.toast(f"✅ {uploaded_file.name} connected!")
                    
                    with st.spinner("🚀 Insight AI is analyzing the data..."):
                        # Single optimized call
                        prime = get_workspace_prime(df)
                        st.session_state.ai_summary = prime.get('summary', 'Dataset mapped.')
                        st.session_state.smart_suggestions = prime.get('suggestions', [])
                        st.session_state.messages = [{"role": "assistant", "content": prime.get('greeting', 'Ready.'), "id": "greeting_init"}]
                    
                    st.rerun()
                else:
                    st.error("⚠️ File appears to be empty.")
            except Exception as e:
                st.error(f"❌ Connection Failed: {str(e)}")
                st.info("Tip: Ensure your Excel file is not password protected and uses a standard .xlsx format.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.df is not None:
        df = st.session_state.df

        # --- 2. Health Overview ---
        st.markdown("<h3 style='margin-bottom: 1.5rem;'>🏥 Dataset Health Diagnostics</h3>", unsafe_allow_html=True)
        hc1, hc2, hc3, hc4 = st.columns(4)
        
        total_cells = df.size
        total_missing = df.isna().sum().sum()
        health_score = max(0, int((1 - (total_missing / total_cells)) * 100)) if total_cells > 0 else 0
        
        with hc1:
            st.markdown(f'<div class="diag-card"><div class="diag-stat-label">Total Rows</div><div class="diag-stat-value">{df.shape[0]:,}</div></div>', unsafe_allow_html=True)
        with hc2:
            st.markdown(f'<div class="diag-card"><div class="diag-stat-label">Columns</div><div class="diag-stat-value">{df.shape[1]}</div></div>', unsafe_allow_html=True)
        with hc3:
            st.markdown(f'<div class="diag-card"><div class="diag-stat-label">Null Cells</div><div class="diag-stat-value" style="color:var(--error);">{total_missing:,}</div></div>', unsafe_allow_html=True)
        with hc4:
            score_color = "var(--success)" if health_score > 80 else "var(--warning)" if health_score > 50 else "var(--error)"
            st.markdown(f'<div class="diag-card" style="border-color: {score_color}44;"><div class="diag-stat-label">Health Score</div><div class="diag-stat-value" style="color:{score_color};">{health_score}%</div></div>', unsafe_allow_html=True)

        # --- 3. AI Persona ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card" style="border-left: 5px solid var(--accent);">', unsafe_allow_html=True)
        st.subheader("🛰️ AI Dataset Persona")
        
        if st.session_state.ai_summary:
            st.write(st.session_state.ai_summary)
        else:
            if st.button("Generate Smart Insights ✨", type="primary", use_container_width=True):
                with st.spinner("Analyzing context..."):
                    st.session_state.ai_summary = get_dataset_summary(df)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 4. Data Preview ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 👁️ Live Data Stream")
        row_count = st.slider("Preview Depth", 5, 100, 10)
        
        with st.expander("Show Detailed Grid", expanded=True):
            try:
                preview_slice = df.head(row_count).copy()
                style_df = pd.DataFrame('', index=preview_slice.index, columns=preview_slice.columns)
                
                for col in preview_slice.columns:
                    is_null = preview_slice[col].isna()
                    style_df.loc[is_null, col] += 'background-color: rgba(245, 158, 11, 0.2); color: #f59e0b;'
                    
                    if pd.api.types.is_numeric_dtype(preview_slice[col]):
                        col_data = preview_slice[col].dropna()
                        if not col_data.empty:
                            q1, q3 = col_data.quantile([0.25, 0.75])
                            iqr = q3 - q1
                            is_outlier = (preview_slice[col] < (q1 - 1.5 * iqr)) | (preview_slice[col] > (q3 + 1.5 * iqr))
                            style_df.loc[is_outlier, col] += 'background-color: rgba(239, 68, 68, 0.2); color: #ef4444;'

                display_df = preview_slice.astype(str).replace(['nan', 'None', '<NA>', 'NaN', 'null'], '∅ Empty')
                safe_dataframe(display_df.style.apply(lambda _: style_df, axis=None))
            except Exception as e:
                st.error(f"Render Error: {e}")
                safe_dataframe(df.head(row_count))

        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        if st.button("Continue to Data Preparation ➔", use_container_width=True):
            st.session_state.current_page = "2 Prepare"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
