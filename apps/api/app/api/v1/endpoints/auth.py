from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_owner
from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.schemas.owner import OwnerOut
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new owner",
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new landlord/owner account."""
    return auth_service.register(db=db, request=request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in an existing owner",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password to receive JWT tokens."""
    return auth_service.login(db=db, request=request)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Obtain a new access token using a valid refresh token."""
    return auth_service.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
    )


@router.get(
    "/me",
    response_model=OwnerOut,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated owner profile",
)
def get_me(
    current_owner: Owner = Depends(get_current_owner),
):
    """Retrieve details of the authenticated owner from JWT."""
    return current_owner
