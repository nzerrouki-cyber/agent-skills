# services/firestore_client.py
from google.cloud import firestore
from config.settings import settings

class FirestoreClient:
    def __init__(self):
        self.db = firestore.AsyncClient(project=settings.PROJECT_ID)
        # Instantiate the exact collection path
        self.registry = self.db.collection(settings.FIRESTORE_REGISTRY_COLLECTION)