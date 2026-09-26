# DogFood Hackathon Platform — Canonical Domain Rules

This document is the source of truth for DogFood product behavior.

## Product Goal

Build a production-like hackathon platform focused on:

1. Hackathon discovery and registration
2. Solo/team participation
3. Team invitations
4. Project submission
5. Private submissions before results
6. Configurable judging
7. Anonymous judge workspace
8. Rankings
9. Winner selection
10. Public results/project showcase

Prioritize correctness and polished T1/T2 functionality over unnecessary
stretch features.

---

# Roles

Roles are NOT combinable inside the same hackathon.

Global:

- DOGFOOD_SUPER_ADMIN

Hackathon scoped:

- ORGANIZER
- HACKATHON_ADMIN
- JUDGE
- PARTICIPANT

TEAM_LEADER is a team-level responsibility, not an additional hackathon role.

A PARTICIPANT may be the leader of their team.

---

# Organizer

There is one Organizer per hackathon.

Organizer can:

- edit hackathon configuration
- configure registration dates
- configure submission deadline
- configure judging dates
- configure team size rules
- create/edit tracks
- configure judging criteria
- create/remove hackathon admins
- invite/remove judges
- assign judges
- view all submissions
- view participant identities
- inspect calculated rankings
- select winners
- publish results
- configure post-results project visibility

Organizer project edits must be exceptional overrides and must create an
audit-log entry with a reason.

Organizer cannot directly delete the hackathon or transfer ownership.

Those actions require approval from DOGFOOD_SUPER_ADMIN.

---

# Hackathon Admin

Hackathon Admin is organizer-appointed operational staff.

Admin can:

- view submissions
- view participant/team identities
- invite judges
- assign judges
- remove judges
- manage participants
- ban/remove a participant from that hackathon
- view judging progress
- view rankings
- select/propose winners
- configure whether public results show winners only or all projects

Admin cannot:

- modify contestant project content
- change core hackathon settings
- change deadlines
- manage Organizer ownership
- directly delete the hackathon
- publish final results

---

# DogFood Super Admin

Global platform administrator.

Can:

- manage platform-level moderation
- create/edit/delete/pin platform announcements
- review hackathon deletion requests
- review ownership-transfer requests
- approve or reject those requests
- intervene for platform safety/integrity

Normal hackathon operation should remain with the Organizer/Admin.

---

# Participants and Teams

Whether solo participation is allowed is configured per hackathon.

Examples:

min_team_size=1, max_team_size=1
=> solo only

min_team_size=1, max_team_size=5
=> solo or team

min_team_size=2, max_team_size=5
=> team required

max_team_size=NULL
=> no configured upper limit

Each participant may belong to only one team per hackathon.

A solo participant is represented internally as a one-person team.

Only Team Leader can:

- invite members
- remove members before submission
- edit team details
- create/submit project
- edit project before deadline
- delete project before deadline

Normal team members can view their own project but cannot edit it.

Team members may leave only before project submission.

Once the project is submitted, official team membership is frozen.

---

# Team Invitations

Team Leader generates/sends an invitation.

Invite may be email/token/link based.

Invite must:

- have an expiration
- be single-purpose
- be revocable
- not allow joining a second team in the same hackathon
- enforce hackathon team-size limits

---

# Registration

User must join/register for a hackathon before competing.

Registration captures minimal information such as:

- SOLO / LOOKING_FOR_TEAM / HAVE_TEAM
- referral source
- country
- age eligibility confirmation
- rules acceptance
- terms acceptance

Avoid collecting unnecessary personal data.

---

# Project Submission

Exactly one project per team per hackathon.

Project fields include:

- project name
- elevator pitch
- inspiration
- what it does
- how we built it
- challenges
- accomplishments
- what we learned
- what's next
- technologies / built with
- images
- GitHub URL
- live demo URL
- YouTube URL
- Google Drive URL
- OneDrive URL
- other relevant project URLs

Use a generic project_links table instead of adding one database column per
provider.

There is no persistent draft project state.

Project row is created when Team Leader submits.

After submission and before deadline:
- Team Leader may edit.

After submission deadline:
- project is locked.

Admin cannot modify project content.

Organizer override edits require:
- explicit reason
- audit log

---

# Project Privacy

Before result publication:

Guest:
- cannot see submitted projects

Participant:
- cannot see competitors' submissions

Judge:
- can see only assigned projects

Admin:
- can see submissions and participants

Organizer:
- can see submissions and participants

After results publication the hackathon chooses:

- WINNERS_ONLY
- ALL_PROJECTS

---

# Judge Privacy

Judging is blind.

Judge may see:

- project name
- elevator pitch
- project story
- technologies
- screenshots/media
- GitHub URL if submitted
- demo URL
- demo video/drive links
- number of participants

Judge must NOT see:

- team name
- participant names
- participant emails
- usernames
- profile photos
- LinkedIn profiles
- private team metadata
- other judges' scores
- average score while judging
- current ranking

Do not merely hide these fields in the frontend.

The Judge API response must not contain them.

---

# Judge Assignment

Judges may access ONLY explicitly assigned projects.

Authorization must verify the assignment server-side for every request.

A changed URL/project ID must not expose an unassigned project.

---

# Judging Criteria

Organizer configures criteria.

Example:

Innovation: 25%
Technical Execution: 30%
Impact: 20%
UX: 15%
Presentation: 10%

Requirements:

- weights must be valid
- total configured weight should equal 100%
- score must be within criterion bounds
- criteria should be frozen once judging starts unless an authorized,
  audited exceptional change is made

---

# Judge Scores

Judge may:

- create own review
- view own review
- edit own scores until judging_end_at
- submit review

Judge may NOT:

- score unassigned projects
- inspect another judge's review
- inspect average score
- inspect rankings
- delete another review
- score after judging closes

---

# Ranking

Calculated result is derived from judge scores.

Do not make a manually stored total score the primary source of truth.

Weighted criterion score:

(score / max_score) * weight

Project ranking may use an aggregate across completed judge reviews.

Ranking is advisory until Organizer/Admin confirms winners.

---

# Winner Flow

Judging closes
→ calculate ranking
→ Admin/Organizer review
→ Admin or Organizer selects winners
→ Organizer confirms
→ Organizer publishes results
→ configured projects become public

Winner selection and result publication are separate permissions.

---

# Results Visibility

result_gallery_mode:

- WINNERS_ONLY
- ALL_PROJECTS

Before results_published_at:
- public gallery must not expose private submissions.

---

# Hackathon Deletion and Ownership Transfer

Organizer must create a request containing a reason.

Request types:

- DELETE_HACKATHON
- TRANSFER_OWNERSHIP

Statuses:

- PENDING
- APPROVED
- REJECTED

Only DOGFOOD_SUPER_ADMIN approves/rejects.

Never immediately delete a hackathon from an Organizer request.

Prefer soft deletion/archival before irreversible deletion.

---

# Announcements

Current MVP:

DOGFOOD_SUPER_ADMIN manages platform announcements.

If hackathon-specific announcements are added later, separate:

- platform_announcements
- hackathon_announcements

rather than mixing permission scopes.

---

# Security Principles

- deny by default
- backend authorization is authoritative
- frontend visibility is not authorization
- prevent cross-hackathon IDOR
- check ownership on mutations
- check judge assignment on judging reads/writes
- enforce deadlines on server
- validate team-size constraints transactionally
- use audit logs for privileged overrides
- avoid exposing unnecessary PII
- never share Organizer credentials
