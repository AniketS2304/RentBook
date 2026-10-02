import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.owner import Owner
from app.repositories.owner import owner_repo

# auto_error=False allows us to provide custom, standard error responses
security = HTTPBearer(auto_error=False)


def get_current_owner(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Owner:
    """FastAPI dependency to extract and validate the authenticated owner strictly from JWT.

    Critical security rule (ADR-006):
    owner_id comes exclusively from the validated JWT claims.
    Never trust or accept client-controlled owner_id from headers, bodies, or query params.
    """
    if not credentials:
        raise UnauthorizedError(
            detail="Authentication credentials were not provided",
            code="NOT_AUTHENTICATED",
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthorizedError(
            detail="Invalid or expired token",
            code="INVALID_TOKEN",
        )

    token_type = payload.get("type")
    if token_type != "access":
        raise UnauthorizedError(
            detail="Invalid token type for authentication",
            code="INVALID_TOKEN_TYPE",
        )

    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError(
            detail="Token subject missing",
            code="INVALID_TOKEN_SUBJECT",
        )

    try:
        owner_id = uuid.UUID(sub)
    except ValueError:
        raise UnauthorizedError(
            detail="Invalid token subject format",
            code="INVALID_TOKEN_SUBJECT",
        )

    owner = owner_repo.get_by_id(db, owner_id)
    if not owner:
        raise UnauthorizedError(
            detail="Authenticated owner not found",
            code="USER_NOT_FOUND",
        )

    if not owner.is_active:
        raise UnauthorizedError(
            detail="Account is inactive",
            code="ACCOUNT_INACTIVE",
        )

    return owner
