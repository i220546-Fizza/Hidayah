"""Data written through one connection pool must survive that pool being thrown away."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import Bookmark, Surah, User, Verse
from tests.conftest import TEST_DATABASE_URL
from tests.factories import make_source, make_version


def test_committed_data_survives_new_engine_and_cleanup(migrated_engine):
    engine1 = create_engine(TEST_DATABASE_URL)
    with Session(engine1) as s:
        user = User(email="persist@example.test")
        s.add(user)
        src_version = None
        src = make_source(s)
        src_version = make_version(s, src)
        s.add(Surah(number=1, name_arabic="x", name_english="Test", verse_count=7))
        s.flush()
        verse = Verse(surah_number=1, verse_number=1, text_arabic="t", source_version_id=src_version.id)
        s.add(verse)
        s.flush()
        s.add(Bookmark(user_id=user.id, verse_id=verse.id))
        s.commit()
        user_id = user.id
    engine1.dispose()  # simulates the backend process stopping

    engine2 = create_engine(TEST_DATABASE_URL)  # "restarted" backend
    try:
        with Session(engine2) as s:
            found = s.get(User, user_id)
            assert found is not None and found.email == "persist@example.test"
            assert s.scalar(text("SELECT count(*) FROM bookmarks")) == 1
    finally:
        with Session(engine2) as s:
            s.execute(text("DELETE FROM bookmarks"))
            s.execute(text("DELETE FROM users WHERE email='persist@example.test'"))
            s.execute(text("DELETE FROM verses"))
            s.execute(text("DELETE FROM surahs"))
            s.execute(text("DELETE FROM source_versions"))
            s.execute(text("DELETE FROM sources"))
            s.commit()
        engine2.dispose()
