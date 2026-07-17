import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_app = firebase_admin.initialize_app(_cred)
