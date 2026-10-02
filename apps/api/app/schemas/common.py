from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


class FieldError(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str
    errors: Optional[List[FieldError]] = None

    model_config = ConfigDict(extra="ignore")


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
