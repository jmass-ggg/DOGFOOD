"""Additional migration-built DB guard coverage identified during final audit."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.models import AuditEvent, Award, JudgeInvite, ResultPublication, ResultEntry
from tests.persistence.test_invariants import rejected


def test_scheduled_judging_freezes_coverage_without_lock(db, records):
    event, *_ = records.event()
    event.judging_start_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.flush()
    assert event.rubric_locked_at is None
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.hackathons SET minimum_reviews_per_project=2 WHERE id=:id"
            ),
            {"id": event.id},
        )
    with rejected(db, "23514"):
        db.execute(
            text(
                "UPDATE dogfood.hackathons SET judging_start_at=clock_timestamp()+interval '1 day' WHERE id=:id"
            ),
            {"id": event.id},
        )


def test_result_coverage_and_sealed_child_inserts(db, records):
    context = records.event()
    event, owner, *_ = context
    event.minimum_reviews_per_project = 2
    db.flush()
    project, *_ = records.project(context)
    with rejected(db, "23514"):
        records.add(
            ResultPublication(
                hackathon_id=event.id,
                publication_number=1,
                published_by_user_id=owner.id,
                scoring_method="weighted_normalized_mean_v1",
                calculation_snapshot={"minimum_reviews_per_project": 1},
            )
        )
    publication = records.add(
        ResultPublication(
            hackathon_id=event.id,
            publication_number=1,
            published_by_user_id=owner.id,
            scoring_method="weighted_normalized_mean_v1",
            calculation_snapshot={"minimum_reviews_per_project": 2},
        )
    )
    values = dict(
        hackathon_id=event.id,
        publication_id=publication.id,
        project_id=project.id,
        final_score=90,
        rank=1,
        project_name_snapshot=project.name,
    )
    with rejected(db, "23514"):
        records.add(ResultEntry(**values, review_count=1))
    records.add(ResultEntry(**values, review_count=2))
    event.current_result_publication_id = publication.id
    db.flush()
    other, *_ = records.project(context)
    with rejected(db, "23514"):
        records.add(ResultEntry(**{**values, "project_id": other.id}, review_count=2))
    award = records.add(Award(hackathon_id=event.id, name="Award"))
    with rejected(db, "23514"):
        db.execute(
            text(
                "INSERT INTO dogfood.result_awards(hackathon_id,publication_id,award_id,project_id,award_name_snapshot,selected_by_user_id) VALUES (:e,:p,:a,:project,'Award',:u)"
            ),
            dict(
                e=event.id, p=publication.id, a=award.id, project=project.id, u=owner.id
            ),
        )


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_audit_history_cannot_change(db, records, operation):
    owner = records.user()
    records.add(
        AuditEvent(
            actor_user_id=owner.id,
            action="TEST",
            entity_type="user",
            entity_id=owner.id,
        )
    )
    statement = (
        "UPDATE dogfood.audit_events SET action='CHANGED'"
        if operation == "UPDATE"
        else "DELETE FROM dogfood.audit_events"
    )
    with rejected(db, "23514"):
        db.execute(text(statement))


def test_updated_at_is_database_maintained(db, records):
    user = records.user()
    old = datetime(2000, 1, 1, tzinfo=timezone.utc)
    user.updated_at = old
    user.full_name = "Changed"
    db.flush()
    db.refresh(user)
    assert user.updated_at > old
    assert user.updated_at == db.scalar(
        text("SELECT updated_at FROM dogfood.users WHERE id=:id"), dict(id=user.id)
    )


def test_project_reparent_guard(db, records):
    context = records.event()
    project, *_ = records.project(context)
    target = records.event()[0]
    with rejected(db, "23514"):
        db.execute(
            text("UPDATE dogfood.projects SET hackathon_id=:e WHERE id=:p"),
            dict(e=target.id, p=project.id),
        )


def test_pending_judge_invite_partial_uniqueness(db, records):
    event, owner, *_ = records.event()
    now = datetime.now(timezone.utc)
    values = dict(
        hackathon_id=event.id,
        target_email="judge@example.invalid",
        invited_by_user_id=owner.id,
        expires_at=now + timedelta(days=1),
    )
    invitation = records.add(JudgeInvite(**values, token_hash=str(uuid4())))
    with rejected(db, "23505"):
        records.add(
            JudgeInvite(
                **{**values, "target_email": " JUDGE@EXAMPLE.INVALID "},
                token_hash=str(uuid4())
            )
        )
    invitation.status = "REVOKED"
    invitation.revoked_at = now
    db.flush()
    replacement = records.add(JudgeInvite(**values, token_hash=str(uuid4())))
    assert replacement.status == "PENDING"


def test_nullable_audit_json_accepts_python_none(db, records):
    owner = records.user()
    event = records.add(
        AuditEvent(
            actor_user_id=owner.id,
            action="TEST",
            entity_type="user",
            entity_id=owner.id,
            before_data=None,
            after_data=None,
        )
    )
    assert db.execute(
        text(
            "SELECT before_data IS NULL, after_data IS NULL FROM dogfood.audit_events WHERE id=:id"
        ),
        dict(id=event.id),
    ).one() == (True, True)
