import os
import streamlit as st
# Force reload for new env values
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv
import json

class FileStorage:
    def __init__(self, filename=".supabase_session.json"):
        self.filename = filename

    def get_item(self, key: str) -> str | None:
        try:
            with open(self.filename, "r") as f:
                return json.load(f).get(key)
        except Exception:
            return None

    def set_item(self, key: str, value: str) -> None:
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[key] = value
        with open(self.filename, "w") as f:
            json.dump(data, f)

    def remove_item(self, key: str) -> None:
        try:
            with open(self.filename, "r") as f:
                data = json.load(f)
            if key in data:
                del data[key]
                with open(self.filename, "w") as f:
                    json.dump(data, f)
        except Exception:
            pass

def get_supabase() -> Client:
    # Load dotenv every time to ensure fresh environment
    load_dotenv(override=True)
    
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        return None
        
    try:
        opts = ClientOptions(flow_type="implicit", storage=FileStorage())
        return create_client(url, key, options=opts)
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

import threading

def _sync_profile_task(user):
    try:
        client = get_supabase()
        if not client: return
        res = client.table("profiles").select("id").eq("id", user.id).execute()
        if not res.data:
            client.table("profiles").insert({"id": user.id, "email": user.email}).execute()
            print(f"Profile synced for {user.email}")
    except Exception as e:
        print(f"Error syncing profile: {e}")

def sync_user_profile(user):
    """Automatically sync authenticated user to public.profiles table in background"""
    if not user:
        return
    threading.Thread(target=_sync_profile_task, args=(user,), daemon=True).start()


# Singleton instance
supabase = get_supabase()

def save_chart_to_db(user_id, title, viz_type, intent, ai_memo=""):
    """Saves a pinned chart to Supabase"""
    if not supabase: return False
    try:
        data = {
            "user_id": user_id,
            "title": str(title),
            "viz_type": str(viz_type),
            "intent": intent,
            "ai_memo": str(ai_memo)
        }
        res = supabase.table("saved_charts").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Supabase Insert Error: {e}")
        return False

def load_charts_from_db(user_id):
    """Loads all pinned charts for a user"""
    if not supabase: return []
    try:
        res = supabase.table("saved_charts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"Supabase Load Error: {e}")
        return []

def delete_chart_from_db(chart_id):
    """Deletes a chart from Supabase"""
    if not supabase: return False
    try:
        supabase.table("saved_charts").delete().eq("id", chart_id).execute()
        return True
    except Exception as e:
        st.error(f"Supabase Delete Error: {e}")
        return False

def clear_user_charts(user_id):
    """Deletes all charts for a user"""
    if not supabase: return False
    try:
        supabase.table("saved_charts").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Supabase Clear Error: {e}")
        return False
