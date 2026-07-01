# Notas App API — Plan de Implementación

**Versión:** 1.0
**Propósito:** Guía exhaustiva para que agents implementen la API REST de la aplicación Notas App.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura](#3-arquitectura)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [API Endpoints](#6-api-endpoints)
7. [Autenticación](#7-autenticación)
8. [Base de Datos — Estrategia de Abstracción](#8-base-de-datos--estrategia-de-abstracción)
9. [Manejo de Errores](#9-manejo-de-errores)
10. [Logging](#10-logging)
11. [Plan de Implementación Detallado](#11-plan-de-implementación-detallado)
12. [Especificación por Archivo](#12-especificación-por-archivo)
13. [Tests](#13-tests)
14. [Infraestructura](#14-infraestructura)
15. [Comandos Útiles](#15-comandos-útiles)

---

## 1. Resumen Ejecutivo

Backend de una aplicación Android de bloc de notas con Markdown. El backend es un servidor **FastAPI** con **PostgreSQL** en producción y **SQLite** en desarrollo local. Sincronización REST con API Key. Un solo usuario (el dueño).

**Principios:**
- API REST stateless
- API Key en header `X-API-Key` en cada request
- Servidor = única fuente de verdad
- Sin autenticación de usuarios múltiples
- Sin caché offline
- Sin paginación (MVP, 1 usuario)
- Sin async (sync SQLAlchemy es suficiente para MVP)

---

## 2. Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|---|---|---|---|
| Lenguaje | Python | 3.11+ | Runtime |
| Framework web | FastAPI | 0.111+ | API REST |
| ORM | SQLAlchemy | 2.0+ | Abstracción de base de datos |
| Validación | Pydantic | 2.7+ | Schemas request/response |
| Configuración | Pydantic-Settings | 2.2+ | Variables de entorno |
| Base de datos (dev) | SQLite | — | Desarrollo local |
| Base de datos (prod) | PostgreSQL | 16+ | Producción (Supabase) |
| Migraciones | Alembic | 1.13+ | Versionado de esquema |
| Auth | API Key + hmac | — | Validación en cada request |
| Servidor ASGI | Uvicorn | 0.29+ | Servir la app |
| Driver PostgreSQL | psycopg2-binary | 2.9+ | Conexión a PostgreSQL |
| Tests | pytest + httpx | 8.0+ / 0.27+ | TestClient + asincrónico |
| Dependencias | Poetry | — | Gestión de paquetes |

---

## 3. Arquitectura

```
┌─────────────────────┐      HTTP/JSON       ┌──────────────────────────────┐
│  Android App        │ ◄──────────────────► │  FastAPI Server              │
│  (Kotlin + Compose) │   X-API-Key header   │  Python 3.11                 │
│                     │   GET/POST/PUT/DELETE │                              │
│                     │                      │  app/main.py                 │
│                     │                      │  app/routers/notes.py        │
│                     │                      │  app/routers/health.py       │
│                     │                      │  app/crud.py                 │
│                     │                      │  app/auth.py                 │
└─────────────────────┘                      └──────────┬───────────────────┘
                                                         │
                                                 ┌───────┴────────┐
                                                 │  SQLAlchemy    │
                                                 │  ORM           │
                                                 └───────┬────────┘
                                                         │
                                            ┌────────────┴────────────┐
                                            │                         │
                                    ┌───────┴───────┐       ┌────────┴────────┐
                                    │  SQLite (dev) │       │ PostgreSQL     │
                                    │  local .db    │       │ (Supabase prod)│
                                    └───────────────┘       └─────────────────┘
```

### Flujo de un request típico

1. Android envía `GET /api/notes` con header `X-API-Key`
2. FastAPI recibe el request
3. Middleware/dependencia `verify_api_key` valida la API Key (comparación constant-time con `hmac.compare_digest`)
4. Si es inválida → `401 Unauthorized`
5. Si es válida → router `notes.py` llama a `crud.get_notes()`
6. `crud.py` ejecuta query via SQLAlchemy Session
7. SQLAlchemy traduce a SQL según el dialecto (SQLite o PostgreSQL)
8. Respuesta se serializa con Pydantic → JSON → Android

---

## 4. Estructura del Proyecto

```
backend/                          # Raíz del backend
├── app/                          # Código fuente
│   ├── __init__.py               # Paquete Python
│   ├── main.py                   # FastAPI app, CORS, error handlers, startup
│   ├── config.py                 # Settings desde env vars + logging setup
│   ├── database.py               # Engine SQLAlchemy + SessionLocal + get_db
│   ├── models.py                 # SQLAlchemy ORM: Note
│   ├── schemas.py                # Pydantic: request/response models
│   ├── crud.py                   # Funciones de acceso a datos
│   ├── auth.py                   # Dependencia FastAPI: verify_api_key
│   ├── exceptions.py             # Excepciones custom + handlers
│   └── routers/
│       ├── __init__.py           # Paquete Python
│       ├── notes.py              # /api/notes CRUD endpoints
│       └── health.py             # /api/health endpoint
├── tests/                        # Tests
│   ├── __init__.py
│   ├── conftest.py               # Fixtures globales (client, db, auth override)
│   ├── test_health.py            # Health endpoint tests
│   ├── test_auth.py              # API Key validation tests
│   ├── test_notes.py             # CRUD integration tests
│   └── test_crud.py              # CRUD unit tests
├── alembic/                      # Migraciones
│   ├── env.py                    # Configuración de Alembic
│   ├── script.py.mako            # Template para migraciones
│   └── versions/                 # Archivos de migración
├── alembic.ini                   # Configuración de Alembic
├── docs/
│   └── api/
│       └── README.md             # Este documento
├── pyproject.toml                # Poetry: dependencias y config
├── .env.example                  # Template de variables de entorno
├── .gitignore                    # Archivos ignorados por git
├── Makefile                      # Comandos útiles (dev, test, migrate)
├── Dockerfile                    # Imagen Docker para producción
└── render.yaml                   # Blueprint Render (deploy)
```

---

## 5. Modelo de Datos

### Tabla: `notes`

| Columna | Tipo SQLAlchemy | Tipo PostgreSQL | Nullable | Default | Descripción |
|---|---|---|---|---|---|
| `id` | `Integer, primary_key` | `SERIAL PRIMARY KEY` | NO | auto-increment | Identificador único |
| `title` | `String(255)` | `VARCHAR(255)` | SÍ | `""` | Título de la nota |
| `content` | `Text` | `TEXT` | NO | — | Contenido en Markdown |
| `created_at` | `DateTime` | `TIMESTAMP` | NO | `func.now()` | Fecha de creación |
| `updated_at` | `DateTime` | `TIMESTAMP` | NO | `func.now()` + onupdate | Última modificación |

### SQLAlchemy Model (`app/models.py`)

```python
class Note(Base):
    __tablename__ = "notes"

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
```

### Pydantic Schemas (`app/schemas.py`)

| Schema | Campos | Uso |
|---|---|---|
| `NoteCreate` | `title: str = ""`, `content: str` | Request body POST |
| `NoteUpdate` | `title: str \| None = None`, `content: str \| None = None` | Request body PUT |
| `NoteResponse` | `id, title, content, created_at, updated_at` | Response body individual |
| `NoteListResponse` | `data: list[NoteResponse]` | Response body lista |
| `NoteSingleResponse` | `data: NoteResponse` | Response body individual envuelto |
| `DeleteResponse` | `data: dict = {"ok": True}` | Response body DELETE |
| `HealthResponse` | `status: str = "ok"` | Response body health |
| `ErrorResponse` | `detail: str` | Response body error |

---

## 6. API Endpoints

Base URL: `http://<host>:<port>` (sin prefijo `/api` en la base, el prefijo está en cada router)

| Método | Ruta | Auth | Request Body | Response (éxito) | Errores |
|---|---|---|---|---|---|
| `GET` | `/api/health` | No | — | `200: {"status": "ok"}` | 500 |
| `GET` | `/api/notes` | Sí | — | `200: {"data": [NoteResponse]}` | 401, 500 |
| `GET` | `/api/notes/{id}` | Sí | — | `200: {"data": NoteResponse}` | 401, 404, 500 |
| `POST` | `/api/notes` | Sí | `NoteCreate` | `201: {"data": NoteResponse}` | 401, 422, 500 |
| `PUT` | `/api/notes/{id}` | Sí | `NoteUpdate` | `200: {"data": NoteResponse}` | 401, 404, 422, 500 |
| `DELETE` | `/api/notes/{id}` | Sí | — | `200: {"data": {"ok": true}}` | 401, 404, 500 |

### Headers requeridos en endpoints con Auth

```
X-API-Key: <api_key_value>
Content-Type: application/json
```

### Códigos de error HTTP

| Código | Significado | Causa |
|---|---|---|
| `401` | Unauthorized | API Key inválida o faltante |
| `404` | Not Found | La nota con ese ID no existe |
| `422` | Unprocessable Entity | Datos inválidos (falló validación Pydantic) |
| `500` | Internal Server Error | Error inesperado (loggeado en servidor) |

### Ejemplos de Requests/Responses

**GET /api/health**
```
Response 200:
{"status": "ok"}
```

**GET /api/notes**
```
Response 200:
{
  "data": [
    {
      "id": 1,
      "title": "Mi primera nota",
      "content": "# Hola\n\nEsto es **markdown**",
      "created_at": "2026-06-30T10:00:00",
      "updated_at": "2026-06-30T10:00:00"
    }
  ]
}
```

**POST /api/notes**
```
Request:
{
  "title": "Nota nueva",
  "content": "Contenido en **markdown**"
}

Response 201:
{
  "data": {
    "id": 2,
    "title": "Nota nueva",
    "content": "Contenido en **markdown**",
    "created_at": "2026-06-30T11:00:00",
    "updated_at": "2026-06-30T11:00:00"
  }
}
```

**PUT /api/notes/1**
```
Request (solo campos a actualizar):
{
  "title": "Título actualizado"
}

Response 200:
{
  "data": {
    "id": 1,
    "title": "Título actualizado",
    "content": "# Hola\n\nEsto es **markdown**",
    "created_at": "2026-06-30T10:00:00",
    "updated_at": "2026-06-30T11:30:00"
  }
}
```

**DELETE /api/notes/1**
```
Response 200:
{
  "data": {
    "ok": true
  }
}
```

---

## 7. Autenticación

### Server Side

1. Al iniciar el servidor, `config.py` lee `NOTAS_API_KEY` de env vars
2. Si no existe → genera una automáticamente con `secrets.token_urlsafe(32)` y la loggea
3. Se guarda en `settings.api_key` durante todo el lifecycle

### Validación en cada request

1. FastAPI extrae header `X-API-Key` via `Header(...)` (parámetro requerido)
2. Compara con `settings.api_key` usando `hmac.compare_digest()` (constant-time, previene timing attacks)
3. Si no coincide → `HTTPException(status_code=401)`
4. Si coincide → el request continúa normalmente

### Implementación como dependencia de router

```python
async def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

Esta dependencia se aplica a nivel de router (`dependencies=[Depends(verify_api_key)]`), no a nivel de cada endpoint. El endpoint `/api/health` NO usa esta dependencia.

### Seguridad

- API Key NUNCA hardcodeada en código fuente
- Server: en variable de entorno (`.env` que no se sube a git)
- `hmac.compare_digest` previene timing attacks

---

## 8. Base de Datos — Estrategia de Abstracción

### Cómo funciona

La abstracción se logra mediante el **connection string** (`NOTAS_DATABASE_URL`):

- **Dev local:** `sqlite:///./notas.db` (default en `config.py`)
- **Producción:** `postgresql://user:pass@host:5432/postgres` (configurado en Render)

SQLAlchemy detecta automáticamente el dialecto desde la URL y adapta el SQL generado. **No se necesita cambiar código.**

### Configuración del Engine

```python
engine = create_engine(
    settings.database_url,
    pool_size=5,              # Connection pool (PostgreSQL)
    max_overflow=10,
    pool_pre_ping=True,       # Verifica conexión antes de usarla
)
```

Para SQLite, `pool_size` y `pool_pre_ping` son ignorados por SQLAlchemy automáticamente.

### Tests

En tests, se sobreescribe `settings.database_url` a `sqlite:///:memory:` en el fixture `conftest.py`. La base en memoria se crea y destruye por cada test.

### Migraciones

Alembic se configura con `sqlalchemy.url` en `alembic.ini`. En desarrollo se usa SQLite. En producción se cambia la URL en la máquina objetivo (Render).

---

## 9. Manejo de Errores

### Estrategia

| Tipo de Error | Handler | Respuesta HTTP |
|---|---|---|
| API Key inválida | `auth.py` vía `HTTPException` | `401: {"detail": "Invalid API Key"}` |
| Nota no encontrada | `routers/notes.py` vía `HTTPException` | `404: {"detail": "Note not found"}` |
| Validación Pydantic | FastAPI automático (RequestValidationError) | `422: {"detail": [...]}` |
| Error interno no esperado | Handler global en `main.py` | `500: {"detail": "Internal server error"}` |

### Exception Handlers globales

En `main.py` se registra un handler para `Exception` genérica que atrapa cualquier error no manejado, loggea el traceback y devuelve un `500` genérico (sin exponer detalles internos).

---

## 10. Logging

### Configuración (`config.py`)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
```

### Uso

- `config.py` loggea la API Key generada automáticamente
- `exceptions.py` loggea errores internos con traceback
- `database.py` loggea errores de conexión
- FastAPI loggea automáticamente los requests (vía uvicorn)

---

## 11. Plan de Implementación Detallado

### Fase 0 — Fundación (1 sesión de agent)

**Objetivo:** Inicializar el proyecto, estructura de directorios, dependencias.

**Archivos a crear:**
1. `backend/pyproject.toml`
2. `backend/.env.example`
3. `backend/.gitignore`
4. `backend/Makefile`

**Detalle de cada archivo:**

#### `pyproject.toml`

```toml
[tool.poetry]
name = "notas-api"
version = "1.0.0"
description = "API REST para Notas App - Markdown notes sync"
authors = ["Notas App"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.29.0"}
sqlalchemy = "^2.0.30"
alembic = "^1.13.0"
pydantic = "^2.7.0"
pydantic-settings = "^2.2.0"
psycopg2-binary = "^2.9.9"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
httpx = "^0.27.0"
pytest-cov = "^5.0.0"
```

#### `.env.example`

```
# Database - SQLite para dev, PostgreSQL para prod
NOTAS_DATABASE_URL=sqlite:///./notas.db
# NOTAS_DATABASE_URL=postgresql://user:password@host:5432/postgres

# API Key - Si está vacía, se genera automáticamente al iniciar
NOTAS_API_KEY=

# Debug mode
NOTAS_DEBUG=false
```

#### `.gitignore`

```
__pycache__/
*.py[cod]
*.db
.env
venv/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
*.pyc
```

#### `Makefile`

```makefile
.PHONY: dev test migrate

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app

migrate:
	alembic upgrade head

migrations:
	alembic revision --autogenerate -m "$(name)"

shell:
	python -c "from app.database import SessionLocal; db=SessionLocal()"
```

---

### Fase 1 — Core (pueden ejecutar 3 agents en paralelo)

#### Agent A: Config + Database

**Archivo:** `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
import secrets
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("notas-api")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./notas.db"
    api_key: str = ""
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_prefix": "NOTAS_",
        "case_sensitive": False,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
            logger.info("⚡ API Key generada automáticamente")
            logger.info("⚡ NOTAS_API_KEY=%s", self.api_key)
            logger.info("⚡ Guárdala en .env si querés mantenerla entre reinicios")


settings = Settings()
```

**Archivo:** `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Agent B: Models + Schemas

**Archivo:** `backend/app/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="", server_default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

**Archivo:** `backend/app/schemas.py`

```python
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
```

#### Agent C: Auth + Exceptions

**Archivo:** `backend/app/auth.py`

```python
from fastapi import Header, HTTPException
from app.config import settings
import hmac


async def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

**Archivo:** `backend/app/exceptions.py`

```python
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("notas-api")


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Error interno no manejado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

---

### Fase 2 — Business Logic (depende de Fase 1)

**Archivo:** `backend/app/crud.py`

```python
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
```

**Detalles importantes de `crud.py`:**
- `get_notes`: ordena por `updated_at` descendente (más reciente primero)
- `create_note`: hace commit + refresh para obtener el ID generado y timestamps
- `update_note`: usa `model_dump(exclude_unset=True)` para solo actualizar campos enviados (parcial update)
- `delete_note`: retorna `bool` indicando si se eliminó algo

---

### Fase 3 — API Layer (depende de Fase 2, 2 agents en paralelo)

#### Agent A: Routers

**Archivo:** `backend/app/routers/__init__.py` (vacio)

**Archivo:** `backend/app/routers/health.py`

```python
from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
```

**Archivo:** `backend/app/routers/notes.py`

```python
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
```

**Reglas de negocio validadas en routers:**
- `get_note`: 404 si no existe
- `create_note`: 201 en éxito
- `update_note`: 404 si no existe, partial update (solo campos enviados)
- `delete_note`: 404 si no existe, 200 si se eliminó

#### Agent B: Main App

**Archivo:** `backend/app/main.py`

```python
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
```

**Detalles importantes de `main.py`:**
- `Base.metadata.create_all(bind=engine)`: crea tablas si no existen (útil para dev con SQLite). En producción se usa Alembic para migraciones.
- CORS abierto (`*`) para desarrollo. En producción se puede restringir.
- `add_exception_handler` captura errores no manejados y devuelve 500 genérico.
- El orden de `include_router` no importa porque las rutas no se solapan.

---

### Fase 4 — Infraestructura (pueden ejecutar 2 agents en paralelo con Fase 3)

#### Agent A: Alembic

**Archivo:** `backend/alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///./notas.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Archivo:** `backend/alembic/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database import Base
from app.models import Note

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Archivo:** `backend/alembic/script.py.mako`

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

**Nota sobre Alembic:** La migración inicial se genera manualmente (o se usa `Base.metadata.create_all` en `main.py` para desarrollo). En producción, se corre `alembic upgrade head` como parte del deploy.

#### Agent B: Docker + Render

**Archivo:** `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Archivo:** `backend/render.yaml`

```yaml
services:
  - type: web
    name: notas-api
    runtime: python
    buildCommand: pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 8000
    envVars:
      - key: NOTAS_DATABASE_URL
        sync: false
      - key: NOTAS_API_KEY
        sync: false
      - key: NOTAS_DEBUG
        value: "false"
```

---

### Fase 5 — Tests (pueden ejecutar 2 agents en paralelo con Fase 3/4)

#### Agent A: Test Infrastructure + Auth + Health

**Archivo:** `backend/tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def api_key():
    from app.config import settings
    return settings.api_key
```

**Detalle de `conftest.py`:**
- `setup_db`: fixture autouse que crea tablas al inicio de cada test y las destruye al final
- `client`: TestClient de FastAPI con override de `get_db` para usar SQLite in-memory
- `api_key`: retorna la API Key generada automáticamente por `config.py`
- `check_same_thread=False`: necesario para SQLite compartido entre hilos

**Archivo:** `backend/tests/test_health.py`

```python
def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Archivo:** `backend/tests/test_auth.py`

```python
from app.config import settings


def test_missing_api_key_returns_401(client):
    response = client.get("/api/notes")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}


def test_invalid_api_key_returns_401(client):
    response = client.get("/api/notes", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}


def test_valid_api_key_succeeds(client, api_key):
    response = client.get("/api/notes", headers={"X-API-Key": api_key})
    assert response.status_code == 200


def test_health_endpoint_does_not_require_auth(client):
    response = client.get("/api/health")
    assert response.status_code == 200
```

#### Agent B: Notes CRUD Tests + CRUD Unit Tests

**Archivo:** `backend/tests/test_notes.py`

```python
def test_create_note(client, api_key):
    headers = {"X-API-Key": api_key}
    payload = {"title": "Test Note", "content": "Hello **world**"}
    response = client.post("/api/notes", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Test Note"
    assert data["content"] == "Hello **world**"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_notes_empty(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.get("/api/notes", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_list_notes_with_data(client, api_key):
    headers = {"X-API-Key": api_key}
    client.post("/api/notes", json={"title": "A", "content": "A"}, headers=headers)
    client.post("/api/notes", json={"title": "B", "content": "B"}, headers=headers)
    response = client.get("/api/notes", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2


def test_get_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Test", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.get(f"/api/notes/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test"


def test_get_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.get("/api/notes/999", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}


def test_update_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Original", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.put(
        f"/api/notes/{created['id']}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Updated"
    assert data["content"] == "Body"


def test_update_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.put("/api/notes/999", json={"title": "X"}, headers=headers)
    assert response.status_code == 404


def test_delete_note(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "To Delete", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.delete(f"/api/notes/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}}
    get_response = client.get(f"/api/notes/{created['id']}", headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent_note_returns_404(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.delete("/api/notes/999", headers=headers)
    assert response.status_code == 404


def test_create_note_empty_title(client, api_key):
    headers = {"X-API-Key": api_key}
    response = client.post(
        "/api/notes", json={"title": "", "content": "Body"}, headers=headers
    )
    assert response.status_code == 201
    assert response.json()["data"]["title"] == ""


def test_partial_update(client, api_key):
    headers = {"X-API-Key": api_key}
    created = client.post(
        "/api/notes", json={"title": "Original", "content": "Body"}, headers=headers
    ).json()["data"]
    response = client.put(
        f"/api/notes/{created['id']}",
        json={"content": "New body only"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Original"
    assert data["content"] == "New body only"
```

**Archivo:** `backend/tests/test_crud.py`

```python
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
```

---

## 12. Especificación por Archivo

Resumen de cada archivo con sus responsabilidades:

| Archivo | Responsabilidad | Depende de |
|---|---|---|
| `pyproject.toml` | Dependencias y metadata | Nada |
| `.env.example` | Template de configuración | Nada |
| `.gitignore` | Archivos ignorados | Nada |
| `Makefile` | Comandos útiles | Nada |
| `app/__init__.py` | Marca `app/` como paquete | Nada |
| `app/config.py` | Settings desde env vars + logging | Nada |
| `app/database.py` | Engine, SessionLocal, get_db | `config.py` |
| `app/models.py` | ORM Note model | `database.py` |
| `app/schemas.py` | Pydantic schemas | Nada |
| `app/auth.py` | API Key validation | `config.py` |
| `app/exceptions.py` | Error handlers | Nada |
| `app/crud.py` | Data access functions | `models.py`, `schemas.py`, `database.py` |
| `app/routers/__init__.py` | Marca `routers/` como paquete | Nada |
| `app/routers/health.py` | GET /api/health | `schemas.py` |
| `app/routers/notes.py` | CRUD /api/notes | `schemas.py`, `crud.py`, `database.py`, `auth.py` |
| `app/main.py` | App assembly, CORS, error handlers | Todos los anteriores |
| `alembic.ini` | Configuración de Alembic | Nada |
| `alembic/env.py` | Entorno de migraciones | `models.py`, `database.py` |
| `alembic/script.py.mako` | Template de migraciones | Nada |
| `tests/conftest.py` | Fixtures de test | `app.main`, `app.database` |
| `tests/test_health.py` | Tests de health endpoint | `conftest.py` |
| `tests/test_auth.py` | Tests de autenticación | `conftest.py` |
| `tests/test_notes.py` | Tests de CRUD integración | `conftest.py` |
| `tests/test_crud.py` | Tests de CRUD unitarios | `models.py`, `schemas.py`, `crud.py` |
| `Dockerfile` | Imagen Docker | `pyproject.toml` |
| `render.yaml` | Blueprint Render | Nada |

---

## 13. Tests

### Estrategia general

- **Framework:** pytest con TestClient de FastAPI (httpx)
- **Base de datos de test:** SQLite `:memory:` (se crea y destruye por cada test)
- **Auth en tests:** `conftest.py` expone la API Key generada automáticamente como fixture

### Cobertura de tests

| Test file | Cantidad de tests | Lo que cubre |
|---|---|---|
| `test_health.py` | 1 | GET /api/health retorna 200 con status ok |
| `test_auth.py` | 4 | Sin API Key → 401, Key inválida → 401, Key válida → 200, Health sin auth → 200 |
| `test_notes.py` | 11 | CRUD completo: crear, listar, obtener, actualizar, eliminar, 404s, empty title, partial update |
| `test_crud.py` | 9 | Unit tests de cada función CRUD: create, get_notes, get_note, update, delete, casos borde |

### Cómo ejecutar tests

```bash
make test
# o directamente:
pytest -v --cov=app
```

### Cobertura esperada

- Líneas de código: >95%
- Branch coverage: >90%
- Endpoints cubiertos: 100% (todos los códigos de estado y casos borde)

---

## 14. Infraestructura

### Docker

```bash
# Build
docker build -t notas-api .

# Run
docker run -p 8000:8000 \
  -e NOTAS_DATABASE_URL=sqlite:///./notas.db \
  -e NOTAS_API_KEY=mi_clave \
  notas-api
```

### Render

1. Conectar repo de GitHub
2. Root directory: `backend/`
3. Build Command: `pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Agregar env vars: `NOTAS_DATABASE_URL`, `NOTAS_API_KEY`, `NOTAS_DEBUG`

### Supabase

1. Crear proyecto en Supabase
2. Ir a Project Settings → Database → Connection string (URI)
3. Usar ese string como `NOTAS_DATABASE_URL` en Render

---

## 15. Comandos Útiles

```bash
# Desarrollo local
make dev                    # uvicorn app.main:app --reload

# Tests
make test                   # pytest -v --cov=app

# Migraciones
make migrate                # alembic upgrade head
make migrations name="desc" # alembic revision --autogenerate

# Shell interactivo con DB
make shell                  # python -c "from app.database import SessionLocal; db=SessionLocal()"

# Swagger UI
# Abrir http://localhost:8000/docs

# ReDoc
# Abrir http://localhost:8000/redoc
```
