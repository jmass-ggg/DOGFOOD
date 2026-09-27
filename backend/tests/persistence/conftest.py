"""Opt-in PostgreSQL tests; every test rolls back its own outer transaction."""

import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models import (
    User,
    Hackathon,
    HackathonMembership,
    PlatformTermsVersion,
    HackathonRulesVersion,
    HackathonRegistration,
    Team,
    TeamMember,
    Project,
    JudgeAssignment,
    JudgeReview,
    JudgingCriterion,
)


@pytest.fixture(scope="session")
def persistence_engine():
    url = os.environ.get("T2_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set T2_DATABASE_URL to a disposable dogfood_t2_* PostgreSQL database"
        )
    parsed = make_url(url)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database or ""
    ).startswith("dogfood_t2_"):
        raise RuntimeError(
            "T2_DATABASE_URL must use psycopg and a dedicated dogfood_t2_* database"
        )
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            assert (
                int(conn.exec_driver_sql("SHOW server_version_num").scalar_one())
                >= 160000
            )
            # Never migrate an existing unrelated database.
            occupied = conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema'))"
                )
            ).scalar_one()
            if occupied:
                revision = conn.execute(
                    text("SELECT version_num FROM public.alembic_version")
                ).scalar_one()
                assert (
                    revision == "0001_dogfood_v1"
                ), "Expected a database at the T2 migration head"
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).resolve().parents[2],
            env={**os.environ, "DATABASE_URL": url},
            check=True,
        )
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db(persistence_engine):
    with persistence_engine.connect() as conn:
        outer = conn.begin()
        try:
            with Session(
                bind=conn,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                yield session
                # Rollback isolation must not hide violations that would fail at commit.
                session.flush()
                session.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        finally:
            outer.rollback()


class Records:
    """Minimal valid persistence fixtures, not application workflow implementations."""

    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        self.session.flush()
        return obj

    def user(self, **values):
        key = str(uuid4())
        return self.add(
            User(
                **dict(
                    email=f"{key}@example.invalid",
                    username=key,
                    password_hash="fixture-only",
                    full_name="Test",
                    **values,
                )
            )
        )

    def event(self):
        owner = self.user()
        event = self.add(
            Hackathon(
                created_by_user_id=owner.id,
                organizer_user_id=owner.id,
                name="Test event",
                slug=str(uuid4()),
                judging_start_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )
        self.add(
            HackathonMembership(
                hackathon_id=event.id, user_id=owner.id, role="ORGANIZER"
            )
        )
        terms = self.add(
            PlatformTermsVersion(
                version_label=str(uuid4()), body="Terms", created_by_user_id=owner.id
            )
        )
        rules = self.add(
            HackathonRulesVersion(
                hackathon_id=event.id,
                version_number=1,
                rules="Rules",
                created_by_user_id=owner.id,
            )
        )
        event.current_rules_version_id = rules.id
        self.session.flush()
        return event, owner, terms, rules

    def participant(self, context):
        event, owner, terms, rules = context
        user = self.user()
        self.add(
            HackathonMembership(
                hackathon_id=event.id, user_id=user.id, role="PARTICIPANT"
            )
        )
        self.add(
            HackathonRegistration(
                hackathon_id=event.id,
                user_id=user.id,
                participation_preference="SOLO",
                country_snapshot="NP",
                accepted_rules_version_id=rules.id,
                accepted_terms_version_id=terms.id,
            )
        )
        return user

    def team(self, context):
        event, *_ = context
        user = self.participant(context)
        team = self.add(
            Team(
                hackathon_id=event.id,
                created_by_user_id=user.id,
                leader_user_id=user.id,
                name="Team",
            )
        )
        self.add(TeamMember(hackathon_id=event.id, team_id=team.id, user_id=user.id))
        return team, user

    def project(self, context):
        team, user = self.team(context)
        project = self.add(
            Project(
                hackathon_id=context[0].id,
                team_id=team.id,
                submitted_by_user_id=user.id,
                name="Project",
                tagline="Pitch",
                inspiration="Inspiration",
                what_it_does="Purpose",
                how_it_was_built="Build",
                challenges="Challenges",
                accomplishments="Achievements",
                what_we_learned="Lessons",
                whats_next="Next",
            )
        )
        return project, team, user

    def review(self, context, project):
        event, owner, *_ = context
        judge = self.user()
        self.add(
            HackathonMembership(hackathon_id=event.id, user_id=judge.id, role="JUDGE")
        )
        assignment = self.add(
            JudgeAssignment(
                hackathon_id=event.id,
                judge_user_id=judge.id,
                project_id=project.id,
                assigned_by_user_id=owner.id,
            )
        )
        review = self.add(
            JudgeReview(hackathon_id=event.id, assignment_id=assignment.id)
        )
        criterion = self.add(
            JudgingCriterion(
                hackathon_id=event.id, name="Quality", weight_bps=10000, max_score=10
            )
        )
        return assignment, review, criterion


@pytest.fixture
def records(db):
    return Records(db)
