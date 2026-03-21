"""Model registry — import all ORM models here so SQLAlchemy can resolve
all relationships and forward references before any queries run.
This module must be imported before any database operations."""

from app.domain.user.models import User  # noqa: F401
from app.domain.profile.models import Profile  # noqa: F401
from app.domain.theme.models import Theme  # noqa: F401
from app.domain.subscription.models import Subscription  # noqa: F401
from app.domain.link.models import Link  # noqa: F401
from app.domain.contact.models import Contact  # noqa: F401
from app.domain.media.models import Media  # noqa: F401
