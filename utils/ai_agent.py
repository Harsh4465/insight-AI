import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import streamlit as st
import re
import json

@st.cache_resource
def _get_cached_llm(provider: str):
    load_dotenv(override=True) 
    if "Gemini" in provider:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            try: key = st.secrets.get("GOOGLE_API_KEY")
            except: pass
        if not key: return None
        for model in ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]:
            try: return ChatGoogleGenerativeAI(google_api_key=key, model=model, temperature=0.1)
            except: continue
    else:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            try: key = st.secrets.get("GROQ_API_KEY")
            except: pass
        
        if not key: return None
        os.environ["GROQ_API_KEY"] = key
        for model in ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-70b-8192"]:
            try: return ChatGroq(model_name=model, temperature=0.1)
            except: continue
    return None

def get_llm():
    provider = st.session_state.get('ai_provider', 'Groq (Llama)')
    return _get_cached_llm(provider)

def get_consultant_greeting(df):
    llm = get_llm()
    if not llm: return "Hello! I'm your Senior AI Data Strategist. Ready to extract intelligence from your metrics."
    cols = df.columns.tolist()
    prompt = f"You are a World-Class Data Analyst. Dataset cols: {cols}. Give a 2-sentence sharp, professional greeting. Highlight one deep pattern you'll look for. No ** bold."
    try:
        response = llm.invoke(prompt)
        return re.sub(r'\*\*', '', response.content.strip())
    except:
        return "Insight AI: System Prime. I've mapped your data structure. Shall we begin the strategic deep-dive?"

def get_intent_and_narrative(query, df, history=None):
    llm = get_llm()
    if not llm: return None

    cols = df.columns.tolist()
    dtypes_str = ", ".join([f"'{c}': {str(t)}" for c, t in df.dtypes.items()])
    
    # NEW: Inform AI about missing data so it avoids empty columns
    missing_info = [f"'{c}' ({df[c].isna().sum()} missing)" for c in cols if df[c].isna().sum() > 0]
    missing_str = ", ".join(missing_info) if missing_info else "None"
    
    head = df.head(3).to_string()
    
    # Check for geographic potential
    has_geo = any(c.lower() in ['lat', 'lon', 'latitude', 'longitude', 'country', 'city', 'state'] for c in cols)

    prompt = f"""
    You are the 'Insight Oracle' - a Senior Strategic Data Analyst & Executive AI.
    
    USER QUERY: "{query}"
    DATA SCHEMA (Crucial for X/Y axes): {dtypes_str}
    MISSING DATA PROFILE: {missing_str}
    SAMPLE DATA: {head}
    HISTORY: {history if history else 'None'}

    CORE DIRECTIVES:
    1. PERSONA: Act as an elite Data Analyst. Explain *why* the data matters.
    2. MULTI-CHART INTELLIGENCE: 
       - If the user asks for a specific metric (e.g. "sales by region"), return 1 chart.
       - If the user asks for "insights", "overview", or general analysis, return 2 to 4 diverse charts that build a complete story (e.g., trend + distribution + KPI).
    3. AXIS INTELLIGENCE (CRITICAL):
       - 'x' should ALWAYS be a Dimension (categorical, datetime, or grouped numeric). Do NOT use High-Cardinality IDs (like 'PassengerId' or 'UUID') as 'x'.
       - 'y' MUST be a Metric (numeric types like float64/int64) if 'agg' is sum/mean. 
       - If 'y' is categorical/object, 'agg' MUST be "count".
       - DO NOT use columns with high missing data (refer to MISSING DATA PROFILE) as 'x' or 'y' unless explicitly requested.
    4. DIVERSITY (CRITICAL RULE): 
       - NEVER repeat the exact same 'x' and 'y' column combination in the same response. Every chart in the 'visuals' array MUST explore different columns or use a completely different perspective.
       - DO NOT repeat any chart from HISTORY.
    
    SUPPORTED CHART TYPES: 
    'bar', 'line', 'pie', 'scatter', 'heatmap', 'sunburst', 'treemap', 'map', 'waterfall', 'funnel', 'box', 'violin', 'kpi', 'radar', 'bubble'.
    
    OUTPUT JSON STRUCTURE:
    {{
      "answer": "Senior Strategic narrative (2-3 sentences max). Start by directly answering the user.",
      "display_type": "chart" | "table" | "text_only",
      "visuals": [
        {{ "type": "chart_type", "x": "col_name", "y": "col_name", "agg": "sum/count/mean", "title": "Insight Title" }}
      ],
      "table_filter": "Pandas query string if display_type is 'table' (e.g., \"Age > 30\"). Optional.",
      "business_impact": "1 concise sentence explaining the commercial or operational impact of these findings.",
      "recommended_action": "1 highly actionable next step the user should take based on this data.",
      "insights": ["Specific Trend 1", "Hidden Pattern 2"],
      "suggestions": ["Follow-up question 1?", "Follow-up question 2?"]
    }}
    
    Return ONLY pure JSON. No markdown bolding or extra text outside JSON.
    """

    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(re.sub(r'[\r\n\t]', ' ', match.group(0)))
        return {"answer": text, "visuals": [], "insights": [], "suggestions": []}
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
            return {"answer": "⚠️ **Google Gemini API Limit Reached!**\n\nYou've exceeded the free tier quota for Google Gemini. Please wait a minute and try again, or **switch to Groq (Llama)** using the model selector below the chat to continue your analysis immediately.", "visuals": [], "insights": [], "suggestions": []}
        return {"answer": f"Analysis interrupted: {e}", "visuals": [], "insights": [], "suggestions": []}

def auto_clean(df):
    report = {"duplicates": [], "types": [], "missing_ledger": [], "outlier_events": [], "outlier_ledger": []}
    # (Clean logic preserved)
    initial_rows = len(df)
    df = df.drop_duplicates()
    if len(df) < initial_rows: report["duplicates"].append(f"Removed {initial_rows - len(df)} duplicates.")
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                c = df[col].astype(str).str.replace(r'[$,%]', '', regex=True).str.strip()
                n = pd.to_numeric(c, errors='coerce')
                if n.notnull().mean() > 0.8: 
                    df[col] = n
                    report["types"].append(f"{col} ➔ Numeric")
            except: pass
        if df[col].isnull().sum() > 0:
            fill = df[col].median() if pd.api.types.is_numeric_dtype(df[col]) else (df[col].mode()[0] if not df[col].mode().empty else "N/A")
            report["missing_ledger"].append({"col": col, "fill": fill, "count": int(df[col].isnull().sum())})
            df[col] = df[col].fillna(fill)
        if pd.api.types.is_numeric_dtype(df[col]):
            Q1, Q3 = df[col].quantile([0.25, 0.75])
            IQR = Q3 - Q1
            l, u = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
            mask = (df[col] < l) | (df[col] > u)
            if mask.any():
                report["outlier_ledger"].append({"col": col, "count": int(mask.sum()), "lower": round(l,2), "upper": round(u,2)})
                df[col] = df[col].clip(l, u)
    return df, report

def get_cleaning_narrative(report):
    llm = get_llm()
    if not llm: return "Automated data cleaning and imputation sequence completed."
    prompt = f"""
    You are an AI Data Engineer. You just ran an automated data cleaning script.
    Here is the ledger of changes made: {json.dumps(report)}
    
    TASK: Write a brief, professional 2-sentence summary explaining to the user what you just did to prepare their dataset.
    Make it sound smart but accessible. Do not list every single column, just summarize the major actions (e.g., "I imputed missing values and capped anomalies to stabilize your metrics"). No ** bolding.
    """
    try:
        response = llm.invoke(prompt)
        return re.sub(r'\*\*', '', response.content.strip())
    except:
        return "Automated data cleaning and imputation sequence completed."

def get_executive_summary(title, intent, df):
    llm = get_llm()
    if not llm or not intent: return "Strategic insight pending."
    
    # Extract variables for better context
    x_var = intent.get('x', 'dimension')
    y_var = intent.get('y', 'metric')
    sample_cols = df.columns.tolist()
    
    prompt = f"""
    You are an Expert Data Analyst. 
    Analysis Title: "{title}"
    Variables: {x_var} vs {y_var}
    Dataset Columns: {sample_cols}
    
    TASK: Write a sharp, 1-sentence analytical takeaway from this visualization. 
    CRITICAL: Adapt your tone to the actual dataset domain (e.g., if it's the Titanic dataset, talk about survival patterns, NOT business growth or customer outcomes). Do not use corporate buzzwords unless the data is clearly corporate/sales data. Explain what the relationship between {x_var} and {y_var} actually signifies in reality.
    No ** bolding.
    """
    try:
        response = llm.invoke(prompt)
        return re.sub(r'\*\*', '', response.content.strip())
    except Exception as e:
        print(f"Summary Error: {e}")
        return "Key performance indicator identified for growth monitoring."

def get_smart_suggestions(df):
    llm = get_llm()
    if not llm: return ["Strategic Overview", "Trend Analysis"]
    prompt = f"Suggest 6 deep analytical questions for a dataset with columns {df.columns.tolist()}. No ** bold."
    try:
        return [re.sub(r'^\d+\.\s*', '', s).strip() for s in llm.invoke(prompt).content.strip().split("\n")][:6]
    except:
        return ["Analyze anomalies", "Predict growth"]

def get_dataset_summary(df):
    llm = get_llm()
    if not llm: return "Dataset structure mapped."
    prompt = f"Identify the domain and 3 high-level strategic opportunities in this data: {df.columns.tolist()}. No ** bold."
    try:
        return re.sub(r'\*\*', '', llm.invoke(prompt).content.strip())
    except:
        return "Strategic mapping complete."

def get_workspace_prime(df):
    """Combines greeting, summary, and suggestions into ONE LLM call for speed."""
    llm = get_llm()
    if not llm: return {"greeting": "Welcome.", "summary": "Data loaded.", "suggestions": ["Analyze"]}
    
    cols = df.columns.tolist()
    prompt = f"""
    You are a Senior Data Architect. Dataset Columns: {cols}
    
    TASK: Provide the following in JSON format:
    1. "greeting": A sharp, professional 1-sentence welcome.
    2. "summary": Identify the domain and 3 high-level strategic opportunities (max 2 sentences).
    3. "suggestions": 5 deep analytical questions for this data.
    
    Return ONLY JSON. No ** bolding.
    """
    try:
        response = llm.invoke(prompt)
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    return {"greeting": "Ready for analysis.", "summary": "Dataset mapped.", "suggestions": ["Trend Analysis", "Anomalies"]}

def generate_template_charts(template_name, df):
    llm = get_llm()
    if not llm: return []
    
    cols = df.columns.tolist()
    dtypes_str = ", ".join([f"'{c}': {str(t)}" for c, t in df.dtypes.items()])
    
    # Give explicit flavor to each template so they never overlap
    template_rules = {
        "Executive Overview": "Focus on high-level sums, counts, and simple visuals. Use 'bar', 'pie', and 'funnel'. Keep it high-level.",
        "Performance & Deep Dive": "Focus on correlations, distributions, and complex metrics. Use 'scatter', 'box', 'heatmap', 'radar'. Explore relationships.",
        "Demographics & Trends": "Focus on segments, time-series (if available), or geospatial. Use 'line', 'sunburst', 'treemap', 'bubble'. Explore groupings."
    }
    
    specific_rule = template_rules.get(template_name, "Create diverse charts.")
    
    prompt = f"""
    You are an AI Dashboard Architect. 
    The user wants to generate a "{template_name}" dashboard template.
    
    DATA SCHEMA: {dtypes_str}
    
    TEMPLATE RULE: {specific_rule}
    
    TASK: Generate an array of exactly 6 strategic visual intents that fit this template perfectly.
    - Exactly 2 must be 'kpi' type (high-level metrics).
    - 4 should be diverse charts (MUST strictly follow the TEMPLATE RULE above).
    - Ensure 'x' and 'y' column names EXACTLY match the schema provided.
    - NEVER repeat the same combination of x and y in this array.
    - Do NOT use columns with high missing data.
    
    JSON FORMAT MUST BE EXACTLY:
    {{
       "visuals": [
           {{"type": "kpi", "x": null, "y": "col_name", "agg": "sum", "title": "Total Sales KPI"}},
           {{"type": "bar", "x": "col1", "y": "col2", "agg": "mean", "title": "Average by Category"}}
       ]
    }}
    
    Return ONLY JSON. No ** bolding.
    """
    try:
        response = llm.invoke(prompt)
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("visuals", [])
    except Exception as e:
        print(f"Template Gen Error: {e}")
    return []

def get_ppt_storytelling(db_charts, chat_history=None, cols=None):
    """Generates a cohesive storytelling narrative for a PPTX deck based on all pinned insights, user intent, and data domain."""
    llm = get_llm()
    if not llm or not db_charts:
        return {
            "exec_summary": "Analysis of key metrics and strategic trends.",
            "slide_stories": {c['title']: c.get('ai_memo', 'Strategic insight.') for c in db_charts},
            "strategic_recommendations": ["Continue monitoring key metrics for growth."]
        }
    
    context = "\n".join([f"Insight: {c['title']}\nMemo: {c.get('ai_memo', '')}" for c in db_charts])
    chat_context = f"RECENT USER CHATS:\n{chat_history}" if chat_history else "No chat history available."
    domain_context = f"DATASET COLUMNS:\n{cols}" if cols else "Unknown domain."
    
    prompt = f"""
    You are an Expert Strategic Communicator creating a presentation for an executive board.
    I have several data insights. You must weave them into a cohesive, high-impact storytelling narrative.
    
    CRITICAL INSTRUCTION: Analyze the DATASET COLUMNS and RECENT USER CHATS. You must adapt your entire tone and vocabulary to match the actual domain of the dataset (e.g., medical, maritime/Titanic, sales, scientific) and directly address the goals the user was trying to achieve in their chats. Do NOT use generic corporate buzzwords if the data is not corporate.
    
    {domain_context}
    
    {chat_context}
    
    PINNED INSIGHTS TO INCLUDE IN PPT:
    {context}
    
    TASK: Provide a JSON with:
    1. "exec_summary": A high-level overview of what this data means globally (2-3 sentences).
    2. "slide_stories": For EACH insight title provided, write a 3-part strategic "story".
       - Part 1: What exactly this metric/chart represents.
       - Part 2: The deeper strategic reason behind tracking this pattern or metric.
       - Part 3: What this means for business/domain decision-making.
       CRITICAL: Keep each part to exactly 1 concise sentence to ensure the JSON parses correctly. If exact data values are missing, explain why the metric itself is strategically vital. Use the EXACT insight title as the JSON key.
    3. "strategic_recommendations": 3 clear, highly domain-specific action points.
    
    Return ONLY JSON. No ** bold.
    """
    try:
        response = llm.invoke(prompt)
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    return {
        "exec_summary": "Data analysis complete. Please review individual slides for specific findings.",
        "slide_stories": {c['title']: c.get('ai_memo', 'Key performance indicator analysis.') for c in db_charts},
        "strategic_recommendations": ["Optimize current workflows", "Monitor identified trends", "Scale successful patterns"]
    }
