from auth_manager import GoogleAuthManager
from social_crawler import CrawlerManager, DuckDuckGoSpider
from security_checker import SecurityAuditor
from face_verifier import FaceVerifier
import os


def calculate_exposure_score(email_breaches, face_matches, text_matches):
    score = 0.0
    score += email_breaches * 1.5
    score += face_matches * 2.5
    score += text_matches * 0.5
    return min(round(score, 1), 10.0)


def main():
    print("========================================")
    print("   🛡️ OSINT & Security Scanner Pro 🛡️   ")
    print("========================================")
    print("Please log in with Google to verify your identity...")

    try:
        auth = GoogleAuthManager()
        user_data = auth.get_verified_user_info()

        full_name = user_data["full_name"]
        email = user_data["email"]
        username = email.split("@")[0]
        google_pic = user_data["profile_pic_url"]

        print(f"\n✅ Identity Verified: {full_name} ({email})")

        print("\nתמונת הפרופיל שגוגל מספקת קטנה מאוד. מומלץ להשתמש בתמונה מהמחשב.")
        custom_pic = input(
            "הכנס שם של תמונה ברורה שלך מהמחשב (למשל 'me.jpg'), או לחץ Enter להשתמש בזו של גוגל: ").strip()

        if custom_pic and os.path.exists(custom_pic):
            reference_image = custom_pic
            print(f"✅ משתמש בתמונה איכותית מהמחשב: {custom_pic}")
        else:
            reference_image = google_pic
            print("⚠️ משתמש בתמונת גוגל כברירת מחדל.")

        names_to_search = [full_name, username, input("name in other language: ")]
        print(f"\n🔍 Searching public web for: {names_to_search}...")

        DuckDuckGoSpider.found_profiles = []
        CrawlerManager.run_crawler(names_to_search, max_pages=2)

        print("\n🔍 Checking for Email Breaches...")
        auditor = SecurityAuditor()
        email_breaches_count = auditor.check_email_leak(email)

        total_profiles = len(DuckDuckGoSpider.found_profiles)
        print(f"\n🤖 מצאנו {total_profiles} רשומות בסך הכל. מפעיל למידת מכונה (זיהוי פנים)...")

        verifier = FaceVerifier(reference_image)

        links_with_faces = set()
        links_with_text = set()
        processed_images = set()

        # --- התיקון: אוספים רק את הקישורים האמיתיים ומסננים את בינג ---
        for profile in DuckDuckGoSpider.found_profiles:
            link = profile["link"]
            if "bing.com/images/search" not in link:
                links_with_text.add(link)

        profiles_with_images = [p for p in DuckDuckGoSpider.found_profiles if p["img"]]

        CONFIDENCE_THRESHOLD = 0.75

        for i, profile in enumerate(profiles_with_images, 1):
            link = profile["link"]
            img_url = profile["img"]
            title = profile["title"][:40] + "..." if len(profile["title"]) > 40 else profile["title"]

            if img_url not in processed_images:
                processed_images.add(img_url)

                print(f"  [{i}/{len(profiles_with_images)}] בודק תמונה מהאתר: {title}")

                try:
                    is_me, score = verifier.is_it_me(img_url)

                    if is_me and score >= CONFIDENCE_THRESHOLD:
                        links_with_faces.add(link)
                        print(f"   ⭐⭐⭐ התאמת פנים ודאית נמצאה! (ביטחון: {score:.2%})")
                    elif is_me:
                        print(f"   ⚠️ סונן: נמצא דמיון, אבל הביטחון נמוך מ-75% ({score:.2%})")

                except Exception:
                    pass

        # מורידים מהטקסט את הקישורים שעליהם כבר קיבלנו נקודות של זיהוי פנים
        links_with_text = links_with_text - links_with_faces

        face_matches_count = len(links_with_faces)
        text_matches_count = len(links_with_text)

        if face_matches_count == 0:
            print("\n   ✅ ה-AI לא זיהה התאמת פנים ודאית באף אחת מהתוצאות.")

        final_score = calculate_exposure_score(email_breaches_count, face_matches_count, text_matches_count)

        print("\n========================================")
        print("📊 סיכום דוח חשיפה אישי (Exposure Score)")
        print("========================================")
        print(f"מיילים שדלפו: {email_breaches_count}")
        print(f"קישורים עם התאמות פנים ודאיות (AI): {face_matches_count}")
        print(f"קישורים עם אזכורי טקסט: {text_matches_count}")
        print("-" * 40)

        if final_score < 3:
            print(f"🟢 ציון חשיפה: {final_score}/10 (בטוח, חשיפה מינימלית)")
        elif final_score < 7:
            print(f"🟡 ציון חשיפה: {final_score}/10 (בינוני, מומלץ לבדוק את הלינקים)")
        else:
            print(f"🔴 ציון חשיפה: {final_score}/10 (קריטי! חשיפה גבוהה ברשת)")
        print("========================================\n")

        if links_with_faces:
            print("📸 פירוט קישורים עם זיהוי פנים ודאי:")
            for i, link in enumerate(links_with_faces, 1):
                print(f"  [{i}] {link}")
            print()

        if links_with_text:
            print("📝 פירוט קישורים עם אזכור טקסטואלי/פרופיל (ללא זיהוי פנים):")
            for i, link in enumerate(links_with_text, 1):
                print(f"  [{i}] {link}")
            print()

        if not links_with_faces and not links_with_text:
            print("✨ לא נמצאו קישורים חשופים ברשת.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()