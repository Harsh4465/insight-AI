import streamlit as st
import pandas as pd
import re
from utils.ai_agent import get_intent_and_narrative, get_smart_suggestions, get_consultant_greeting
from utils.viz_engine import generate_visual, render_hybrid_viz
from utils.ui_components import scroll_to_bottom

def strip_symbols(text):
    return re.sub(r'\*\*', '', str(text))

def get_possible_visuals(df):
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    has_geo = any(c.lower() in ['lat', 'lon', 'latitude', 'longitude', 'country', 'city', 'state'] for c in df.columns)
    
    options = [
        {"icon": "🏙️", "label": "Strategic Overview", "prompt": "Perform a comprehensive strategic analysis of this dataset and show me the key trends and multi-visual insights."},
        {"icon": "🔍", "label": "Deep Dive", "prompt": "Identify anomalies, outliers, and perform a statistical deep-dive summary."},
    ]
    if has_geo:
        options.append({"icon": "🗺️", "label": "Geographic Map", "prompt": "Generate a geographic map visualization and analyze spatial patterns."})
    
    if len(num_cols) >= 2:
        options.append({"icon": "📉", "label": "Correlations", "prompt": "Show correlation between numeric variables and uncover hidden relationships using a heatmap."})
    
    return options

def phase3_chat():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    if st.session_state.df is None:
        st.warning("Please connect a data source in Phase 1.")
        return

    df = st.session_state.df
    filename = st.session_state.get('filename', 'Live Dataset')
    rows, cols = df.shape

    # --- 1. Header Hub ---
    st.markdown(f"""
        <div class="glass-card" style="padding: 10px 20px; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid var(--secondary);">
             <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.5rem;">🧠</span>
                <div>
                    <div style="font-weight: 800; color: var(--text-main); font-size: 1.1rem;">Strategic Command Center</div>
                    <div style="color: var(--text-dim); font-size: 0.8rem;">{filename} • {rows:,} rows • {len(df.columns)} features</div>
                </div>
             </div>
        </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []

    # --- 2. Initial Onboarding ---
    if not st.session_state.messages:
        st.markdown("""
            <div style='text-align:center; padding: 2rem 0;'>
                <h1 class="hero-title">Talk to your <span class="text-gradient">Data Oracle</span></h1>
                <p style='color:var(--text-dim); font-size: 1.2rem; max-width: 700px; margin: 0 auto;'>Ask complex questions, find hidden trends, or request a full strategic deep-dive with a single prompt.</p>
            </div>
        """, unsafe_allow_html=True)
        
        chips = get_possible_visuals(df)
        cols_ui = st.columns(len(chips))
        for idx, chip in enumerate(chips):
            with cols_ui[idx]:
                if st.button(f"{chip['icon']} {chip['label']}", key=f"tool_{idx}", use_container_width=True, type="secondary"):
                    st.session_state.messages.append({"role": "user", "content": chip['prompt']})
                    st.rerun()
    
    # --- 3. Chat History ---
    for idx, message in enumerate(st.session_state.messages):
        role_icon = "👤" if message["role"] == "user" else "🧑‍💼"
        with st.chat_message(message["role"], avatar=role_icon):
            content = strip_symbols(message["content"])
            
            if message["role"] == "assistant":
                st.markdown(f'<div style="font-size:1.1rem; line-height:1.6; color:var(--text-main);">{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:1.05rem; line-height:1.5;">{content}</div>', unsafe_allow_html=True)
            
            if "structured" in message:
                struct = message["structured"]
                
                # Render Visuals
                visuals_list = message.get("visuals_data", [])
                if visuals_list:
                    # Dynamically adjust columns based on number of visuals
                    num_viz = len(visuals_list)
                    if num_viz > 1:
                        viz_cols = st.columns(2)
                        for v_idx, v_item in enumerate(visuals_list):
                            with viz_cols[v_idx % 2]:
                                render_hybrid_viz(v_item["type"], v_item["obj"], title=v_item["title"], key=f"viz_{idx}_{v_idx}", intent=v_item.get("intent"))
                    else:
                        v_item = visuals_list[0]
                        render_hybrid_viz(v_item["type"], v_item["obj"], title=v_item["title"], key=f"viz_{idx}_0", intent=v_item.get("intent"))
                
                # Executive Summary & Action
                b_impact = struct.get("business_impact")
                r_action = struct.get("recommended_action")
                
                if b_impact or r_action:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background: rgba(34, 211, 238, 0.05); border: 1px solid rgba(34, 211, 238, 0.2); border-radius: 12px; padding: 1.5rem;">
                        <h4 style="margin-top:0; color:var(--primary); display:flex; align-items:center; gap:8px;">
                            <span style="font-size:1.2rem;">⚡</span> Executive Summary
                        </h4>
                        {f'<div style="margin-bottom: 1rem;"><b>Business Impact:</b><br><span style="color:var(--text-dim);">{strip_symbols(b_impact)}</span></div>' if b_impact else ''}
                        {f'<div><b>Recommended Action:</b><br><span style="color:var(--secondary); font-weight:600;">{strip_symbols(r_action)}</span></div>' if r_action else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Legacy Insights (if still returned)
                elif struct.get("insights"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    cols_in = st.columns(len(struct["insights"]))
                    for i_idx, insight in enumerate(struct["insights"]):
                        with cols_in[i_idx]:
                            st.markdown(f"""
                                <div class="glass-card" style="padding: 1rem; border-radius: 12px; height: 100%; border-top: 3px solid var(--primary);">
                                    <div style="font-size: 1.2rem; margin-bottom: 5px;">🎯</div>
                                    <div style="font-size: 0.85rem; color: var(--text-main); font-weight: 500;">{strip_symbols(insight)}</div>
                                </div>
                            """, unsafe_allow_html=True)

    # Automatically scroll to latest response if exists
    if st.session_state.messages:
        scroll_to_bottom()

    # --- 4. Processing ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_prompt = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Insight AI is analyzing your data..."):
                try:
                    # Construct rich history
                    history_items = []
                    prev_visuals = []
                    for m in st.session_state.messages[-6:]:
                        history_items.append(f"{m['role']}: {m['content'][:200]}")
                        if "structured" in m and m.get("structured", {}).get("visuals"):
                            for v in m["structured"]["visuals"]:
                                prev_visuals.append(f"{v['type']}({v.get('x')},{v.get('y')})")
                    
                    history_str = "\n".join(history_items)
                    if prev_visuals:
                        history_str += f"\nALREADY SHOWN VISUALS: {', '.join(list(set(prev_visuals)))}"

                    result = get_intent_and_narrative(last_prompt, df, history=history_str)
                    
                    if result:
                        visuals_data = []
                        display_type = result.get("display_type", "chart")
                        
                        if display_type == "table":
                            t_filter = result.get("table_filter")
                            if t_filter:
                                try:
                                    # Safe query execution
                                    tdf = st.session_state.df.query(t_filter).head(50)
                                    if not tdf.empty:
                                        render_hybrid_viz("table", tdf, title="Target Records", show_pin=True, key=f"tbl_{len(st.session_state.messages)}")
                                        visuals_data.append({"type": "table", "obj": tdf, "title": "Target Records"})
                                except Exception as qe:
                                    st.warning(f"Filter failed: {qe}. Showing overview instead.")
                                    render_hybrid_viz("table", st.session_state.df.head(10), title="Data Overview")
                            else:
                                render_hybrid_viz("table", st.session_state.df.head(10), title="Data Overview")

                        elif display_type == "chart" and result.get("visuals"):
                            for v_idx, v_intent in enumerate(result.get("visuals", [])):
                                v_type, v_obj = generate_visual(v_intent, st.session_state.df)
                                if v_obj is not None:
                                    render_hybrid_viz(v_type, v_obj, title=v_intent.get("title", "Insight"), show_pin=True, key=f"v_{len(st.session_state.messages)}_{v_idx}", intent=v_intent)
                                    visuals_data.append({
                                        "type": v_type, 
                                        "obj": v_obj,
                                        "title": v_intent.get("title", "Analysis"),
                                        "intent": v_intent
                                    })
                        
                        clean_answer = strip_symbols(result.get("answer", "Strategic analysis computed."))
                        st.markdown(f'<div style="font-size:1.05rem; line-height:1.5;">{clean_answer}</div>', unsafe_allow_html=True)
                        
                        # Store and Rerun to keep UI consistent
                        msg_entry = {
                            "role": "assistant", 
                            "content": clean_answer, 
                            "structured": result,
                            "visuals_data": visuals_data
                        }
                        st.session_state.messages.append(msg_entry)
                        st.rerun()
                except Exception as e:
                    st.error(f"Nexus Error: {e}")

    # --- 5. Suggestions (Quick Action Chips) ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_struct = st.session_state.messages[-1].get("structured", {})
        suggestions = last_struct.get("suggestions", [])
        if suggestions:
            st.markdown("<br>", unsafe_allow_html=True)
            # Create a scrolling container or wrapped columns for chips
            s_cols = st.columns(len(suggestions[:4])) # Max 4 chips
            for s_idx, suggestion in enumerate(suggestions[:4]):
                with s_cols[s_idx]:
                    if st.button(f"{suggestion}", key=f"sug_bottom_{len(st.session_state.messages)}_{s_idx}", use_container_width=True, type="secondary"):
                        st.session_state.messages.append({"role": "user", "content": suggestion})
                        st.rerun()

    # --- 6. Input ---
    st.markdown("<br>", unsafe_allow_html=True)
    prompt = st.chat_input("Ask for patterns, trends, or a full strategic deep-dive...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
