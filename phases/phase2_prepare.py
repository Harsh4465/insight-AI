import streamlit as st
import pandas as pd
import numpy as np
from utils.ai_agent import auto_clean
from utils.ui_components import safe_dataframe

def get_outlier_count(series):
    if not pd.api.types.is_numeric_dtype(series):
        return 0
    clean_series = series.dropna()
    if clean_series.empty:
        return 0
    Q1, Q3 = clean_series.quantile([0.25, 0.75])
    IQR = Q3 - Q1
    return ((clean_series < (Q1 - 1.5 * IQR)) | (clean_series > (Q3 + 1.5 * IQR))).sum()

def highlight_changes(data, original_data):
    attr = pd.DataFrame('', index=data.index, columns=data.columns)
    for col in data.columns:
        if col not in original_data.columns: continue
        orig_col = original_data.loc[data.index, col]
        clean_col = data[col]
        
        is_filled = orig_col.isna() & clean_col.notna()
        attr.loc[is_filled, col] = 'background-color: rgba(16, 185, 129, 0.2); color: #10b981; font-weight: bold; border: 1px solid #10b981;'
        
        is_diff = orig_col.notna() & clean_col.notna() & (orig_col.astype(str) != clean_col.astype(str))
        attr.loc[is_diff, col] = 'background-color: rgba(59, 130, 246, 0.2); color: #3b82f6; font-weight: bold; border: 1px solid #3b82f6;'
    return attr

def phase2_prepare():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    if st.session_state.df is None:
        st.warning("Please connect a data source in Phase 1.")
        return

    if 'clean_report' not in st.session_state: st.session_state.clean_report = None
    if 'df_pre_clean' not in st.session_state: st.session_state.df_pre_clean = None

    df = st.session_state.df

    # --- Header ---
    st.markdown("""
        <div class="glass-card" style="border-left: 5px solid var(--primary); margin-bottom: 2rem;">
            <h1 style="margin:0;">🛠️ Data <span class="text-gradient">Optimization Hub</span></h1>
            <p style="color: var(--text-dim); margin-top:0.5rem; font-size: 1.1rem;">AI-powered automated cleaning and feature engineering.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- Column Health Cards ---
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>🔍 Interactive Column Audit</h3>", unsafe_allow_html=True)
    
    # We display columns in a grid
    cols_per_row = 3
    all_cols = list(df.columns)
    
    for i in range(0, len(all_cols), cols_per_row):
        row_cols = all_cols[i:i + cols_per_row]
        st_cols = st.columns(cols_per_row)
        for idx, col_name in enumerate(row_cols):
            with st_cols[idx]:
                missing = df[col_name].isna().sum()
                outliers = get_outlier_count(df[col_name])
                dtype = str(df[col_name].dtype)
                
                st.markdown(f"""
                    <div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-weight: 800; color: var(--accent); margin-bottom: 0.5rem; font-size: 0.9rem;">{col_name}</div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                            <span style="color: var(--text-dim);">Nulls:</span>
                            <span style="color: {'var(--error)' if missing > 0 else 'var(--success)'}; font-weight: bold;">{missing}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                            <span style="color: var(--text-dim);">Outliers:</span>
                            <span style="color: {'var(--warning)' if outliers > 0 else 'var(--success)'}; font-weight: bold;">{outliers}</span>
                        </div>
                        <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 0.5rem; opacity: 0.6;">{dtype}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🗑️ Drop", key=f"drop_{col_name}", use_container_width=True, type="secondary"):
                    st.session_state.df = st.session_state.df.drop(columns=[col_name])
                    st.rerun()

    # --- Action Center ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card" style="background: rgba(99, 102, 241, 0.05); border-color: var(--primary-glow);">', unsafe_allow_html=True)
    st.subheader("✨ AI Data Master")
    st.write("Trigger the automated cleaning sequence to impute missing values and normalize metrics.")
    
    if st.button("🚀 Run AI Master Cleaner", type="primary", use_container_width=True):
        with st.spinner("Insight AI is cleaning and organizing the data..."):
            st.session_state.df_pre_clean = st.session_state.df.copy()
            cleaned_df, report = auto_clean(st.session_state.df)
            st.session_state.df = cleaned_df
            st.session_state.clean_report = report
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Results ---
    if st.session_state.clean_report:
        report = st.session_state.clean_report
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🧪 Optimization Ledger")
        
        with st.expander("🛡️ View AI Corrections", expanded=True):
            if report.get("missing_ledger"):
                st.markdown("#### 🩹 Imputation Events")
                for m in report["missing_ledger"]:
                    ml_col, mr_col = st.columns([5, 1])
                    with ml_col:
                        st.markdown(f"• **{m['col']}**: Filled with `{m['fill']}`")
                    with mr_col:
                        if st.button("✖", key=f"rev_imp_{m['col']}", help=f"Reject imputation for {m['col']}"):
                            if st.session_state.df_pre_clean is not None:
                                col_name = m['col']
                                st.session_state.df[col_name] = st.session_state.df_pre_clean[col_name]
                                report["missing_ledger"] = [item for item in report["missing_ledger"] if item["col"] != col_name]
                                st.rerun()
            
            if report.get("outlier_ledger"):
                st.markdown("#### 🛡️ Outlier Capping")
                for e in report["outlier_ledger"]:
                    l_col, r_col = st.columns([5, 1])
                    with l_col:
                        st.markdown(f"• **{e['col']}**: Capped `{e['count']}` values to `[{e['lower']}, {e['upper']}]`")
                    with r_col:
                        if st.button("✖", key=f"rev_out_{e['col']}", help=f"Reject changes for {e['col']}"):
                            if st.session_state.df_pre_clean is not None:
                                col_name = e['col']
                                # Restore only the relevant column from pre-clean state
                                st.session_state.df[col_name] = st.session_state.df_pre_clean[col_name]
                                # Remove from ledger so it doesn't show up again
                                report["outlier_ledger"] = [item for item in report["outlier_ledger"] if item["col"] != col_name]
                                st.rerun()

        # --- Preview ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 👁️ Post-Optimization Audit")
        row_count = st.slider("Audit Depth", 5, 100, 10)
        
        if st.session_state.df_pre_clean is not None:
            p_df = st.session_state.df.head(row_count).copy()
            safe_dataframe(p_df.style.apply(highlight_changes, original_data=st.session_state.df_pre_clean, axis=None))
        else:
            safe_dataframe(st.session_state.df.head(row_count))

    st.markdown("<div style='margin-top: 3rem;'>", unsafe_allow_html=True)
    if st.button("Proceed to Strategic Chat ➔", use_container_width=True):
        st.session_state.current_page = "3 Chat"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
