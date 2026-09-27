"""Pydantic schemas for public API responses."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class HackathonListItem(BaseModel):
    """Schema for hackathon items in list view."""
    id: UUID
    name: str
    slug: str
    tagline: str | None
    description: str | None
    lifecycle_status: str
    registration_start_at: datetime | None
    registration_end_at: datetime | None
    hackathon_start_at: datetime | None
    hackathon_end_at: datetime | None
    submission_deadline_at: datetime | None
    team_min_size: int
    team_max_size: int | None
    
    class Config:
        from_attributes = True


class HackathonDetail(BaseModel):
    """Schema for detailed hackathon view."""
    id: UUID
    name: str
    slug: str
    tagline: str | None
    description: str | None
    logo_key: str | None
    cover_key: str | None
    format: str | None
    venue: str | None
    display_timezone: str
    lifecycle_status: str
    registration_start_at: datetime | None
    registration_end_at: datetime | None
    hackathon_start_at: datetime | None
    hackathon_end_at: datetime | None
    submission_deadline_at: datetime | None
    judging_start_at: datetime | None
    judging_end_at: datetime | None
    team_min_size: int
    team_max_size: int | None
    result_gallery_mode: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class HackathonRules(BaseModel):
    """Schema for hackathon rules version."""
    id: UUID
    version_number: int
    rules: str
    eligibility_description: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HackathonTrack(BaseModel):
    """Schema for hackathon track."""
    id: UUID
    name: str
    description: str | None
    sort_order: int
    
    class Config:
        from_attributes = True


class HackathonScheduleItem(BaseModel):
    """Schema for hackathon schedule item."""
    id: UUID
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime | None
    location: str | None
    link: str | None
    sort_order: int
    
    class Config:
        from_attributes = True


class HackathonSponsor(BaseModel):
    """Schema for hackathon sponsor."""
    id: UUID
    name: str
    logo_key: str | None
    url: str | None
    tier: str | None
    sort_order: int
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Schema for paginated list responses."""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
