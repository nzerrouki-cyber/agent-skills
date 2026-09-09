# utils/security.py
from fastapi import Request, HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from utils.logger import logger


async def verify_cloud_tasks_oidc_token(request: Request) -> dict:
    """
    Validates the incoming OIDC Bearer token injected by Cloud Tasks on worker HTTP endpoints.
    Ensures endpoints like /worker/{target_datastore_id} only accept authenticated GCP dispatches.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Unauthorized request attempt: Missing or malformed Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    token = auth_header.split("Bearer ")[1]

    try:
        # Validates Google-signed OIDC ID token signature and expiration
        request_adapter = requests.Request()
        claims = id_token.verify_oauth2_token(token, request_adapter)
        return claims
    except Exception as e:
        logger.error(f"OIDC Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"OIDC token verification failed: {str(e)}",
        )


def sanitize_header_value(val: str) -> str:
    """Sanitizes header or string values to prevent injection or unexpected characters."""
    if not val:
        return ""
    return "".join(c for c in val if c.isalnum() or c in " -_.").strip()