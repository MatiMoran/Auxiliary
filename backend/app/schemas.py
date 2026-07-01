from pydantic import BaseModel
from datetime import datetime


class NoteCreate(BaseModel):
    title: str = ""
    content: str


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    data: list[NoteResponse]


class NoteSingleResponse(BaseModel):
    data: NoteResponse


class DeleteResponse(BaseModel):
    data: dict = {"ok": True}


class HealthResponse(BaseModel):
    status: str = "ok"


class ErrorResponse(BaseModel):
    detail: str
