# Notas App — MVP Specification

**Version:** 1.0
**Propósito:** Guía completa para que un agente implemente la solución.

---

## 1. Resumen

Aplicación Android de bloc de notas con soporte para Markdown. Las notas se sincronizan en la nube a través de una API REST propia. El backend es un servidor FastAPI con PostgreSQL (Supabase). Solo hay un usuario (el dueño).

**Flujo base:**
1. El usuario abre la app Android
2. La app pide las notas al servidor vía API REST
3. El usuario puede crear, editar y eliminar notas
4. Cada cambio se envía al servidor inmediatamente (online-only en v0)
5. Pull-to-refresh para recargar desde el servidor

---

## 2. Stack Tecnológico

### Backend (API)

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Lenguaje | Python | 3.11+ |
| Framework web | FastAPI | 0.111+ |
| ORM | SQLAlchemy | 2.0+ |
| Base de datos | PostgreSQL (Supabase) | 16+ |
| Migraciones | Alembic | 1.13+ |
| Validación | Pydantic | 2.7+ |
| Configuración | Pydantic-Settings | 2.2+ |
| Auth | API Key via header | — |
| Servidor | Uvicorn | 0.29+ |

### Android Cliente

| Componente | Tecnología |
|-----------|-----------|
| Lenguaje | Kotlin |
| UI | Jetpack Compose |
| HTTP | Retrofit 2 + OkHttp |
| JSON | Gson / Moshi |
| Markdown | Markwon |
| Almacenamiento seguro | EncryptedSharedPreferences |
| Navegación | Navigation Compose |
| Min SDK | 26 (Android 8.0) |
| Target SDK | 34 |

---

## 3. Arquitectura General

```
┌────────────────────────────┐       HTTP/JSON        ┌────────────────────────────┐
│  Android App               │ ◄─────────────────────► │  FastAPI Server            │
│  (Kotlin + Jetpack Compose)│    REST API            │  (Python)                  │
│                            │                         │                            │
│  Retrofit → HTTP calls     │  GET/POST/PUT/DELETE    │  SQLAlchemy ORM            │
│  Markwon → Markdown render │  Header: X-API-Key      │  PostgreSQL (Supabase)     │
│  EncryptedSharedPrefs      │                         │  Alembic migrations        │
│  Pull-to-refresh sync      │                         │  Swagger UI en /docs       │
└────────────────────────────┘                         └──────────┬─────────────────┘
                                                                   │
                                                           ┌───────┴──────────────┐
                                                           │  Supabase PostgreSQL │
                                                           │  (Render deploy)     │
                                                           └──────────────────────┘
```

**Principios arquitectónicos:**
- La app Android **nunca** accede directamente a la base de datos
- Toda interacción con datos pasa por la API REST
- El servidor es la única fuente de verdad (source of truth)
- La API Key se valida en cada request (middleware/dependencia)

---

## 4. Data Model

### SQLAlchemy Model (`app/models.py`)

```python
class Note(Base):
    __tablename__ = "notes"

    id: int          # Primary key, auto-increment
    title: str       # Título de la nota (nullable, puede ser vacío)
    content: str     # Contenido en Markdown (obligatorio)
    created_at: datetime  # Fecha de creación (server default)
    updated_at: datetime  # Fecha de última modificación (se actualiza solo)
```

### Pydantic Schemas (`app/schemas.py`)

```python
# Request bodies
class NoteCreate(BaseModel):
    title: str = ""
    content: str

class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None

# Response bodies
class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

class NoteListResponse(BaseModel):
    data: list[NoteResponse]

class ErrorResponse(BaseModel):
    detail: str

class HealthResponse(BaseModel):
    status: str
```

---

## 5. API Endpoints

Base URL: `http://<host>:<port>/api`

| Método | Ruta | Auth | Request Body | Response (200) | Errores |
|--------|------|------|-------------|----------------|---------|
| `GET` | `/api/notes` | API Key | — | `{"data": [NoteResponse]}` | 401, 500 |
| `GET` | `/api/notes/{id}` | API Key | — | `{"data": NoteResponse}` | 401, 404, 500 |
| `POST` | `/api/notes` | API Key | `NoteCreate` | `{"data": NoteResponse}` | 401, 422, 500 |
| `PUT` | `/api/notes/{id}` | API Key | `NoteUpdate` | `{"data": NoteResponse}` | 401, 404, 422, 500 |
| `DELETE` | `/api/notes/{id}` | API Key | — | `{"data": {"ok": true}}` | 401, 404, 500 |
| `GET` | `/api/health` | No | — | `{"status": "ok"}` | 500 |

**Headers requeridos en endpoints con Auth:**
```
X-API-Key: <api_key_value>
Content-Type: application/json
```

**Códigos de error HTTP:**
- `401 Unauthorized` — API Key inválida o faltante
- `404 Not Found` — Nota no existe
- `422 Unprocessable Entity` — Datos inválidos (validación Pydantic)
- `500 Internal Server Error` — Error inesperado del servidor

### Ejemplos de requests/responses

**GET /api/notes**
```json
// Response 200
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
```json
// Request
{
  "title": "Nota nueva",
  "content": "Contenido en **markdown**"
}

// Response 201
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
```json
// Request (solo campos a actualizar)
{
  "title": "Título actualizado"
}

// Response 200
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
```json
// Response 200
{
  "data": {
    "ok": true
  }
}
```

---

## 6. Autenticación — API Key

### Server Side

```
1. Al iniciar el servidor, verificar variable de entorno NOTAS_API_KEY
2. Si no existe → generar una automáticamente y loguearla en consola
3. Guardar en una constante durante el lifecycle de la app

Validación en cada request:
1. Extraer header "X-API-Key"
2. Comparar con NOTAS_API_KEY (constant-time comparison)
3. Si no coincide → HTTP 401
```

**Implementación como dependencia de FastAPI:**

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

### Android Side

```
1. Primera ejecución:
   - Mostrar pantalla de configuración con 2 campos:
     - Server URL (ej: https://api.misnotas.com)
     - API Key (string)
   - Guardar ambos en EncryptedSharedPreferences

2. Requests subsiguientes:
   - ApiKeyInterceptor (OkHttp Interceptor) lee de EncryptedSharedPreferences
   - Agrega header "X-API-Key" a cada request

3. Si el servidor responde 401:
   - Limpiar credenciales guardadas
   - Redirigir a pantalla de configuración
```

### Seguridad

- API Key **NUNCA** hardcodeada en el código fuente
- Server: en variable de entorno (`.env` que no se sube a git)
- Android: en EncryptedSharedPreferences (cifrado AES-256 con Android Keystore)
- Si alguien decompila el APK **no encuentra** la API Key

---

## 7. Estructura del Proyecto

```
notas-app/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, CORS setup, routers
│   │   ├── config.py                # Settings desde env vars
│   │   ├── database.py              # SQLAlchemy engine + SessionLocal
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── crud.py                  # Business logic functions
│   │   ├── auth.py                  # API Key validation dependency
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── notes.py             # /api/notes endpoints
│   │       └── health.py            # /api/health endpoint
│   ├── alembic/                     # Migration environment
│   │   └── versions/                # Migration files
│   ├── alembic.ini                  # Alembic configuration
│   ├── requirements.txt
│   ├── .env.example                 # Template (sin keys reales)
│   ├── .gitignore
│   ├── Dockerfile                   # Para deployment
│   └── render.yaml                  # Render blueprint (opcional)
│
├── android/
│   └── app/
│       └── src/main/java/com/notasapp/
│           ├── NotasApplication.kt       # Application class
│           ├── MainActivity.kt           # Single activity
│           ├── data/
│           │   ├── api/
│           │   │   ├── NotasApi.kt       # Retrofit interface
│           │   │   ├── ApiClient.kt      # Retrofit singleton
│           │   │   └── ApiKeyInterceptor.kt  # OkHttp interceptor
│           │   └── model/
│           │       ├── NoteDto.kt        # API response model
│           │       ├── NoteRequest.kt    # Create/Update request
│           │       └── ApiResponse.kt    # Generic response wrapper
│           ├── ui/
│           │   ├── theme/
│           │   │   ├── Theme.kt
│           │   │   ├── Color.kt
│           │   │   └── Type.kt
│           │   ├── navigation/
│           │   │   └── NavGraph.kt
│           │   ├── setup/
│           │   │   ├── SetupScreen.kt
│           │   │   └── SetupViewModel.kt
│           │   ├── noteslist/
│           │   │   ├── NotesListScreen.kt
│           │   │   └── NotesListViewModel.kt
│           │   └── notedetail/
│           │       ├── NoteDetailScreen.kt
│           │       └── NoteDetailViewModel.kt
│           └── util/
│               └── SettingsManager.kt    # EncryptedSharedPreferences wrapper
│
└── docs/
    ├── mvp-specification.md         # Este archivo
    └── hosting-options.md           # Comparativa de proveedores
```

---

## 8. Backend — Detalle de Implementación

### `app/config.py`

```python
from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    database_url: str = "sqlite:///./notas.db"
    # Producción: configurar NOTAS_DATABASE_URL=postgresql://user:pass@host:5432/postgres
    # Supabase: usar el connection string de Project Settings → Database → URI
    api_key: str = ""  # Si es vacío, se genera automáticamente
    debug: bool = False

    class Config:
        env_file = ".env"
        env_prefix = "notas_"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
            print(f"⚡ API Key generada: {self.api_key}")
            print("⚡ Guárdala y configúrala como NOTAS_API_KEY en .env")

settings = Settings()
```

### `app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite local (dev): sqlite:///./notas.db
# PostgreSQL (prod/Supabase): postgresql://user:pass@host:5432/postgres
engine = create_engine(
    settings.database_url,
    pool_size=5,           # PostgreSQL connection pool
    max_overflow=10,
    pool_pre_ping=True,    # Verifica conexión antes de usarla
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

### `app/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### `app/schemas.py`

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

### `app/crud.py`

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

def update_note(db: Session, note_id: int, note: schemas.NoteUpdate) -> models.Note | None:
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

### `app/auth.py`

```python
from fastapi import Header, HTTPException
from app.config import settings
import hmac

async def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
```

### `app/routers/health.py`

```python
from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
```

### `app/routers/notes.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes"],
    dependencies=[Depends(verify_api_key)]
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
def update_note(note_id: int, note: schemas.NoteUpdate, db: Session = Depends(get_db)):
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

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import notes, health

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notas App API",
    description="API REST para la aplicación de notas Markdown",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a origen de la app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(notes.router)
```

### `requirements.txt`

```
fastapi>=0.111.0,<1.0.0
uvicorn[standard]>=0.29.0,<1.0.0
sqlalchemy>=2.0.30,<3.0.0
alembic>=1.13.0,<2.0.0
pydantic>=2.7.0,<3.0.0
pydantic-settings>=2.2.0,<3.0.0
python-dotenv>=1.0.0,<2.0.0
psycopg2-binary>=2.9.9,<3.0.0   # PostgreSQL driver (producción)
```

### `.env.example`

```
# Notas App API — Configuración
# Para desarrollo local (SQLite):
# NOTAS_DATABASE_URL=sqlite:///./notas.db

# Para producción con Supabase PostgreSQL:
# Obtener URL en Supabase: Project Settings → Database → Connection string (URI)
NOTAS_DATABASE_URL=postgresql://user:password@host.supabase.co:5432/postgres

NOTAS_API_KEY=genera_una_clave_segura_aqui
NOTAS_DEBUG=false
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `.gitignore`

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
```

---

## 9. Android — Detalle de Implementación

### `data/api/NotasApi.kt` (Retrofit Interface)

```kotlin
interface NotasApi {
    @GET("api/notes")
    suspend fun listNotes(): NoteListResponse

    @GET("api/notes/{id}")
    suspend fun getNote(@Path("id") id: Int): NoteSingleResponse

    @POST("api/notes")
    suspend fun createNote(@Body request: NoteRequest): NoteSingleResponse

    @PUT("api/notes/{id}")
    suspend fun updateNote(@Path("id") id: Int, @Body request: NoteRequest): NoteSingleResponse

    @DELETE("api/notes/{id}")
    suspend fun deleteNote(@Path("id") id: Int): DeleteResponse
}
```

### `data/api/ApiKeyInterceptor.kt`

```kotlin
class ApiKeyInterceptor(private val settingsManager: SettingsManager) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val apiKey = settingsManager.getApiKey()

        val request = if (apiKey.isNotEmpty()) {
            originalRequest.newBuilder()
                .header("X-API-Key", apiKey)
                .build()
        } else {
            originalRequest
        }

        return chain.proceed(request)
    }
}
```

### `data/api/ApiClient.kt`

```kotlin
object ApiClient {
    fun create(settingsManager: SettingsManager): NotasApi? {
        val baseUrl = settingsManager.getServerUrl()
        if (baseUrl.isEmpty()) return null

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(ApiKeyInterceptor(settingsManager))
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()

        return Retrofit.Builder()
            .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(NotasApi::class.java)
    }
}
```

### `data/model/NoteDto.kt`

```kotlin
data class NoteDto(
    val id: Int,
    val title: String,
    val content: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String
)

data class NoteListResponse(val data: List<NoteDto>)
data class NoteSingleResponse(val data: NoteDto)
data class DeleteResponse(val data: Map<String, Boolean>)
```

### `data/model/NoteRequest.kt`

```kotlin
data class NoteRequest(
    val title: String? = null,
    val content: String? = null
)
```

### `util/SettingsManager.kt`

```kotlin
class SettingsManager(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        "notas_app_prefs",
        MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun getServerUrl(): String = prefs.getString("server_url", "") ?: ""
    fun setServerUrl(url: String) = prefs.edit().putString("server_url", url).apply()

    fun getApiKey(): String = prefs.getString("api_key", "") ?: ""
    fun setApiKey(key: String) = prefs.edit().putString("api_key", key).apply()

    fun isConfigured(): Boolean = getServerUrl().isNotEmpty() && getApiKey().isNotEmpty()
    fun clear() = prefs.edit().clear().apply()
}
```

### Android Dependencies (`build.gradle.kts` app module)

```kotlin
dependencies {
    // Core
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.9.0")

    // Compose
    implementation(platform("androidx.compose:compose-bom:2024.05.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.7")

    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")

    // Retrofit + OkHttp
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Markdown
    implementation("io.noties.markwon:core:4.6.2")
    implementation("io.noties.markwon:ext-strikethrough:4.6.2")

    // Encrypted SharedPreferences
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0")

    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
}
```

### UI Screens

#### SetupScreen
- Se muestra si `SettingsManager.isConfigured()` es `false`
- Campos: Server URL, API Key
- Botón "Guardar y conectar"
- Valida la conexión con `GET /api/health`
- Si es exitoso, navega a NotesListScreen

#### NotesListScreen
- Muestra lista de notas (título + preview del contenido + fecha)
- FloatingActionButton "+" → navega a NoteDetailScreen en modo crear
- Tap en nota → navega a NoteDetailScreen en modo editar
- Pull-to-refresh → recarga desde API
- Menú de opciones → "Configuración" (vuelve a SetupScreen)

#### NoteDetailScreen
- Modo crear: campos vacíos, botón "Crear"
- Modo editar: campos precargados, botón "Guardar"
- Campo título (TextField)
- Campo contenido (TextField multilínea para markdown)
- Opcional: preview del markdown renderizado con Markwon
- Swipe para borrar o botón "Eliminar"

### Navigation

```kotlin
sealed class Screen(val route: String) {
    object Setup : Screen("setup")
    object NotesList : Screen("notes")
    object NoteDetail : Screen("note/{noteId}?mode={mode}") {
        fun createRoute(noteId: Int? = null, mode: String = "create") =
            "note/${noteId ?: -1}?mode=$mode"
    }
}
```

---

## 10. Sync Strategy

**Estrategia v0: Online-only con Last-Write-Wins**

- La app requiere conexión a internet para operar
- Cada acción (crear, editar, eliminar) envía un request HTTP inmediato
- Pull-to-refresh en NotesListScreen: `GET /api/notes`
- Si no hay conexión: mostrar error con opción a reintentar
- No hay caché local ni base de datos offline en Android

**Last-Write-Wins:**
- Cada nota tiene `updated_at` timestamp
- El servidor asigna el timestamp al hacer `PUT`
- En caso de ediciones simultáneas (improbable con 1 usuario), gana el último `PUT`
- La app siempre muestra el estado actual del servidor

---

## 11. Consideraciones de Desarrollo

### CORS
- En desarrollo, permitir `allow_origins=["*"]`
- En producción, configurar con el origen de la app Android (no es estrictamente necesario para mobile, pero sí si se accede desde web)

### Errores de red en Android
- Mostrar Snackbar con mensaje de error
- Opción "Reintentar"
- No perder datos locales no guardados (mostrar advertencia antes de navegar)

### Formato de fechas
- ISO 8601 en API responses: `"2026-06-30T10:00:00"`
- Android: mostrar formato relativo ("hace 5 minutos") o fecha localizada

---

## 12. Cómo Probar Localmente

### Backend (desarrollo con SQLite)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar API Key (opcional, si no se genera sola)
export NOTAS_API_KEY=mi_clave_secreta

# Iniciar servidor (usa SQLite por defecto)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Luego abrir `http://localhost:8000/docs` para ver Swagger UI y probar endpoints.

### Backend (producción con PostgreSQL via Docker)

Para probar con PostgreSQL local (más cercano a Supabase):

```bash
# Levantar PostgreSQL con Docker
docker run -d --name notas-pg \
  -e POSTGRES_PASSWORD=notas_dev \
  -e POSTGRES_DB=notas \
  -p 5432:5432 \
  postgres:16-alpine

# Configurar variable de entorno
export NOTAS_DATABASE_URL=postgresql://postgres:notas_dev@localhost:5432/notas
export NOTAS_API_KEY=mi_clave_secreta

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Android

1. Abrir `android/` en Android Studio
2. Configurar server URL y API Key en la pantalla de setup
3. Para desarrollo local: usar `http://10.0.2.2:8000` (localhost del emulador Android)

---

## 13. Deploy a Render + Supabase

### 13.1 Crear infraestructura

1. Crear cuenta en **Supabase** (sin tarjeta)
2. Crear nuevo proyecto → copiar **Database connection string (URI)** de Project Settings → Database
3. Crear cuenta en **Render** (sin tarjeta)

### 13.2 Variables de entorno en Render

Agregar en Render Dashboard → Web Service → Environment:

```
NOTAS_API_KEY=<tu_clave_segura>
NOTAS_DATABASE_URL=postgresql://user:password@host.supabase.co:5432/postgres
NOTAS_DEBUG=false
```

> El connection string de Supabase usa el puerto `5432` (PostgreSQL directo).
> Para production usar el puerto `6543` de PgBouncer (connection pooling) si hay muchas conexiones.

### 13.3 Deploy

1. Conectar repo de GitHub a Render
2. Seleccionar `backend/` como root directory
3. Runtime: **Python 3**
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
6. Free tier: el servicio se duerme a los 15 min sin actividad (cold start ~30-50s)
7. Probar `GET https://<app>.onrender.com/api/health`

### 13.4 render.yaml (opcional)

```yaml
services:
  - type: web
    name: notas-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port 8000
    envVars:
      - key: NOTAS_DATABASE_URL
        fromDatabase:
          type: postgresql  # o setear manual con Supabase URL
      - key: NOTAS_API_KEY
        sync: false
      - key: NOTAS_DEBUG
        value: "false"
```

---

## 14. Orden de Implementación Sugerido

### Fase 1: Backend
1. `config.py` — Settings + variable de entorno
2. `database.py` — Engine + Session (PostgreSQL pool config)
3. `models.py` — Note model
4. `schemas.py` — Pydantic schemas
5. `auth.py` — API Key validation
6. `crud.py` — Business logic
7. `routers/health.py` — Health check endpoint
8. `routers/notes.py` — CRUD endpoints
9. `main.py` — App assembly
10. Probar con Swagger en `/docs`

### Fase 2: Android
1. `SettingsManager.kt` — EncryptedSharedPreferences wrapper
2. Modelos: `NoteDto.kt`, `NoteRequest.kt`, `ApiResponse.kt`
3. `ApiKeyInterceptor.kt` + `ApiClient.kt` + `NotasApi.kt`
4. `SetupScreen.kt` + `SetupViewModel.kt`
5. `NotesListScreen.kt` + `NotesListViewModel.kt`
6. `NoteDetailScreen.kt` + `NoteDetailViewModel.kt`
7. `NavGraph.kt` + `MainActivity.kt`

---

## 15. Notas Finales para el Agente

- El proyecto es para **1 solo usuario**. No hay registro de múltiples cuentas, ni planes, ni suscripciones.
- La API Key es compartida entre servidor y cliente Android. No hay OAuth, no hay JWT.
- PostgreSQL (Supabase) es la base de datos en producción. SQLite se usa solo para desarrollo local.
- En v0 no hay offline support. Si no hay internet, la app muestra error.
- El diseño UI debe ser **minimalista y funcional**, no fancy. Sin animaciones complejas.
- El código debe ser **limpio y comentado solo donde sea necesario** para que el dueño pueda aprender y modificar después.
- Priorizar simplicidad sobre abstracción. No usar patrones complejos innecesariamente.
