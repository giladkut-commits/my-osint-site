import requests
import os
from deepface import DeepFace


class FaceVerifier:
    def __init__(self, reference_img_url):
        self.reference_path = "my_identity.jpg"
        if reference_img_url:
            try:
                # הורדת תמונת הפרופיל מגוגל
                res = requests.get(reference_img_url)
                with open(self.reference_path, "wb") as f:
                    f.write(res.content)
            except Exception:
                pass

    def is_it_me(self, target_img_url):
        """משווה תמונה מהרשת לתמונת המקור באמצעות VGG-Face"""
        if not target_img_url or not os.path.exists(self.reference_path):
            return False, 0

        try:
            result = DeepFace.verify(
                img1_path=self.reference_path,
                img2_path=target_img_url,
                enforce_detection=False,
                model_name="VGG-Face"
            )
            return result["verified"], 1 - result["distance"]
        except Exception:
            return False, 0