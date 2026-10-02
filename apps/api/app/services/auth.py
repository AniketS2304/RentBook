import uuid
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.repositories.owner import owner_repo
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.schemas.owner import OwnerBrief


class AuthService:
    """Authentication business logic."""

    def register(self, db: Session, request: RegisterRequest) -> RegisterResponse:
        """Register a new owner."""
        existing_owner = owner_repo.get_by_email(db, request.email)
        if existing_owner:
            raise ConflictError(
                detail="Email already registered",
                code="EMAIL_ALREADY_EXISTS",
                errors=[{"field": "email", "message": "Email already registered"}],
            )

        password_hash = get_password_hash(request.password)
        owner = owner_repo.create(
            db=db,
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            phone=request.phone,
        )

        access_token = create_access_token(subject=owner.id)
        refresh_token = create_refresh_token(subject=owner.id)

        return RegisterResponse(
            id=owner.id,
            email=owner.email,
            full_name=owner.full_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def login(self, db: Session, request: LoginRequest) -> LoginResponse:
        """Authenticate an owner by email and password."""
        owner = owner_repo.get_by_email(db, request.email)
        if not owner or not verify_password(request.password, owner.password_hash):
            raise InvalidCredentialsError(
                detail="Invalid email or password",
                code="INVALID_CREDENTIALS",
            )

        if not owner.is_active:
            raise ForbiddenError(
                detail="Account is inactive",
                code="ACCOUNT_INACTIVE",
            )

        access_token = create_access_token(subject=owner.id)
        refresh_token = create_refresh_token(subject=owner.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=OwnerBrief(
                id=owner.id,
                email=owner.email,
                full_name=owner.full_name,
            ),
        )

    def refresh_access_token(self, db: Session, refresh_token: str) -> RefreshResponse:
        """Issue a new access token using a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise UnauthorizedError(
                detail="Invalid or expired refresh token",
                code="INVALID_REFRESH_TOKEN",
            )

        token_type = payload.get("type")
        if token_type != "refresh":
            raise UnauthorizedError(
                detail="Token is not a refresh token",
                code="INVALID_TOKEN_TYPE",
            )

        subject = payload.get("sub")
        if not subject:
            raise UnauthorizedError(
                detail="Missing subject in refresh token",
                code="INVALID_TOKEN_SUBJECT",
            )

        try:
            owner_id = uuid.UUID(subject)
        except ValueError:
            raise UnauthorizedError(
                detail="Invalid subject in token",
                code="INVALID_TOKEN_SUBJECT",
            )

        owner = owner_repo.get_by_id(db, owner_id)
        if not owner or not owner.is_active:
            raise UnauthorizedError(
                detail="User not found or inactive",
                code="USER_NOT_FOUND",
            )

        new_access_token = create_access_token(subject=owner.id)
        new_refresh_token = create_refresh_token(subject=owner.id)
        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )


auth_service = AuthService()
