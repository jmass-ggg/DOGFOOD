"""Frozen constraints and triggers exercised on an Alembic-built PostgreSQL DB."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, text, inspect
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import selectinload

from app.models import (
    Base,
    User,
    Hackathon,
    HackathonMembership,
    Team,
    TeamMember,
    TeamMembershipEvent,
    Project,
    ProjectSubmissionMember,
    ProjectLink,
    ProjectTechnology,
    HackathonTrack,
    JudgeInvite,
    JudgeAssignment,
    JudgeReview,
    JudgeScore,
    ParticipantProfile,
    ResultPublication,
    ResultEntry,
    ResultAward,
    Award,
)


@contextmanager
def rejected(db, code):
    with pytest.raises(DBAPIError) as error:
        with db.begin_nested():
            yield
            db.flush()
    assert error.value.orig.sqlstate == code


def check_deferred(db):
    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    db.execute(text("SET CONSTRAINTS ALL DEFERRED"))


def test_all_models_registered_and_platform_scope(persistence_engine):
    assert len(Base.registry.mappers) == len(Base.metadata.tables) == 34
    inspector = inspect(persistence_engine)
    assert set(inspector.get_table_names(schema="dogfood")) == {
        t.name for t in Base.metadata.tables.values()
    }
    assert {t.schema for t in Base.metadata.tables.values()} == {"dogfood"}
    assert "hackathon_id" not in {
        c["name"]
        for c in inspector.get_columns("platform_announcements", schema="dogfood")
    }
    assert not {"announcements", "hackathon_announcements"}.intersection(
        inspector.get_table_names(schema="dogfood")
    )
    assert inspector.get_enums(schema="dogfood") == []


@pytest.mark.parametrize("field", ["email", "username"])
def test_canonical_identity_uniqueness(db, records, field):
    first = records.user()
    attrs = dict(
        email=f"{uuid4()}@example.invalid",
        username=str(uuid4()),
        password_hash="fixture",
        full_name="Test",
    )
    attrs[field] = " " + getattr(first, field).upper() + " "
    with rejected(db, "23505"):
        db.add(User(**attrs))


@pytest.mark.parametrize(
    "role",
    [
        "PARTICIPANT",
        "JUDGE",
        "HACKATHON_ADMIN",
        "ORGANIZER",
        "TEAM_LEADER",
        "DOGFOOD_SUPER_ADMIN",
        "ADMIN",
    ],
)
def test_membership_roles(db, records, role):
    event, owner, *_ = records.event()
    user = records.user()
    if role == "ORGANIZER":
        with rejected(db, "23505"):
            records.add(
                HackathonMembership(hackathon_id=event.id, user_id=user.id, role=role)
            )
    elif role in {"PARTICIPANT", "JUDGE", "HACKATHON_ADMIN"}:
        member = records.add(
            HackathonMembership(hackathon_id=event.id, user_id=user.id, role=role)
        )
        assert db.get(HackathonMembership, (event.id, user.id)).role == role
    else:
        with rejected(db, "23514"):
            records.add(
                HackathonMembership(hackathon_id=event.id, user_id=user.id, role=role)
            )


@pytest.mark.parametrize("status", ["ACTIVE", "BANNED", "REVOKED", "LEFT", "SUSPENDED"])
def test_membership_statuses(db, records, status):
    event, owner, *_ = records.event()
    user = records.user()
    member = HackathonMembership(
        hackathon_id=event.id,
        user_id=user.id,
        role="PARTICIPANT",
        status=status,
        status_changed_by_user_id=owner.id,
        status_reason="Test",
    )
    if status in {"ACTIVE", "BANNED", "REVOKED"}:
        records.add(member)
        assert db.get(HackathonMembership, (event.id, user.id)).status == status
    else:
        with rejected(db, "23514"):
            records.add(member)


def test_deferred_organizer_creation_and_missing_owner(db, records):
    event, owner, *_ = records.event()
    check_deferred(db)
    assert event.organizer_role == "ORGANIZER" and event.organizer_status == "ACTIVE"
    with rejected(db, "23503"):
        records.add(
            Hackathon(
                created_by_user_id=owner.id,
                organizer_user_id=owner.id,
                name="Invalid",
                slug=str(uuid4()),
            )
        )
        check_deferred(db)
    with rejected(db, "23503"):
        db.execute(
            text(
                "UPDATE dogfood.hackathon_memberships SET status='REVOKED',status_reason='Test',status_changed_by_user_id=:u WHERE hackathon_id=:e AND user_id=:u"
            ),
            dict(u=owner.id, e=event.id),
        )
        check_deferred(db)


def test_team_creation_uniqueness_leader_and_history(db, records):
    context = records.event()
    team, user = records.team(context)
    check_deferred(db)
    assert (
        db.scalar(
            select(TeamMembershipEvent.event_type).where(
                TeamMembershipEvent.team_id == team.id
            )
        )
        == "JOINED"
    )
    second, other = records.team(context)
    with rejected(db, "23505"):
        records.add(
            TeamMember(hackathon_id=context[0].id, team_id=second.id, user_id=user.id)
        )
    with rejected(db, "23503"):
        db.execute(
            text("UPDATE dogfood.teams SET leader_user_id=:u WHERE id=:t"),
            dict(u=other.id, t=team.id),
        )
        check_deferred(db)
    team.dissolved_at = datetime.now(timezone.utc)
    team.leader_user_id = None
    db.flush()
    db.delete(db.get(TeamMember, (context[0].id, user.id)))
    db.flush()
    check_deferred(db)
    assert set(
        db.scalars(
            select(TeamMembershipEvent.event_type).where(
                TeamMembershipEvent.team_id == team.id
            )
        )
    ) == {"JOINED", "LEFT"}
    assert db.get(HackathonMembership, (context[0].id, user.id)).status == "ACTIVE"


def test_project_story_unique_team_and_generated_tag(db, records):
    context = records.event()
    project, team, user = records.project(context)
    db.expire(project)
    assert [
        getattr(project, key)
        for key in (
            "inspiration",
            "what_it_does",
            "how_it_was_built",
            "challenges",
            "accomplishments",
            "what_we_learned",
            "whats_next",
        )
    ] == [
        "Inspiration",
        "Purpose",
        "Build",
        "Challenges",
        "Achievements",
        "Lessons",
        "Next",
    ]
    with rejected(db, "23505"):
        db.execute(
            text(
                "INSERT INTO dogfood.projects SELECT gen_random_uuid(),hackathon_id,team_id,track_id,submitted_by_user_id,name,tagline,inspiration,what_it_does,how_it_was_built,challenges,accomplishments,what_we_learned,whats_next,submitted_at,updated_at,deleted_at,deleted_by_user_id,disqualified_at,disqualified_by_user_id,disqualification_reason,version FROM dogfood.projects WHERE id=:p"
            ),
            dict(p=project.id),
        )
    tag = records.add(
        ProjectTechnology(project_id=project.id, display_name=" PostgreSQL ")
    )
    assert tag.normalized_key == "postgresql"
    loaded = db.scalar(
        select(Project)
        .options(selectinload(Project.technologies))
        .where(Project.id == project.id)
    )
    assert loaded.technologies[0].display_name == " PostgreSQL "


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_submission_roster_immutable(db, records, operation):
    context = records.event()
    project, team, user = records.project(context)
    records.add(
        ProjectSubmissionMember(
            project_id=project.id, team_id=team.id, user_id=user.id, was_leader=True
        )
    )
    statement = (
        "UPDATE dogfood.project_submission_members SET was_leader=false"
        if operation == "UPDATE"
        else "DELETE FROM dogfood.project_submission_members"
    )
    with rejected(db, "23514"):
        db.execute(text(statement))


@pytest.mark.parametrize(
    "kind",
    ["GITHUB", "LIVE_DEMO", "YOUTUBE", "GOOGLE_DRIVE", "ONEDRIVE", "OTHER", "VIDEO"],
)
def test_project_link_vocabulary(db, records, kind):
    context = records.event()
    project, *_ = records.project(context)
    link = ProjectLink(
        project_id=project.id, link_type=kind, url="https://example.invalid"
    )
    if kind == "VIDEO":
        with rejected(db, "23514"):
            records.add(link)
    else:
        records.add(link)
        db.expire(link)
        assert link.link_type == kind


def test_cross_event_project_track_rejected(db, records):
    context = records.event()
    project, *_ = records.project(context)
    other = records.event()
    track = records.add(HackathonTrack(hackathon_id=other[0].id, name="Other event"))
    with rejected(db, "23503"):
        db.execute(
            text("UPDATE dogfood.projects SET track_id=:t WHERE id=:p"),
            dict(t=track.id, p=project.id),
        )


@pytest.mark.parametrize(
    "status", ["PENDING", "ACCEPTED", "EXPIRED", "REVOKED", "DECLINED"]
)
def test_judge_invitation_vocabulary(db, records, status):
    context = records.event()
    event, owner, *_ = context
    now = datetime.now(timezone.utc)
    invitation = JudgeInvite(
        hackathon_id=event.id,
        target_email="judge@example.invalid",
        token_hash=str(uuid4()),
        invited_by_user_id=owner.id,
        status=status,
        expires_at=now + timedelta(days=1),
        accepted_at=now if status == "ACCEPTED" else None,
        accepted_by_user_id=owner.id if status == "ACCEPTED" else None,
        revoked_at=now if status == "REVOKED" else None,
    )
    if status == "DECLINED":
        with rejected(db, "23514"):
            records.add(invitation)
    else:
        records.add(invitation)
        db.expire(invitation)
        assert invitation.status == status
        if status in {"EXPIRED", "REVOKED"}:
            with rejected(db, "23514"):
                db.execute(
                    text(
                        "UPDATE dogfood.judge_invites SET status='ACCEPTED',accepted_at=:now,accepted_by_user_id=:u,revoked_at=NULL WHERE id=:i"
                    ),
                    dict(now=now, u=owner.id, i=invitation.id),
                )


def test_judging_uniqueness_completion_and_freeze(db, records):
    context = records.event()
    event, owner, *_ = context
    project, *_ = records.project(context)
    assignment, review, criterion = records.review(context, project)
    with rejected(db, "23505"):
        records.add(
            JudgeAssignment(
                hackathon_id=event.id,
                judge_user_id=assignment.judge_user_id,
                project_id=project.id,
                assigned_by_user_id=owner.id,
            )
        )
    with rejected(db, "23505"):
        records.add(JudgeReview(hackathon_id=event.id, assignment_id=assignment.id))
    event.rubric_locked_at = datetime.now(timezone.utc)
    db.flush()
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.judge_reviews SET status='SUBMITTED',submitted_at=clock_timestamp() WHERE id=:r"
            ),
            dict(r=review.id),
        )
    score = records.add(
        JudgeScore(
            hackathon_id=event.id,
            review_id=review.id,
            criterion_id=criterion.id,
            score=Decimal("8.1250"),
        )
    )
    assert score.score == Decimal("8.1250")
    with rejected(db, "23505"):
        # SQL avoids identity-map warnings when deliberately violating the composite PK.
        db.execute(
            text(
                "INSERT INTO dogfood.judge_scores(hackathon_id,review_id,criterion_id,score) VALUES (:e,:r,:c,8)"
            ),
            dict(e=event.id, r=review.id, c=criterion.id),
        )
    review.status = "SUBMITTED"
    review.submitted_at = datetime.now(timezone.utc)
    db.flush()
    with rejected(db, "23514"):
        db.execute(
            text("UPDATE dogfood.judge_scores SET score=9 WHERE review_id=:r"),
            dict(r=review.id),
        )
    with rejected(db, "23514"):
        db.execute(
            text("UPDATE dogfood.judging_criteria SET max_score=20 WHERE id=:c"),
            dict(c=criterion.id),
        )


@pytest.mark.parametrize("score", ["-1", "10.0001", "NaN", "Infinity"])
def test_score_range(db, records, score):
    context = records.event()
    project, *_ = records.project(context)
    assignment, review, criterion = records.review(context, project)
    with rejected(db, "22003" if score == "Infinity" else "23514"):
        records.add(
            JudgeScore(
                hackathon_id=context[0].id,
                review_id=review.id,
                criterion_id=criterion.id,
                score=Decimal(score),
            )
        )


def test_review_coverage_defaults_configuration_and_freeze(db, records):
    context = records.event()
    event, *_ = context
    assert event.minimum_reviews_per_project == 1
    event.minimum_reviews_per_project = 2
    db.flush()
    db.expire(event)
    assert event.minimum_reviews_per_project == 2
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.hackathons SET minimum_reviews_per_project=0 WHERE id=:e"
            ),
            dict(e=event.id),
        )
    project, *_ = records.project(context)
    records.review(context, project)
    event.rubric_locked_at = datetime.now(timezone.utc)
    db.flush()
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.hackathons SET minimum_reviews_per_project=3 WHERE id=:e"
            ),
            dict(e=event.id),
        )


@pytest.mark.parametrize(
    "table", ["result_publications", "result_entries", "result_awards"]
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_immutable_results_and_publication_sealing(db, records, table, operation):
    context = records.event()
    event, owner, *_ = context
    project, *_ = records.project(context)
    publication = records.add(
        ResultPublication(
            hackathon_id=event.id,
            publication_number=1,
            published_by_user_id=owner.id,
            scoring_method="weighted_normalized_mean_v1",
            calculation_snapshot={"minimum_reviews_per_project": 1},
        )
    )
    records.add(
        ResultEntry(
            hackathon_id=event.id,
            publication_id=publication.id,
            project_id=project.id,
            final_score=Decimal("80.123456"),
            review_count=1,
            rank=1,
            project_name_snapshot=project.name,
        )
    )
    award = records.add(Award(hackathon_id=event.id, name="Winner"))
    records.add(
        ResultAward(
            hackathon_id=event.id,
            publication_id=publication.id,
            award_id=award.id,
            project_id=project.id,
            award_name_snapshot="Winner",
            selected_by_user_id=owner.id,
        )
    )
    event.current_result_publication_id = publication.id
    db.flush()
    # Table names are the fixed parametrized test constants, never user input.
    statement = (
        f"UPDATE dogfood.{table} SET hackathon_id=hackathon_id"
        if operation == "UPDATE"
        else f"DELETE FROM dogfood.{table}"
    )
    with rejected(db, "23514"):
        db.execute(text(statement))
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.hackathons SET current_result_publication_id=NULL WHERE id=:e"
            ),
            dict(e=event.id),
        )


def test_json_arrays_discovery_defaults_and_server_timestamp(db, records):
    context = records.event()
    user = records.participant(context)
    profile = records.add(
        ParticipantProfile(hackathon_id=context[0].id, user_id=user.id)
    )
    assert profile.skills == [] and profile.discovery_opt_in is False
    profile.skills = ["Python"]
    profile.external_profile_urls = {"github": "https://example.invalid"}
    db.flush()
    db.refresh(profile)
    assert (
        profile.skills == ["Python"]
        and profile.external_profile_urls["github"] == "https://example.invalid"
    )
    assert profile.updated_at.tzinfo is not None


async def test_async_orm_generated_values_and_rollback(persistence_engine):
    """Exercise the mappings with the async driver used by T1."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

    engine = create_async_engine(persistence_engine.url)
    user_id = None
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                async with AsyncSession(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                    expire_on_commit=False,
                ) as session:
                    key = str(uuid4())
                    user = User(
                        email=f" {key}@EXAMPLE.INVALID ",
                        username=key,
                        password_hash="fixture-only",
                        full_name="Test",
                    )
                    session.add(user)
                    await session.flush()
                    user_id = user.id
                    assert user.email_key == f"{key}@example.invalid"
                    assert user.created_at.tzinfo is not None
                    await session.commit()
            finally:
                await transaction.rollback()
        async with engine.connect() as connection:
            assert (
                await connection.scalar(select(User.id).where(User.id == user_id))
                is None
            )
    finally:
        await engine.dispose()
