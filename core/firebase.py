from firebase_admin import credentials, initialize_app
from core.config import settings


def initialize_firebase():
    cred = credentials.Certificate(settings.firebase_key_path)
    initialize_app(cred, {"storageBucket": "sign-language-learning.appspot.com"})
