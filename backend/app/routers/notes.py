from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=schemas.NoteListResponse)
def list_notes(db: Session = Depends(get_db)):
    notes = crud.get_notes(db)
    return schemas.NoteListResponse(data=notes)


@router.get("/{note_id}", response_model=schemas.NoteSingleResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return schemas.NoteSingleResponse(data=note)


@router.post("", response_model=schemas.NoteSingleResponse, status_code=201)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    db_note = crud.create_note(db, note)
    return schemas.NoteSingleResponse(data=db_note)


@router.put("/{note_id}", response_model=schemas.NoteSingleResponse)
def update_note(
    note_id: int, note: schemas.NoteUpdate, db: Session = Depends(get_db)
):
    db_note = crud.update_note(db, note_id, note)
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return schemas.NoteSingleResponse(data=db_note)


@router.delete("/{note_id}", response_model=schemas.DeleteResponse)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return schemas.DeleteResponse()
