import os
import pandas as pd
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import streamlit as st
import re
import json

def get_llm(provider="groq", model_name="llama-3.3-70b-versatile"):
    load_dotenv(override=True) 
    key = os.getenv("GROQ_API_KEY")
    if not key: 
        return None
    models_to_try = [model_name, "mixtral-8x7b-32768", "llama3-70b-8192"]
    for model in models_to_try:
        try:
            return ChatGroq(api_key=key, model_name=model, temperature=0.1)
        except Exception:
            continue
    return None

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
    head = df.head(3).to_string()
    
    # Check for geographic potential
    has_geo = any(c.lower() in ['lat', 'lon', 'latitude', 'longitude', 'country', 'city', 'state'] for c in cols)

    prompt = f"""
    You are the 'Insight Oracle' - a Senior Strategic Data Analyst & Executive AI.
    
    USER QUERY: "{query}"
    DATA SCHEMA (Crucial for X/Y axes): {dtypes_str}
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
    4. DIVERSITY (CRITICAL RULE): 
       - NEVER repeat the exact same 'x' and 'y' column combination in the same response. Every chart in the 'visuals' array MUST explore different columns or use a completely different perspective.
       - DO NOT repeat any chart from HISTORY.
    
    SUPPORTED CHART TYPES: 
    'bar', 'line', 'pie', 'scatter', 'heatmap', 'sunburst', 'treemap', 'map', 'waterfall', 'funnel', 'box', 'violin', 'kpi'.
    
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
    1. "exec_summary": A high-level overview of what this data means globally, referencing the user's overarching goals (3-4 sentences).
    2. "slide_stories": For EACH insight title provided, write a 2-paragraph "story" that explains the 'why', connects it to the bigger picture, and aligns with the dataset's true domain. Use the EXACT insight title as the key.
    3. "strategic_recommendations": 3 clear, highly domain-specific action points based on the collective data.
    
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
