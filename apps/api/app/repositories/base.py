from typing import Generic, Optional, Type, TypeVar
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseOwnerScopedRepository(Generic[ModelType]):
    """Base repository enforcing owner isolation on every query."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(
        self,
        db: Session,
        resource_id: UUID,
        owner_id: UUID,
    ) -> Optional[ModelType]:
        """Fetch a single resource by ID, strictly enforcing owner_id."""
        stmt = select(self.model).where(
            self.model.id == resource_id,
            self.model.owner_id == owner_id,
        )
        return db.scalar(stmt)

    def list_all(
        self,
        db: Session,
        owner_id: UUID,
    ) -> list[ModelType]:
        """Fetch all resources belonging to the owner."""
        stmt = select(self.model).where(self.model.owner_id == owner_id)
        return list(db.scalars(stmt).all())
