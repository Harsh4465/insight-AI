# 🚀 Deploying Insight AI (Streamlit Cloud)

The fastest, easiest, and **100% free** way to deploy this application is via **Streamlit Community Cloud**.

### Step 1: Upload to GitHub
1. Create a free account on [GitHub](https://github.com/).
2. Create a new repository (e.g., `insight-ai`).
3. Upload all the files from this folder into that GitHub repository.

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New App"**.
3. Select your GitHub repository (`insight-ai`) and the `main` branch.
4. Set the "Main file path" to **`app.py`**.

### Step 3: Add Secure API Keys
Before clicking Deploy, you must add your private keys so the AI works online:
1. Click on **Advanced Settings** at the bottom of the deployment page.
2. In the "Secrets" box, paste the variables from your local `.env` file exactly like this:
```toml
SUPABASE_URL = "your_supabase_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
GROQ_API_KEY = "your_groq_api_key"
```
3. Click **Save** and then **Deploy**!

Within a few minutes, your app will be live and you will get a public URL (e.g., `https://insight-ai.streamlit.app`) to share with the world!
