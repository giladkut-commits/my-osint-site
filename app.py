import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import streamlit as st
import json
import subprocess
import pandas as pd
from google_auth_oauthlib.flow import Flow
from face_verifier import FaceVerifier # הקובץ שלך

# --- הגדרות בסיסיות ---
st.set_page_config(page_title="Cyber OSINT Pro", layout="wide")

# פונקציה ליצירת ה-Flow של גוגל מתוך ה-Secrets
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

# --- ניהול אימות (Authentication) ---
if 'user' not in st.session_state:
    # בדיקה אם חזרנו מגוגל עם "קוד אימות" בכתובת האתר
    query_params = st.query_params
    if "code" in query_params:
        flow = create_flow()
        flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()
        st.session_state.user = user_info
        st.rerun()
    else:
        # דף כניסה
        st.title("🛡️ כניסה למערכת OSINT & Security")
        st.write("אנא התחבר עם חשבון Google כדי לאמת את זהותך ולהתחיל בסריקה.")
        flow = create_flow()
        flow.redirect_uri = st.secrets["google_auth"]["redirect_uri"]
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.link_button("התחבר באמצעות Google", auth_url)
        st.stop()

# --- הממשק הראשי (מוצג רק אחרי התחברות) ---
user = st.session_state.user
st.sidebar.image(user.get("picture"), width=100)
st.sidebar.write(f"שלום, {user.get('name')}")
if st.sidebar.button("התנתק"):
    del st.session_state.user
    st.rerun()

st.title("🔍 סורק חשיפה אישית וזיהוי פנים")

# קלט מהמשתמש
col1, col2 = st.columns(2)
with col1:
    target_name = st.text_input("שם מלא לחיפוש:", value=user.get('name'))
    other_lang = st.text_input("שם בשפה נוספת (אופציונלי):")
with col2:
    st.info("תמונת הפרופיל שלך מגוגל תשמש כבסיס להשוואת הפנים (Face Recognition).")

# הפעלת הסריקה
if st.button("🚀 הפעל סריקה גלובלית"):
    names = [target_name]
    if other_lang: names.append(other_lang)
    
    with st.status("מבצע סריקה אינטנסיבית...", expanded=True) as status:
        # 1. הרצת ה-Crawler כ-Subprocess
        st.write("🌐 אוסף מידע ממנועי חיפוש (DuckDuckGo & Bing)...")
        names_arg = ",".join(names)
        cmd = f'python -c "from social_crawler import CrawlerManager; CrawlerManager.run_crawler({names}, \'results.json\')"'
        subprocess.run(cmd, shell=True)
        
        # 2. טעינת התוצאות
        if os.path.exists("results.json"):
            with open("results.json", "r") as f:
                results = json.load(f)
            
            st.write(f"✅ נמצאו {len(results)} קישורים ותמונות. מנתח ב-AI...")
            
            # 3. זיהוי פנים בעזרת המחלקה שלך
            verifier = FaceVerifier(user.get("picture"))
            matches = []
            
            for item in results:
                if item.get("img"):
                    is_me, confidence = verifier.is_it_me(item["img"])
                    if is_me and confidence > 0.70:
                        item["is_match"] = True
                        item["confidence"] = confidence
                        matches.append(item)
            
            # הצגת תוצאות
            status.update(label="הסריקה הושלמה!", state="complete")
            
            st.subheader("📊 ממצאים עיקריים")
            if matches:
                st.warning(f"נמצאו {len(matches)} התאמות פנים ודאיות!")
                for m in matches:
                    c1, c2 = st.columns([1, 3])
                    c1.image(m["img"], width=150)
                    c2.markdown(f"**מקור:** [{m['title']}]({m['link']})")
                    c2.write(f"רמת ביטחון: {m['confidence']:.2%}")
            else:
                st.success("לא נמצאו התאמות פנים ודאיות ברשת.")
                
            with st.expander("ראה את כל הקישורים שנמצאו (טקסט)"):
                st.table(pd.DataFrame(results)[["title", "link"]])
        else:
            st.error("הסריקה נכשלה. נסה שוב בעוד כמה דקות.")
