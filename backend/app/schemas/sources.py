import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Permission, SourceCategory, SourceStatus, VerificationStatus


class SourceCreate(BaseModel):
    slug: str = Field(min_length=3, max_length=120, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=300)
    category: SourceCategory
    language: str = Field(min_length=2, max_length=10)
    author_or_publisher: str | None = Field(default=None, max_length=300)
    translator: str | None = Field(default=None, max_length=300)
    edition: str | None = Field(default=None, max_length=200)
    original_url: str | None = Field(default=None, max_length=1000)


class SourceDescribe(BaseModel):
    """Descriptive fields only; rights fields have their own endpoint so changes are deliberate."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    author_or_publisher: str | None = Field(default=None, max_length=300)
    translator: str | None = Field(default=None, max_length=300)
    edition: str | None = Field(default=None, max_length=200)
    original_url: str | None = Field(default=None, max_length=1000)


class SourceRights(BaseModel):
    rights_holder: str | None = Field(default=None, max_length=300)
    license_name: str | None = Field(default=None, max_length=200)
    license_url: str | None = Field(default=None, max_length=1000)
    commercial_use: Permission | None = None
    redistribution: Permission | None = None
    storage_permission: Permission | None = None
    indexing_permission: Permission | None = None
    rag_permission: Permission | None = None
    attribution_required: bool | None = None
    attribution_text: str | None = Field(default=None, max_length=1000)
    rights_notes: str | None = Field(default=None, max_length=4000)


class StatusChange(BaseModel):
    to_status: SourceStatus
    note: str = Field(min_length=3, max_length=2000)


class Note(BaseModel):
    note: str = Field(min_length=3, max_length=2000)


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    category: SourceCategory
    language: str
    author_or_publisher: str | None
    translator: str | None
    edition: str | None
    original_url: str | None
    rights_holder: str | None
    license_name: str | None
    license_url: str | None
    commercial_use: Permission
    redistribution: Permission
    storage_permission: Permission
    indexing_permission: Permission
    rag_permission: Permission
    attribution_required: bool
    attribution_text: str | None
    rights_notes: str | None
    license_verified_at: datetime | None
    license_verified_by: uuid.UUID | None
    verification_status: VerificationStatus
    approval_status: SourceStatus
    created_at: datetime
    updated_at: datetime


class PublicSourceOut(BaseModel):
    """What visitors may see: only approved sources, with the credit we owe."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    category: SourceCategory
    language: str
    author_or_publisher: str | None
    translator: str | None
    edition: str | None
    rights_holder: str | None
    license_name: str | None
    license_url: str | None
    attribution_text: str | None
    original_url: str | None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reviewer_id: uuid.UUID | None
    from_status: SourceStatus
    to_status: SourceStatus
    note: str | None
    created_at: datetime


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    details: dict | None
    created_at: datetime


class ApprovalReadiness(BaseModel):
    ready: bool
    missing: list[str]
