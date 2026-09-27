#!/usr/bin/env python3
"""Verify the proposed schema on a disposable, empty PostgreSQL 16+ database.

Usage: SCHEMA_TEST_DATABASE_URL='postgresql://.../dedicated_empty_database' \
       python verify_schema.py
Requires psycopg 3 (already a T1 dependency). Installs the schema once; fixtures
are rolled back. Refuses databases containing user relations. Does not drop data,
create roles, use application DATABASE_URL, or display connection credentials.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parent
passed = 0


def ok(name, condition=True):
    global passed
    if not condition:
        raise AssertionError(name)
    passed += 1
    print(f"PASS {name}")


def main():
    url = os.environ.get("SCHEMA_TEST_DATABASE_URL")
    if not url:
        raise SystemExit(
            "Set SCHEMA_TEST_DATABASE_URL to a dedicated empty PostgreSQL 16+ database."
        )
    with psycopg.connect(url, autocommit=True) as c:
        if c.info.server_version < 160000:
            raise SystemExit("PostgreSQL 16+ required.")
        print("PostgreSQL", c.execute("SHOW server_version").fetchone()[0])
        occupied = c.execute("""SELECT EXISTS (
          SELECT 1 FROM pg_class x JOIN pg_namespace n ON n.oid=x.relnamespace
          WHERE n.nspname NOT IN ('pg_catalog','information_schema')
          AND n.nspname NOT LIKE 'pg_toast%%' AND n.nspname NOT LIKE 'pg_temp%%'
          AND x.relkind IN ('r','p','v','m','S','f')) OR EXISTS (
          SELECT 1 FROM pg_namespace WHERE nspname='dogfood')""").fetchone()[0]
        if occupied:
            raise SystemExit(
                "Refusing nonempty database; use a new disposable database."
            )
        ddl = (ROOT / "dogfood_schema_v2.sql").read_text()
        c.execute(ddl)
        ok("atomic schema installation")
        try:
            c.execute(ddl)
        except psycopg.errors.DuplicateSchema:
            c.execute("ROLLBACK")
            ok("second installation fails safely")
        else:
            raise AssertionError("second installation should fail")
        tables = c.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='dogfood'"
        ).fetchall()
        ok("33 tables after failed reinstall", len(tables) == 33)
        names = {r[0] for r in tables}
        ok(
            "platform announcements only",
            "platform_announcements" in names
            and not {"announcements", "hackathon_announcements"} & names,
        )
        ok(
            "no event ID on platform announcements",
            not c.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_schema='dogfood' AND table_name='platform_announcements' AND column_name='hackathon_id'"
            ).fetchone(),
        )
        ok(
            "zero native enum types",
            c.execute(
                "SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='dogfood' AND t.typtype='e'"
            ).fetchone()[0]
            == 0,
        )
        vocabularies = {
            "hackathons_lifecycle_status": "DRAFT PUBLISHED CANCELLED ARCHIVED",
            "hackathons_result_gallery_mode": "WINNERS_ONLY ALL_PROJECTS",
            "hackathon_memberships_role": "PARTICIPANT JUDGE HACKATHON_ADMIN ORGANIZER",
            "hackathon_memberships_status": "ACTIVE BANNED REVOKED",
            "hackathon_change_requests_request_type": "DELETE_HACKATHON TRANSFER_OWNERSHIP",
            "hackathon_change_requests_status": "PENDING APPROVED REJECTED",
            "hackathon_registrations_participation_preference": "SOLO LOOKING_FOR_TEAM HAVE_TEAM",
            "team_membership_events_event_type": "JOINED LEFT",
            "team_invites_invite_kind": "TARGETED SHARE_LINK",
            "project_links_link_type": "GITHUB LIVE_DEMO YOUTUBE GOOGLE_DRIVE ONEDRIVE OTHER",
            "judge_invites_status": "PENDING ACCEPTED EXPIRED REVOKED",
            "judge_reviews_status": "DRAFT SUBMITTED",
        }
        for name, values in vocabularies.items():
            expr = c.execute(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='dogfood'::regnamespace AND conname=%s",
                ("ck_" + name,),
            ).fetchone()[0]
            ok(
                "exact vocabulary " + name,
                re.findall("'([^']*)'::text", expr) == values.split(),
            )
        constraints = c.execute(
            """SELECT conname,contype,condeferrable,condeferred,confdeltype
          FROM pg_constraint WHERE connamespace='dogfood'::regnamespace"""
        ).fetchall()
        fks = [x for x in constraints if x[1] == "f"]
        ok("92 explicit FKs", len(fks) == 92)
        ok(
            "only owner/leader FKs deferred",
            {x[0] for x in fks if x[2] and x[3]}
            == {"fk_hackathons_organizer", "fk_teams_leader"},
        )
        ok(
            "all other FKs restrict deletion",
            all(x[4] == ("a" if x[2] else "r") for x in fks),
        )
        ok(
            "49 user triggers",
            c.execute(
                "SELECT count(*) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='dogfood'::regnamespace) AND NOT tgisinternal"
            ).fetchone()[0]
            == 49,
        )
        ok(
            "311 dictionary columns",
            c.execute(
                "SELECT count(*) FROM information_schema.columns WHERE table_schema='dogfood'"
            ).fetchone()[0]
            == 311,
        )

        with c.transaction(force_rollback=True):
            c.execute("SET LOCAL search_path = dogfood, pg_catalog")

            def run(s, args=()):
                return c.execute(s, args)

            def one(s, args=()):
                return run(s, args).fetchone()[0]

            def reject(name, s, args=(), states=("23514",)):
                try:
                    with c.transaction():
                        run(s, args)
                except psycopg.Error as e:
                    if e.sqlstate not in states:
                        raise AssertionError(
                            f"{name}: unexpected SQLSTATE {e.sqlstate}"
                        ) from e
                    ok(name)
                else:
                    raise AssertionError(f"{name}: write incorrectly accepted")

            def user():
                key = str(uuid4())
                return one(
                    "INSERT INTO users(email,username,password_hash,full_name) VALUES (%s,%s,'test-only','Test') RETURNING id",
                    (key + "@example.invalid", key),
                )

            owner, replacement, participant, participant2, judge = [
                user() for _ in range(5)
            ]
            terms = one(
                "INSERT INTO platform_terms_versions(version_label,body,created_by_user_id) VALUES ('v1','terms',%s) RETURNING id",
                (owner,),
            )

            def event():
                eid = one(
                    "INSERT INTO hackathons(created_by_user_id,organizer_user_id,name,slug,judging_start_at) VALUES (%s,%s,'Event',%s,clock_timestamp()+interval '1 day') RETURNING id",
                    (owner, owner, str(uuid4())),
                )
                run(
                    "INSERT INTO hackathon_memberships(hackathon_id,user_id,role) VALUES (%s,%s,'ORGANIZER')",
                    (eid, owner),
                )
                rid = one(
                    "INSERT INTO hackathon_rules_versions(hackathon_id,version_number,rules,created_by_user_id) VALUES (%s,1,'rules',%s) RETURNING id",
                    (eid, owner),
                )
                run(
                    "UPDATE hackathons SET current_rules_version_id=%s WHERE id=%s",
                    (rid, eid),
                )
                return eid, rid

            e, rules = event()
            other, other_rules = event()
            run("SET CONSTRAINTS ALL IMMEDIATE")
            run("SET CONSTRAINTS ALL DEFERRED")
            ok("valid deferred event creation")
            with c.transaction():
                bad = one(
                    "INSERT INTO hackathons(created_by_user_id,organizer_user_id,name,slug) VALUES (%s,%s,'Bad','bad') RETURNING id",
                    (owner, owner),
                )
                reject(
                    "missing organizer fails deferred check",
                    "SET CONSTRAINTS ALL IMMEDIATE",
                    states=("23503",),
                )
                run("DELETE FROM hackathons WHERE id=%s", (bad,))
            reject(
                "duplicate organizer",
                "INSERT INTO hackathon_memberships(hackathon_id,user_id,role) VALUES (%s,%s,'ORGANIZER')",
                (e, replacement),
                ("23505",),
            )
            reject(
                "foreign-event rules pointer",
                "UPDATE hackathons SET current_rules_version_id=%s WHERE id=%s",
                (other_rules, e),
                ("23503",),
            )
            reject(
                "negative review coverage",
                "UPDATE hackathons SET minimum_reviews_per_project=0 WHERE id=%s",
                (e,),
            )
            ok(
                "coverage default one",
                one(
                    "SELECT minimum_reviews_per_project FROM hackathons WHERE id=%s",
                    (e,),
                )
                == 1,
            )
            run("UPDATE hackathons SET minimum_reviews_per_project=2 WHERE id=%s", (e,))
            ok("coverage configurable before judging")
            reject(
                "canonical email duplicate",
                "INSERT INTO users(email,username,password_hash,full_name) SELECT upper(email),%s,'test','Test' FROM users WHERE id=%s",
                (str(uuid4()), owner),
                ("23505",),
            )
            for status in ["LEFT", "SUSPENDED"]:
                reject(
                    f"membership {status} forbidden",
                    "INSERT INTO hackathon_memberships(hackathon_id,user_id,role,status) VALUES (%s,%s,'JUDGE',%s)",
                    (e, replacement, status),
                )

            def register(eid, rid, uid):
                run(
                    "INSERT INTO hackathon_memberships(hackathon_id,user_id,role) VALUES (%s,%s,'PARTICIPANT')",
                    (eid, uid),
                )
                run(
                    "INSERT INTO hackathon_registrations(hackathon_id,user_id,participation_preference,country_snapshot,accepted_rules_version_id,accepted_terms_version_id) VALUES (%s,%s,'SOLO','NP',%s,%s)",
                    (eid, uid, rid, terms),
                )

            register(e, rules, participant)
            register(e, rules, participant2)
            register(other, other_rules, participant)
            ok("multi-event registration")
            run(
                "INSERT INTO participant_profiles(hackathon_id,user_id) VALUES (%s,%s)",
                (e, participant),
            )
            ok(
                "discovery disabled by default and empty arrays",
                one(
                    "SELECT NOT discovery_opt_in AND skills='{}'::text[] AND looking_for_roles='{}'::text[] FROM participant_profiles WHERE hackathon_id=%s AND user_id=%s",
                    (e, participant),
                ),
            )
            reject(
                "profile JSON must be object",
                "UPDATE participant_profiles SET external_profile_urls='[]' WHERE hackathon_id=%s AND user_id=%s",
                (e, participant),
            )

            def team(eid, uid):
                tid = one(
                    "INSERT INTO teams(hackathon_id,created_by_user_id,leader_user_id,name) VALUES (%s,%s,%s,'Team') RETURNING id",
                    (eid, uid, uid),
                )
                run(
                    "INSERT INTO team_members(hackathon_id,team_id,user_id) VALUES (%s,%s,%s)",
                    (eid, tid, uid),
                )
                return tid

            t = team(e, participant)
            t2 = team(e, participant2)
            ot = team(other, participant)
            run("SET CONSTRAINTS ALL IMMEDIATE")
            run("SET CONSTRAINTS ALL DEFERRED")
            ok("valid deferred team leader cycles")
            ok(
                "automatic JOINED history",
                one(
                    "SELECT count(*) FROM team_membership_events WHERE team_id=%s AND event_type='JOINED'",
                    (t,),
                )
                == 1,
            )
            reject(
                "one current team per participant/event",
                "INSERT INTO team_members(hackathon_id,team_id,user_id) VALUES (%s,%s,%s)",
                (e, t2, participant),
                ("23505",),
            )
            reject(
                "member reparent forbidden",
                "UPDATE team_members SET team_id=%s WHERE hackathon_id=%s AND user_id=%s",
                (t2, e, participant),
            )
            # Explicitly test the deferred leader constraint at transaction end.
            try:
                with c.transaction():
                    run(
                        "UPDATE teams SET leader_user_id=%s WHERE id=%s",
                        (replacement, t),
                    )
                    run("SET CONSTRAINTS ALL IMMEDIATE")
            except psycopg.errors.ForeignKeyViolation:
                ok("missing leader fails deferred check")
            else:
                raise AssertionError("missing leader allowed")

            def project(eid, tid, uid):
                return one(
                    """INSERT INTO projects(hackathon_id,team_id,submitted_by_user_id,name,tagline,
                  inspiration,what_it_does,how_it_was_built,challenges,accomplishments,what_we_learned,whats_next)
                  VALUES (%s,%s,%s,'Project','Tagline','','','','','','','') RETURNING id""",
                    (eid, tid, uid),
                )

            p = project(e, t, participant)
            op = project(other, ot, participant)
            run(
                "INSERT INTO project_submission_members(project_id,team_id,user_id,was_leader) VALUES (%s,%s,%s,true)",
                (p, t, participant),
            )
            run("UPDATE teams SET roster_locked_at=clock_timestamp() WHERE id=%s", (t,))
            reject(
                "one project per team",
                "INSERT INTO projects SELECT gen_random_uuid(),hackathon_id,team_id,track_id,submitted_by_user_id,name,tagline,inspiration,what_it_does,how_it_was_built,challenges,accomplishments,what_we_learned,whats_next,submitted_at,updated_at,deleted_at,deleted_by_user_id,disqualified_at,disqualified_by_user_id,disqualification_reason,version FROM projects WHERE id=%s",
                (p,),
                ("23505",),
            )
            track = one(
                "INSERT INTO hackathon_tracks(hackathon_id,name) VALUES (%s,'Track') RETURNING id",
                (other,),
            )
            reject(
                "cross-event project track",
                "UPDATE projects SET track_id=%s WHERE id=%s",
                (track, p),
                ("23503",),
            )
            reject(
                "cross-team snapshot",
                "INSERT INTO project_submission_members(project_id,team_id,user_id,was_leader) VALUES (%s,%s,%s,false)",
                (p, t2, participant2),
                ("23503",),
            )
            reject(
                "two snapshot leaders",
                "INSERT INTO project_submission_members(project_id,team_id,user_id,was_leader) VALUES (%s,%s,%s,true)",
                (p, t, participant2),
                ("23505",),
            )
            reject(
                "project parent immutable",
                "UPDATE projects SET team_id=%s WHERE id=%s",
                (t2, p),
            )
            reject(
                "link HTTPS guard",
                "INSERT INTO project_links(project_id,link_type,url) VALUES (%s,'OTHER','http://example.invalid')",
                (p,),
            )
            reject(
                "media positive size",
                "INSERT INTO project_media(project_id,storage_key,mime_type,size_bytes) VALUES (%s,'key','image/png',0)",
                (p,),
            )
            run(
                "UPDATE projects SET deleted_at=clock_timestamp(),deleted_by_user_id=%s WHERE id=%s",
                (participant, p),
            )
            run(
                "UPDATE projects SET deleted_at=NULL,deleted_by_user_id=NULL WHERE id=%s",
                (p,),
            )
            ok(
                "restore retains original identity and roster",
                one(
                    "SELECT count(*) FROM project_submission_members WHERE project_id=%s",
                    (p,),
                )
                == 1
                and one(
                    "SELECT roster_locked_at IS NOT NULL FROM teams WHERE id=%s", (t,)
                ),
            )
            # Dissolution before submission retains shell, history and active event membership.
            run(
                "UPDATE teams SET dissolved_at=clock_timestamp(),leader_user_id=NULL WHERE id=%s",
                (t2,),
            )
            run(
                "DELETE FROM team_members WHERE hackathon_id=%s AND user_id=%s",
                (e, participant2),
            )
            ok(
                "LEFT history without LEFT membership",
                one(
                    "SELECT count(*) FROM team_membership_events WHERE team_id=%s AND event_type='LEFT'",
                    (t2,),
                )
                == 1
                and one(
                    "SELECT status FROM hackathon_memberships WHERE hackathon_id=%s AND user_id=%s",
                    (e, participant2),
                )
                == "ACTIVE",
            )
            for status in ["BANNED", "REVOKED", "ACTIVE"]:
                run(
                    "UPDATE hackathon_memberships SET status=%s,status_changed_by_user_id=%s,status_reason='test' WHERE hackathon_id=%s AND user_id=%s",
                    (status, owner, e, participant2),
                )
                ok(f"approved membership state {status}")
            # Owner transfer in correct order, retaining historical creator.
            run(
                "UPDATE hackathon_memberships SET role='HACKATHON_ADMIN' WHERE hackathon_id=%s AND user_id=%s",
                (e, owner),
            )
            run(
                "INSERT INTO hackathon_memberships(hackathon_id,user_id,role) VALUES (%s,%s,'ORGANIZER')",
                (e, replacement),
            )
            run(
                "UPDATE hackathons SET organizer_user_id=%s WHERE id=%s",
                (replacement, e),
            )
            run("SET CONSTRAINTS ALL IMMEDIATE")
            run("SET CONSTRAINTS ALL DEFERRED")
            ok(
                "organizer transfer retains creator",
                one("SELECT created_by_user_id FROM hackathons WHERE id=%s", (e,))
                == owner,
            )
            run(
                "INSERT INTO hackathon_memberships(hackathon_id,user_id,role) VALUES (%s,%s,'JUDGE')",
                (e, judge),
            )
            assignment = one(
                "INSERT INTO judge_assignments(hackathon_id,judge_user_id,project_id,assigned_by_user_id) VALUES (%s,%s,%s,%s) RETURNING id",
                (e, judge, p, owner),
            )
            reject(
                "cross-event assignment project",
                "INSERT INTO judge_assignments(hackathon_id,judge_user_id,project_id,assigned_by_user_id) VALUES (%s,%s,%s,%s)",
                (e, judge, op, owner),
                ("23503",),
            )
            reject(
                "duplicate assignment",
                "INSERT INTO judge_assignments(hackathon_id,judge_user_id,project_id,assigned_by_user_id) VALUES (%s,%s,%s,%s)",
                (e, judge, p, owner),
                ("23505",),
            )
            review = one(
                "INSERT INTO judge_reviews(hackathon_id,assignment_id) VALUES (%s,%s) RETURNING id",
                (e, assignment),
            )
            reject(
                "duplicate review",
                "INSERT INTO judge_reviews(hackathon_id,assignment_id) VALUES (%s,%s)",
                (e, assignment),
                ("23505",),
            )
            criterion = one(
                "INSERT INTO judging_criteria(hackathon_id,name,weight_bps,max_score) VALUES (%s,'Quality',10000,10) RETURNING id",
                (e,),
            )
            foreign_criterion = one(
                "INSERT INTO judging_criteria(hackathon_id,name,weight_bps,max_score) VALUES (%s,'Quality',10000,10) RETURNING id",
                (other,),
            )
            reject(
                "cross-event score criterion",
                "INSERT INTO judge_scores(hackathon_id,review_id,criterion_id,score) VALUES (%s,%s,%s,1)",
                (e, review, foreign_criterion),
                ("P0002", "23503"),
            )
            for score in ["-1", "11", "NaN", "Infinity"]:
                reject(
                    f"invalid score {score}",
                    "INSERT INTO judge_scores(hackathon_id,review_id,criterion_id,score) VALUES (%s,%s,%s,%s)",
                    (e, review, criterion, score),
                    ("23514", "22003"),
                )
            reject(
                "unlocked review submission",
                "UPDATE judge_reviews SET status='SUBMITTED',submitted_at=clock_timestamp() WHERE id=%s",
                (review,),
            )
            run(
                "UPDATE hackathons SET rubric_locked_at=clock_timestamp() WHERE id=%s",
                (e,),
            )
            reject(
                "coverage frozen on rubric lock",
                "UPDATE hackathons SET minimum_reviews_per_project=3 WHERE id=%s",
                (e,),
            )
            reject(
                "rubric cannot unlock",
                "UPDATE hackathons SET rubric_locked_at=NULL WHERE id=%s",
                (e,),
            )
            reject(
                "frozen criterion update",
                "UPDATE judging_criteria SET max_score=20 WHERE id=%s",
                (criterion,),
            )
            reject(
                "frozen criterion insert",
                "INSERT INTO judging_criteria(hackathon_id,name,weight_bps,max_score) VALUES (%s,'New',0,10)",
                (e,),
            )
            reject(
                "frozen criterion delete",
                "DELETE FROM judging_criteria WHERE id=%s",
                (criterion,),
            )
            reject(
                "incomplete submitted review",
                "UPDATE judge_reviews SET status='SUBMITTED',submitted_at=clock_timestamp() WHERE id=%s",
                (review,),
            )
            run(
                "INSERT INTO judge_scores(hackathon_id,review_id,criterion_id,score) VALUES (%s,%s,%s,8)",
                (e, review, criterion),
            )
            reject(
                "duplicate criterion score",
                "INSERT INTO judge_scores(hackathon_id,review_id,criterion_id,score) VALUES (%s,%s,%s,8)",
                (e, review, criterion),
                ("23505",),
            )
            run(
                "UPDATE judge_reviews SET status='SUBMITTED',submitted_at=clock_timestamp() WHERE id=%s",
                (review,),
            )
            ok("complete submitted review")
            reject(
                "submitted score update",
                "UPDATE judge_scores SET score=9 WHERE review_id=%s",
                (review,),
            )
            reject(
                "submitted score delete",
                "DELETE FROM judge_scores WHERE review_id=%s",
                (review,),
            )
            run(
                "UPDATE judge_reviews SET status='DRAFT',submitted_at=NULL WHERE id=%s",
                (review,),
            )
            run("UPDATE judge_scores SET score=9 WHERE review_id=%s", (review,))
            run(
                "UPDATE judge_reviews SET status='SUBMITTED',submitted_at=clock_timestamp() WHERE id=%s",
                (review,),
            )
            ok("atomic draft-edit-resubmit sequence")
            run(
                "UPDATE hackathons SET judging_start_at=clock_timestamp()-interval '1 second' WHERE id=%s",
                (other,),
            )
            reject(
                "coverage frozen at scheduled start",
                "UPDATE hackathons SET minimum_reviews_per_project=2 WHERE id=%s",
                (other,),
            )
            reject(
                "date change cannot reopen judging",
                "UPDATE hackathons SET judging_start_at=clock_timestamp()+interval '1 day' WHERE id=%s",
                (other,),
            )
            reject(
                "rubric frozen at scheduled start",
                "UPDATE judging_criteria SET max_score=20 WHERE id=%s",
                (foreign_criterion,),
            )
            for status in ["EXPIRED", "REVOKED"]:
                iid = one(
                    "INSERT INTO judge_invites(hackathon_id,target_email,token_hash,invited_by_user_id,status,expires_at,revoked_at) VALUES (%s,%s,%s,%s,%s,clock_timestamp()+interval '1 day',CASE WHEN %s='REVOKED' THEN clock_timestamp() END) RETURNING id",
                    (
                        e,
                        str(uuid4()) + "@example.invalid",
                        str(uuid4()),
                        owner,
                        status,
                        status,
                    ),
                )
                reject(
                    f"{status} invitation cannot accept",
                    "UPDATE judge_invites SET status='ACCEPTED',accepted_at=clock_timestamp(),accepted_by_user_id=%s,revoked_at=NULL WHERE id=%s",
                    (judge, iid),
                )
                reject(
                    f"{status} invitation cannot reopen",
                    "UPDATE judge_invites SET status='PENDING',revoked_at=NULL WHERE id=%s",
                    (iid,),
                )
            iid = one(
                "INSERT INTO judge_invites(hackathon_id,target_email,token_hash,invited_by_user_id,expires_at) VALUES (%s,'invite@example.invalid','pending-hash',%s,clock_timestamp()+interval '1 day') RETURNING id",
                (e, owner),
            )
            reject(
                "canonical pending invitation unique",
                "INSERT INTO judge_invites(hackathon_id,target_email,token_hash,invited_by_user_id,expires_at) VALUES (%s,' INVITE@example.invalid ','other-hash',%s,clock_timestamp()+interval '1 day')",
                (e, owner),
                ("23505",),
            )
            reject(
                "DECLINED invitation forbidden",
                "UPDATE judge_invites SET status='DECLINED' WHERE id=%s",
                (iid,),
            )
            run(
                "UPDATE judge_invites SET status='ACCEPTED',accepted_at=clock_timestamp(),accepted_by_user_id=%s WHERE id=%s",
                (judge, iid),
            )
            ok("pending nonexpired invitation accepts structurally")
            # Clock check must reject stale PENDING even with a backdated acceptance.
            stale = one(
                "INSERT INTO judge_invites(hackathon_id,target_email,token_hash,invited_by_user_id,created_at,expires_at) VALUES (%s,'stale@example.invalid','stale-hash',%s,clock_timestamp()-interval '2 days',clock_timestamp()-interval '1 day') RETURNING id",
                (e, owner),
            )
            reject(
                "backdating cannot accept expired pending invite",
                "UPDATE judge_invites SET status='ACCEPTED',accepted_at=created_at+interval '1 hour',accepted_by_user_id=%s WHERE id=%s",
                (judge, stale),
            )
            ti = one(
                "INSERT INTO team_invites(hackathon_id,team_id,invited_by_user_id,token_hash,invite_kind,max_uses,expires_at) VALUES (%s,%s,%s,'team-hash','SHARE_LINK',2,clock_timestamp()+interval '1 day') RETURNING id",
                (e, t, participant),
            )
            run(
                "INSERT INTO team_invite_redemptions(invite_id,user_id,team_id) VALUES (%s,%s,%s)",
                (ti, participant2, t),
            )
            reject(
                "duplicate invite redemption",
                "INSERT INTO team_invite_redemptions(invite_id,user_id,team_id) VALUES (%s,%s,%s)",
                (ti, participant2, t),
                ("23505",),
            )
            reject(
                "invite use limit",
                "UPDATE team_invites SET use_count=3 WHERE id=%s",
                (ti,),
            )
            run(
                "INSERT INTO audit_events(hackathon_id,actor_user_id,action,entity_type,entity_id) VALUES (%s,%s,'TEST','project',%s)",
                (e, owner, p),
            )
            snapshot = '{"schema_version":1,"scoring_method":"weighted_normalized_mean_v1","minimum_reviews_per_project":2,"criteria":[],"included_reviews":[],"excluded_projects":[]}'
            # Snapshot service data is intentionally abbreviated: SQL checks structure, not calculation truth.
            reject(
                "snapshot must include configured coverage",
                "INSERT INTO result_publications(hackathon_id,publication_number,published_by_user_id,scoring_method,calculation_snapshot) VALUES (%s,1,%s,'weighted_normalized_mean_v1','{}')",
                (e, owner),
            )
            pub = one(
                "INSERT INTO result_publications(hackathon_id,publication_number,published_by_user_id,scoring_method,calculation_snapshot) VALUES (%s,1,%s,'weighted_normalized_mean_v1',%s) RETURNING id",
                (e, owner, snapshot),
            )
            reject(
                "result requires configured review_count",
                "INSERT INTO result_entries(hackathon_id,publication_id,project_id,final_score,review_count,rank,project_name_snapshot) VALUES (%s,%s,%s,90,1,1,'Project')",
                (e, pub, p),
            )
            run(
                "INSERT INTO result_entries(hackathon_id,publication_id,project_id,final_score,review_count,rank,project_name_snapshot) VALUES (%s,%s,%s,90,2,1,'Project')",
                (e, pub, p),
            )
            award = one(
                "INSERT INTO awards(hackathon_id,name) VALUES (%s,'Prize') RETURNING id",
                (e,),
            )
            run(
                "INSERT INTO result_awards(hackathon_id,publication_id,award_id,project_id,award_name_snapshot,selected_by_user_id) VALUES (%s,%s,%s,%s,'Prize',%s)",
                (e, pub, award, p, owner),
            )
            run(
                "UPDATE hackathons SET current_result_publication_id=%s WHERE id=%s",
                (pub, e),
            )
            ok("atomic publication build then seal")
            reject(
                "sealed publication cannot add entries",
                "INSERT INTO result_entries(hackathon_id,publication_id,project_id,final_score,review_count,rank,project_name_snapshot) VALUES (%s,%s,%s,90,2,1,'Project')",
                (e, pub, p),
            )
            reject(
                "sealed publication cannot add awards",
                "INSERT INTO result_awards(hackathon_id,publication_id,award_id,project_id,award_name_snapshot,selected_by_user_id) VALUES (%s,%s,%s,%s,'Prize',%s)",
                (e, pub, award, p, owner),
            )
            reject(
                "publication pointer cannot clear",
                "UPDATE hackathons SET current_result_publication_id=NULL WHERE id=%s",
                (e,),
            )
            reject(
                "publication sequence cannot skip",
                "INSERT INTO result_publications(hackathon_id,publication_number,supersedes_publication_id,published_by_user_id,scoring_method,calculation_snapshot,correction_reason) VALUES (%s,3,%s,%s,'weighted_normalized_mean_v1',%s,'correction')",
                (e, pub, owner, snapshot),
            )
            pub2 = one(
                "INSERT INTO result_publications(hackathon_id,publication_number,supersedes_publication_id,published_by_user_id,scoring_method,calculation_snapshot,correction_reason) VALUES (%s,2,%s,%s,'weighted_normalized_mean_v1',%s,'correction') RETURNING id",
                (e, pub, owner, snapshot),
            )
            run(
                "UPDATE hackathons SET current_result_publication_id=%s WHERE id=%s",
                (pub2, e),
            )
            reject(
                "publication pointer cannot revert",
                "UPDATE hackathons SET current_result_publication_id=%s WHERE id=%s",
                (pub, e),
            )
            ok(
                "correction preserves old snapshot",
                one(
                    "SELECT count(*) FROM result_entries WHERE publication_id=%s",
                    (pub,),
                )
                == 1,
            )
            immutable = [
                "platform_terms_versions",
                "hackathon_rules_versions",
                "hackathon_registrations",
                "team_membership_events",
                "team_invite_redemptions",
                "project_submission_members",
                "audit_events",
                "result_publications",
                "result_entries",
                "result_awards",
            ]
            for table in immutable:
                # All have at least one fixture row; UPDATE no-op must still be rejected.
                col = one(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema='dogfood' AND table_name=%s ORDER BY ordinal_position LIMIT 1",
                    (table,),
                )
                reject(
                    f"immutable {table} UPDATE",
                    sql.SQL("UPDATE {} SET {}={}").format(
                        sql.Identifier(table), sql.Identifier(col), sql.Identifier(col)
                    ),
                )
                reject(
                    f"immutable {table} DELETE",
                    sql.SQL("DELETE FROM {}").format(sql.Identifier(table)),
                )
            reject(
                "restrict deleting referenced user",
                "DELETE FROM users WHERE id=%s",
                (owner,),
                ("23503",),
            )
            run("SET CONSTRAINTS ALL IMMEDIATE")
            ok("all final deferred constraints satisfied")
        ok(
            "all fixtures rolled back",
            c.execute("SELECT count(*) FROM dogfood.users").fetchone()[0] == 0,
        )
    print(f"{passed} checks passed")


if __name__ == "__main__":
    main()
