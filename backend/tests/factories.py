"""Small helpers for creating valid rows in tests. Values are obvious test data only."""
import hashlib
from datetime import datetime, timezone
from itertools import count

from sqlalchemy.orm import Session

from app.models import Source, SourceVersion, User
from app.models.enums import Permission, SourceCategory, SourceStatus, VerificationStatus

_n = count(1)


def make_user(session: Session, **kw) -> User:
    i = next(_n)
    user = User(email=kw.pop("email", f"test{i}@example.com"), **kw)
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
            storage_permission=Permission.ALLOWED,
            indexing_permission=Permission.ALLOWED,
            rag_permission=Permission.ALLOWED,
            license_verified_at=datetime.now(timezone.utc),
            verification_status=VerificationStatus.VERIFIED,
            approval_status=SourceStatus.APPROVED,
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


def make_verse(session: Session, surah: int = 1, verse: int = 1):
    from app.models import Surah, Verse

    if session.get(Surah, surah) is None:
        session.add(Surah(number=surah, name_arabic="x", name_english=f"Test surah {surah}", verse_count=300))
        session.flush()
    version = make_version(session, make_source(session), label=f"v-{next(_n)}", content=f"verse-{next(_n)}")
    row = Verse(surah_number=surah, verse_number=verse, text_arabic="test", source_version_id=version.id)
    session.add(row)
    session.flush()
    return row


def make_hadith(session: Session):
    from app.models import HadithCollection, HadithRecord

    source = make_source(session)
    version = make_version(session, source, label=f"v-{next(_n)}", content=f"hadith-{next(_n)}")
    coll = HadithCollection(slug=f"coll-{next(_n)}", name_english="Test collection", source_id=source.id)
    session.add(coll)
    session.flush()
    row = HadithRecord(collection_id=coll.id, hadith_number="1", source_version_id=version.id)
    session.add(row)
    session.flush()
    return row


def make_dua(session: Session):
    from app.models import Dua, DuaCategory
    from app.models.enums import DuaProvenance

    cat = DuaCategory(slug=f"cat-{next(_n)}", name_english="Test")
    session.add(cat)
    session.flush()
    row = Dua(category_id=cat.id, title="t", arabic_text="x", provenance=DuaProvenance.EDITORIAL)
    session.add(row)
    session.flush()
    return row
