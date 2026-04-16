import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import streamlit as st
import tensorflow as tf
import json
import subprocess
from google_auth_oauthlib.flow import Flow
from face_verifier import FaceVerifier

tf.config.set_visible_devices([], 'GPU')

st.set_page_config(page_title="Cyber OSINT Pro", layout="wide")

# פונקציה ליצירת ה-Flow
def create_flow():
    # שים לב: הורדתי את ה-code_challenge_method כדי למנוע את שגיאת ה-Verifier
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["google_auth"]["client_id"],
                "client_secret": st.secrets["google_auth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid']
    )
    flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
    return flow

# --- לוגיקת אימות ---

if 'user' not in st.session_state:
    params = st.query_params
    
    if "code" in params:
        try:
            flow = create_flow()
            # אנחנו משתמשים בשיטה ישירה שלא דורשת verifier
            flow.fetch_token(code=params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
            
            st.session_state.user = user_info
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאת התחברות: {e}")
            if st.button("נסה שוב"):
                st.query_params.clear()
                st.rerun()
            st.stop()
    else:
        st.title("🛡️ כניסה למערכת OSINT")
        flow = create_flow()
        
        # יצירת לינק בשיטה הישנה והיציבה (בלי PKCE)
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.markdown(f"""
            <a href="{auth_url}" target="_self" style="
                text-decoration: none;
                color: white;
                background-color: #4285F4;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                display: inline-block;
            ">התחבר באמצעות Google</a>
        """, unsafe_allow_html=True)
        st.stop()

# --- ממשק ראשי ---
user = st.session_state.user
st.sidebar.image(user.get("picture"), width=80)
st.sidebar.write(f"שלום, **{user.get('name')}**")

st.title("🔍 מערכת סריקה OSINT")
target_name = st.text_input("שם לחיפוש:", value=user.get('name'))

if st.button("🚀 הפעל סריקה"):
    st.write("מבצע חיפוש...")
    # כאן יבוא הקוד של הקראולר שלך
