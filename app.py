import os
# 1. פתרון לשגיאת ה-Import של TensorFlow בשרת - חייב להיות בשורה הראשונה
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import streamlit as st
import tensorflow as tf
import json
import subprocess
import pandas as pd
from google_auth_oauthlib.flow import Flow
from face_verifier import FaceVerifier # וודא שזה שם הקובץ שלך לזיהוי פנים

# 2. הגבלת משאבים לחיסכון בזיכרון (RAM) - קריטי למניעת "המסך הלבן"
tf.config.set_visible_devices([], 'GPU')

# הגדרות דף
st.set_page_config(page_title="Cyber OSINT Pro", layout="wide", page_icon="🛡️")

# פונקציה ליצירת ה-Flow של גוגל
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

# אם המשתמש לא מחובר ב-Session
if 'user' not in st.session_state:
    query_params = st.query_params
    
    # בדיקה אם חזרנו מגוגל עם קוד אימות
    if "code" in query_params:
        try:
            flow = create_flow()
            flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
            
            # החלפת הקוד בטוקן
            flow.fetch_token(code=query_params["code"])
            session = flow.authorized_session()
            user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
            
            # שמירת המשתמש ב-Session
            st.session_state.user = user_info
            
            # ניקוי כתובת ה-URL וריענון דף נקי
            st.query_params.clear() 
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאת התחברות: {e}")
            st.info("נסה להתחבר שוב.")
            if st.button("חזרה למסך כניסה"):
                st.query_params.clear()
                st.rerun()
            st.stop() # מונע מהקוד להמשיך להרצה בלי משתמש
    else:
        # הצגת מסך כניסה בלבד
        st.title("🛡️ כניסה למערכת OSINT")
        st.write("ברוך הבא למערכת הסריקה. אנא הזדהה כדי להמשיך.")
        
        flow = create_flow()
        flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
        # יצירת לינק להתחברות
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.link_button("התחבר באמצעות Google", auth_url)
        st.stop() # עוצר כאן! כל מה שמתחת לשורה זו ירוץ רק אם יש משתמש

# --- הממשק הראשי (רץ רק אם יש משתמש ב-session_state) ---
user = st.session_state.user

# תפריט צד
st.sidebar.image(user.get("picture"), width=80)
st.sidebar.write(f"שלום, **{user.get('name')}**")
if st.sidebar.button("התנתק"):
    del st.session_state.user
    st.rerun()

st.title("🔍 סורק חשיפה אישית וזיהוי פנים")
st.markdown("---")

# קלט מהמשתמש
col1, col2 = st.columns(2)
with col1:
    target_name = st.text_input("שם מלא לחיפוש:", value=user.get('name'))
    other_lang = st.text_input("שם בשפה נוספת (אופציונלי):")
with col2:
    st.info("הסורק יחפש אזכורים ותמונות ברשת וישווה אותם לתמונת הפרופיל שלך.")

# כפתור הפעלה
if st.button("🚀 הפעל סריקה גלובלית"):
    names = [target_name]
    if other_lang: names.append(other_lang)
    
    with st.status("מבצע סריקה וניתוח...", expanded=True) as status:
        # 1. הרצת הקראולר (וודא ש-crawler.py קיים בתיקייה)
        st.write("🌐 אוסף מידע ממנועי חיפוש...")
        cmd = f'python -c "from crawler import CrawlerManager; CrawlerManager.run_crawler({names}, \'results.json\')"'
        subprocess.run(cmd, shell=True)
        
        if os.path.exists("results.json"):
            with open("results.json", "r") as f:
                results = json.load(f)
            
            st.write(f"✅ נמצאו {len(results)} קישורים. מנתח תמונות ב-AI...")
            
            # 2. זיהוי פנים (Face Verification)
            verifier = FaceVerifier(user.get("picture"))
            matches = []
            
            progress_bar = st.progress(0)
            for i, item in enumerate(results):
                if item.get("img"):
                    try:
                        is_me, confidence = verifier.is_it_me(item["img"])
                        if is_me and confidence > 0.70:
                            item["confidence"] = confidence
                            matches.append(item)
                    except:
                        continue
                progress_bar.progress((i + 1) / len(results))
            
            status.update(label="הסריקה הושלמה!", state="complete")
            
            # הצגת תוצאות
            st.subheader("📊 ממצאים עיקריים")
            if matches:
                st.warning(f"נמצאו {len(matches)} תמונות עם התאמה גבוהה לפניך!")
                for m in matches:
                    with st.container():
                        c1, c2 = st.columns([1, 4])
                        c1.image(m["img"], use_container_width=True)
                        c2.markdown(f"**מקור:** [{m['title']}]({m['link']})")
                        c2.write(f"רמת ביטחון: {m['confidence']:.2%}")
                        st.divider()
            else:
                st.success("לא נמצאו התאמות פנים חריגות ברשת.")
                
            with st.expander("ראה את כל רשימת המקורות שנמצאו"):
                st.dataframe(pd.DataFrame(results)[["title", "link"]])
        else:
            st.error("שגיאה: הקראולר לא הצליח לייצר תוצאות. וודא ש-crawler.py מוגדר נכון.")
