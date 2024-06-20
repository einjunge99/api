from firebase_admin import firestore


def get_firestore_client():
    db = firestore.client()
    return db
