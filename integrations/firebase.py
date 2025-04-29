"""
Google Firebase
- Firestore Database: useful for storing configurations
"""

from google.cloud import firestore
from loguru import logger

from .utils import Config

cfg = Config()


def init(service_account_info: dict):
    """
    service_account_info: dict to authenticate with Firebase
    """
    global cfg
    required_fields = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
        "universe_domain",
    ]
    if not all(k in required_fields for k in service_account_info):
        logger.error("Invalid service account info, initialization failed.")
        return

    cfg.service_account_info = service_account_info
    cfg.db = firestore.Client.from_service_account_info(service_account_info)
    cfg.mark_initialized()


class SimpleDocument:
    def __init__(self, collection: str, document: str):
        assert cfg.initialized
        db: firestore.Client = cfg.db
        doc_ref: firestore.DocumentReference = db.collection(collection).document(
            document
        )
        doc_ref.set({}, merge=True)  # make sure the document exists

        self.db = db
        self.doc_ref = doc_ref

    def get(self):
        return self.doc_ref.get().to_dict()

    def update(self, **data):
        self.doc_ref.update(data)

    def insert_array(self, key: str, array: list):
        "more efficient way to insert element to an array"
        self.doc_ref.update({key: firestore.ArrayUnion(array)})

    def remove_array(self, key: str, array: list):
        "more efficient way to remove element from an array"
        self.doc_ref.update({key: firestore.ArrayRemove(array)})


@cfg.check_initialized
def request_document(collection: str, document: str):
    "get a document reference, create if it doesn't exist"
    return SimpleDocument(collection, document)
