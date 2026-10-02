from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.owner import Owner


class OwnerRepository:
    """Repository for Owner entity (users table)."""

    def get_by_id(self, db: Session, owner_id: UUID) -> Optional[Owner]:
        """Fetch owner by primary key."""
        stmt = select(Owner).where(Owner.id == owner_id)
        return db.scalar(stmt)

    def get_by_email(self, db: Session, email: str) -> Optional[Owner]:
        """Fetch owner by email."""
        stmt = select(Owner).where(Owner.email == email.lower().strip())
        return db.scalar(stmt)

    def create(
        self,
        db: Session,
        email: str,
        password_hash: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> Owner:
        """Create and persist a new owner."""
        owner = Owner(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            is_active=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        return owner


owner_repo = OwnerRepository()
