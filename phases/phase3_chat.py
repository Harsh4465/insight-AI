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

    # Check if user has sent any messages
    user_has_messaged = any(m["role"] == "user" for m in st.session_state.messages)
    
    # --- 2. Initial Onboarding ---
    if not user_has_messaged:
        st.markdown("""
            <div style='text-align:center; padding: 2rem 0;'>
                <h1 style="font-size: 3rem; margin-bottom: 0;">✨</h1>
                <h2 style='color:var(--text-main); margin-bottom: 0.5rem;'>Interactive Dashboards — Just Ask!</h2>
                <p style='color:var(--text-dim); font-size: 1.1rem; max-width: 700px; margin: 0 auto 2rem auto;'>Select any chart type below that your dataset supports.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Custom CSS for compact pills
        st.markdown("""
        <style>
            div[data-testid="column"] button {
                border-radius: 20px;
                padding: 0.2rem 0.5rem;
                font-size: 0.85rem;
                height: auto;
                min-height: 0;
            }
        </style>
        """, unsafe_allow_html=True)

        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        has_geo = any(c.lower() in ['lat', 'lon', 'latitude', 'longitude', 'country', 'city', 'state'] for c in df.columns)

        options = [
            {"icon": "📊", "label": "Full Dashboard", "prompt": "Generate a full dashboard with 4 diverse charts (like bar, line, pie, KPI) showing the most important insights."},
            {"icon": "🔍", "label": "Summarize", "prompt": "Provide a comprehensive summary of the dataset including key KPIs and a high-level overview chart."},
            {"icon": "🧹", "label": "Clean data", "prompt": "Explain what cleaning operations could be performed on this data, like handling missing values and outliers."},
        ]

        if len(num_cols) >= 1 and len(cat_cols) >= 1:
            options.append({"icon": "🥧", "label": "Pie + Bar", "prompt": "Create a pie chart showing category distribution and a bar chart comparing top values."})
            options.append({"icon": "🎯", "label": "Radar", "prompt": "Create a radar chart to compare multi-dimensional variables across categories."})
            options.append({"icon": "📊", "label": "Funnel", "prompt": "Create a funnel chart showing conversion rates or stage progression."})
            options.append({"icon": "🌊", "label": "Waterfall", "prompt": "Generate a waterfall chart showing cumulative positive and negative contributions."})
            
        if len(num_cols) >= 2:
            options.append({"icon": "📉", "label": "Scatter", "prompt": "Create a scatter plot comparing two numeric columns to uncover relationships or clusters."})
            options.append({"icon": "🔥", "label": "Heatmap", "prompt": "Generate a correlation heatmap of the numeric columns to find hidden patterns."})
            options.append({"icon": "🫧", "label": "Bubble", "prompt": "Create a bubble chart using 3 numeric dimensions (X, Y, and Size)."})
            
        if len(num_cols) >= 1:
            options.append({"icon": "📦", "label": "Box Plot", "prompt": "Create a box plot to show the distribution and outliers of a key numeric variable."})
            
        if len(date_cols) >= 1 or len(cat_cols) >= 1:
            options.append({"icon": "📈", "label": "Trends", "prompt": "Analyze the trends over time or categories. Generate line and bar charts to show these trends."})
            
        if has_geo:
            options.append({"icon": "🗺️", "label": "Map", "prompt": "Generate a geographic map visualization and analyze spatial patterns."})

        # Centered layout using empty side columns
        col_spacer1, col_main, col_spacer2 = st.columns([1, 8, 1])
        
        with col_main:
            # We can have up to 13 options. Let's chunk them into rows of 6.
            chunk_size = 6
            for i in range(0, len(options), chunk_size):
                chunk = options[i:i+chunk_size]
                cols = st.columns(chunk_size)
                for idx, opt in enumerate(chunk):
                    with cols[idx]:
                        if st.button(f"{opt['icon']} {opt['label']}", key=f"chip_{i}_{idx}", use_container_width=True):
                            st.session_state.messages.append({"role": "user", "content": opt['prompt']})
                            st.rerun()
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
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
                
                # Render Visuals Vertically
                visuals_list = message.get("visuals_data", [])
                if visuals_list:
                    for v_idx, v_item in enumerate(visuals_list):
                        render_hybrid_viz(v_item["type"], v_item["obj"], title=v_item["title"], key=f"viz_{idx}_{v_idx}", intent=v_item.get("intent"))
                
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
            # Create a scrolling container or wrapped columns for chips
            s_cols = st.columns(len(suggestions[:4])) # Max 4 chips
            for s_idx, suggestion in enumerate(suggestions[:4]):
                with s_cols[s_idx]:
                    if st.button(f"{suggestion}", key=f"sug_bottom_{len(st.session_state.messages)}_{s_idx}", use_container_width=True, type="secondary"):
                        st.session_state.messages.append({"role": "user", "content": suggestion})
                        st.rerun()

    # --- 6. Input ---
    prompt = st.chat_input("Ask for patterns, trends, or a full strategic deep-dive...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
