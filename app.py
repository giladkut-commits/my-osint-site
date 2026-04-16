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

# הגבלת משאבים לחיסכון בזיכרון
tf.config.set_visible_devices([], 'GPU')

st.set_page_config(page_title="Cyber OSINT Pro", layout="wide", page_icon="🛡️")

def create_flow():
    # יצירת ה-Flow מתוך ה-Secrets
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
    params = st.query_params
    
    if "code" in params:
        try:
            # 2. התיקון הקריטי: יצירת פלואו ושחזור ה-verifier מהזיכרון
            flow = create_flow()
            flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
            
            # אם המפתח הסודי (Verifier) נמצא בזיכרון - נשלוף אותו
            if 'code_verifier' in st.session_state:
                flow.code_verifier = st.session_state['code_verifier']
            
            # החלפת הקוד בטוקן מול גוגל
            flow.fetch_token(code=params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
            
            # שמירת המשתמש והסרת המפתח הזמני
            st.session_state.user = user_info
            if 'code_verifier' in st.session_state:
                del st.session_state['code_verifier']
            
            # ניקוי הכתובת וריענון דף נקי
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאת התחברות: {e}")
            st.info("החיבור פג תוקף. נסה להתחבר שוב.")
            if st.button("חזרה למסך כניסה"):
                st.query_params.clear()
                st.rerun()
            st.stop()
    else:
        # דף כניסה
        st.title("🛡️ מערכת OSINT וזיהוי פנים")
        st.write("אנא התחבר עם חשבון Google כדי להתחיל.")
        
        flow = create_flow()
        flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
        
        # 3. יצירת הלינק ושמירת ה-verifier בזיכרון לפני המעבר לגוגל
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        st.session_state['code_verifier'] = flow.code_verifier
        
        st.link_button("התחבר באמצעות Google", auth_url)
        st.stop()

# --- הממשק הראשי (רץ רק אם המשתמש מחובר) ---
user = st.session_state.user
st.sidebar.image(user.get("picture"), width=80)
st.sidebar.write(f"שלום, **{user.get('name')}**")

if st.sidebar.button("התנתק"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.title("🔍 סריקה ואיתור חשיפה")
st.markdown("---")

# קלט מהמשתמש
target_name = st.text_input("שם מלא לחיפוש:", value=user.get('name'))

if st.button("🚀 הפעל סריקה"):
    with st.status("מבצע סריקה...", expanded=True) as status:
        st.write("🌐 מחפש מידע ברשת...")
        
        # הרצת הקראולר (וודא שזה השם של הקובץ שלך!)
        cmd = f'python -c "from crawler import CrawlerManager; CrawlerManager.run_crawler([\'{target_name}\'], \'results.json\')"'
        subprocess.run(cmd, shell=True)
        
        if os.path.exists("results.json"):
            with open("results.json", "r") as f:
                results = json.load(f)
            
            st.write(f"✅ נמצאו {len(results)} תוצאות. מנתח התאמה...")
            
            verifier = FaceVerifier(user.get("picture"))
            matches = []
            
            for item in results:
                if item.get("img"):
                    try:
                        is_me, conf = verifier.is_it_me(item["img"])
                        if is_me and conf > 0.7:
                            item["confidence"] = conf
                            matches.append(item)
                    except:
                        continue
            
            status.update(label="הסריקה הושלמה!", state="complete")
            
            if matches:
                st.warning(f"נמצאו {len(matches)} התאמות פנים!")
                for m in matches:
                    c1, c2 = st.columns([1, 4])
                    c1.image(m["img"], width=150)
                    c2.markdown(f"**מקור:** [{m['title']}]({m['link']})")
                    c2.write(f"ביטחון: {m['confidence']:.2%}")
            else:
                st.success("לא נמצאו התאמות פנים.")
        else:
            st.error("הסריקה נכשלה. וודא שקובץ crawler.py תקין.")
