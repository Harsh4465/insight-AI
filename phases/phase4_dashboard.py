import streamlit as st
from utils.viz_engine import render_hybrid_viz, generate_visual
from utils.ai_agent import get_executive_summary
from utils.db_manager import load_charts_from_db, delete_chart_from_db, supabase
import json
from pptx import Presentation
from pptx.util import Inches
import io
import plotly.io as pio

from utils.ai_agent import get_executive_summary, get_ppt_storytelling
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def apply_dark_theme(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(15, 23, 42) # #0f172a

def apply_slide_branding(slide):
    apply_dark_theme(slide)
    """Adds a professional footer to the slide."""
    left = Inches(0.5)
    top = Inches(7.1)
    width = Inches(9)
    height = Inches(0.3)
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    p = tf.add_paragraph()
    p.text = "INSIGHT AI | STRATEGIC COMMAND CENTER • CONFIDENTIAL"
    p.font.size = Inches(0.12)
    p.font.color.rgb = RGBColor(148, 163, 184) # Slate 400

def generate_pptx_report(db_charts, df, chat_history_str=None):
    cols = df.columns.tolist() if df is not None else None
    story = get_ppt_storytelling(db_charts, chat_history_str, cols)
    prs = Presentation()
    
    # --- 1. Title Slide ---
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    apply_dark_theme(slide)
    
    title = slide.shapes.title
    title.text = "Strategic Intelligence Report"
    title.text_frame.paragraphs[0].font.color.rgb = RGBColor(99, 102, 241) # Indigo 500
    
    subtitle = slide.placeholders[1]
    subtitle.text = f"Cohesive Storytelling & Data Synthesis\nPowered by Insight AI Nexus"
    for p in subtitle.text_frame.paragraphs:
        p.font.color.rgb = RGBColor(226, 232, 240)

    # --- 2. Executive Summary ---
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    apply_slide_branding(slide)
    slide.shapes.title.text = "Executive Summary"
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    body = slide.placeholders[1]
    body.text = str(story.get("exec_summary", "Strategic data mapping completed."))
    for p in body.text_frame.paragraphs:
        p.font.color.rgb = RGBColor(226, 232, 240)

    # --- 3. Individual Insight Stories ---
    for item in db_charts:
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        apply_slide_branding(slide)
        title_shape = slide.shapes.title
        title_shape.text = item['title']
        title_shape.text_frame.paragraphs[0].font.size = Inches(0.35)
        title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

        intent = item.get('intent', {})
        if isinstance(intent, str):
            try: intent = json.loads(intent)
            except: intent = {}

        # Storytelling Box (Left Column)
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.2), Inches(5.0))
        tf = txBox.text_frame
        tf.word_wrap = True
        
        # Get specific story for this slide
        p = tf.add_paragraph()
        p.text = "THE STORY:"
        p.font.bold = True
        p.font.color.rgb = RGBColor(34, 211, 238) # Cyan 400
        
        # Defensive string extraction
        raw_story = story.get("slide_stories", {}).get(item['title'], item.get('ai_memo', 'Critical insight.'))
        if isinstance(raw_story, dict):
            raw_story = raw_story.get("answer", str(raw_story))
        
        p2 = tf.add_paragraph()
        p2.text = str(raw_story)
        p2.font.size = Inches(0.18)
        p2.font.color.rgb = RGBColor(226, 232, 240)

        # Chart Image (Right Column)
        if df is not None and intent:
            try:
                v_type, v_obj = generate_visual(intent, df)
                if v_type == "plotly":
                    img_bytes = pio.to_image(v_obj, format='png', width=800, height=600)
                    img_stream = io.BytesIO(img_bytes)
                    slide.shapes.add_picture(img_stream, Inches(4.8), Inches(1.8), width=Inches(4.7))
            except Exception as e:
                print(f"PPTX Image Error: {e}")

    # --- 4. Final Recommendations ---
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    apply_slide_branding(slide)
    slide.shapes.title.text = "Strategic Roadmap"
    slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    body = slide.placeholders[1]
    recs = story.get("strategic_recommendations", ["Monitor trends", "Scale operations"])
    body.text = "\n".join([f"• {r}" for r in recs])
    for p in body.text_frame.paragraphs:
        p.font.color.rgb = RGBColor(226, 232, 240)

    ppt_output = io.BytesIO()
    prs.save(ppt_output)
    ppt_output.seek(0)
    return ppt_output

def phase4_dashboard():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # --- Header ---
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("""
            <div class="glass-card" style="border-left: 5px solid var(--secondary); margin-bottom: 2rem;">
                <h1 style="margin:0;">📈 Insights <span class="text-gradient">Gallery</span></h1>
                <p style="color: var(--text-dim); margin-top:0.5rem; font-size: 1.1rem;">Your permanent collection of AI-driven discoveries, preserved in the cloud.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # --- 1. Global Actions ---
    user = st.session_state.get('user')
    if not user:
        st.warning("Please login to access your gallery.")
        return

    # Load from DB
    db_charts = load_charts_from_db(user.id)

    if not db_charts:
        st.info("Your gallery is empty. Pin insights from the Chat Hub to see them here.")
        return

    with col_h2:
        st.markdown("<br>", unsafe_allow_html=True)
        # Interactive HTML Report Generator
        html_content = f"""
        <html>
        <head>
            <title>Insight AI Strategic Report</title>
            <style>
                body {{ background: #020617; color: white; font-family: 'Inter', sans-serif; padding: 40px; line-height: 1.6; }}
                .card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 30px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                h1 {{ color: #6366f1; font-size: 2.5rem; margin-bottom: 10px; }}
                h2 {{ color: #22d3ee; margin-top: 0; }}
                .insight {{ border-left: 4px solid #a855f7; padding: 15px 20px; background: rgba(168, 85, 247, 0.05); border-radius: 0 10px 10px 0; margin-top: 20px; }}
                .chart {{ min-height: 450px; margin: 20px 0; background: rgba(0,0,0,0.2); border-radius: 10px; overflow: hidden; }}
                .header-section {{ margin-bottom: 50px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header-section">
                <h1>🔮 Insight AI Strategic Report</h1>
                <p style="color: #cbd5e1;">Intelligence extracted from: <strong>{st.session_state.get('filename', 'Live Dataset')}</strong></p>
            </div>
        """
        
        for i, item in enumerate(db_charts):
            intent = item.get('intent', {})
            if isinstance(intent, str):
                try: intent = json.loads(intent)
                except: intent = {}
            
            html_content += f'<div class="card"><h2>💡 {item["title"]}</h2>'
            
            if st.session_state.df is not None and intent:
                v_type, v_obj = generate_visual(intent, st.session_state.df)
                if v_type == "plotly":
                    # Use 'cdn' and ensure it's only loaded once by Plotly's internal logic or per chart
                    chart_html = v_obj.to_html(full_html=False, include_plotlyjs='cdn')
                    html_content += f'<div class="chart">{chart_html}</div>'
                else:
                    html_content += '<p style="color: #94a3b8; font-style: italic;">Non-Plotly visualization (Map/Table) not supported in static HTML.</p>'
            
            memo = item.get('ai_memo', 'Strategic analysis pending.')
            html_content += f'<div class="insight"><strong>AI Strategic Narrative:</strong><br>{memo}</div>'
            html_content += '</div>'
        
        html_content += """
            <div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 50px;">
                Generated by Insight AI • Senior Strategic Command Center
            </div>
        </body></html>"""
        
        st.download_button(
            label="🌐 Download HTML Report",
            data=html_content,
            file_name=f"Insight_AI_Report_{st.session_state.get('filename', 'export')}.html",
            mime="text/html",
            use_container_width=True
        )
        
        # PPTX Download
        if st.button("📊 Generate PPTX Deck", use_container_width=True, type="secondary"):
            with st.spinner("Creating professional slides..."):
                chat_history_str = ""
                if "messages" in st.session_state:
                    chat_history_str = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in st.session_state.messages[-10:]])
                ppt_data = generate_pptx_report(db_charts, st.session_state.df, chat_history_str)
                st.download_button(
                    label="📥 Click to Download PPTX",
                    data=ppt_data,
                    file_name=f"Strategic_Report_{st.session_state.get('filename', 'export')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )

    # --- Render Masonry-ish Layout ---
    for i, item in enumerate(db_charts):
        st.markdown(f'<div class="glass-card" style="margin-bottom: 2rem;">', unsafe_allow_html=True)
        
        header_col, action_col = st.columns([3, 1.5])
        with header_col:
            st.markdown(f"### 💡 {item['title']}")
        
        # Parse intent if it's a string
        intent = item.get('intent', {})
        if isinstance(intent, str):
            try: intent = json.loads(intent)
            except: intent = {}

        with action_col:
            ac1, ac2 = st.columns(2)
            with ac1:
                # Data Download
                if st.session_state.df is not None and intent:
                    try:
                        x, y = intent.get('x'), intent.get('y')
                        if x and y and x in st.session_state.df.columns and y in st.session_state.df.columns:
                            csv_data = st.session_state.df[[x, y]].head(100).to_csv(index=False)
                            st.download_button(
                                "📥 Data", 
                                data=csv_data, 
                                file_name=f"{item['title'].lower().replace(' ', '_')}.csv",
                                mime="text/csv",
                                key=f"dl_{i}",
                                use_container_width=True
                            )
                    except: pass
            with ac2:
                if st.button("🗑️ Clear", key=f"rm_{i}", help="Remove from Cloud", type="secondary", use_container_width=True):
                    if delete_chart_from_db(item['id']):
                        st.toast("Insight removed.")
                        st.rerun()

        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            if intent and st.session_state.df is not None:
                v_type, v_obj = generate_visual(intent, st.session_state.df)
                if v_obj:
                    render_hybrid_viz(v_type, v_obj, show_pin=False, key=f"dash_{i}")
                else:
                    st.warning("Could not reconstruct visualization.")
            else:
                st.info("⚠️ Re-upload dataset to view live chart.")
        
        with col_side:
            st.markdown("#### 🪄 AI Narrative")
            current_memo = item.get('ai_memo', '') or ""
            
            if current_memo:
                st.markdown(f"""
                    <div style="background: rgba(99, 102, 241, 0.05); padding: 1rem; border-radius: 10px; border-left: 3px solid var(--accent); margin-bottom: 1rem; font-size: 0.95rem;">
                        {current_memo}
                    </div>
                """, unsafe_allow_html=True)
            
            # Action Buttons
            if not current_memo:
                if st.button("Generate AI Takeaway ✨", key=f"ai_gen_{i}", type="primary", use_container_width=True):
                    with st.spinner("Insight AI is analyzing..."):
                        summary = get_executive_summary(item['title'], intent, st.session_state.df)
                        if summary:
                            try:
                                supabase.table("saved_charts").update({"ai_memo": summary}).eq("id", item['id']).execute()
                                st.toast("Summary Created!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"DB Error: {e}")
            else:
                with st.expander("Refine Summary"):
                    user_memo = st.text_area("Notes", value=current_memo, key=f"memo_input_{i}", height=120)
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("💾 Save", key=f"save_memo_{i}", use_container_width=True):
                            supabase.table("saved_charts").update({"ai_memo": user_memo}).eq("id", item['id']).execute()
                            st.toast("Saved!")
                            st.rerun()
                    with bc2:
                        if st.button("🔄 Re-Gen", key=f"regen_{i}", use_container_width=True):
                            with st.spinner("Insight AI is analyzing..."):
                                summary = get_executive_summary(item['title'], intent, st.session_state.df)
                                if summary:
                                    supabase.table("saved_charts").update({"ai_memo": summary}).eq("id", item['id']).execute()
                                    st.rerun()
                                else:
                                    st.error("Re-generation failed.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Footer Actions ---
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if st.button("🏠 Return to Home Hub", type="primary", use_container_width=True):
        st.session_state.current_page = "Home"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
