# 🚀 Insight AI - Autonomous Data Intelligence Platform

Insight AI is a cutting-edge, "Zero-Labor" Data Analyst web application. It transforms raw datasets into strategic, executive-level insights using advanced Artificial Intelligence. 

Instead of writing code or manually building charts, you simply connect your data and **talk** to the AI.

---

## 🌟 How to Use Insight AI

The platform is divided into four intelligent phases designed to mimic a professional data analyst's workflow.

### 🔌 Phase 1: Connect
- **What it does:** Upload your raw CSV or Excel datasets.
- **How to use:** Drag and drop your file. The system will instantly perform a health diagnostic, revealing the shape of your data, memory usage, and alerting you to any missing values or outliers.

### ⚙️ Phase 2: Prepare
- **What it does:** Automated Data Engineering.
- **How to use:** With a single click, ask the AI to "Auto-Clean" your data. It handles missing value imputation, text cleaning, and scaling. You can also manually drop columns or filter rows using the interactive sidebar. Download the cleaned dataset when finished.

### 💬 Phase 3: Chat with Data (The Core Hub)
- **What it does:** Conversational Analytics powered by Groq's high-speed LLMs.
- **How to use:** Type natural language questions (e.g., *"Show me the survival rate by passenger class"* or *"Give me a strategic overview of the sales data"*). 
- **Features:** 
  - The AI will automatically generate dynamic Plotly charts (Bar, Line, Waterfall, Funnel, KPI, etc.) and write an Executive Summary.
  - **Pin to Dashboard:** Click the 📌 icon on any chart you like to save it permanently to the cloud database.

### 🖼️ Phase 4: Dashboard
- **What it does:** Your permanent collection of insights and automated reporting.
- **How to use:** View all the charts you pinned in Phase 3. The AI generates cohesive, domain-aware storytelling connecting all your charts.
- **Exports:** 
  - Click **Download HTML Report** to get a fully interactive web report.
  - Click **Generate PPTX Deck** to download a dark-themed PowerPoint presentation with your charts and AI-generated speaker notes automatically embedded!

---

## 🛠️ Local Installation Guide

If you want to run Insight AI on your own computer, follow these steps:

### 1. Prerequisites
- Python 3.10 or higher.
- A free [Groq](https://console.groq.com/) API key (for the AI Brain).
- A free [Supabase](https://supabase.com/) project (for authentication and database).

### 2. Setup Instructions
```bash
# Clone or download this folder
cd "Insight Ai"

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# Activate it (Mac/Linux)
# source venv/bin/activate

# Install all required libraries
pip install -r requirements.txt
```

### 3. Environment Variables
Create a file named `.env` in the root folder and add your keys:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```

### 4. Run the App
```bash
streamlit run app.py
```
Your browser will open automatically at `http://localhost:8501`.

---

## 🔒 Security
- **OAuth Integration:** The app features a secure Google Login and email authentication system backed by Supabase.
- **Data Privacy:** Datasets are processed in-memory during your session and are not permanently stored on the server.
