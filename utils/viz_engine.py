import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import numpy as np
import streamlit as st
from streamlit_folium import st_folium
from utils.db_manager import save_chart_to_db
from sklearn.linear_model import LinearRegression
from utils.ui_components import safe_dataframe
import datetime

def fuzzy_get_col(col_name, df):
    if not col_name: return None
    if col_name in df.columns: return col_name
    normalized_target = str(col_name).lower().replace(" ", "").replace("_", "")
    for col in df.columns:
        normalized_col = str(col).lower().replace(" ", "").replace("_", "")
        if normalized_col == normalized_target:
            return col
    return None

def ensure_numeric_safe(series):
    return pd.to_numeric(series, errors='coerce')

def generate_visual(intent, df_input):
    if df_input is None or df_input.empty: return (None, None)
    df = df_input.copy()
    
    # --- 1. Smart Defaults & Extraction ---
    v_type = intent.get("type", "bar").lower()
    raw_x = intent.get("x")
    raw_y = intent.get("y")
    agg = intent.get("agg", "sum")
    title = intent.get("title", "Data Insight")

    # Fuzzy find columns
    x = fuzzy_get_col(raw_x, df)
    y = fuzzy_get_col(raw_y, df)
    color = fuzzy_get_col(intent.get("color"), df)

    # --- 2. Auto-Repair Logic ---
    if y:
        df[y] = pd.to_numeric(df[y], errors='coerce')
        if df[y].isna().all():
            agg = "count"
    else:
        agg = "count"

    if not x:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        x = cat_cols[0] if cat_cols else df.columns[0]

    # --- 3. Processing ---
    try:
        pdf = df.dropna(subset=[x])
        if y and agg != "count":
            pdf = pdf.dropna(subset=[y])

        if pdf.empty:
            # If no data after dropna, return as table to be safe
            return ("table", df.head(10))

        # --- 4. Chart Generation ---
        fig = None
        
        if v_type == "forecast":
            pdf_f = pdf.groupby(x)[y].agg(agg).reset_index()
            try:
                pdf_f[x] = pd.to_datetime(pdf_f[x])
                pdf_f = pdf_f.sort_values(x)
                pdf_f['x_num'] = pdf_f[x].map(datetime.datetime.toordinal)
                X = pdf_f[['x_num']].values
                Y = pdf_f[y].values
                model = LinearRegression().fit(X, Y)
                last_date = pdf_f[x].max()
                future_dates = [last_date + datetime.timedelta(days=i*30) for i in range(1, 4)]
                future_x_num = [[d.toordinal()] for d in future_dates]
                predictions = model.predict(future_x_num)
                plot_df = pd.concat([pdf_f[[x, y]].assign(Type='Historical'), pd.DataFrame({x: future_dates, y: predictions, 'Type': 'Forecast'})])
                fig = px.line(plot_df, x=x, y=y, color='Type', title=f"🔮 Predictive Forecast: {title}", markers=True, template="plotly_dark")
            except: v_type = "line"

        if v_type == "bar":
            if color and color != x:
                data = pdf.groupby([x, color]).size().reset_index(name='count') if agg == "count" else pdf.groupby([x, color])[y].agg(agg).reset_index()
                fig = px.bar(data, x=x, y=data.columns[2], color=color, title=title, template="plotly_dark", barmode='group')
            else:
                data = pdf.groupby(x).size().reset_index(name='count') if agg == "count" else pdf.groupby(x)[y].agg(agg).reset_index()
                data = data.sort_values(by=data.columns[1], ascending=False).head(15)
                # Fix: Do not force color=x to prevent legend spam and invisible datetime bars
                fig = px.bar(data, x=x, y=data.columns[1], title=title, template="plotly_dark", color_discrete_sequence=["#6366f1"])

        elif v_type == "line":
            if color and color != x:
                data = pdf.groupby([x, color]).size().reset_index(name='count') if agg == "count" else pdf.groupby([x, color])[y].agg(agg).reset_index()
                try: data = data.sort_values(by=x)
                except: pass
                fig = px.line(data, x=x, y=data.columns[2], color=color, title=title, markers=True, template="plotly_dark")
            else:
                data = pdf.groupby(x).size().reset_index(name='count') if agg == "count" else pdf.groupby(x)[y].agg(agg).reset_index()
                try: data = data.sort_values(by=x)
                except: pass
                fig = px.line(data, x=x, y=data.columns[1], title=title, markers=True, template="plotly_dark", color_discrete_sequence=["#22d3ee"])

        elif v_type == "pie":
            data = pdf[x].value_counts().head(8).reset_index()
            fig = px.pie(data, names=x, values='count', title=title, hole=0.4, template="plotly_dark")

        elif v_type == "scatter":
            if not y:
                num_cols = df.select_dtypes(include=['number']).columns.tolist()
                y = num_cols[1] if len(num_cols) > 1 else num_cols[0] if num_cols else x
            fig = px.scatter(pdf.head(1000), x=x, y=y, color=color if color else None, title=title, template="plotly_dark")

        elif v_type in ["sunburst", "treemap"]:
            path = [color, x] if color and color != x else [x]
            fig = px.sunburst(pdf.head(500), path=path, values=y if agg != "count" else None, title=title, template="plotly_dark") if v_type == "sunburst" else \
                  px.treemap(pdf.head(500), path=path, values=y if agg != "count" else None, title=title, template="plotly_dark")

        elif v_type == "heatmap":
            num_df = df.select_dtypes(include=[np.number])
            if not num_df.empty:
                fig = px.imshow(num_df.corr(), text_auto=".2f", title=title, template="plotly_dark", color_continuous_scale="Viridis")

        elif v_type == "waterfall":
            data = pdf.groupby(x)[y].agg(agg).reset_index()
            data['measure'] = 'relative'
            fig = go.Figure(go.Waterfall(
                x=data[x], y=data[y], measure=data['measure'],
                textposition="outside", text=[f"{v:,.0f}" for v in data[y]]
            ))
            fig.update_layout(title=title, template="plotly_dark")

        elif v_type == "funnel":
            data = pdf.groupby(x).size().reset_index(name='count') if agg == "count" else pdf.groupby(x)[y].agg(agg).reset_index()
            data = data.sort_values(by=data.columns[1], ascending=False)
            fig = px.funnel(data, x=data.columns[1], y=x, title=title, template="plotly_dark")

        elif v_type == "box":
            fig = px.box(pdf, x=x, y=y, color=color if color else x, title=title, template="plotly_dark")

        elif v_type == "violin":
            fig = px.violin(pdf, x=x, y=y, color=color if color else x, box=True, title=title, template="plotly_dark")

        elif v_type == "kpi":
            val = pdf[y].agg(agg) if y else len(pdf)
            return ("kpi", {"value": val, "label": title})

        elif v_type == "map":
            lat_col = fuzzy_get_col("latitude", df) or fuzzy_get_col("lat", df)
            lon_col = fuzzy_get_col("longitude", df) or fuzzy_get_col("lon", df)
            if lat_col and lon_col:
                pdf_map = df.dropna(subset=[lat_col, lon_col]).head(300)
                m = folium.Map(location=[pdf_map[lat_col].mean(), pdf_map[lon_col].mean()], zoom_start=4, tiles="CartoDB dark_matter")
                for _, row in pdf_map.iterrows():
                    folium.CircleMarker([row[lat_col], row[lon_col]], radius=5, color="#22d3ee", fill=True).add_to(m)
                return ("folium", m)
            
        # --- 5. Final Safety Check & Data Validation ---
        if fig and hasattr(fig, 'data') and len(fig.data) > 0:
            # Check if all data in traces is null or empty
            has_actual_data = False
            for trace in fig.data:
                if hasattr(trace, 'y') and trace.y is not None and len(trace.y) > 0: has_actual_data = True
                elif hasattr(trace, 'values') and trace.values is not None and len(trace.values) > 0: has_actual_data = True
            
            if has_actual_data:
                return ("plotly", fig)
        
        # If Plotly has no data, return a styled table instead of a black box
        return ("table", pdf.head(20))

    except Exception as e:
        print(f"Bulletproof Viz Error: {e}")
        return ("table", df_input.head(10))

def render_hybrid_viz(viz_type, viz_obj, title="Insight", key=None, show_pin=True, intent=None):
    if viz_obj is None: return
    
    if viz_type == "plotly": 
        st.plotly_chart(viz_obj, use_container_width=True, key=key)
    elif viz_type == "folium": 
        st_folium(viz_obj, width=None, height=400, key=f"folium_{key}" if key else None)
    elif viz_type == "table":
        st.markdown(f"##### 📊 Data Table: {title}")
        safe_dataframe(viz_obj, key=f"table_{key}" if key else None)
    elif viz_type == "kpi":
        val = viz_obj.get("value", 0)
        formatted_val = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
        st.markdown(f"""
        <div class="glass-card" style="padding: 1.5rem; text-align: center; border-left: 4px solid var(--primary);">
            <div style="font-size: 0.9rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px;">{title}</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: var(--text-main); margin-top: 5px;">{formatted_val}</div>
        </div>
        """, unsafe_allow_html=True)
        
    if show_pin and viz_type != "kpi":
        if st.button(f"📌 Save to Gallery", key=f"pin_{key}" if key else None):
            user = st.session_state.get('user')
            if user:
                with st.spinner("Syncing to cloud..."):
                    success = save_chart_to_db(user.id, title, viz_type, intent)
                    if success: st.toast("✅ Insight pinned to dashboard!")
                    else: st.error("Save failed.")
            else:
                st.warning("Please login to pin insights.")
