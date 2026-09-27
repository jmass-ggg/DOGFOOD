"""FastAPI router for public hackathon endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import math
from uuid import UUID

from app.core.database import get_db_session
from app.hackathons.models import (
    Hackathon,
    HackathonRulesVersion,
    HackathonTrack,
    HackathonScheduleItem,
    HackathonSponsor,
)
from app.public import schemas

router = APIRouter(prefix="/hackathons", tags=["public"])


@router.get("", response_model=schemas.PaginatedResponse)
async def list_hackathons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """List public hackathons with pagination.
    
    Only returns hackathons with lifecycle_status='PUBLISHED'.
    Results are ordered deterministically by created_at desc, then id.
    """
    # Base query: only PUBLISHED hackathons are public
    query = select(Hackathon).where(Hackathon.lifecycle_status == "PUBLISHED")
    
    # Apply optional status filter (note: status filter applies on top of PUBLISHED filter)
    # This means if status is provided and it's not "PUBLISHED", no results will be returned
    if status:
        query = query.where(Hackathon.lifecycle_status == status)
    
    # Order deterministically: created_at desc, then id
    query = query.order_by(Hackathon.created_at.desc(), Hackathon.id)
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(Hackathon).where(
        Hackathon.lifecycle_status == "PUBLISHED"
    )
    if status:
        count_query = count_query.where(Hackathon.lifecycle_status == status)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    hackathons = result.scalars().all()
    
    # Build response
    return schemas.PaginatedResponse(
        items=[schemas.HackathonListItem.model_validate(h) for h in hackathons],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get("/{identifier}", response_model=schemas.HackathonDetail)
async def get_hackathon(
    identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hackathon details by UUID or slug.
    
    Only returns hackathons with lifecycle_status='PUBLISHED'.
    Returns 404 for non-existent or non-public hackathons.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Try to parse as UUID first, otherwise treat as slug
    try:
        hackathon_id = UUID(identifier)
        query = select(Hackathon).where(
            Hackathon.id == hackathon_id,
            Hackathon.lifecycle_status == "PUBLISHED"
        )
    except ValueError:
        # Not a valid UUID, treat as slug
        query = select(Hackathon).where(
            Hackathon.slug == identifier,
            Hackathon.lifecycle_status == "PUBLISHED"
        )
    
    # Execute query
    result = await db.execute(query)
    hackathon = result.scalar_one_or_none()
    
    # Return 404 if not found or not public
    if hackathon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hackathon not found"
        )
    
    return schemas.HackathonDetail.model_validate(hackathon)


@router.get("/{identifier}/rules", response_model=schemas.HackathonRules)
async def get_hackathon_rules(
    identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hackathon rules.
    
    Returns the current rules version for the hackathon.
    Returns 404 if hackathon is not public or if no rules are configured.
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    # Get hackathon and verify it's public
    hackathon = await _get_public_hackathon(identifier, db)
    
    # Check if rules are configured
    if hackathon.current_rules_version_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hackathon rules not found"
        )
    
    # Get the current rules version
    result = await db.execute(
        select(HackathonRulesVersion).where(
            HackathonRulesVersion.id == hackathon.current_rules_version_id
        )
    )
    rules = result.scalar_one_or_none()
    
    # This should not happen due to foreign key constraints, but handle it gracefully
    if rules is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hackathon rules not found"
        )
    
    return schemas.HackathonRules.model_validate(rules)


@router.get("/{identifier}/tracks", response_model=list[schemas.HackathonTrack])
async def get_hackathon_tracks(
    identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hackathon tracks ordered by sort_order, then id.
    
    Returns an empty list if no tracks are configured.
    
    Requirements: 8.1, 8.2, 8.3
    """
    # Get hackathon and verify it's public
    hackathon = await _get_public_hackathon(identifier, db)
    
    # Get tracks ordered by sort_order, then id
    result = await db.execute(
        select(HackathonTrack)
        .where(HackathonTrack.hackathon_id == hackathon.id)
        .order_by(HackathonTrack.sort_order, HackathonTrack.id)
    )
    tracks = result.scalars().all()
    
    return [schemas.HackathonTrack.model_validate(track) for track in tracks]


@router.get("/{identifier}/schedule", response_model=list[schemas.HackathonScheduleItem])
async def get_hackathon_schedule(
    identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hackathon schedule ordered chronologically.
    
    Returns schedule items ordered by start_at, then sort_order, then id.
    Returns an empty list if no schedule items are configured.
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    # Get hackathon and verify it's public
    hackathon = await _get_public_hackathon(identifier, db)
    
    # Get schedule items ordered chronologically: start_at, then sort_order, then id
    result = await db.execute(
        select(HackathonScheduleItem)
        .where(HackathonScheduleItem.hackathon_id == hackathon.id)
        .order_by(
            HackathonScheduleItem.start_at,
            HackathonScheduleItem.sort_order,
            HackathonScheduleItem.id
        )
    )
    schedule_items = result.scalars().all()
    
    return [schemas.HackathonScheduleItem.model_validate(item) for item in schedule_items]


@router.get("/{identifier}/sponsors", response_model=list[schemas.HackathonSponsor])
async def get_hackathon_sponsors(
    identifier: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get hackathon sponsors ordered by sort_order, then id.
    
    Returns an empty list if no sponsors are configured.
    
    Requirements: 10.1, 10.2, 10.3, 10.4
    """
    # Get hackathon and verify it's public
    hackathon = await _get_public_hackathon(identifier, db)
    
    # Get sponsors ordered by sort_order, then id
    result = await db.execute(
        select(HackathonSponsor)
        .where(HackathonSponsor.hackathon_id == hackathon.id)
        .order_by(HackathonSponsor.sort_order, HackathonSponsor.id)
    )
    sponsors = result.scalars().all()
    
    return [schemas.HackathonSponsor.model_validate(sponsor) for sponsor in sponsors]


async def _get_public_hackathon(identifier: str, db: AsyncSession) -> Hackathon:
    """Helper to get a public hackathon by slug or UUID.
    
    Raises 404 if hackathon doesn't exist or is not public.
    """
    try:
        hackathon_id = UUID(identifier)
        query = select(Hackathon).where(
            Hackathon.id == hackathon_id,
            Hackathon.lifecycle_status == "PUBLISHED"
        )
    except ValueError:
        # Not a valid UUID, treat as slug
        query = select(Hackathon).where(
            Hackathon.slug == identifier,
            Hackathon.lifecycle_status == "PUBLISHED"
        )
    
    result = await db.execute(query)
    hackathon = result.scalar_one_or_none()
    
    if hackathon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hackathon not found"
        )
    
    return hackathon
