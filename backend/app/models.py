"""Import registry for all 34 DogFood models and the shared Base.

Importing this module is sufficient for Alembic discovery. Domain model modules
import only core.model_base, so registration never creates circular imports.
"""

from app.core.model_base import Base
from app.auth.models import AuthSession
from app.users.models import User
from app.users.models import PlatformTermsVersion
from app.hackathons.models import Hackathon
from app.hackathons.models import HackathonMembership
from app.hackathons.models import HackathonRulesVersion
from app.hackathons.models import HackathonTrack
from app.hackathons.models import HackathonSponsor
from app.hackathons.models import HackathonScheduleItem
from app.registrations.models import HackathonRegistration
from app.registrations.models import ParticipantProfile
from app.teams.models import Team
from app.teams.models import TeamMember
from app.teams.models import TeamMembershipEvent
from app.teams.models import TeamInvite
from app.teams.models import TeamInviteRedemption
from app.projects.models import Project
from app.projects.models import ProjectSubmissionMember
from app.projects.models import ProjectLink
from app.projects.models import ProjectMedia
from app.projects.models import ProjectTechnology
from app.judging.models import JudgeInvite
from app.judging.models import JudgeProfile
from app.judging.models import JudgeAssignment
from app.judging.models import JudgingCriterion
from app.judging.models import JudgeReview
from app.judging.models import JudgeScore
from app.awards.models import Award
from app.results.models import ResultPublication
from app.results.models import ResultEntry
from app.results.models import ResultAward
from app.governance.models import HackathonChangeRequest
from app.announcements.models import PlatformAnnouncement
from app.audit.models import AuditEvent

__all__ = [
    "Base",
    "AuthSession",
    "User",
    "PlatformTermsVersion",
    "Hackathon",
    "HackathonMembership",
    "HackathonRulesVersion",
    "HackathonTrack",
    "HackathonSponsor",
    "HackathonScheduleItem",
    "HackathonRegistration",
    "ParticipantProfile",
    "Team",
    "TeamMember",
    "TeamMembershipEvent",
    "TeamInvite",
    "TeamInviteRedemption",
    "Project",
    "ProjectSubmissionMember",
    "ProjectLink",
    "ProjectMedia",
    "ProjectTechnology",
    "JudgeInvite",
    "JudgeProfile",
    "JudgeAssignment",
    "JudgingCriterion",
    "JudgeReview",
    "JudgeScore",
    "Award",
    "ResultPublication",
    "ResultEntry",
    "ResultAward",
    "HackathonChangeRequest",
    "PlatformAnnouncement",
    "AuditEvent",
]
