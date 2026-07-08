import json
import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


logger = logging.getLogger(__name__)


def initialize_firebase_admin() -> None:
    if firebase_admin._apps:
        return

    if not settings.firebase_service_account_path and not settings.firebase_service_account_json:
        logger.info("Firebase Admin SDK is not configured")
        return

    if settings.firebase_service_account_json:
        service_account = json.loads(settings.firebase_service_account_json)
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")
        return

    credential_path = Path(settings.firebase_service_account_path).expanduser()
    if not credential_path.is_absolute():
        credential_path = Path.cwd() / credential_path

    if not credential_path.exists():
        logger.warning(
            "Firebase service account file does not exist",
            extra={"path": str(credential_path)},
        )
        return

    cred = credentials.Certificate(str(credential_path))
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized")
