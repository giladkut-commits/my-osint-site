import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleAuthManager:
    def __init__(self):
        # הגדרת ההרשאות - כולל גישה לפרופיל כדי למשוך את התמונה
        self.SCOPES = [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ]
        # מציאת קובץ הקרדנשלס בתיקייה הנוכחית
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = os.path.join(current_dir, 'credentials.json')

    def get_verified_user_info(self):
        """מבצע תהליך אימות מול גוגל ומחזיר את פרטי המשתמש"""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Missing file: {self.credentials_path}")

        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
        creds = flow.run_local_server(port=0)

        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()

        return {
            "full_name": user_info.get("name"),
            "email": user_info.get("email"),
            "first_name": user_info.get("given_name"),
            "profile_pic_url": user_info.get("picture")
        }