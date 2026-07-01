# Opciones de Hosting — Notas App

**Propósito:** Ayudar a elegir dónde deployar el backend FastAPI + base de datos.
**Nota:** El backend está diseñado para ser hosting-agnostic y database-agnostic. Podés cambiar hosting y DB sin tocar código.

---

## ⚠️ SQLite ya no es requisito duro

Originalmente este proyecto usaba SQLite, pero **SQLite es incompatible con la mayoría de los free tiers de PaaS/serverless** porque requieren filesystem efímero.

**Decisión:** Si la infraestructura gratis requiere cambiar de DB, se cambia. La migración es mínima porque SQLAlchemy abstrae la diferencia. La opción recomendada hoy es:

| Backend (API) | Base de datos |
|--------------|---------------|
| **Render** (free, 750h/mes, sin tarjeta) | **Supabase PostgreSQL** (500 MB, sin tarjeta) |

---

## Resumen Rápido

| Proveedor | Free Tier | Costo/mes | Cold Start | DB incluida | Tarjeta | Dificultad | Sirve para FastAPI? |
|-----------|-----------|-----------|------------|-------------|---------|------------|-------------------|
| **Render** | ✅ 750h/mes | $0 | 30-50s | PostgreSQL (90d) | No | Baja | ✅ |
| **Koyeb** | ✅ 1 servicio | $0 | 5-15s | PostgreSQL (1GB) | No | Baja | ✅ |
| **Vercel** | ✅ Hobby | $0 | ~1s | ❌ No (serverless) | No | Baja | ⚠️ Serverless |
| **SnapDeploy** | ✅ 4 contenedores | $0 | 10-30s | No | No | Media | ✅ Docker |
| **Shorlabs** | ✅ 3000 req/mes | $0 | ~1s | No | No | Baja | ✅ |
| **Railway** | ❌ ($5 crédito) | ~$5/mes | No | PostgreSQL/MySQL | Sí | Baja | ✅ |
| **Fly.io** | ❌ ($5 crédito) | ~$5/mes | 100ms | PostgreSQL (1GB) | Sí | Media | ✅ |
| **Oracle Cloud** | ✅ Siempre gratis | $0 | No | MySQL 50GB / 2 DBs | Sí | Alta | ✅ VM |
| **Hetzner VPS** | ❌ | ~$4/mes | No | Instalás vos | Sí | Alta | ✅ |
| **Azure Static Web Apps** | ✅ Free | $0 | ~5s | No (Cosmos DB free 25GB) | Sí | Media | ✅ via Functions |
| **GCP Cloud Run** | ✅ 2M req/mes | $0 | 2-5s | No (Firestore 1GB) | Sí | Media | ✅ Nativo |
| **AWS Lambda + DynamoDB** | ✅ Siempre gratis | $0 | ~1s | DynamoDB 25GB | Sí | Media | ✅ via Mangum |
| **DigitalOcean App** | ❌ | ~$6/mes | No | PostgreSQL $7/mes | Sí | Baja | ✅ |
| **PythonAnywhere** | ✅ 1 web app | $0 | No | MySQL (limitado) | No | Baja | ❌ No ASGI |

---

## Recomendación final: Render + Supabase

| Componente | Servicio | Free tier | Costo |
|-----------|----------|-----------|-------|
| API (Python FastAPI) | **Render** | 750h/mes web service | $0 |
| Base de datos | **Supabase** | 500MB PostgreSQL, 5GB egress | $0 |
| **Total** | | | **$0** |

**Por qué:**
- Sin tarjeta de crédito para ninguno
- FastAPI funciona nativo en Render (buildpacks, sin Docker)
- Supabase da una URL de PostgreSQL estándar → solo cambiar `DATABASE_URL`
- Si después querés migrar, cambias hosting y la DB queda igual

---

## Comparativa Detallada

### 1. Render ✅ RECOMENDADO

**Web:** https://render.com
**Tipo:** PaaS (Platform as a Service)

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 750 horas/mes web service, 512MB RAM, CPU compartido |
| **Database gratis** | PostgreSQL 256MB (expira a los 90 días) — pero usamos Supabase afuera |
| **Cold start** | 30-50 segundos (el servicio se duerme a los 15 min de inactividad) |
| **Siempre activo** | Starter $7/mes, Standard $25/mes |
| **Tarjeta de crédito** | No requerida para free tier |
| **Deploy** | Git push + auto-detecta runtime, o Dockerfile |
| **Regiones** | Oregon, Frankfurt, Singapur, Ohio |
| **SSL/HTTPS** | Automático (gratis) |
| **Custom domain** | Sí |

**✅ Pros:**
- Free tier real sin tarjeta de crédito
- Muy fácil de usar (similar a Heroku)
- HTTPS automático
- Ideal para MVP sin compromiso
- Buildpacks nativos para Python (FastAPI funciona directo)

**❌ Contras:**
- Cold starts de 30-50s en free tier (el servicio se duerme a los 15 min)
- SQLite no persiste en free tier — por eso usamos Supabase
- Límite de 750h/mes (~50% uptime continuo)

**Conclusión:** La mejor opción para MVP sin tarjeta. Combinado con Supabase resolvés la persistencia de datos.

---

### 2. Koyeb

**Web:** https://koyeb.com
**Tipo:** PaaS serverless

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 1 web service, 512MB RAM, 0.1 vCPU |
| **DB incluida** | PostgreSQL gratis (5h activo, 1GB) |
| **Cold start** | 5-15 segundos |
| **Tarjeta de crédito** | No |
| **Deploy** | Git push + buildpacks o Dockerfile |
| **Regiones** | Frankfurt, Washington DC |
| **SSL/HTTPS** | Automático |

**✅ Pros:**
- Cold starts más rápidos que Render
- Sin tarjeta de crédito
- [One-click deploy para FastAPI](https://www.koyeb.com/deploy/fastapi)

**❌ Contras:**
- Ecosistema más chico que Render
- PostgreSQL free solo 5h de actividad
- Sin disco persistente en free tier

**Conclusión:** Alternativa sólida a Render. Cold starts más rápidos. Misma estrategia: conectar Supabase afuera.

---

### 3. Vercel ❌ NO RECOMENDADO (serverless)

**Web:** https://vercel.com
**Tipo:** Serverless Functions

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ Hobby plan, gratis para siempre |
| **FastAPI** | ✅ Zero-config desde 2025 (Python 3.12-3.14) |
| **Cold start** | ~1s (Fluid Compute) |
| **Tarjeta de crédito** | No |
| **Deploy** | Git push, auto-detecta |
| **SSL/HTTPS** | Automático |
| **Bundle size** | ⚠️ Máximo 500MB por función |

**✅ Lo bueno:**
- FastAPI zero-config, primera vez que un serverless hace esto bien
- Sin tarjeta
- Muy fácil

**❌ Por qué NO para este proyecto:**

Vercel es **serverless**: cada request crea una invocación nueva que arranca, responde y muere. Esto choca con el modelo de FastAPI + SQLAlchemy:

| Aspecto | Serverless (Vercel) | Web Service (Render/Koyeb) | Impacto |
|---------|-------------------|---------------------------|---------|
| **Conexiones a DB** | Nueva en cada request | Pool persistente | Cada request paga handshake TCP+SSL a Supabase |
| **Background tasks** | ❌ No confiable | ✅ Sí | Función muere al responder |
| **Cache en memoria** | ❌ No existe | ✅ Sí | Cada request empieza desde cero |
| **SQLAlchemy engine** | Se crea/destruye por request | Se mantiene vivo | Latencia + overhead |
| **/docs de FastAPI** | ⚠️ No funciona sin config extra | ✅ Funciona de una | Swagger necesita ruteo especial |
| **WebSockets / SSE** | ❌ No soportado | ✅ Sí | Limita features futuras |
| **Filesystem** | ❌ Efímero (solo /tmp) | ✅ Persistente | Subir archivos, logs |

**Veredicto:** Vercel está optimizado para frontends + serverless ligeros. Para un backend con estado (DB pool, ORM, sesiones), **Render o Koyeb son más apropiados**. Si en el futuro querés explorar Vercel, investigá cómo maneja conexiones pooled a Supabase con `connection pooling` de Supabase (PgBouncer en puerto 6543).

---

### 4. SnapDeploy

**Web:** https://snapdeploy.dev
**Tipo:** Container hosting

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 10 deploys/día, hasta 4 contenedores, 512MB RAM c/u |
| **Cold start** | 10-30s (auto-sleep/wake) |
| **Tarjeta de crédito** | No |
| **Deploy** | Docker (requerido) o buildpacks |
| **FastAPI** | ✅ Detecta Python automáticamente |

**✅ Pros:**
- Hasta 4 contenedores gratis
- Sin tarjeta
- Soporte Docker completo

**❌ Contras:**
- Límite de 10 deploys/día
- Menos conocido y probado
- Pocas regiones

**Conclusión:** Alternativa si querés Docker gratis. Contenedores dedicados.

---

### 5. Shorlabs

**Web:** https://shorlabs.com
**Tipo:** Serverless Functions

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 3000 requests/mes, 1200 GB-seconds |
| **Cold start** | ~1s |
| **Tarjeta de crédito** | No |
| **Deploy** | GitHub, sin Docker, sin config |
| **FastAPI** | ✅ Detecta automáticamente |

**✅ Pros:**
- No requiere Docker, ni YAML, ni CLI
- Subís el repo y ya
- Sin tarjeta

**❌ Contras:**
- Muy nuevo (poca comunidad)
- Límite bajo: 3000 requests/mes
- Serverless (mismas limitaciones de Vercel pero más chico)

**Conclusión:** Para experimentar rápido. No para un MVP que planeás mantener.

---

### 6. Railway

**Web:** https://railway.app
**Tipo:** PaaS

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ❌ No tiene. $5 crédito único + $1/mes adicional |
| **Costo base** | Hobby ~$5/mes |
| **DB incluida** | ✅ PostgreSQL, MySQL, Redis (plugins) |
| **Cold start** | No |
| **Tarjeta de crédito** | Sí |
| **Deploy** | Git push + Nixpacks auto-detecta |

**✅ Pros:**
- Mejor DX del mercado
- Sin cold starts
- PR preview environments

**❌ Contras:**
- No tiene free tier real
- Requiere tarjeta de crédito

**Conclusión:** La mejor opción paga (~$5/mes). Ideal cuando quieras salir del free tier.

---

### 7. Fly.io

**Web:** https://fly.io
**Tipo:** PaaS con Firecracker microVMs

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ❌ $5/mes crédito incluido (no es free permanente) |
| **Costo base** | ~$5-10/mes |
| **Cold start** | No (escala a cero, wake ~100ms) |
| **Tarjeta de crédito** | Sí |
| **Deploy** | Dockerfile + flyctl CLI obligatorio |

**Conclusión:** Bueno si ya sabés Docker, pero requiere tarjeta y tiene costo.

---

### 8. Oracle Cloud — Free Tier

**Web:** https://oracle.com/cloud/free
**Tipo:** IaaS (VM)

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ Siempre gratis (no expira) |
| **Recursos** | 4 ARM cores + 24GB RAM + 200GB SSD |
| **DB incluida** | **MySQL HeatWave 50GB** siempre gratis + 2 Oracle Autonomous DB de 20GB c/u |
| **Cold start** | No (es una VM 24/7) |
| **Tarjeta de crédito** | Sí (solo para verificar identidad, no cobran) |
| **Deploy** | SSH + Docker |

**✅ Pros:**
- Potencia bestial: 4 cores + 24GB RAM + 200GB SSD gratis para siempre
- MySQL 50GB gratis incluido (ideal si no querés Supabase)
- VM completa: corrés lo que quieras, SQLite incluido
- Sin límite de uptime ni cold starts

**❌ Contras:**
- Requiere configurar una VM Linux (más técnico)
- Necesita tarjeta de crédito para crear cuenta (nunca cobran)
- Disponibilidad de ARM no garantizada en todas las regiones

**Conclusión:** Mejor relación precio/rendimiento del mercado (es gratis). Si estás dispuesto a aprender Linux, esto supera a cualquier PaaS.

---

### 9. Hetzner — VPS

**Web:** https://hetzner.com
**Tipo:** VPS

| Aspecto | Detalle |
|---------|---------|
| **Costo** | Desde €3.79/mes (CX22: 2 cores, 4GB RAM, 40GB SSD) |
| **Free tier** | ❌ No |
| **DB incluida** | No (instalás lo que quieras) |
| **Tarjeta** | Sí (o PayPal) |

**Conclusión:** Para cuando quieras máximo control pagando mínimo. Ideal si ya sabés Linux.

---

### 10. DigitalOcean App Platform

**Web:** https://digitalocean.com
**Tipo:** PaaS

| Aspecto | Detalle |
|---------|---------|
| **Costo base** | $6/mes (512MB RAM, 1 core) |
| **Free tier** | ❌ (trial $200 por 60 días) |
| **DB incluida** | PostgreSQL desde $7/mes |

**Conclusión:** Más caro que Railway a mismo precio. No es competitivo para este proyecto.

---

### 11. PythonAnywhere ❌ NO SIRVE

**Web:** https://pythonanywhere.com
**Tipo:** PaaS especializado en Python

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 1 web app, 512MB storage, 100s CPU/día |
| **Tarjeta** | No |
| **FastAPI** | ❌ **No funciona.** Solo soporta WSGI (Flask, Django). FastAPI es ASGI. |

**Conclusión:** Descartado. FastAPI no corre en el free tier por falta de soporte ASGI.

---

### 12. Azure Static Web Apps

**Web:** https://azure.microsoft.com/en-us/pricing/details/app-service/static/
**Tipo:** Serverless + Functions

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 100GB bandwidth, 1M Azure Functions ejec./mes, 500MB storage |
| **FastAPI** | ✅ Via Azure Functions (Python 3.11 soportado) |
| **DB incluida** | ❌ No. Opcional: Cosmos DB free tier (1000 RU/s + 25GB, vitalicio) |
| **Tarjeta de crédito** | Sí (requiere Azure subscription) |
| **SQLite persistente** | ❌ Efímero (Azure Functions no tiene disco persistente) |

**¿Sirve con Supabase?** Sí, pero necesitás tarjeta para Azure. Si igual tenés tarjeta, Oracle Cloud es mejor.

---

### 13. GCP Cloud Run

**Web:** https://cloud.google.com/run
**Tipo:** Serverless containers

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 2M requests/mes, 240K vCPU-seconds, 450K GB-seconds (siempre gratis) |
| **FastAPI** | ✅ Nativo, [quickstart oficial de Google](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service) |
| **DB recomendada gratis** | Firestore (1GB) — NoSQL. O Supabase afuera. |
| **Tarjeta de crédito** | Sí (requiere billing account) |
| **SQLite persistente** | ❌ Efímero (Cloud Run solo tiene /tmp) |

**¿Sirve con Supabase?** Sí, pero requiere tarjeta para GCP. FastAPI funciona excelente igual que Render.

---

### 14. AWS Lambda + DynamoDB

**Web:** https://aws.amazon.com/lambda/
**Tipo:** Serverless Functions

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 1M requests/mes + 400K GB-seconds (siempre gratis) |
| **FastAPI** | ✅ Via [Mangum](https://mangum.io/) o [Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter) |
| **DB gratis** | DynamoDB 25GB siempre gratis |
| **Tarjeta de crédito** | Sí |
| **SQLite persistente** | ❌ Efímero |

**¿Sirve con Supabase?** Sí. DynamoDB es NoSQL y requeriría cambiar el modelo de datos. Si querés SQL posta, mejor Lambda + Supabase.

**Importante:** EC2 free tier (t2.micro, 750h/mes) solo dura **12 meses**, después se cobra. No es "siempre gratis".

---

### 15. Supabase — Base de datos recomendada

**Web:** https://supabase.com
**Tipo:** PostgreSQL as a Service (open-source)

| Aspecto | Detalle |
|---------|---------|
| **Free tier** | ✅ 500MB PostgreSQL, 50K MAU, 5GB egress, 1GB storage |
| **API requests** | Ilimitadas |
| **Conexiones** | 200 conexiones concurrentes (con PgBouncer integrado en puerto 6543) |
| **Auto-pausa** | ⚠️ Se pausa tras 7 días de inactividad. Se reactiva desde el dashboard. |
| **Tarjeta de crédito** | No |
| **Proyectos gratis** | Hasta 2 |
| **Features extras** | Auth, Realtime, Edge Functions, Storage, Auto-documentación |

**Alternativas a Supabase (gratis, sin tarjeta):**

| Servicio | DB | Límite | Diferencias |
|----------|----|--------|-------------|
| **Supabase** | PostgreSQL 500MB | 5GB egress, auto-pausa 7 días | Tiene Auth, Realtime, Storage incluido |
| **Neon** | PostgreSQL 512MB | 190 compute h/mes | Serverless PostgreSQL sin auto-pausa (más moderno) |

**Si tenés tarjeta y querés algo más grande:**
- **Oracle MySQL HeatWave** — 50GB siempre gratis
- **Oracle Autonomous DB** — 2 DBs de 20GB siempre gratis

---

## Bases de datos gratis por proveedor cloud (si usás su ecosistema)

| Cloud | Servicio DB gratis | Tipo | Límite | Tarjeta |
|-------|-------------------|------|--------|---------|
| **Oracle** | MySQL HeatWave | SQL (MySQL) | 50GB, siempre gratis | Sí |
| **Oracle** | Autonomous Database | SQL (Oracle) | 2 DBs x 20GB, siempre gratis | Sí |
| **Oracle** | NoSQL Database | NoSQL | 133M reads/mes, 3 tablas x 25GB | Sí |
| **AWS** | DynamoDB | NoSQL | 25GB, 25 WCU/RCU, siempre gratis | Sí |
| **AWS** | Aurora PostgreSQL | SQL (PostgreSQL) | 4 ACUs, 1GB (nuevo Mar 2026) | Sí |
| **GCP** | Firestore | NoSQL | 1GB, siempre gratis | Sí |
| **Azure** | Cosmos DB | NoSQL/MongoDB | 1000 RU/s + 25GB, vitalicio | Sí |
| **Supabase** | PostgreSQL | SQL | 500MB, sin tarjeta | No |
| **Neon** | PostgreSQL | SQL | 512MB, 190h compute/mes | No |

---

## El problema de SQLite en la nube (archivado)

Originalmente este proyecto apuntaba a SQLite. El desafío es la **persistencia del archivo .db** en plataformas cloud:

| Proveedor | SQLite persistente? | Cómo |
|-----------|-------------------|------|
| **Oracle Cloud** | ✅ Sí | Disco local 200GB, siempre persiste |
| **Hetzner** | ✅ Sí | Disco local, siempre persiste |
| **Railway** | ✅ Sí | Volumes (~$0.20/GB/mes) |
| **Fly.io** | ✅ Sí | Volumes (~$0.15/GB/mes) |
| **Render (pago)** | ✅ Sí | Disco persistente (Starter+) |
| **Render (free)** | ❌ No | Sin disco persistente. Se pierde al redeployar |
| **Vercel** | ❌ No | Efímero (serverless function) |
| **Koyeb (free)** | ❌ No | Sin volume persistente documentado |
| **Azure Functions** | ❌ No | Efímero |
| **GCP Cloud Run** | ❌ No | Solo /tmp efímero |
| **AWS Lambda** | ❌ No | Efímero |

**Decisión:** SQLite no es requisito duro. Si el hosting necesita otra DB, se cambia. La abstracción de SQLAlchemy lo hace trivial.

---

## Serverless vs Web Service (por qué descartamos Vercel)

Este proyecto necesita un **web service** (proceso permanente), no serverless functions:

| Característica | Web Service (Render, Koyeb) | Serverless (Vercel, Lambda, Cloud Run) |
|---------------|---------------------------|---------------------------------------|
| Modelo | Uvicorn 24/7 | Función por request |
| Pool de conexiones DB | ✅ Persistente | ❌ Se crea en cada request |
| SQLAlchemy engine reutilizable | ✅ Sí | ❌ No |
| Background tasks | ✅ Sí | ❌ No confiable |
| WebSockets / SSE | ✅ Sí | ❌ No |
| Cache en memoria | ✅ Sí | ❌ No existe |
| Filesystem persistente | ✅ Sí (o montado) | ❌ Efímero |
| FastAPI /docs | ✅ Funciona de una | ⚠️ Requiere config |
| Tiempo máximo por request | Sin límite | ⚠️ 10s (free) |
| Cold start | 5-50s | 0.1-2s |

**Regla general:** Si tu app tiene un ORM y base de datos, querés web service. Si es un microservicio stateless (ej. enviar emails, procesar webhooks), serverless está bien.

---

## Matriz de decisión: qué elegir según tu situación

| Situación | Elegir | Por qué |
|-----------|--------|---------|
| MVP, $0, sin tarjeta, quiero empezar ya | **Render + Supabase** | Sin tarjeta, fácil, soluciona persistencia |
| Igual pero cold starts me molestan | **Koyeb + Supabase** | Cold starts más rápidos (5-15s) |
| Tengo tarjeta, quiero máximo $0 | **Oracle VM + MySQL HeatWave** | 4 ARM + 24GB RAM + 50GB MySQL, siempre gratis |
| No quiero saber nada de configuración | **Render + Supabase** | Git push y listo |
| Quiero PostgreSQL serverless moderno | **Neon + Koyeb/Render** | Sin auto-pausa de 7 días |
| Estoy dispuesto a pagar ~$5/mes | **Railway + SQLite en volume** | Mejor DX, sin cold starts |

---

## Comparativa de Costos Mensuales Estimados

| Proveedor | Plan | CPU/RAM | Costo hosting | DB | Total |
|-----------|------|---------|--------------|----|-------|
| **Render** | Free | 512MB shared | $0 | Supabase $0 | **$0** |
| **Koyeb** | Free | 512MB | $0 | Supabase $0 | **$0** |
| **SnapDeploy** | Free | 512MB x4 | $0 | Supabase $0 | **$0** |
| **Shorlabs** | Hobby | serverless | $0 | Supabase $0 | **$0** |
| **Oracle Cloud** | Free | 4 ARM/24GB | $0 | MySQL 50GB $0 | **$0** |
| **Vercel** | Hobby | serverless | $0 | Supabase $0 | **$0** ❌ |
| **Railway** | Hobby | 1vCPU/1GB | ~$5 | SQLite volume ~$0.20 | **~$5.20** |
| **Fly.io** | Shared | 256MB | ~$2 | Volume 1GB ~$0.15 | **~$3** |
| **Hetzner** | CX22 | 2 cores/4GB | €3.79 | Incluido | **~$4** |
| **Render** | Starter | 512MB | $7 | Supabase $0 | **$7** |

---

## Próximos Pasos

El backend está diseñado para ser **hosting-agnostic y database-agnostic**. Cuando deployes:

1. Crear cuenta en **Render** (sin tarjeta)
2. Crear cuenta en **Supabase** (sin tarjeta)
3. Obtener la URL de PostgreSQL de Supabase (`postgresql://...`)
4. Configurar variables de entorno en Render:
   ```
   NOTAS_API_KEY=<tu_clave>
   NOTAS_DATABASE_URL=postgresql://user:pass@host:5432/postgres
   NOTAS_DEBUG=false
   ```
5. Conectar repo de GitHub a Render
6. Deployar
7. Probar `GET /api/health`
8. Configurar la app Android con la URL del servidor + API Key

Cuando quieras cambiar de proveedor o DB, solo ajustás variables de entorno. El resto no cambia.
