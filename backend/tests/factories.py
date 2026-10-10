"""Small helpers for creating valid rows in tests. Values are obvious test data only."""
import hashlib
from datetime import datetime, timezone
from itertools import count

from sqlalchemy.orm import Session

from app.models import Source, SourceVersion, User
from app.models.enums import ApprovalStatus, Permission, SourceCategory, VerificationStatus

_n = count(1)


def make_user(session: Session, **kw) -> User:
    i = next(_n)
    user = User(email=kw.pop("email", f"test{i}@example.test"), **kw)
    session.add(user)
    session.flush()
    return user


def make_source(session: Session, *, approved: bool = False, **kw) -> Source:
    i = next(_n)
    fields = dict(
        slug=f"test-source-{i}",
        title=f"Test source {i}",
        category=SourceCategory.EDUCATIONAL,
        language="en",
    )
    if approved:
        fields.update(
            rights_holder="Test Rights Holder",
            license_name="Test License",
            commercial_use=Permission.ALLOWED,
            license_verified_at=datetime.now(timezone.utc),
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
        )
    fields.update(kw)
    source = Source(**fields)
    session.add(source)
    session.flush()
    return source


def make_version(session: Session, source: Source, label: str = "v1", content: str = "x") -> SourceVersion:
    version = SourceVersion(
        source_id=source.id,
        version_label=label,
        checksum_sha256=hashlib.sha256(content.encode()).hexdigest(),
    )
    session.add(version)
    session.flush()
    return version
