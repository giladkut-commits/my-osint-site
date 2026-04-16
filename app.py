import os
# 1. מניעת שגיאות ייבוא של TensorFlow - חייב להיות בראש הקובץ
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import streamlit as st
import tensorflow as tf
import json
import subprocess
import pandas as pd
from google_auth_oauthlib.flow import Flow
from face_verifier import FaceVerifier # וודא שזה שם הקובץ שלך

# 2. חיסכון בזיכרון (RAM) למניעת קריסת השרת (המסך הלבן)
tf.config.set_visible_devices([], 'GPU')

st.set_page_config(page_title="Cyber OSINT Pro", layout="wide", page_icon="🛡️")

# פונקציה ליצירת ה-Flow של גוגל
def create_flow():
    # הגדרת ה-Scopes בצורה המדויקת ביותר שגוגל דורשת
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["google_auth"]["client_id"],
                "client_secret": st.secrets["google_auth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=scopes
    )
    flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
    return flow

# --- לוגיקת אימות (Authentication) ---

if 'user' not in st.session_state:
    # בדיקת פרמטרים ב-URL (כשחוזרים מגוגל)
    params = st.query_params
    
    if "code" in params:
        try:
            # שחזור ה-Flow
            flow = create_flow()
            
            # פתרון ל-Missing code verifier: שחזור מה-Session
            if 'code_verifier' in st.session_state:
                flow.code_verifier = st.session_state['code_verifier']
            
            # המרת הקוד לטוקן
            flow.fetch_token(code=params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
            
            # שמירה ב-Session וניקוי זמניים
            st.session_state.user = user_info
            st.query_params.clear()
            if 'code_verifier' in st.session_state:
                del st.session_state['code_verifier']
            
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאת אימות: {e}")
            if st.button("נסה להתחבר שוב"):
                st.query_params.clear()
                st.rerun()
            st.stop()
    else:
        # מסך כניסה
        st.title("🛡️ מערכת OSINT")
        st.write("אנא התחבר עם חשבון Google כדי להמשיך.")
        
        flow = create_flow()
        # יצירת לינק ושמירת ה-verifier בזיכרון ה-Session
        auth_url, _ = flow.authorization_url(prompt='select_account')
        st.session_state['code_verifier'] = flow.code_verifier
        
        st.link_button("התחבר באמצעות Google", auth_url)
        st.stop() # עוצר כאן כדי שלא ירוץ קוד בלי משתמש

# --- הממשק הראשי (מוצג רק למחוברים) ---

user = st.session_state.user

# תפריט צדדי
st.sidebar.image(user.get("picture"), width=80)
st.sidebar.write(f"שלום, **{user.get('name')}**")
if st.sidebar.button("התנתק"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.title("🔍 סורק חשיפה אישית וזיהוי פנים")
st.markdown("---")

# קלט מהמשתמש
target_name = st.text_input("שם מלא לחיפוש:", value=user.get('name'))

if st.button("🚀 הפעל סריקה"):
    with st.status("מבצע סריקה...", expanded=True) as status:
        st.write("🌐 אוסף מידע ממנועי חיפוש...")
        
        # הרצת הקראולר (וודא ש-crawler.py נמצא בתיקייה)
        cmd = f'python -c "from crawler import CrawlerManager; CrawlerManager.run_crawler([\'{target_name}\'], \'results.json\')"'
        subprocess.run(cmd, shell=True)
        
        if os.path.exists("results.json"):
            with open("results.json", "r") as f:
                results = json.load(f)
            
            st.write(f"✅ נמצאו {len(results)} תוצאות. מנתח התאמת פנים...")
            
            # זיהוי פנים
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
            st.error("הסריקה נכשלה. בדוק את הטרמינל לפרטים.")
