from __future__ import annotations

from fastapi import Header, HTTPException, status
from typing import Optional
from .config import get_settings


async def api_key_auth(
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Simple API key authentication dependency.

    Business:
    - Accept either `x-api-key: <key>` or `Authorization: ApiKey <key>` headers.
    - Keys are provided via environment `API_KEYS` (comma-separated). Use Secret Manager + Cloud Run.
    - Evaluate VPC egress + Cloud Armor for additional perimeter security.

    Compliance:
    - Avoid embedding user-identifying data in keys. Rotate keys periodically.
    """
    settings = get_settings()
    provided_key: Optional[str] = None

    if x_api_key:
        provided_key = x_api_key.strip()
    elif authorization and authorization.lower().startswith("apikey "):
        provided_key = authorization.split(" ", 1)[1].strip()

    if not provided_key or provided_key not in settings.api_keys_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: invalid or missing API key",
        )

    return True
