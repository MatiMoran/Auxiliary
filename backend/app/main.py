from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import notes, health
from app.exceptions import global_exception_handler

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notas App API",
    description="API REST para la aplicación de notas Markdown",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(health.router)
app.include_router(notes.router)
