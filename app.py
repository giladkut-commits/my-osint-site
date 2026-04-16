import os
# 1. פתרון לשגיאת ה-Import
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import streamlit as st
import tensorflow as tf
import json
import subprocess
import pandas as pd
from google_auth_oauthlib.flow import Flow
from face_verifier import FaceVerifier

# הגבלת משאבים
tf.config.set_visible_devices([], 'GPU')

st.set_page_config(page_title="Cyber OSINT Pro", layout="wide", page_icon="🛡️")

def create_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["google_auth"]["client_id"],
                "client_secret": st.secrets["google_auth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["google_auth"]["redirect_uri"]]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid']
    )

# --- לוגיקת אימות (Authentication) ---

if 'user' not in st.session_state:
    query_params = st.query_params
    
    if "code" in query_params:
        try:
            flow = create_flow()
            flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
            
            # --- התיקון הקריטי: שחזור ה-verifier מה-session_state ---
            if 'code_verifier' in st.session_state:
                flow.code_verifier = st.session_state['code_verifier']
            
            flow.fetch_token(code=query_params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
            
            st.session_state.user = user_info
            
            # ניקוי
            st.query_params.clear() 
            if 'code_verifier' in st.session_state:
                del st.session_state['code_verifier']
                
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאת התחברות: {e}")
            if st.button("נסה להתחבר שוב מההתחלה"):
                st.query_params.clear()
                st.rerun()
            st.stop()
    else:
        st.title("🛡️ כניסה למערכת OSINT")
        flow = create_flow()
        flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
        
        # יצירת הלינק ושמירת ה-verifier ב-session_state לפני שהמשתמש עוזב את האתר
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.session_state['code_verifier'] = flow.code_verifier
        
        st.link_button("התחבר באמצעות Google", auth_url)
        st.stop()

# --- הממשק הראשי ---
# בזכות ה-st.stop מקודם, הקוד יגיע לכאן רק אם באמת יש user
user = st.session_state.user

st.sidebar.image(user.get("picture"), width=80)
st.sidebar.write(f"שלום, **{user.get('name')}**")
if st.sidebar.button("התנתק"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.title("🔍 סורק חשיפה אישית וזיהוי פנים")
st.markdown("---")

# שאר הקוד (חיפוש, קראולר וזיהוי פנים) נשאר אותו דבר כמו ששלחתי לך קודם...
# (השארתי את זה קצר כדי שתתמקד בתיקון ה-Login)
target_name = st.text_input("שם מלא לחיפוש:", value=user.get('name'))
if st.button("🚀 הפעל סריקה"):
    st.write("מריץ סריקה...")
    # כאן יבוא המשך הקוד של הקראולר שנתתי לך
