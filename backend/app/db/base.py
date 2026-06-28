# Import all models here so that Alembic's env.py can see Base.metadata containing everything.
from app.models.base import Base
from app.models.region import Region
from app.models.user import User
from app.models.department import Department
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.status_history import StatusHistory
from app.models.notification import Notification
from app.models.badge import Badge
from app.models.user_badge import UserBadge
from app.models.issue_follower import IssueFollower
