# 🗺️ PathAR — Backend API

Backend desarrollado con **FastAPI + PostgreSQL** para el sistema inteligente de navegación peatonal asistida con AR e IA.

---

## 🛠️ Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje base |
| FastAPI | 0.111.0 | Framework API REST |
| PostgreSQL | 16 | Base de datos |
| SQLAlchemy | 2.0.30 | ORM |
| psycopg2 | 2.9.9 | Driver PostgreSQL |
| python-jose | 3.3.0 | JWT tokens |
| passlib | 1.7.4 | Hashing |
| google-auth | 2.29.0 | Verificación Google OAuth |
| httpx | 0.27.0 | HTTP client async |
| Uvicorn | 0.29.0 | Servidor ASGI |

---

## ⚙️ Instalación (Ubuntu 24.04 / WSL)

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd 2026-ra-api

# 2. Crear entorno virtual
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
nano .env  # completar los valores

# 5. Iniciar PostgreSQL
sudo pg_ctlcluster 16 main start

# 6. Crear BD y usuario (primera vez)
sudo -u postgres psql
```

```sql
CREATE USER pathar_user WITH PASSWORD 'pathar_password';
CREATE DATABASE pathar_db OWNER pathar_user;
GRANT ALL PRIVILEGES ON DATABASE pathar_db TO pathar_user;
\q
```

```bash
# 7. Levantar el servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔐 Variables de entorno (`.env`)

```env
# Base de datos
DATABASE_URL=postgresql://pathar_user:pathar_password@localhost:5433/pathar_db

# JWT
JWT_SECRET_KEY=tu_clave_super_secreta_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Google OAuth (Web Client ID de Firebase Console)
GOOGLE_CLIENT_ID=732484081824-xxxxxxxx.apps.googleusercontent.com
```

---

## 📁 Estructura del proyecto

```
app/
├── api/
│   ├── auth_router.py        # Registro, login, Google OAuth
│   ├── profile_router.py     # Perfil, favoritos
│   ├── history_router.py     # Historial de lugares
│   └── locations_router.py   # CRUD ubicaciones universitarias
├── core/
│   ├── config.py             # Carga de .env
│   └── security.py           # SHA256, JWT
├── database/
│   └── database.py           # Conexión SQLAlchemy
├── models/
│   ├── user_model.py         # Tabla users
│   ├── place_history_model.py # Tabla place_history
│   └── location_model.py     # Tabla locations
├── schemas/
│   └── auth_schemas.py       # Schemas Pydantic
└── main.py                   # Punto de entrada, registro de routers
```

---

## 🔗 Endpoints implementados

### 🔑 Autenticación — `/api/auth`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | ❌ | Registro con nombre, correo y contraseña (SHA256) | ✅ Listo |
| `POST` | `/api/auth/login` | ❌ | Login con correo y contraseña, devuelve JWT | ✅ Listo |
| `POST` | `/api/auth/google` | ❌ | Login/registro con Firebase ID Token | ✅ Listo |
| `GET` | `/api/auth/profile` | ✅ JWT | Obtener perfil del usuario actual | ✅ Listo |
| `PUT` | `/api/auth/profile` | ✅ JWT | Actualizar nombre del perfil | ✅ Listo |
| `POST` | `/api/auth/logout` | ✅ JWT | Cerrar sesión | ⏳ Pendiente |
| `POST` | `/api/auth/refresh-token` | ✅ JWT | Renovar token expirado | ⏳ Pendiente |
| `DELETE` | `/api/auth/account` | ✅ JWT | Eliminar cuenta | ⏳ Pendiente |

### 👤 Usuarios — `/api/users`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/users` | ✅ Admin | Listar usuarios | ⏳ Pendiente |
| `GET` | `/api/users/{id}` | ✅ JWT | Obtener usuario por ID | ⏳ Pendiente |
| `PUT` | `/api/users/{id}` | ✅ Admin | Actualizar usuario | ⏳ Pendiente |
| `DELETE` | `/api/users/{id}` | ✅ Admin | Eliminar usuario | ⏳ Pendiente |

### 📍 Historial de lugares — `/api/history`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/history/places` | ✅ JWT | Guardar lugar visitado/buscado | ✅ Listo |
| `GET` | `/api/history/places` | ✅ JWT | Obtener últimos 10 lugares | ✅ Listo |
| `DELETE` | `/api/history/places` | ✅ JWT | Limpiar historial | ✅ Listo |
| `GET` | `/api/history/routes` | ✅ JWT | Historial de rutas navegadas | ⏳ Pendiente |
| `GET` | `/api/history/searches` | ✅ JWT | Historial de búsquedas | ⏳ Pendiente |

### ❤️ Favoritos — `/api/favorites`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/favorites` | ✅ JWT | Listar favoritos del usuario | ✅ Listo (vacío) |
| `POST` | `/api/favorites` | ✅ JWT | Agregar favorito | ✅ Listo (stub) |
| `DELETE` | `/api/favorites/{id}` | ✅ JWT | Eliminar favorito | ✅ Listo (stub) |

> ⚠️ Los favoritos retornan vacío por ahora — falta tabla `favorites` en BD.

### 🏫 Ubicaciones universitarias — `/api/locations`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/locations/` | ✅ JWT | Listar todas las ubicaciones | ✅ Listo |
| `GET` | `/api/locations/nearby` | ✅ JWT | Ubicaciones cercanas por radio | ✅ Listo |
| `GET` | `/api/locations/{id}` | ✅ JWT | Obtener una ubicación | ✅ Listo |
| `POST` | `/api/locations/` | ✅ JWT | Crear ubicación (admin) | ✅ Listo |
| `PUT` | `/api/locations/{id}` | ✅ JWT | Editar ubicación | ✅ Listo |
| `DELETE` | `/api/locations/{id}` | ✅ JWT | Desactivar ubicación (soft delete) | ✅ Listo |

### 🧭 Navegación — `/api/navigation`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/navigation/route` | ✅ JWT | Calcular ruta | ⏳ Pendiente |
| `POST` | `/api/navigation/start` | ✅ JWT | Iniciar navegación | ⏳ Pendiente |
| `POST` | `/api/navigation/finish` | ✅ JWT | Finalizar navegación | ⏳ Pendiente |
| `POST` | `/api/navigation/recalculate` | ✅ JWT | Recalcular ruta | ⏳ Pendiente |
| `GET` | `/api/navigation/history` | ✅ JWT | Historial de rutas | ⏳ Pendiente |

### 📌 POIs — `/api/poi`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/poi` | ✅ JWT | Listar POIs | ⏳ Pendiente |
| `GET` | `/api/poi/nearby` | ✅ JWT | POIs cercanos | ⏳ Pendiente |
| `POST` | `/api/poi` | ✅ Admin | Crear POI | ⏳ Pendiente |

### 🤖 IA — `/api/ai`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/ai/analyze-frame` | ✅ JWT | Analizar frame de cámara | ⏳ Pendiente (YOLOv8) |
| `POST` | `/api/ai/detect-obstacles` | ✅ JWT | Detectar obstáculos | ⏳ Pendiente |
| `POST` | `/api/ai/detect-sidewalk` | ✅ JWT | Detectar acera (SegFormer) | ⏳ Pendiente |
| `POST` | `/api/ai/context-analysis` | ✅ JWT | Análisis contextual | ⏳ Pendiente |
| `POST` | `/api/ai/recommendations` | ✅ JWT | Recomendaciones inteligentes | ⏳ Pendiente |

### 👁️ Visión — `/api/vision`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/vision/upload-frame` | ✅ JWT | Subir frame de cámara | ⏳ Pendiente |
| `POST` | `/api/vision/recognize-object` | ✅ JWT | Reconocer objeto | ⏳ Pendiente (YOLOv8) |
| `POST` | `/api/vision/segment-scene` | ✅ JWT | Segmentación semántica | ⏳ Pendiente (SegFormer) |

### 🔮 AR — `/api/ar`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/ar/update-overlay` | ✅ JWT | Actualizar overlay AR | ⏳ Pendiente |
| `GET` | `/api/ar/config` | ✅ JWT | Configuración AR | ⏳ Pendiente |
| `POST` | `/api/ar/update-route` | ✅ JWT | Actualizar ruta en AR | ⏳ Pendiente |

---

## 🗄️ Modelos de BD implementados

```
users
├── id (UUID, PK)
├── name
├── email (único)
├── password_hash (SHA256, NULL si Google)
├── google_id (NULL si login manual)
├── auth_provider ('local' | 'google')
├── is_active
├── created_at
└── updated_at

place_history
├── id (UUID, PK)
├── user_id (FK → users)
├── name
├── address
├── place_type
├── latitude
├── longitude
└── visited_at

locations (ubicaciones universitarias)
├── id (UUID, PK)
├── name
├── description
├── location_type ('classroom'|'lab'|'office'|'cafeteria'|'bathroom'|'parking'|'other')
├── latitude
├── longitude
├── building
├── floor
├── is_active
├── created_at
└── updated_at
```

---

## 🔒 Seguridad

- Contraseñas hasheadas con **SHA256**
- Autenticación stateless con **JWT (HS256)**
- Google Sign-In verificado vía **Firebase ID Token**
- Tokens con expiración configurable (default 60 min)

---

## 📖 Documentación interactiva

Con el servidor corriendo:
- **Swagger:** `http://localhost:8000/docs`
- **Redoc:** `http://localhost:8000/redoc`

---

## 🚀 Desarrollo futuro

```
feature/navigation    → Cálculo de rutas peatonales
feature/yolo          → Detección de objetos con YOLOv8
feature/segformer     → Segmentación de escena
feature/ar            → Overlays de realidad aumentada
feature/favorites     → Tabla y CRUD completo de favoritos
feature/admin         → Panel de administración y roles
feature/alerts        → Sistema de alertas en tiempo real
```