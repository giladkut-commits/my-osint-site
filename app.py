import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import streamlit as st
import json
import subprocess
import pandas as pd
from face_verifier import FaceVerifier

# כאן נייבא את המחלקות האחרות שלך כשנגיע לחיבור הסופי

st.set_page_config(page_title="OSINT Scanner Pro", layout="wide")

st.title("🛡️ מערכת OSINT וציון חשיפה")

# כפתור התחברות (כרגע נדמה את זה לצורך הממשק)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    if st.button("התחבר עם Google"):
        st.session_state.logged_in = True
        st.rerun()
else:
    st.success("מחובר למערכת!")

    # הגדרות חיפוש
    target_name = st.text_input("הזן שם לחיפוש:")
    other_lang = st.text_input("שם בשפה נוספת:")

    if st.button("הפעל סריקה"):
        with st.status("סורק את הרשת...", expanded=True) as status:
            st.write("🔍 מריץ Crawler...")
            # כאן נריץ את הקוד שלך בעתיד
            st.write("📧 בודק דליפות מייל...")
            st.write("🤖 מנתח תמונות ב-AI...")
            status.update(label="הסריקה הושלמה!", state="complete")

        # תצוגת ציור לדוגמה
        st.metric("ציון חשיפה", "4.5/10")
