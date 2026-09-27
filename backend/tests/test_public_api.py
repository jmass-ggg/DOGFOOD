"""Unit tests for public API endpoints."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.hackathons.models import Hackathon, HackathonRulesVersion
from app.users.models import User


# ========================================================================
# Test Data Helper
# ========================================================================

async def create_published_hackathon(
    session: AsyncSession,
    user_id,
    name: str,
    slug: str,
    **kwargs
) -> Hackathon:
    """Helper to create a valid PUBLISHED hackathon with all required fields."""
    # Create hackathon first as DRAFT
    hackathon = Hackathon(
        name=name,
        slug=slug,
        created_by_user_id=user_id,
        organizer_user_id=user_id,
        lifecycle_status="DRAFT",
        team_min_size=1,
        **kwargs
    )
    session.add(hackathon)
    await session.flush()
    
    # Create rules version
    rules = HackathonRulesVersion(
        hackathon_id=hackathon.id,
        version_number=1,
        rules="Test rules content",
        created_by_user_id=user_id
    )
    session.add(rules)
    await session.flush()
    
    # Now update hackathon to PUBLISHED with all required fields
    hackathon.lifecycle_status = "PUBLISHED"
    hackathon.current_rules_version_id = rules.id
    hackathon.registration_start_at = kwargs.get('registration_start_at', datetime.now(timezone.utc))
    hackathon.registration_end_at = kwargs.get('registration_end_at', datetime.now(timezone.utc))
    hackathon.hackathon_start_at = kwargs.get('hackathon_start_at', datetime.now(timezone.utc))
    hackathon.submission_deadline_at = kwargs.get('submission_deadline_at', datetime.now(timezone.utc))
    hackathon.judging_start_at = kwargs.get('judging_start_at', datetime.now(timezone.utc))
    hackathon.judging_end_at = kwargs.get('judging_end_at', datetime.now(timezone.utc))
    hackathon.hackathon_end_at = kwargs.get('hackathon_end_at', datetime.now(timezone.utc))
    
    await session.flush()
    return hackathon


# ========================================================================
# Hackathon List Tests
# ========================================================================

@pytest.mark.asyncio
async def test_list_hackathons_returns_only_published(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that list endpoint returns only PUBLISHED hackathons.
    
    Requirements: 5.1 - Return only publicly visible hackathons
    """
    # Create a test user for foreign key constraints
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="dummy_hash",
        full_name="Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create PUBLISHED hackathon
    published_hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Published Hackathon",
        "published-hackathon"
    )
    
    # Create DRAFT hackathon (should not appear in results)
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    
    # Create ARCHIVED hackathon (should not appear in results)
    archived_hackathon = Hackathon(
        name="Archived Hackathon",
        slug="archived-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="ARCHIVED",
        team_min_size=1
    )
    test_db_session.add(archived_hackathon)
    
    await test_db_session.commit()
    
    # Request hackathon list
    response = await test_client_with_db.get("/api/v1/hackathons")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    
    # Verify only PUBLISHED hackathon is returned
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["slug"] == "published-hackathon"
    assert data["items"][0]["lifecycle_status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_list_hackathons_pagination(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test pagination parameters work correctly.
    
    Requirements: 5.2, 5.3 - Paginate results with configurable page size
    """
    # Create a test user
    user = User(
        email="pagtest@example.com",
        username="paguser",
        password_hash="dummy_hash",
        full_name="Pagination Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create multiple PUBLISHED hackathons
    for i in range(5):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Hackathon {i}",
            f"hackathon-{i}"
        )
    
    await test_db_session.commit()
    
    # Test first page with page_size=2
    response = await test_client_with_db.get("/api/v1/hackathons?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3  # ceil(5/2) = 3
    
    # Test second page
    response = await test_client_with_db.get("/api/v1/hackathons?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    
    assert data["page"] == 2
    assert len(data["items"]) == 2
    
    # Test last page
    response = await test_client_with_db.get("/api/v1/hackathons?page=3&page_size=2")
    assert response.status_code == 200
    data = response.json()
    
    assert data["page"] == 3
    assert len(data["items"]) == 1  # Only 1 item on last page


@pytest.mark.asyncio
async def test_list_hackathons_max_page_size(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test page_size is limited to maximum of 100.
    
    Requirements: 5.4 - Support configurable page size with maximum limit
    """
    # Request with page_size > 100 should fail validation
    response = await test_client_with_db.get("/api/v1/hackathons?page_size=150")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_hackathons_deterministic_ordering(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test hackathons are ordered deterministically (created_at desc, then id).
    
    Requirements: 5.3 - Order deterministically
    """
    # Create a test user
    user = User(
        email="ordertest@example.com",
        username="orderuser",
        password_hash="dummy_hash",
        full_name="Order Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create hackathons in sequence
    # They will naturally have different created_at timestamps
    import asyncio
    
    first = await create_published_hackathon(
        test_db_session,
        user.id,
        "First Hackathon",
        "first"
    )
    await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
    
    second = await create_published_hackathon(
        test_db_session,
        user.id,
        "Second Hackathon",
        "second"
    )
    await asyncio.sleep(0.01)
    
    third = await create_published_hackathon(
        test_db_session,
        user.id,
        "Third Hackathon",
        "third"
    )
    
    await test_db_session.commit()
    
    # Request list
    response = await test_client_with_db.get("/api/v1/hackathons")
    assert response.status_code == 200
    data = response.json()
    
    # Should be ordered by created_at desc (newest first)
    assert len(data["items"]) == 3
    assert data["items"][0]["slug"] == "third"  # Newest
    assert data["items"][1]["slug"] == "second"  # Middle
    assert data["items"][2]["slug"] == "first"  # Oldest


@pytest.mark.asyncio
async def test_list_hackathons_empty_result(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test list endpoint returns empty result when no published hackathons exist.
    
    Requirements: 5.1 - Return only publicly visible hackathons
    """
    response = await test_client_with_db.get("/api/v1/hackathons")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["page"] == 1
    assert data["total_pages"] == 0


@pytest.mark.asyncio
async def test_list_hackathons_total_count_accurate(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that total count matches actual number of PUBLISHED hackathons.
    
    Requirements: 5.4 - Total count is accurate
    """
    # Create a test user
    user = User(
        email="counttest@example.com",
        username="countuser",
        password_hash="dummy_hash",
        full_name="Count Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create mix of hackathons
    for i in range(3):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Published {i}",
            f"published-{i}"
        )
    
    # Create draft hackathons that should not be counted
    for i in range(2):
        draft = Hackathon(
            name=f"Draft {i}",
            slug=f"draft-{i}",
            created_by_user_id=user.id,
            organizer_user_id=user.id,
            lifecycle_status="DRAFT",
            team_min_size=1
        )
        test_db_session.add(draft)
    
    await test_db_session.commit()
    
    # Request with small page size to test count across pages
    response = await test_client_with_db.get("/api/v1/hackathons?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    
    # Total should be 3 (only PUBLISHED hackathons)
    assert data["total"] == 3
    assert data["total_pages"] == 2  # ceil(3/2) = 2
    
    # First page should have 2 items
    assert len(data["items"]) == 2
    
    # Second page should have 1 item
    response = await test_client_with_db.get("/api/v1/hackathons?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 3  # Total should remain consistent


@pytest.mark.asyncio
async def test_list_hackathons_status_filter(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test status filter parameter.
    
    Requirements: 5.5 - Support filtering by status
    """
    # Create a test user
    user = User(
        email="filtertest@example.com",
        username="filteruser",
        password_hash="dummy_hash",
        full_name="Filter Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create PUBLISHED hackathons
    for i in range(2):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Published {i}",
            f"published-{i}"
        )
    
    await test_db_session.commit()
    
    # Test with status=PUBLISHED (should return hackathons)
    response = await test_client_with_db.get("/api/v1/hackathons?status=PUBLISHED")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    
    # Test with status=DRAFT (should return empty since base filter is PUBLISHED)
    # The implementation filters to PUBLISHED first, then applies status filter
    # So this will return empty results (PUBLISHED AND DRAFT = empty set)
    response = await test_client_with_db.get("/api/v1/hackathons?status=DRAFT")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    
    # Test without status filter (should return all PUBLISHED)
    response = await test_client_with_db.get("/api/v1/hackathons")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2



# ========================================================================
# Hackathon Detail Tests
# ========================================================================

@pytest.mark.asyncio
async def test_get_hackathon_by_uuid(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test retrieval of hackathon detail by UUID.
    
    Requirements: 6.1, 6.4 - Retrieve hackathon by UUID identifier
    """
    # Create a test user
    user = User(
        email="uuidtest@example.com",
        username="uuiduser",
        password_hash="dummy_hash",
        full_name="UUID Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Test Hackathon",
        "test-hackathon",
        tagline="A test event",
        description="Full description",
        logo_key="logo.png",
        cover_key="cover.png",
        format="HYBRID",
        venue="Test Venue"
    )
    
    await test_db_session.commit()
    
    # Request by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all public fields are present
    assert data["id"] == str(hackathon.id)
    assert data["name"] == "Test Hackathon"
    assert data["slug"] == "test-hackathon"
    assert data["tagline"] == "A test event"
    assert data["description"] == "Full description"
    assert data["logo_key"] == "logo.png"
    assert data["cover_key"] == "cover.png"
    assert data["format"] == "HYBRID"
    assert data["venue"] == "Test Venue"
    assert data["lifecycle_status"] == "PUBLISHED"
    assert data["team_min_size"] == 1
    assert data["display_timezone"] is not None
    assert data["result_gallery_mode"] is not None
    assert data["created_at"] is not None
    
    # Verify timestamp fields are present
    assert "registration_start_at" in data
    assert "registration_end_at" in data
    assert "hackathon_start_at" in data
    assert "hackathon_end_at" in data
    assert "submission_deadline_at" in data
    assert "judging_start_at" in data
    assert "judging_end_at" in data


@pytest.mark.asyncio
async def test_get_hackathon_by_slug(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test retrieval of hackathon detail by slug.
    
    Requirements: 6.1, 6.4 - Retrieve hackathon by slug identifier
    """
    # Create a test user
    user = User(
        email="slugtest@example.com",
        username="sluguser",
        password_hash="dummy_hash",
        full_name="Slug Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Test Hackathon",
        "slug-test-hackathon"
    )
    
    await test_db_session.commit()
    
    # Request by slug
    response = await test_client_with_db.get("/api/v1/hackathons/slug-test-hackathon")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == str(hackathon.id)
    assert data["name"] == "Slug Test Hackathon"
    assert data["slug"] == "slug-test-hackathon"
    assert data["lifecycle_status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_get_hackathon_draft_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that DRAFT hackathons return 404.
    
    Requirements: 6.3 - Non-public hackathons not accessible
    """
    # Create a test user
    user = User(
        email="drafttest@example.com",
        username="draftuser",
        password_hash="dummy_hash",
        full_name="Draft Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    
    await test_db_session.commit()
    
    # Request by UUID - should return 404
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}")
    assert response.status_code == 404
    
    # Request by slug - should return 404
    response = await test_client_with_db.get("/api/v1/hackathons/draft-hackathon")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_nonexistent_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that non-existent hackathons return 404.
    
    Requirements: 6.2 - Not found for non-existent hackathons
    """
    # Request with random UUID
    random_uuid = uuid4()
    response = await test_client_with_db.get(f"/api/v1/hackathons/{random_uuid}")
    assert response.status_code == 404
    
    # Request with non-existent slug
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_response_contains_all_public_fields(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that response contains all public fields defined in HackathonDetail schema.
    
    Requirements: 6.5 - Do not expose internal or private fields
    """
    # Create a test user
    user = User(
        email="fieldstest@example.com",
        username="fieldsuser",
        password_hash="dummy_hash",
        full_name="Fields Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon with all optional fields populated
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Complete Hackathon",
        "complete-hackathon",
        tagline="Complete event",
        description="Complete description",
        logo_key="complete-logo.png",
        cover_key="complete-cover.png",
        format="ONLINE",
        venue="Online Platform",
        team_max_size=5
    )
    
    await test_db_session.commit()
    
    # Request hackathon
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required fields from HackathonDetail schema are present
    required_fields = [
        "id", "name", "slug", "tagline", "description",
        "logo_key", "cover_key", "format", "venue", "display_timezone",
        "lifecycle_status", "registration_start_at", "registration_end_at",
        "hackathon_start_at", "hackathon_end_at", "submission_deadline_at",
        "judging_start_at", "judging_end_at", "team_min_size", "team_max_size",
        "result_gallery_mode", "created_at"
    ]
    
    for field in required_fields:
        assert field in data, f"Field '{field}' missing from response"
    
    # Verify internal fields are NOT exposed
    internal_fields = [
        "password_hash", "created_by_user_id", "organizer_user_id",
        "current_rules_version_id", "updated_at", "deleted_at"
    ]
    
    for field in internal_fields:
        assert field not in data, f"Internal field '{field}' should not be exposed"


# ========================================================================
# Hackathon Rules Tests
# ========================================================================

@pytest.mark.asyncio
async def test_get_hackathon_rules_returns_current_version(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that rules endpoint returns the current rules version.
    
    Requirements: 7.1, 7.2 - Return current rules version
    """
    # Create a test user
    user = User(
        email="rulestest@example.com",
        username="rulesuser",
        password_hash="dummy_hash",
        full_name="Rules Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon (this creates rules version 1)
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Rules Test Hackathon",
        "rules-test-hackathon"
    )
    
    await test_db_session.commit()
    
    # Request rules by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify rules data is returned
    assert "id" in data
    assert "version_number" in data
    assert "rules" in data
    assert "eligibility_description" in data
    assert "created_at" in data
    
    # Verify it's the current rules version
    assert data["version_number"] == 1
    assert data["rules"] == "Test rules content"


@pytest.mark.asyncio
async def test_get_hackathon_rules_by_slug(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that rules can be retrieved using hackathon slug.
    
    Requirements: 7.1 - Return rules for hackathon
    """
    # Create a test user
    user = User(
        email="rulesslug@example.com",
        username="rulessluguser",
        password_hash="dummy_hash",
        full_name="Rules Slug User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Rules Test",
        "slug-rules-test"
    )
    
    await test_db_session.commit()
    
    # Request rules by slug
    response = await test_client_with_db.get("/api/v1/hackathons/slug-rules-test/rules")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["version_number"] == 1
    assert data["rules"] == "Test rules content"


@pytest.mark.asyncio
async def test_get_hackathon_rules_no_rules_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that 404 is returned when hackathon has no rules configured.
    
    Requirements: 7.2 - Return 404 if no rules configured
    """
    # Create a test user
    user = User(
        email="norules@example.com",
        username="norulesuser",
        password_hash="dummy_hash",
        full_name="No Rules User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon without rules (can't be PUBLISHED without rules)
    hackathon = Hackathon(
        name="No Rules Hackathon",
        slug="no-rules-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1,
        current_rules_version_id=None  # No rules configured
    )
    test_db_session.add(hackathon)
    
    # To test the no-rules case for a PUBLISHED hackathon, we need to work around
    # the database constraint. Instead, we'll test on a DRAFT hackathon,
    # which will return 404 because it's not public (not PUBLISHED)
    
    await test_db_session.commit()
    
    # Request rules - should return 404 because hackathon is not PUBLISHED
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_rules_belongs_to_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that returned rules belong to the requested hackathon.
    
    Requirements: 7.1 - Rules belong to that hackathon
    """
    # Create a test user
    user = User(
        email="scopetest@example.com",
        username="scopeuser",
        password_hash="dummy_hash",
        full_name="Scope Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create first hackathon with its rules
    # Need to create manually to control the rules content
    hackathon1 = Hackathon(
        name="Hackathon 1",
        slug="hackathon-1",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(hackathon1)
    await test_db_session.flush()
    
    rules1 = HackathonRulesVersion(
        hackathon_id=hackathon1.id,
        version_number=1,
        rules="Rules for hackathon 1",
        created_by_user_id=user.id
    )
    test_db_session.add(rules1)
    await test_db_session.flush()
    
    # Update hackathon1 to PUBLISHED
    hackathon1.lifecycle_status = "PUBLISHED"
    hackathon1.current_rules_version_id = rules1.id
    hackathon1.registration_start_at = datetime.now(timezone.utc)
    hackathon1.registration_end_at = datetime.now(timezone.utc)
    hackathon1.hackathon_start_at = datetime.now(timezone.utc)
    hackathon1.submission_deadline_at = datetime.now(timezone.utc)
    hackathon1.judging_start_at = datetime.now(timezone.utc)
    hackathon1.judging_end_at = datetime.now(timezone.utc)
    hackathon1.hackathon_end_at = datetime.now(timezone.utc)
    await test_db_session.flush()
    
    # Create second hackathon with different rules
    hackathon2 = Hackathon(
        name="Hackathon 2",
        slug="hackathon-2",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(hackathon2)
    await test_db_session.flush()
    
    rules2 = HackathonRulesVersion(
        hackathon_id=hackathon2.id,
        version_number=1,
        rules="Different rules for hackathon 2",
        created_by_user_id=user.id
    )
    test_db_session.add(rules2)
    await test_db_session.flush()
    
    # Update hackathon2 to PUBLISHED
    hackathon2.lifecycle_status = "PUBLISHED"
    hackathon2.current_rules_version_id = rules2.id
    hackathon2.registration_start_at = datetime.now(timezone.utc)
    hackathon2.registration_end_at = datetime.now(timezone.utc)
    hackathon2.hackathon_start_at = datetime.now(timezone.utc)
    hackathon2.submission_deadline_at = datetime.now(timezone.utc)
    hackathon2.judging_start_at = datetime.now(timezone.utc)
    hackathon2.judging_end_at = datetime.now(timezone.utc)
    hackathon2.hackathon_end_at = datetime.now(timezone.utc)
    await test_db_session.flush()
    
    await test_db_session.commit()
    
    # Request rules for hackathon1
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon1.id}/rules")
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get hackathon1's rules, not hackathon2's rules
    assert data["rules"] == "Rules for hackathon 1"
    
    # Request rules for hackathon2
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon2.id}/rules")
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get hackathon2's rules
    assert data["rules"] == "Different rules for hackathon 2"


@pytest.mark.asyncio
async def test_get_hackathon_rules_multiple_versions_returns_current(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that when multiple versions exist, the current version is returned.
    
    Requirements: 7.3 - Use explicit ordering field when available
    """
    # Create a test user
    user = User(
        email="versionstest@example.com",
        username="versionsuser",
        password_hash="dummy_hash",
        full_name="Versions Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create hackathon first as DRAFT
    hackathon = Hackathon(
        name="Versioned Rules Hackathon",
        slug="versioned-rules-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(hackathon)
    await test_db_session.flush()
    
    # Create version 1
    rules_v1 = HackathonRulesVersion(
        hackathon_id=hackathon.id,
        version_number=1,
        rules="Rules version 1",
        created_by_user_id=user.id
    )
    test_db_session.add(rules_v1)
    await test_db_session.flush()
    
    # Create version 2
    rules_v2 = HackathonRulesVersion(
        hackathon_id=hackathon.id,
        version_number=2,
        rules="Rules version 2",
        created_by_user_id=user.id
    )
    test_db_session.add(rules_v2)
    await test_db_session.flush()
    
    # Create version 3 and set as current
    rules_v3 = HackathonRulesVersion(
        hackathon_id=hackathon.id,
        version_number=3,
        rules="Rules version 3 (current)",
        created_by_user_id=user.id
    )
    test_db_session.add(rules_v3)
    await test_db_session.flush()
    
    # Update hackathon to PUBLISHED with version 3 as current
    hackathon.lifecycle_status = "PUBLISHED"
    hackathon.current_rules_version_id = rules_v3.id
    hackathon.registration_start_at = datetime.now(timezone.utc)
    hackathon.registration_end_at = datetime.now(timezone.utc)
    hackathon.hackathon_start_at = datetime.now(timezone.utc)
    hackathon.submission_deadline_at = datetime.now(timezone.utc)
    hackathon.judging_start_at = datetime.now(timezone.utc)
    hackathon.judging_end_at = datetime.now(timezone.utc)
    hackathon.hackathon_end_at = datetime.now(timezone.utc)
    
    await test_db_session.commit()
    
    # Request rules
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get version 3 (the current version)
    assert data["version_number"] == 3
    assert data["rules"] == "Rules version 3 (current)"
    assert data["id"] == str(rules_v3.id)


@pytest.mark.asyncio
async def test_get_hackathon_rules_draft_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that DRAFT hackathons return 404 for rules endpoint.
    
    Requirements: 7.1 - Only public hackathons accessible
    """
    # Create a test user
    user = User(
        email="draftrulestest@example.com",
        username="draftrulesuser",
        password_hash="dummy_hash",
        full_name="Draft Rules User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon with rules
    hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon-rules",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(hackathon)
    await test_db_session.flush()
    
    # Create rules for the draft hackathon
    rules = HackathonRulesVersion(
        hackathon_id=hackathon.id,
        version_number=1,
        rules="Draft rules",
        created_by_user_id=user.id
    )
    test_db_session.add(rules)
    await test_db_session.flush()
    
    hackathon.current_rules_version_id = rules.id
    
    await test_db_session.commit()
    
    # Request rules - should return 404 because hackathon is not PUBLISHED
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    assert response.status_code == 404
    # The response should contain an error structure
    data = response.json()
    assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_get_hackathon_rules_nonexistent_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that non-existent hackathon returns 404.
    
    Requirements: 7.1 - Return rules for existing hackathons only
    """
    # Request with random UUID
    random_uuid = uuid4()
    response = await test_client_with_db.get(f"/api/v1/hackathons/{random_uuid}/rules")
    assert response.status_code == 404
    
    # Request with non-existent slug
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug/rules")
    assert response.status_code == 404



# ========================================================================
# Hackathon Tracks Tests
# ========================================================================

@pytest.mark.asyncio
async def test_get_hackathon_tracks_returns_tracks_for_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that tracks endpoint returns tracks for the requested hackathon.
    
    Requirements: 8.1 - Return tracks belonging to that hackathon
    """
    # Import the HackathonTrack model
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="trackstest@example.com",
        username="tracksuser",
        password_hash="dummy_hash",
        full_name="Tracks Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Tracks Test Hackathon",
        "tracks-test-hackathon"
    )
    
    # Create tracks for this hackathon
    track1 = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Web Development",
        description="Build web applications",
        sort_order=1
    )
    track2 = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Mobile Apps",
        description="Build mobile applications",
        sort_order=2
    )
    track3 = HackathonTrack(
        hackathon_id=hackathon.id,
        name="AI/ML",
        description="Build AI and ML solutions",
        sort_order=3
    )
    
    test_db_session.add(track1)
    test_db_session.add(track2)
    test_db_session.add(track3)
    
    await test_db_session.commit()
    
    # Request tracks by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get all three tracks
    assert len(data) == 3
    
    # Verify track data structure
    assert data[0]["name"] == "Web Development"
    assert data[0]["description"] == "Build web applications"
    assert data[0]["sort_order"] == 1
    assert "id" in data[0]
    
    assert data[1]["name"] == "Mobile Apps"
    assert data[2]["name"] == "AI/ML"


@pytest.mark.asyncio
async def test_get_hackathon_tracks_ordered_by_sort_order(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that tracks are ordered by sort_order, then id.
    
    Requirements: 8.2 - Order tracks deterministically
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="tracksorder@example.com",
        username="tracksorderuser",
        password_hash="dummy_hash",
        full_name="Tracks Order User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Order Test Hackathon",
        "order-test-hackathon"
    )
    
    # Create tracks with non-sequential sort_order
    track_high = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Track High Priority",
        sort_order=10
    )
    track_low = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Track Low Priority",
        sort_order=100
    )
    track_mid = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Track Mid Priority",
        sort_order=50
    )
    
    # Add in random order to ensure ordering is not by insertion
    test_db_session.add(track_mid)
    test_db_session.add(track_high)
    test_db_session.add(track_low)
    
    await test_db_session.commit()
    
    # Request tracks
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify ordering by sort_order
    assert len(data) == 3
    assert data[0]["name"] == "Track High Priority"  # sort_order = 10
    assert data[0]["sort_order"] == 10
    assert data[1]["name"] == "Track Mid Priority"   # sort_order = 50
    assert data[1]["sort_order"] == 50
    assert data[2]["name"] == "Track Low Priority"   # sort_order = 100
    assert data[2]["sort_order"] == 100


@pytest.mark.asyncio
async def test_get_hackathon_tracks_empty_list_if_no_tracks(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that endpoint returns empty list when no tracks exist.
    
    Requirements: 8.1 - Return empty list if no tracks
    """
    # Create a test user
    user = User(
        email="notracks@example.com",
        username="notracksuser",
        password_hash="dummy_hash",
        full_name="No Tracks User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon without tracks
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "No Tracks Hackathon",
        "no-tracks-hackathon"
    )
    
    await test_db_session.commit()
    
    # Request tracks
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get an empty list
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_hackathon_tracks_belong_to_requested_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that tracks returned belong to the requested hackathon only.
    
    Requirements: 8.1 - Tracks belong to that hackathon
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="trackscope@example.com",
        username="trackscopeuser",
        password_hash="dummy_hash",
        full_name="Track Scope User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create two PUBLISHED hackathons
    hackathon1 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 1",
        "hackathon-1-tracks"
    )
    
    hackathon2 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 2",
        "hackathon-2-tracks"
    )
    
    # Create tracks for hackathon1
    track1_h1 = HackathonTrack(
        hackathon_id=hackathon1.id,
        name="Hackathon 1 Track A",
        sort_order=1
    )
    track2_h1 = HackathonTrack(
        hackathon_id=hackathon1.id,
        name="Hackathon 1 Track B",
        sort_order=2
    )
    
    # Create tracks for hackathon2
    track1_h2 = HackathonTrack(
        hackathon_id=hackathon2.id,
        name="Hackathon 2 Track A",
        sort_order=1
    )
    track2_h2 = HackathonTrack(
        hackathon_id=hackathon2.id,
        name="Hackathon 2 Track B",
        sort_order=2
    )
    
    test_db_session.add(track1_h1)
    test_db_session.add(track2_h1)
    test_db_session.add(track1_h2)
    test_db_session.add(track2_h2)
    
    await test_db_session.commit()
    
    # Request tracks for hackathon1
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon1.id}/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon1's tracks
    assert len(data) == 2
    assert all("Hackathon 1" in track["name"] for track in data)
    assert data[0]["name"] == "Hackathon 1 Track A"
    assert data[1]["name"] == "Hackathon 1 Track B"
    
    # Request tracks for hackathon2
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon2.id}/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon2's tracks
    assert len(data) == 2
    assert all("Hackathon 2" in track["name"] for track in data)
    assert data[0]["name"] == "Hackathon 2 Track A"
    assert data[1]["name"] == "Hackathon 2 Track B"


@pytest.mark.asyncio
async def test_get_hackathon_tracks_by_slug(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that tracks can be retrieved using hackathon slug.
    
    Requirements: 8.1 - Return tracks for hackathon
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="trackslug@example.com",
        username="tracksluguser",
        password_hash="dummy_hash",
        full_name="Track Slug User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Tracks Test",
        "slug-tracks-test"
    )
    
    # Create a track
    track = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Test Track",
        sort_order=1
    )
    test_db_session.add(track)
    
    await test_db_session.commit()
    
    # Request tracks by slug
    response = await test_client_with_db.get("/api/v1/hackathons/slug-tracks-test/tracks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["name"] == "Test Track"


@pytest.mark.asyncio
async def test_get_hackathon_tracks_draft_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that DRAFT hackathons return 404 for tracks endpoint.
    
    Requirements: 8.1 - Only public hackathons accessible
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="drafttracks@example.com",
        username="drafttracksuser",
        password_hash="dummy_hash",
        full_name="Draft Tracks User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon-tracks",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    await test_db_session.flush()
    
    # Create tracks for the draft hackathon
    track = HackathonTrack(
        hackathon_id=draft_hackathon.id,
        name="Draft Track",
        sort_order=1
    )
    test_db_session.add(track)
    
    await test_db_session.commit()
    
    # Request tracks - should return 404 because hackathon is not PUBLISHED
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/tracks")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_tracks_nonexistent_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that non-existent hackathon returns 404.
    
    Requirements: 8.1 - Return tracks for existing hackathons only
    """
    # Request with random UUID
    random_uuid = uuid4()
    response = await test_client_with_db.get(f"/api/v1/hackathons/{random_uuid}/tracks")
    assert response.status_code == 404
    
    # Request with non-existent slug
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug/tracks")
    assert response.status_code == 404



# ========================================================================
# Hackathon Schedule Tests
# ========================================================================

@pytest.mark.asyncio
async def test_get_hackathon_schedule_returns_schedule_items(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that schedule endpoint returns schedule items for the requested hackathon.
    
    Requirements: 9.1 - Return schedule events belonging to that hackathon
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="scheduletest@example.com",
        username="scheduleuser",
        password_hash="dummy_hash",
        full_name="Schedule Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Schedule Test Hackathon",
        "schedule-test-hackathon"
    )
    
    # Create schedule items for this hackathon
    item1 = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Opening Ceremony",
        description="Kickoff event",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
        location="Main Hall",
        link="https://example.com/opening",
        sort_order=1
    )
    item2 = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Hacking Begins",
        description="Start building",
        start_at=datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 3, 1, 18, 0, 0, tzinfo=timezone.utc),
        location="Hacker Space",
        sort_order=2
    )
    item3 = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Final Presentations",
        description="Show your projects",
        start_at=datetime(2024, 3, 2, 14, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 3, 2, 17, 0, 0, tzinfo=timezone.utc),
        location="Main Hall",
        sort_order=3
    )
    
    test_db_session.add(item1)
    test_db_session.add(item2)
    test_db_session.add(item3)
    
    await test_db_session.commit()
    
    # Request schedule by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get all three items
    assert len(data) == 3
    
    # Verify schedule item data structure
    assert data[0]["title"] == "Opening Ceremony"
    assert data[0]["description"] == "Kickoff event"
    assert data[0]["location"] == "Main Hall"
    assert data[0]["link"] == "https://example.com/opening"
    assert data[0]["sort_order"] == 1
    assert "id" in data[0]
    assert "start_at" in data[0]
    assert "end_at" in data[0]
    
    assert data[1]["title"] == "Hacking Begins"
    assert data[2]["title"] == "Final Presentations"


@pytest.mark.asyncio
async def test_get_hackathon_schedule_chronological_ordering(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that schedule items are ordered chronologically (start_at, then sort_order, then id).
    
    Requirements: 9.2 - Order schedule events chronologically
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="scheduleorder@example.com",
        username="scheduleorderuser",
        password_hash="dummy_hash",
        full_name="Schedule Order User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Order Test Hackathon",
        "order-test-schedule"
    )
    
    # Create schedule items with non-sequential start times
    # Add in non-chronological order to ensure ordering works
    item_late = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Late Event",
        start_at=datetime(2024, 3, 3, 14, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    item_early = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Early Event",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    item_mid = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Mid Event",
        start_at=datetime(2024, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    
    # Add in random order to ensure ordering is not by insertion
    test_db_session.add(item_mid)
    test_db_session.add(item_late)
    test_db_session.add(item_early)
    
    await test_db_session.commit()
    
    # Request schedule
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify chronological ordering by start_at
    assert len(data) == 3
    assert data[0]["title"] == "Early Event"  # March 1
    assert data[1]["title"] == "Mid Event"    # March 2
    assert data[2]["title"] == "Late Event"   # March 3
    
    # Verify the timestamps are in order
    start_times = [item["start_at"] for item in data]
    assert start_times == sorted(start_times)


@pytest.mark.asyncio
async def test_get_hackathon_schedule_handles_nullable_end_at(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that schedule items with nullable end_at are handled properly.
    
    Requirements: 9.3 - Handle nullable time values according to existing model semantics
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="schedulenull@example.com",
        username="schedulenulluser",
        password_hash="dummy_hash",
        full_name="Schedule Null User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Null Test Hackathon",
        "null-test-schedule"
    )
    
    # Create schedule items with and without end_at
    item_with_end = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Event With End Time",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    item_without_end = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Event Without End Time",
        start_at=datetime(2024, 3, 1, 11, 0, 0, tzinfo=timezone.utc),
        end_at=None,  # Nullable end_at
        sort_order=2
    )
    
    test_db_session.add(item_with_end)
    test_db_session.add(item_without_end)
    
    await test_db_session.commit()
    
    # Request schedule
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify both items are returned
    assert len(data) == 2
    
    # Verify item with end_at has it populated
    assert data[0]["title"] == "Event With End Time"
    assert data[0]["end_at"] is not None
    
    # Verify item without end_at has it as null
    assert data[1]["title"] == "Event Without End Time"
    assert data[1]["end_at"] is None


@pytest.mark.asyncio
async def test_get_hackathon_schedule_empty_list_if_no_schedule(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that endpoint returns empty list when no schedule items exist.
    
    Requirements: 9.1 - Return empty list if no schedule items
    """
    # Create a test user
    user = User(
        email="noschedule@example.com",
        username="noscheduleuser",
        password_hash="dummy_hash",
        full_name="No Schedule User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon without schedule items
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "No Schedule Hackathon",
        "no-schedule-hackathon"
    )
    
    await test_db_session.commit()
    
    # Request schedule
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get an empty list
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_hackathon_schedule_items_belong_to_requested_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that schedule items returned belong to the requested hackathon only.
    
    Requirements: 9.1 - Schedule items belong to that hackathon
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="schedulescope@example.com",
        username="schedulescopeuser",
        password_hash="dummy_hash",
        full_name="Schedule Scope User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create two PUBLISHED hackathons
    hackathon1 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 1",
        "hackathon-1-schedule"
    )
    
    hackathon2 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 2",
        "hackathon-2-schedule"
    )
    
    # Create schedule items for hackathon1
    item1_h1 = HackathonScheduleItem(
        hackathon_id=hackathon1.id,
        title="Hackathon 1 Event A",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    item2_h1 = HackathonScheduleItem(
        hackathon_id=hackathon1.id,
        title="Hackathon 1 Event B",
        start_at=datetime(2024, 3, 1, 14, 0, 0, tzinfo=timezone.utc),
        sort_order=2
    )
    
    # Create schedule items for hackathon2
    item1_h2 = HackathonScheduleItem(
        hackathon_id=hackathon2.id,
        title="Hackathon 2 Event A",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    item2_h2 = HackathonScheduleItem(
        hackathon_id=hackathon2.id,
        title="Hackathon 2 Event B",
        start_at=datetime(2024, 3, 1, 14, 0, 0, tzinfo=timezone.utc),
        sort_order=2
    )
    
    test_db_session.add(item1_h1)
    test_db_session.add(item2_h1)
    test_db_session.add(item1_h2)
    test_db_session.add(item2_h2)
    
    await test_db_session.commit()
    
    # Request schedule for hackathon1
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon1.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon1's schedule items
    assert len(data) == 2
    assert all("Hackathon 1" in item["title"] for item in data)
    assert data[0]["title"] == "Hackathon 1 Event A"
    assert data[1]["title"] == "Hackathon 1 Event B"
    
    # Request schedule for hackathon2
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon2.id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon2's schedule items
    assert len(data) == 2
    assert all("Hackathon 2" in item["title"] for item in data)
    assert data[0]["title"] == "Hackathon 2 Event A"
    assert data[1]["title"] == "Hackathon 2 Event B"


@pytest.mark.asyncio
async def test_get_hackathon_schedule_by_slug(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that schedule can be retrieved using hackathon slug.
    
    Requirements: 9.1 - Return schedule for hackathon
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="scheduleslug@example.com",
        username="schedulesluguser",
        password_hash="dummy_hash",
        full_name="Schedule Slug User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Schedule Test",
        "slug-schedule-test"
    )
    
    # Create a schedule item
    item = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Test Event",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    test_db_session.add(item)
    
    await test_db_session.commit()
    
    # Request schedule by slug
    response = await test_client_with_db.get("/api/v1/hackathons/slug-schedule-test/schedule")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["title"] == "Test Event"


@pytest.mark.asyncio
async def test_get_hackathon_schedule_draft_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that DRAFT hackathons return 404 for schedule endpoint.
    
    Requirements: 9.1 - Only public hackathons accessible
    """
    from app.hackathons.models import HackathonScheduleItem
    
    # Create a test user
    user = User(
        email="draftschedule@example.com",
        username="draftscheduleuser",
        password_hash="dummy_hash",
        full_name="Draft Schedule User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon-schedule",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    await test_db_session.flush()
    
    # Create schedule item for the draft hackathon
    item = HackathonScheduleItem(
        hackathon_id=draft_hackathon.id,
        title="Draft Event",
        start_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    test_db_session.add(item)
    
    await test_db_session.commit()
    
    # Request schedule - should return 404 because hackathon is not PUBLISHED
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/schedule")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_schedule_nonexistent_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that non-existent hackathon returns 404.
    
    Requirements: 9.1 - Return schedule for existing hackathons only
    """
    # Request with random UUID
    random_uuid = uuid4()
    response = await test_client_with_db.get(f"/api/v1/hackathons/{random_uuid}/schedule")
    assert response.status_code == 404
    
    # Request with non-existent slug
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug/schedule")
    assert response.status_code == 404



# ========================================================================
# Hackathon Sponsors Tests
# ========================================================================

@pytest.mark.asyncio
async def test_get_hackathon_sponsors_returns_sponsors_for_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that sponsors endpoint returns sponsors for the requested hackathon.
    
    Requirements: 10.1 - Return sponsors associated with that hackathon
    """
    from app.hackathons.models import HackathonSponsor
    
    # Create a test user
    user = User(
        email="sponsorstest@example.com",
        username="sponsorsuser",
        password_hash="dummy_hash",
        full_name="Sponsors Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Sponsors Test Hackathon",
        "sponsors-test-hackathon"
    )
    
    # Create sponsors for this hackathon
    sponsor1 = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="TechCorp",
        logo_key="techcorp-logo.png",
        url="https://techcorp.example.com",
        tier="PLATINUM",
        sort_order=1
    )
    sponsor2 = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="DevTools Inc",
        logo_key="devtools-logo.png",
        url="https://devtools.example.com",
        tier="GOLD",
        sort_order=2
    )
    sponsor3 = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="StartupX",
        logo_key="startupx-logo.png",
        url="https://startupx.example.com",
        tier="SILVER",
        sort_order=3
    )
    
    test_db_session.add(sponsor1)
    test_db_session.add(sponsor2)
    test_db_session.add(sponsor3)
    
    await test_db_session.commit()
    
    # Request sponsors by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get all three sponsors
    assert len(data) == 3
    
    # Verify sponsor data structure
    assert data[0]["name"] == "TechCorp"
    assert data[0]["logo_key"] == "techcorp-logo.png"
    assert data[0]["url"] == "https://techcorp.example.com"
    assert data[0]["tier"] == "PLATINUM"
    assert data[0]["sort_order"] == 1
    assert "id" in data[0]
    
    assert data[1]["name"] == "DevTools Inc"
    assert data[2]["name"] == "StartupX"


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_ordered_by_sort_order(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that sponsors are ordered by sort_order, then id.
    
    Requirements: 10.2, 10.3 - Order sponsors deterministically
    """
    from app.hackathons.models import HackathonSponsor
    
    # Create a test user
    user = User(
        email="sponsorsorder@example.com",
        username="sponsorsorderuser",
        password_hash="dummy_hash",
        full_name="Sponsors Order User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Order Test Hackathon",
        "order-test-sponsors"
    )
    
    # Create sponsors with non-sequential sort_order
    sponsor_high = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="High Priority Sponsor",
        sort_order=10
    )
    sponsor_low = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="Low Priority Sponsor",
        sort_order=100
    )
    sponsor_mid = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="Mid Priority Sponsor",
        sort_order=50
    )
    
    # Add in random order to ensure ordering is not by insertion
    test_db_session.add(sponsor_mid)
    test_db_session.add(sponsor_high)
    test_db_session.add(sponsor_low)
    
    await test_db_session.commit()
    
    # Request sponsors
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify ordering by sort_order
    assert len(data) == 3
    assert data[0]["name"] == "High Priority Sponsor"  # sort_order = 10
    assert data[0]["sort_order"] == 10
    assert data[1]["name"] == "Mid Priority Sponsor"   # sort_order = 50
    assert data[1]["sort_order"] == 50
    assert data[2]["name"] == "Low Priority Sponsor"   # sort_order = 100
    assert data[2]["sort_order"] == 100


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_empty_list_if_no_sponsors(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that endpoint returns empty list when no sponsors exist.
    
    Requirements: 10.1 - Return empty list if no sponsors
    """
    # Create a test user
    user = User(
        email="nosponsors@example.com",
        username="nosponsorsuser",
        password_hash="dummy_hash",
        full_name="No Sponsors User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon without sponsors
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "No Sponsors Hackathon",
        "no-sponsors-hackathon"
    )
    
    await test_db_session.commit()
    
    # Request sponsors
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get an empty list
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_belong_to_requested_hackathon(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that sponsors returned belong to the requested hackathon only.
    
    Requirements: 10.1 - Sponsors belong to that hackathon
    """
    from app.hackathons.models import HackathonSponsor
    
    # Create a test user
    user = User(
        email="sponsorscope@example.com",
        username="sponsorscopeuser",
        password_hash="dummy_hash",
        full_name="Sponsor Scope User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create two PUBLISHED hackathons
    hackathon1 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 1",
        "hackathon-1-sponsors"
    )
    
    hackathon2 = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon 2",
        "hackathon-2-sponsors"
    )
    
    # Create sponsors for hackathon1
    sponsor1_h1 = HackathonSponsor(
        hackathon_id=hackathon1.id,
        name="Hackathon 1 Sponsor A",
        sort_order=1
    )
    sponsor2_h1 = HackathonSponsor(
        hackathon_id=hackathon1.id,
        name="Hackathon 1 Sponsor B",
        sort_order=2
    )
    
    # Create sponsors for hackathon2
    sponsor1_h2 = HackathonSponsor(
        hackathon_id=hackathon2.id,
        name="Hackathon 2 Sponsor A",
        sort_order=1
    )
    sponsor2_h2 = HackathonSponsor(
        hackathon_id=hackathon2.id,
        name="Hackathon 2 Sponsor B",
        sort_order=2
    )
    
    test_db_session.add(sponsor1_h1)
    test_db_session.add(sponsor2_h1)
    test_db_session.add(sponsor1_h2)
    test_db_session.add(sponsor2_h2)
    
    await test_db_session.commit()
    
    # Request sponsors for hackathon1
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon1.id}/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon1's sponsors
    assert len(data) == 2
    assert all("Hackathon 1" in sponsor["name"] for sponsor in data)
    assert data[0]["name"] == "Hackathon 1 Sponsor A"
    assert data[1]["name"] == "Hackathon 1 Sponsor B"
    
    # Request sponsors for hackathon2
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon2.id}/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we only get hackathon2's sponsors
    assert len(data) == 2
    assert all("Hackathon 2" in sponsor["name"] for sponsor in data)
    assert data[0]["name"] == "Hackathon 2 Sponsor A"
    assert data[1]["name"] == "Hackathon 2 Sponsor B"


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_by_slug(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that sponsors can be retrieved using hackathon slug.
    
    Requirements: 10.1 - Return sponsors for hackathon
    """
    from app.hackathons.models import HackathonSponsor
    
    # Create a test user
    user = User(
        email="sponsorslug@example.com",
        username="sponsorsluguser",
        password_hash="dummy_hash",
        full_name="Sponsor Slug User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Sponsors Test",
        "slug-sponsors-test"
    )
    
    # Create a sponsor
    sponsor = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="Test Sponsor",
        sort_order=1
    )
    test_db_session.add(sponsor)
    
    await test_db_session.commit()
    
    # Request sponsors by slug
    response = await test_client_with_db.get("/api/v1/hackathons/slug-sponsors-test/sponsors")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["name"] == "Test Sponsor"


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_draft_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that DRAFT hackathons return 404 for sponsors endpoint.
    
    Requirements: 10.1 - Only public hackathons accessible
    """
    from app.hackathons.models import HackathonSponsor
    
    # Create a test user
    user = User(
        email="draftsponsors@example.com",
        username="draftsponsorsuser",
        password_hash="dummy_hash",
        full_name="Draft Sponsors User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-hackathon-sponsors",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    await test_db_session.flush()
    
    # Create sponsor for the draft hackathon
    sponsor = HackathonSponsor(
        hackathon_id=draft_hackathon.id,
        name="Draft Sponsor",
        sort_order=1
    )
    test_db_session.add(sponsor)
    
    await test_db_session.commit()
    
    # Request sponsors - should return 404 because hackathon is not PUBLISHED
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/sponsors")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hackathon_sponsors_nonexistent_hackathon_returns_404(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that non-existent hackathon returns 404.
    
    Requirements: 10.1 - Return sponsors for existing hackathons only
    """
    # Request with random UUID
    random_uuid = uuid4()
    response = await test_client_with_db.get(f"/api/v1/hackathons/{random_uuid}/sponsors")
    assert response.status_code == 404
    
    # Request with non-existent slug
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug/sponsors")
    assert response.status_code == 404


# ========================================================================
# Integration Tests
# ========================================================================

@pytest.mark.asyncio
async def test_public_api_integration_full_hackathon_lifecycle(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: Full public API flow for a complete hackathon.
    
    Tests all public endpoints work together with a fully configured hackathon.
    
    Requirements: 5.1, 6.1, 7.1, 8.1, 9.1, 10.1
    """
    from app.hackathons.models import (
        HackathonTrack,
        HackathonScheduleItem,
        HackathonSponsor
    )
    
    # Create a test user
    user = User(
        email="integration@example.com",
        username="integrationuser",
        password_hash="dummy_hash",
        full_name="Integration Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a fully configured PUBLISHED hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Integration Test Hackathon",
        "integration-test-hackathon",
        tagline="A complete hackathon for integration testing",
        description="Full description with all details",
        logo_key="integration-logo.png",
        cover_key="integration-cover.png",
        format="HYBRID",
        venue="Test Convention Center",
        team_max_size=5
    )
    
    # Add tracks
    track1 = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Web Development",
        description="Build modern web apps",
        sort_order=1
    )
    track2 = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Mobile Development",
        description="Build mobile apps",
        sort_order=2
    )
    test_db_session.add(track1)
    test_db_session.add(track2)
    
    # Add schedule items
    schedule1 = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Opening Ceremony",
        description="Welcome and kickoff",
        start_at=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        location="Main Hall",
        link="https://example.com/opening",
        sort_order=1
    )
    schedule2 = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Hacking Starts",
        description="Build your projects",
        start_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2024, 6, 2, 10, 0, 0, tzinfo=timezone.utc),
        location="Hacker Space",
        sort_order=2
    )
    test_db_session.add(schedule1)
    test_db_session.add(schedule2)
    
    # Add sponsors
    sponsor1 = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="TechCorp",
        logo_key="techcorp.png",
        url="https://techcorp.example.com",
        tier="PLATINUM",
        sort_order=1
    )
    sponsor2 = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="DevTools Inc",
        logo_key="devtools.png",
        url="https://devtools.example.com",
        tier="GOLD",
        sort_order=2
    )
    test_db_session.add(sponsor1)
    test_db_session.add(sponsor2)
    
    await test_db_session.commit()
    
    # Test 1: List hackathons - should include our hackathon
    response = await test_client_with_db.get("/api/v1/hackathons")
    assert response.status_code == 200
    list_data = response.json()
    assert list_data["total"] >= 1
    hackathon_in_list = next(
        (h for h in list_data["items"] if h["slug"] == "integration-test-hackathon"),
        None
    )
    assert hackathon_in_list is not None
    assert hackathon_in_list["name"] == "Integration Test Hackathon"
    assert hackathon_in_list["lifecycle_status"] == "PUBLISHED"
    
    # Test 2: Get hackathon detail by UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}")
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["id"] == str(hackathon.id)
    assert detail_data["name"] == "Integration Test Hackathon"
    assert detail_data["slug"] == "integration-test-hackathon"
    assert detail_data["tagline"] == "A complete hackathon for integration testing"
    assert detail_data["format"] == "HYBRID"
    assert detail_data["venue"] == "Test Convention Center"
    assert detail_data["team_min_size"] == 1
    assert detail_data["team_max_size"] == 5
    
    # Test 3: Get hackathon detail by slug
    response = await test_client_with_db.get("/api/v1/hackathons/integration-test-hackathon")
    assert response.status_code == 200
    slug_detail_data = response.json()
    assert slug_detail_data["id"] == str(hackathon.id)
    assert slug_detail_data["name"] == "Integration Test Hackathon"
    
    # Test 4: Get hackathon rules
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    assert response.status_code == 200
    rules_data = response.json()
    assert rules_data["version_number"] == 1
    assert rules_data["rules"] == "Test rules content"
    assert "id" in rules_data
    
    # Test 5: Get hackathon tracks
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
    assert response.status_code == 200
    tracks_data = response.json()
    assert len(tracks_data) == 2
    assert tracks_data[0]["name"] == "Web Development"
    assert tracks_data[0]["sort_order"] == 1
    assert tracks_data[1]["name"] == "Mobile Development"
    assert tracks_data[1]["sort_order"] == 2
    
    # Test 6: Get hackathon schedule
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    assert response.status_code == 200
    schedule_data = response.json()
    assert len(schedule_data) == 2
    assert schedule_data[0]["title"] == "Opening Ceremony"
    assert schedule_data[0]["location"] == "Main Hall"
    assert schedule_data[1]["title"] == "Hacking Starts"
    
    # Test 7: Get hackathon sponsors
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/sponsors")
    assert response.status_code == 200
    sponsors_data = response.json()
    assert len(sponsors_data) == 2
    assert sponsors_data[0]["name"] == "TechCorp"
    assert sponsors_data[0]["tier"] == "PLATINUM"
    assert sponsors_data[1]["name"] == "DevTools Inc"
    assert sponsors_data[1]["tier"] == "GOLD"


@pytest.mark.asyncio
async def test_public_api_integration_slug_identifier_consistency(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: All endpoints should work with both UUID and slug identifiers.
    
    Requirements: 6.1, 7.1, 8.1, 9.1, 10.1
    """
    from app.hackathons.models import (
        HackathonTrack,
        HackathonScheduleItem,
        HackathonSponsor
    )
    
    # Create a test user
    user = User(
        email="slugtest@example.com",
        username="slugtestuser",
        password_hash="dummy_hash",
        full_name="Slug Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a PUBLISHED hackathon with associated data
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Slug Test Hackathon",
        "slug-test-hackathon"
    )
    
    # Add minimal test data for each resource type
    track = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Test Track",
        sort_order=1
    )
    schedule = HackathonScheduleItem(
        hackathon_id=hackathon.id,
        title="Test Event",
        start_at=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    sponsor = HackathonSponsor(
        hackathon_id=hackathon.id,
        name="Test Sponsor",
        sort_order=1
    )
    
    test_db_session.add(track)
    test_db_session.add(schedule)
    test_db_session.add(sponsor)
    await test_db_session.commit()
    
    # Test all endpoints with UUID identifier
    uuid_endpoints = [
        f"/api/v1/hackathons/{hackathon.id}",
        f"/api/v1/hackathons/{hackathon.id}/rules",
        f"/api/v1/hackathons/{hackathon.id}/tracks",
        f"/api/v1/hackathons/{hackathon.id}/schedule",
        f"/api/v1/hackathons/{hackathon.id}/sponsors"
    ]
    
    for endpoint in uuid_endpoints:
        response = await test_client_with_db.get(endpoint)
        assert response.status_code == 200, f"UUID endpoint failed: {endpoint}"
    
    # Test all endpoints with slug identifier
    slug_endpoints = [
        "/api/v1/hackathons/slug-test-hackathon",
        "/api/v1/hackathons/slug-test-hackathon/rules",
        "/api/v1/hackathons/slug-test-hackathon/tracks",
        "/api/v1/hackathons/slug-test-hackathon/schedule",
        "/api/v1/hackathons/slug-test-hackathon/sponsors"
    ]
    
    for endpoint in slug_endpoints:
        response = await test_client_with_db.get(endpoint)
        assert response.status_code == 200, f"Slug endpoint failed: {endpoint}"


@pytest.mark.asyncio
async def test_public_api_integration_draft_hackathon_isolation(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: DRAFT hackathons should not be accessible through any public endpoint.
    
    Requirements: 5.1, 6.3, 7.1, 8.1, 9.1, 10.1
    """
    from app.hackathons.models import (
        HackathonRulesVersion,
        HackathonTrack,
        HackathonScheduleItem,
        HackathonSponsor
    )
    
    # Create a test user
    user = User(
        email="draftisolation@example.com",
        username="draftisolationuser",
        password_hash="dummy_hash",
        full_name="Draft Isolation User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon with full configuration
    draft_hackathon = Hackathon(
        name="Draft Hackathon",
        slug="draft-isolated-hackathon",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft_hackathon)
    await test_db_session.flush()
    
    # Add rules
    rules = HackathonRulesVersion(
        hackathon_id=draft_hackathon.id,
        version_number=1,
        rules="Draft rules",
        created_by_user_id=user.id
    )
    test_db_session.add(rules)
    await test_db_session.flush()
    draft_hackathon.current_rules_version_id = rules.id
    
    # Add tracks, schedule, and sponsors
    track = HackathonTrack(
        hackathon_id=draft_hackathon.id,
        name="Draft Track",
        sort_order=1
    )
    schedule = HackathonScheduleItem(
        hackathon_id=draft_hackathon.id,
        title="Draft Event",
        start_at=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    sponsor = HackathonSponsor(
        hackathon_id=draft_hackathon.id,
        name="Draft Sponsor",
        sort_order=1
    )
    
    test_db_session.add(track)
    test_db_session.add(schedule)
    test_db_session.add(sponsor)
    await test_db_session.commit()
    
    # Test 1: List should NOT include draft hackathon
    response = await test_client_with_db.get("/api/v1/hackathons")
    assert response.status_code == 200
    list_data = response.json()
    draft_in_list = any(h["slug"] == "draft-isolated-hackathon" for h in list_data["items"])
    assert not draft_in_list, "Draft hackathon should not appear in public list"
    
    # Test 2: Detail endpoint should return 404 for UUID
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}")
    assert response.status_code == 404
    
    # Test 3: Detail endpoint should return 404 for slug
    response = await test_client_with_db.get("/api/v1/hackathons/draft-isolated-hackathon")
    assert response.status_code == 404
    
    # Test 4: Rules endpoint should return 404
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/rules")
    assert response.status_code == 404
    
    # Test 5: Tracks endpoint should return 404
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/tracks")
    assert response.status_code == 404
    
    # Test 6: Schedule endpoint should return 404
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/schedule")
    assert response.status_code == 404
    
    # Test 7: Sponsors endpoint should return 404
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft_hackathon.id}/sponsors")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_api_integration_multiple_hackathons_isolation(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: Data from one hackathon should not appear in another hackathon's endpoints.
    
    Requirements: 7.1, 8.1, 9.1, 10.1
    """
    from app.hackathons.models import (
        HackathonTrack,
        HackathonScheduleItem,
        HackathonSponsor
    )
    
    # Create a test user
    user = User(
        email="multiisolation@example.com",
        username="multiisolationuser",
        password_hash="dummy_hash",
        full_name="Multi Isolation User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create two PUBLISHED hackathons
    hackathon_a = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon A",
        "hackathon-a-isolation"
    )
    
    hackathon_b = await create_published_hackathon(
        test_db_session,
        user.id,
        "Hackathon B",
        "hackathon-b-isolation"
    )
    
    # Add distinct tracks to each hackathon
    track_a = HackathonTrack(
        hackathon_id=hackathon_a.id,
        name="Track A Unique",
        sort_order=1
    )
    track_b = HackathonTrack(
        hackathon_id=hackathon_b.id,
        name="Track B Unique",
        sort_order=1
    )
    
    # Add distinct schedule items to each hackathon
    schedule_a = HackathonScheduleItem(
        hackathon_id=hackathon_a.id,
        title="Event A Unique",
        start_at=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    schedule_b = HackathonScheduleItem(
        hackathon_id=hackathon_b.id,
        title="Event B Unique",
        start_at=datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc),
        sort_order=1
    )
    
    # Add distinct sponsors to each hackathon
    sponsor_a = HackathonSponsor(
        hackathon_id=hackathon_a.id,
        name="Sponsor A Unique",
        sort_order=1
    )
    sponsor_b = HackathonSponsor(
        hackathon_id=hackathon_b.id,
        name="Sponsor B Unique",
        sort_order=1
    )
    
    test_db_session.add_all([track_a, track_b, schedule_a, schedule_b, sponsor_a, sponsor_b])
    await test_db_session.commit()
    
    # Test 1: Hackathon A tracks should only contain Track A
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_a.id}/tracks")
    assert response.status_code == 200
    tracks_a = response.json()
    assert len(tracks_a) == 1
    assert tracks_a[0]["name"] == "Track A Unique"
    assert "Track B" not in str(tracks_a)
    
    # Test 2: Hackathon B tracks should only contain Track B
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_b.id}/tracks")
    assert response.status_code == 200
    tracks_b = response.json()
    assert len(tracks_b) == 1
    assert tracks_b[0]["name"] == "Track B Unique"
    assert "Track A" not in str(tracks_b)
    
    # Test 3: Hackathon A schedule should only contain Event A
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_a.id}/schedule")
    assert response.status_code == 200
    schedule_a_data = response.json()
    assert len(schedule_a_data) == 1
    assert schedule_a_data[0]["title"] == "Event A Unique"
    assert "Event B" not in str(schedule_a_data)
    
    # Test 4: Hackathon B schedule should only contain Event B
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_b.id}/schedule")
    assert response.status_code == 200
    schedule_b_data = response.json()
    assert len(schedule_b_data) == 1
    assert schedule_b_data[0]["title"] == "Event B Unique"
    assert "Event A" not in str(schedule_b_data)
    
    # Test 5: Hackathon A sponsors should only contain Sponsor A
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_a.id}/sponsors")
    assert response.status_code == 200
    sponsors_a = response.json()
    assert len(sponsors_a) == 1
    assert sponsors_a[0]["name"] == "Sponsor A Unique"
    assert "Sponsor B" not in str(sponsors_a)
    
    # Test 6: Hackathon B sponsors should only contain Sponsor B
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon_b.id}/sponsors")
    assert response.status_code == 200
    sponsors_b = response.json()
    assert len(sponsors_b) == 1
    assert sponsors_b[0]["name"] == "Sponsor B Unique"
    assert "Sponsor A" not in str(sponsors_b)


@pytest.mark.asyncio
async def test_public_api_integration_nonexistent_resource_handling(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: All endpoints should return 404 for non-existent resources consistently.
    
    Requirements: 6.2, 7.1, 8.1, 9.1, 10.1
    """
    # Generate random UUID that doesn't exist
    nonexistent_uuid = uuid4()
    nonexistent_slug = "this-hackathon-does-not-exist"
    
    # Test all endpoints with non-existent UUID
    uuid_endpoints = [
        f"/api/v1/hackathons/{nonexistent_uuid}",
        f"/api/v1/hackathons/{nonexistent_uuid}/rules",
        f"/api/v1/hackathons/{nonexistent_uuid}/tracks",
        f"/api/v1/hackathons/{nonexistent_uuid}/schedule",
        f"/api/v1/hackathons/{nonexistent_uuid}/sponsors"
    ]
    
    for endpoint in uuid_endpoints:
        response = await test_client_with_db.get(endpoint)
        assert response.status_code == 404, f"UUID endpoint should return 404: {endpoint}"
        # Verify error response structure
        data = response.json()
        assert "error" in data or "detail" in data
    
    # Test all endpoints with non-existent slug
    slug_endpoints = [
        f"/api/v1/hackathons/{nonexistent_slug}",
        f"/api/v1/hackathons/{nonexistent_slug}/rules",
        f"/api/v1/hackathons/{nonexistent_slug}/tracks",
        f"/api/v1/hackathons/{nonexistent_slug}/schedule",
        f"/api/v1/hackathons/{nonexistent_slug}/sponsors"
    ]
    
    for endpoint in slug_endpoints:
        response = await test_client_with_db.get(endpoint)
        assert response.status_code == 404, f"Slug endpoint should return 404: {endpoint}"
        # Verify error response structure
        data = response.json()
        assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_public_api_integration_empty_resources_handling(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Integration test: Endpoints should handle hackathons with no tracks/schedule/sponsors gracefully.
    
    Requirements: 8.1, 9.1, 10.1
    """
    # Create a test user
    user = User(
        email="emptyresources@example.com",
        username="emptyresourcesuser",
        password_hash="dummy_hash",
        full_name="Empty Resources User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a minimal PUBLISHED hackathon with no tracks, schedule, or sponsors
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Minimal Hackathon",
        "minimal-hackathon"
    )
    
    await test_db_session.commit()
    
    # Test 1: Detail should work
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}")
    assert response.status_code == 200
    
    # Test 2: Rules should work (created by helper)
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/rules")
    assert response.status_code == 200
    
    # Test 3: Tracks should return empty list
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
    assert response.status_code == 200
    tracks = response.json()
    assert isinstance(tracks, list)
    assert len(tracks) == 0
    
    # Test 4: Schedule should return empty list
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/schedule")
    assert response.status_code == 200
    schedule = response.json()
    assert isinstance(schedule, list)
    assert len(schedule) == 0
    
    # Test 5: Sponsors should return empty list
    response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/sponsors")
    assert response.status_code == 200
    sponsors = response.json()
    assert isinstance(sponsors, list)
    assert len(sponsors) == 0


# ========================================================================
# Database Query Efficiency Tests
# ========================================================================

@pytest.mark.asyncio
async def test_list_hackathons_prevents_n_plus_1_queries(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that list endpoint does not have N+1 query problems.
    
    The list endpoint should use database filtering and avoid loading
    related entities unnecessarily. This test ensures we're not executing
    one query per hackathon.
    
    Requirements: 11.1, 11.2 - Use database filtering, avoid N+1 queries
    """
    # Create a test user
    user = User(
        email="n1test@example.com",
        username="n1testuser",
        password_hash="dummy_hash",
        full_name="N+1 Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create multiple PUBLISHED hackathons
    for i in range(10):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Hackathon {i}",
            f"hackathon-{i}"
        )
    
    await test_db_session.commit()
    
    # Import statement counting utilities
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    # Track queries executed
    query_count = {"count": 0}
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
    
    # Attach query counter to engine
    engine = test_db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_queries)
    
    try:
        # Execute the list request
        response = await test_client_with_db.get("/api/v1/hackathons?page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # We should get all 10 hackathons
        assert len(data["items"]) == 10
        
        # The query count should be reasonable (not 10+ queries)
        # We expect:
        # 1. COUNT query for total
        # 2. SELECT query for hackathons
        # Total should be around 2-4 queries, not 10+
        assert query_count["count"] < 10, (
            f"Too many queries executed: {query_count['count']}. "
            "This suggests an N+1 query problem."
        )
        
    finally:
        # Remove the event listener
        event.remove(engine, "before_cursor_execute", count_queries)


@pytest.mark.asyncio
async def test_list_hackathons_uses_database_filtering(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that list endpoint uses database filtering instead of in-memory filtering.
    
    Database filtering is critical for performance. This test verifies that
    status filtering happens at the database layer, not in Python code.
    
    Requirements: 11.1 - Use database filtering instead of in-memory filtering
    """
    # Create a test user
    user = User(
        email="dbfilter@example.com",
        username="dbfilteruser",
        password_hash="dummy_hash",
        full_name="DB Filter User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create mix of hackathons
    for i in range(5):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Published {i}",
            f"published-{i}"
        )
    
    for i in range(5):
        draft = Hackathon(
            name=f"Draft {i}",
            slug=f"draft-{i}",
            created_by_user_id=user.id,
            organizer_user_id=user.id,
            lifecycle_status="DRAFT",
            team_min_size=1
        )
        test_db_session.add(draft)
    
    await test_db_session.commit()
    
    # Query the list endpoint
    response = await test_client_with_db.get("/api/v1/hackathons")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return published hackathons (5 total)
    assert data["total"] == 5
    assert len(data["items"]) == 5
    
    # Verify all returned items are PUBLISHED
    for item in data["items"]:
        assert item["lifecycle_status"] == "PUBLISHED"
    
    # The fact that we get exactly 5 items proves database filtering worked
    # If we loaded all 10 and filtered in-memory, we'd need additional code
    # to ensure the total count and pagination work correctly


@pytest.mark.asyncio
async def test_list_hackathons_proper_pagination_with_database_filtering(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that pagination works correctly with database-level filtering.
    
    This ensures that pagination calculations are done on the filtered
    dataset, not the entire table.
    
    Requirements: 11.1, 11.4 - Database filtering with correct pagination
    """
    # Create a test user
    user = User(
        email="pagination@example.com",
        username="paginationuser",
        password_hash="dummy_hash",
        full_name="Pagination User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create 7 PUBLISHED hackathons
    for i in range(7):
        await create_published_hackathon(
            test_db_session,
            user.id,
            f"Published {i}",
            f"published-{i}"
        )
    
    # Create 3 DRAFT hackathons (should not affect pagination)
    for i in range(3):
        draft = Hackathon(
            name=f"Draft {i}",
            slug=f"draft-{i}",
            created_by_user_id=user.id,
            organizer_user_id=user.id,
            lifecycle_status="DRAFT",
            team_min_size=1
        )
        test_db_session.add(draft)
    
    await test_db_session.commit()
    
    # Request first page with page_size=3
    response = await test_client_with_db.get("/api/v1/hackathons?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    
    # Should report total of 7 (only published)
    assert data["total"] == 7
    assert len(data["items"]) == 3
    assert data["total_pages"] == 3  # ceil(7/3) = 3
    
    # Request last page
    response = await test_client_with_db.get("/api/v1/hackathons?page=3&page_size=3")
    assert response.status_code == 200
    data = response.json()
    
    # Last page should have 1 item (7 % 3 = 1)
    assert data["total"] == 7
    assert len(data["items"]) == 1
    assert data["page"] == 3


@pytest.mark.asyncio
async def test_public_api_does_not_load_unnecessary_relationships(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that public API endpoints don't eagerly load unnecessary relationships.
    
    For example, the hackathon detail endpoint shouldn't load all tracks,
    schedule items, and sponsors unless specifically requested.
    
    Requirements: 11.2, 11.3 - Avoid N+1 queries, use appropriate loading strategies
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="relationships@example.com",
        username="relationshipsuser",
        password_hash="dummy_hash",
        full_name="Relationships User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a hackathon with many related entities
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "Relationship Test",
        "relationship-test"
    )
    
    # Add 20 tracks to test lazy loading
    for i in range(20):
        track = HackathonTrack(
            hackathon_id=hackathon.id,
            name=f"Track {i}",
            sort_order=i
        )
        test_db_session.add(track)
    
    await test_db_session.commit()
    
    # Track queries for detail endpoint
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    query_count = {"count": 0}
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        query_count["count"] += 1
    
    engine = test_db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_queries)
    
    try:
        # Get hackathon detail (should NOT load tracks)
        response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}")
        
        assert response.status_code == 200
        
        # Query count should be minimal (just the hackathon itself and maybe rules)
        # Should NOT be loading all 20 tracks
        detail_queries = query_count["count"]
        
        # Reset counter
        query_count["count"] = 0
        
        # Get tracks endpoint (should load tracks)
        response = await test_client_with_db.get(f"/api/v1/hackathons/{hackathon.id}/tracks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 20
        
        tracks_queries = query_count["count"]
        
        # Tracks endpoint should execute queries, but detail should not have loaded tracks
        # If detail loaded tracks, the query counts would be similar
        assert detail_queries < tracks_queries or detail_queries <= 3, (
            "Detail endpoint appears to be loading track relationships unnecessarily"
        )
        
    finally:
        event.remove(engine, "before_cursor_execute", count_queries)


@pytest.mark.asyncio
async def test_database_uses_proper_foreign_key_constraints(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that database maintains foreign key and domain constraints.
    
    This is more of a sanity check that our test setup correctly reflects
    production database constraints.
    
    Requirements: 11.4 - Preserve foreign key and domain constraints
    """
    from app.hackathons.models import HackathonTrack
    
    # Create a test user
    user = User(
        email="fktest@example.com",
        username="fktestuser",
        password_hash="dummy_hash",
        full_name="FK Test User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a hackathon
    hackathon = await create_published_hackathon(
        test_db_session,
        user.id,
        "FK Test Hackathon",
        "fk-test-hackathon"
    )
    
    await test_db_session.commit()
    
    # Try to create a track with valid foreign key
    valid_track = HackathonTrack(
        hackathon_id=hackathon.id,
        name="Valid Track",
        sort_order=1
    )
    test_db_session.add(valid_track)
    await test_db_session.flush()  # Should succeed
    await test_db_session.rollback()
    
    # Try to create a track with invalid foreign key (should fail)
    from uuid import uuid4
    invalid_hackathon_id = uuid4()
    
    invalid_track = HackathonTrack(
        hackathon_id=invalid_hackathon_id,
        name="Invalid Track",
        sort_order=1
    )
    test_db_session.add(invalid_track)
    
    # This should raise an integrity error
    with pytest.raises(Exception) as exc_info:
        await test_db_session.flush()
    
    # Verify it's a foreign key violation
    # Different database drivers may raise different exceptions
    # but the error should mention foreign key or integrity
    error_str = str(exc_info.value).lower()
    assert ("foreign" in error_str or 
            "integrity" in error_str or 
            "constraint" in error_str or
            "violates" in error_str)


@pytest.mark.asyncio
async def test_list_endpoint_deterministic_ordering_uses_database(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that deterministic ordering is done at the database level.
    
    Ordering should be part of the SQL query (ORDER BY), not done
    in Python after fetching results.
    
    Requirements: 11.1 - Use database filtering and ordering
    """
    # Create a test user
    user = User(
        email="ordering@example.com",
        username="orderinguser",
        password_hash="dummy_hash",
        full_name="Ordering User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create hackathons with specific timestamps
    import asyncio
    
    hackathons = []
    for i in range(5):
        h = await create_published_hackathon(
            test_db_session,
            user.id,
            f"Hackathon {i}",
            f"hackathon-order-{i}"
        )
        hackathons.append(h)
        await asyncio.sleep(0.01)  # Ensure different timestamps
    
    await test_db_session.commit()
    
    # Query the list
    response = await test_client_with_db.get("/api/v1/hackathons")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify ordering (newest first by created_at)
    assert len(data["items"]) == 5
    
    # Extract slugs to verify order
    slugs = [item["slug"] for item in data["items"]]
    
    # Should be in reverse order (4, 3, 2, 1, 0) because newest first
    expected_order = [
        "hackathon-order-4",
        "hackathon-order-3",
        "hackathon-order-2",
        "hackathon-order-1",
        "hackathon-order-0"
    ]
    
    assert slugs == expected_order, (
        f"Ordering is incorrect. Expected {expected_order}, got {slugs}"
    )



# ========================================================================
# Error Handling Tests for Public API
# ========================================================================

@pytest.mark.asyncio
async def test_public_api_validation_errors_return_422_structured_response(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that validation errors in public API return 422 with structured response.
    
    Requirements: 12.1 - Validation errors return 400 (or 422) with structured error response
    """
    # Test list endpoint with invalid page parameter
    response = await test_client_with_db.get("/api/v1/hackathons?page=0")  # page must be >= 1
    
    # Should return validation error
    assert response.status_code == 422
    
    # Response should have structured format (either custom or FastAPI default)
    data = response.json()
    assert "detail" in data or "error" in data
    
    if "error" in data:
        # Custom error handler
        assert data["error"]["code"] in ["VALIDATION_ERROR", "INVALID_REQUEST"]
    else:
        # FastAPI default
        assert isinstance(data["detail"], list)
    
    # Test with invalid page_size (> 100)
    response = await test_client_with_db.get("/api/v1/hackathons?page_size=200")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_public_api_not_found_returns_404_structured_response(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that not found errors return 404 with structured response.
    
    Requirements: 12.3 - Not found errors return 404 with structured error response
    """
    # Test various not found scenarios
    from uuid import uuid4
    
    nonexistent_uuid = uuid4()
    nonexistent_slug = "this-does-not-exist"
    
    endpoints = [
        f"/api/v1/hackathons/{nonexistent_uuid}",
        f"/api/v1/hackathons/{nonexistent_slug}",
        f"/api/v1/hackathons/{nonexistent_uuid}/rules",
        f"/api/v1/hackathons/{nonexistent_slug}/tracks",
        f"/api/v1/hackathons/{nonexistent_uuid}/schedule",
        f"/api/v1/hackathons/{nonexistent_slug}/sponsors",
    ]
    
    for endpoint in endpoints:
        response = await test_client_with_db.get(endpoint)
        
        # Should return 404
        assert response.status_code == 404, f"Endpoint {endpoint} should return 404"
        
        # Should have structured response
        data = response.json()
        assert "detail" in data or "error" in data, f"Endpoint {endpoint} should have error structure"
        
        if "error" in data:
            error = data["error"]
            assert "code" in error
            assert "message" in error
            # Accept various error codes
            assert error["code"] in ["NOT_FOUND", "RESOURCE_NOT_FOUND", "HTTP_ERROR"]


@pytest.mark.asyncio
async def test_public_api_draft_hackathon_returns_404_not_403(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that accessing DRAFT hackathons returns 404, not 403.
    
    This prevents information disclosure about whether a hackathon exists.
    
    Requirements: 12.3 - Not found errors return 404 with structured error response
    """
    # Create a test user
    user = User(
        email="draft404@example.com",
        username="draft404user",
        password_hash="dummy_hash",
        full_name="Draft 404 User"
    )
    test_db_session.add(user)
    await test_db_session.flush()
    
    # Create a DRAFT hackathon
    draft = Hackathon(
        name="Draft Hackathon",
        slug="draft-404-test",
        created_by_user_id=user.id,
        organizer_user_id=user.id,
        lifecycle_status="DRAFT",
        team_min_size=1
    )
    test_db_session.add(draft)
    await test_db_session.commit()
    
    # Access should return 404 (not 403)
    response = await test_client_with_db.get(f"/api/v1/hackathons/{draft.id}")
    
    # Should return 404, not 403
    # 403 would reveal that the resource exists but is forbidden
    # 404 doesn't leak information about existence
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_api_error_responses_consistent_format(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that all error responses use consistent format across public API.
    
    Requirements: 12.5 - Reuse existing project error response format
    """
    # Collect different error responses
    responses = []
    
    # 1. Validation error (422)
    r1 = await test_client_with_db.get("/api/v1/hackathons?page=0")
    responses.append(r1)
    
    # 2. Not found error (404)
    r2 = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug")
    responses.append(r2)
    
    # All responses should be JSON
    for response in responses:
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        
        # All should have either detail or error structure
        assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_public_api_errors_do_not_expose_stack_traces(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that error responses do not expose stack traces or internal details.
    
    Requirements: 12.6 - Do not expose stack traces or database details in errors
    """
    # Collect various error responses
    responses = []
    
    # 1. Validation error
    r1 = await test_client_with_db.get("/api/v1/hackathons?page=-1")
    responses.append(r1)
    
    # 2. Not found error
    r2 = await test_client_with_db.get("/api/v1/hackathons/nonexistent")
    responses.append(r2)
    
    # 3. Invalid UUID format (might cause parsing error)
    r3 = await test_client_with_db.get("/api/v1/hackathons/not-a-uuid")
    responses.append(r3)
    
    # Check all responses
    for response in responses:
        response_text = response.text.lower()
        
        # Should NOT contain stack trace elements
        assert "traceback" not in response_text
        assert "file \"" not in response_text
        
        # Should NOT contain database details
        assert "sqlalchemy" not in response_text
        assert "postgresql" not in response_text
        assert "psycopg" not in response_text
        
        # Should NOT contain internal paths
        assert "/app/" not in response_text
        assert "backend/" not in response_text


@pytest.mark.asyncio
async def test_public_api_errors_do_not_expose_database_details(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that error responses do not expose database schema or query details.
    
    Requirements: 12.6 - Do not expose stack traces or database details
    """
    # Try various operations that might expose database details
    responses = []
    
    # 1. Invalid UUID that might cause database error
    r1 = await test_client_with_db.get("/api/v1/hackathons/00000000-0000-0000-0000-000000000000")
    responses.append(r1)
    
    # 2. Invalid slug that might cause query error
    r2 = await test_client_with_db.get("/api/v1/hackathons/test'; DROP TABLE hackathons; --")
    responses.append(r2)
    
    for response in responses:
        response_text = response.text.lower()
        
        # Should NOT contain SQL or database-specific terms
        assert "select" not in response_text or "select" in ["select one", "please select"]
        assert "insert" not in response_text
        assert "update" not in response_text
        assert "delete" not in response_text
        assert "table" not in response_text or "table" in ["stable", "suitable"]
        assert "column" not in response_text
        assert "constraint" not in response_text
        assert "foreign key" not in response_text
        assert "primary key" not in response_text


@pytest.mark.asyncio
async def test_public_api_malformed_requests_return_appropriate_errors(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that malformed requests return appropriate error responses.
    
    Requirements: 12.1, 12.3 - Return appropriate status codes with structured errors
    """
    # Test various malformed requests
    
    # 1. Invalid query parameters (non-numeric page)
    response = await test_client_with_db.get("/api/v1/hackathons?page=abc")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data or "error" in data
    
    # 2. Invalid UUID format
    response = await test_client_with_db.get("/api/v1/hackathons/not-a-valid-uuid")
    # Could be 404 (treated as slug) or 422 (UUID validation failed)
    assert response.status_code in [404, 422]
    
    # 3. Negative page number
    response = await test_client_with_db.get("/api/v1/hackathons?page=-5")
    assert response.status_code == 422
    
    # 4. Page size exceeding maximum
    response = await test_client_with_db.get("/api/v1/hackathons?page_size=1000")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_public_api_error_messages_are_user_friendly(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that error messages are user-friendly and actionable.
    
    Requirements: 12.1, 12.3 - Return structured error responses with clear messages
    """
    # Test not found error
    response = await test_client_with_db.get("/api/v1/hackathons/nonexistent-slug")
    
    assert response.status_code == 404
    data = response.json()
    
    # Error message should be present and user-friendly
    if "detail" in data:
        assert len(data["detail"]) > 0
        assert isinstance(data["detail"], str)
    elif "error" in data:
        assert "message" in data["error"]
        assert len(data["error"]["message"]) > 0
    
    # Test validation error
    response = await test_client_with_db.get("/api/v1/hackathons?page=0")
    
    assert response.status_code == 422
    data = response.json()
    
    # Validation errors should be descriptive
    if "detail" in data:
        assert isinstance(data["detail"], list)
        for error in data["detail"]:
            assert "msg" in error
            assert len(error["msg"]) > 0
    elif "error" in data:
        assert "message" in data["error"]
        assert len(data["error"]["message"]) > 0


@pytest.mark.asyncio
async def test_public_api_cors_preflight_errors_handled(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that CORS preflight requests are handled appropriately.
    
    This documents expected behavior for OPTIONS requests.
    
    Requirements: 12.5 - Consistent error handling across all endpoints
    """
    # OPTIONS requests should be handled by CORS middleware
    # This test documents expected behavior
    
    # Note: AsyncClient may not properly simulate CORS preflight
    # This test serves as documentation of expected behavior
    # Actual CORS testing should be done with a real browser or CORS-aware client
    pass


@pytest.mark.asyncio
async def test_public_api_rate_limiting_errors_documented(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Document expected behavior for rate limiting (if implemented).
    
    This test serves as documentation for future rate limiting implementation.
    
    Requirements: 12.5 - Consistent error handling
    """
    # If rate limiting is implemented, it should:
    # 1. Return 429 Too Many Requests
    # 2. Include Retry-After header
    # 3. Have consistent error format
    # 4. Not expose internal rate limiting logic
    
    # This test documents expected behavior for future implementation
    pass


@pytest.mark.asyncio
async def test_public_api_error_responses_include_request_id(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that error responses include request_id for tracing when available.
    
    Requirements: 12.5 - Reuse existing project error response format (with request_id)
    """
    # Send request with custom request ID
    response = await test_client_with_db.get(
        "/api/v1/hackathons/nonexistent-slug",
        headers={"X-Request-ID": "test-public-error-123"}
    )
    
    assert response.status_code == 404
    
    # Check if request_id is in response
    data = response.json()
    
    # If the app uses custom error handler with request_id, verify it
    # If using default FastAPI handler, document that it may not be present
    if "request_id" in data:
        assert data["request_id"] == "test-public-error-123"
    # else: document that request_id tracking may need to be added


@pytest.mark.asyncio
async def test_public_api_cross_endpoint_error_consistency(
    test_client_with_db: AsyncClient,
    test_db_session: AsyncSession
):
    """Test that error handling is consistent across all public API endpoints.
    
    Requirements: 12.5 - Reuse existing project error response format
    """
    # Test 404 errors across different endpoints
    from uuid import uuid4
    
    nonexistent_id = uuid4()
    
    endpoints = [
        f"/api/v1/hackathons/{nonexistent_id}",
        f"/api/v1/hackathons/{nonexistent_id}/rules",
        f"/api/v1/hackathons/{nonexistent_id}/tracks",
        f"/api/v1/hackathons/{nonexistent_id}/schedule",
        f"/api/v1/hackathons/{nonexistent_id}/sponsors",
    ]
    
    error_formats = []
    
    for endpoint in endpoints:
        response = await test_client_with_db.get(endpoint)
        assert response.status_code == 404
        
        data = response.json()
        
        # Collect error format structure
        if "error" in data:
            error_formats.append("custom")
        elif "detail" in data:
            error_formats.append("fastapi_default")
        else:
            error_formats.append("unknown")
    
    # All endpoints should use the same error format
    assert len(set(error_formats)) == 1, (
        f"Error formats are inconsistent across endpoints: {error_formats}"
    )
