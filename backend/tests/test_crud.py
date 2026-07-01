import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models, schemas, crud

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_note(db):
    note = schemas.NoteCreate(title="Test", content="Content")
    result = crud.create_note(db, note)
    assert result.id is not None
    assert result.title == "Test"
    assert result.content == "Content"


def test_get_notes_empty(db):
    notes = crud.get_notes(db)
    assert notes == []


def test_get_notes_returns_all(db):
    crud.create_note(db, schemas.NoteCreate(title="A", content="A"))
    crud.create_note(db, schemas.NoteCreate(title="B", content="B"))
    notes = crud.get_notes(db)
    assert len(notes) == 2


def test_get_note(db):
    created = crud.create_note(db, schemas.NoteCreate(title="T", content="C"))
    result = crud.get_note(db, created.id)
    assert result is not None
    assert result.id == created.id


def test_get_nonexistent_note(db):
    result = crud.get_note(db, 999)
    assert result is None


def test_update_note(db):
    created = crud.create_note(db, schemas.NoteCreate(title="Old", content="Old"))
    update = schemas.NoteUpdate(title="New")
    result = crud.update_note(db, created.id, update)
    assert result is not None
    assert result.title == "New"
    assert result.content == "Old"


def test_update_nonexistent_note(db):
    update = schemas.NoteUpdate(title="X")
    result = crud.update_note(db, 999, update)
    assert result is None


def test_delete_note(db):
    created = crud.create_note(db, schemas.NoteCreate(title="D", content="D"))
    result = crud.delete_note(db, created.id)
    assert result is True
    assert crud.get_note(db, created.id) is None


def test_delete_nonexistent_note(db):
    result = crud.delete_note(db, 999)
    assert result is False
