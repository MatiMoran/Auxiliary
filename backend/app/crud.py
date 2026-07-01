from sqlalchemy.orm import Session
from app import models, schemas


def get_notes(db: Session) -> list[models.Note]:
    return db.query(models.Note).order_by(models.Note.updated_at.desc()).all()


def get_note(db: Session, note_id: int) -> models.Note | None:
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def create_note(db: Session, note: schemas.NoteCreate) -> models.Note:
    db_note = models.Note(title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_note(
    db: Session, note_id: int, note: schemas.NoteUpdate
) -> models.Note | None:
    db_note = get_note(db, note_id)
    if not db_note:
        return None
    update_data = note.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int) -> bool:
    db_note = get_note(db, note_id)
    if not db_note:
        return False
    db.delete(db_note)
    db.commit()
    return True
