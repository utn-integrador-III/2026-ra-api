# 🗺️ PathAR — Backend API

Backend desarrollado con **FastAPI + PostgreSQL** para el sistema inteligente de navegación peatonal asistida con AR e IA.

---

## 🛠️ Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje base |
| FastAPI | 0.136.3 | Framework API REST |
| PostgreSQL | 16 | Base de datos |
| SQLAlchemy | 2.0.50 | ORM |
| psycopg2-binary | 2.9.12 | Driver PostgreSQL |
| Pydantic / pydantic-settings | 2.13.4 / 2.14.2 | Validación y config desde `.env` |
| python-jose | 3.3.0 | JWT tokens |
| firebase-admin | 7.5.0 | Verificación de Firebase ID Token (Google Sign-In) |
| Uvicorn | 0.49.0 | Servidor ASGI |
| pytest / httpx | 8.4.2 / 0.28.1 | Pruebas automatizadas (`TestClient`) |

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

> 📘 **¿Recién te sumás al equipo?** Esta sección asume que ya sabés manejarte
> con WSL/Ubuntu. Si es tu primera vez, seguí [`GUIA_PARA_CHOFI.md`](GUIA_PARA_CHOFI.md) —
> instala WSL desde cero, arma el backend y el frontend, crea tu usuario admin
> y explica cómo cargar destinos/aceras para poder probar la app de verdad.

---

## 🔐 Variables de entorno (`.env`)

Copiar `env.example` a `.env` y completar:

```env
# Base de datos
DATABASE_URL=postgresql://pathar_user:pathar_password@localhost:5432/pathar_db

# JWT
JWT_SECRET_KEY=tu_clave_super_secreta_aqui
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Firebase Admin (verificación de Google Sign-In)
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
```

> `.env` está en `.gitignore` — cada quien crea el suyo, no se comparte por git.

---

## 🔥 Firebase Admin — necesario para que `/api/auth/google` funcione

El frontend manda un **Firebase ID Token** (no un token OAuth de Google), así que este backend lo verifica con el SDK de **Firebase Admin**, usando una credencial de cuenta de servicio del proyecto `pathar-e3fc0`. Esa credencial es secreta y **no está en el repo** (está en `.gitignore` como `firebase-service-account.json`). Para conseguir la tuya:

1. Pedile a Ahian que te agregue como miembro del proyecto Firebase (`pathar-e3fc0`) desde la [consola de Firebase](https://console.firebase.google.com) (⚙️ Configuración del proyecto → Usuarios y permisos).
2. Ya con acceso: ⚙️ Configuración del proyecto → pestaña **Cuentas de servicio** → botón **Generar nueva clave privada**. Se descarga un `.json`.
3. Renombralo a `firebase-service-account.json` y colocalo en la raíz de este repo (mismo nivel que `.env`).
4. Instalar dependencias (`pip install -r requirements.txt`, ya incluye `firebase-admin`) y levantar el servidor normalmente.

> Si el `.venv` te tira `Permission denied` al instalar paquetes, probablemente quedó creado con `sudo` en algún momento. Arreglalo con `sudo chown -R $USER:$USER .venv` (no hace falta `sudo` para el resto de los comandos).

---

## 📁 Estructura del proyecto

```
app/
├── admin/
│   └── index.html            # Panel admin (ubicaciones + aceras), estático
├── api/
│   ├── auth_router.py        # Registro, login, Google OAuth
│   ├── profile_router.py     # Perfil, favoritos, admin/users
│   ├── history_router.py     # Historial de lugares
│   ├── locations_router.py   # CRUD ubicaciones universitarias
│   ├── sidewalks_router.py   # CRUD nodos/aristas de acera (admin-only)
│   └── navigation_router.py  # Cálculo/ciclo de vida de rutas
├── core/
│   ├── config.py             # Carga de .env
│   ├── security.py           # SHA256, JWT
│   └── firebase.py           # Init de Firebase Admin
├── database/
│   └── database.py           # Conexión SQLAlchemy
├── models/
│   ├── user_model.py             # Tabla users
│   ├── place_history_model.py    # Tabla place_history
│   ├── location_model.py         # Tabla locations
│   ├── sidewalk_model.py         # Tablas sidewalk_nodes / sidewalk_edges
│   └── navigation_route_model.py # Tabla navigation_routes
├── schemas/
│   └── auth_schemas.py       # Schemas Pydantic
├── services/
│   └── routing_service.py    # Dijkstra + snapping por arista + giros
├── utils/
│   └── geo.py                # Haversine, bearing, ángulo de giro
└── main.py                   # Punto de entrada, registro de routers

tests/                        # pytest (BD sqlite aislada, ver Pruebas más abajo)
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

### 🧭 Navegación — `/api/navigation` (FR-08 a FR-13)

Ruteo real sobre el grafo de aceras (Dijkstra + snapping por arista), no una
línea recta al destino. Ver sección de Aceras más abajo para cómo se arma
ese grafo.

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `POST` | `/api/navigation/route` | ✅ JWT | Calcular ruta (distancia, puntos, instrucciones de giro) | ✅ Listo |
| `POST` | `/api/navigation/recalculate` | ✅ JWT | Recalcular una ruta activa desde la posición actual | ✅ Listo |
| `POST` | `/api/navigation/start` | ✅ JWT | Marcar una ruta como iniciada | ✅ Listo |
| `POST` | `/api/navigation/finish` | ✅ JWT | Marcar una ruta como finalizada | ✅ Listo |
| `GET` | `/api/navigation/history` | ✅ JWT | Últimas 20 rutas del usuario | ✅ Listo |
| `GET` | `/api/navigation/{id}` | ✅ JWT | Obtener una ruta puntual | ✅ Listo |
| `DELETE` | `/api/navigation/{id}` | ✅ JWT | Borrar una ruta del historial | ✅ Listo |

### 🚶 Aceras (grafo peatonal) — `/api/sidewalks`

Puntos y conexiones invisibles para la app de usuarios finales — solo los
usa el panel admin (para dibujarlos/editarlos) y el motor de rutas de arriba
(para saber por dónde se puede caminar). Viven en tablas separadas de
`locations`, a propósito. Todo el router requiere rol `admin`.

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/sidewalks/nodes` | ✅ Admin | Listar nodos de acera | ✅ Listo |
| `POST` | `/api/sidewalks/nodes` | ✅ Admin | Crear un nodo (lat/lng) | ✅ Listo |
| `DELETE` | `/api/sidewalks/nodes/{id}` | ✅ Admin | Borrar nodo (cascada sobre sus aristas) | ✅ Listo |
| `GET` | `/api/sidewalks/edges` | ✅ Admin | Listar conexiones entre nodos | ✅ Listo |
| `POST` | `/api/sidewalks/edges` | ✅ Admin | Conectar dos nodos (rechaza self-edge y duplicados) | ✅ Listo |
| `DELETE` | `/api/sidewalks/edges/{id}` | ✅ Admin | Borrar una conexión | ✅ Listo |

### 🔧 Administración — `/api/admin`

| Método | Endpoint | Auth | Descripción | Estado |
|---|---|---|---|---|
| `GET` | `/api/admin/users` | ✅ Admin | Listar usuarios y su rol | ✅ Listo |
| `PUT` | `/api/admin/users/{id}/role` | ✅ Admin | Cambiar el rol de un usuario (`user`/`admin`) | ✅ Listo |

> ⚠️ No hay forma de crear el primer admin por API a propósito (evita que
> cualquiera se auto-ascienda) — el primero siempre se promueve a mano en la
> base de datos (`UPDATE users SET role='admin' WHERE email='...'`), y de ahí
> en adelante ya se puede usar este endpoint.

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

> ℹ️ El AR en sí (flecha direccional + línea del camino sobre la cámara) ya
> está implementado, pero **100% del lado del frontend** (Flutter, por
> sensores: cámara + brújula + GPS) — no necesita ni usa ningún endpoint de
> este backend. Esta tabla queda para si en el futuro se agrega algo que sí
> necesite guardar/consultar estado de AR en el servidor.

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

sidewalk_nodes (puntos de acera, invisibles para la app)
├── id (UUID, PK)
├── latitude
├── longitude
└── is_active

sidewalk_edges (conexión caminable entre dos nodos)
├── id (UUID, PK)
├── node_a_id (FK → sidewalk_nodes)
├── node_b_id (FK → sidewalk_nodes)
├── distance_m
└── is_active

navigation_routes
├── id (UUID, PK)
├── user_id (FK → users)
├── origin_lat / origin_lng
├── destination_lat / destination_lng
├── destination_name
├── distance_m / duration_s
├── points (JSON — polyline completa)
├── steps (JSON — instrucciones de giro)
├── status ('calculated' | 'active' | 'finished')
├── created_at / started_at / finished_at
```

---

## 🔒 Seguridad

- Contraseñas hasheadas con **SHA256**
- Autenticación stateless con **JWT (HS256)**
- Google Sign-In verificado vía **Firebase ID Token**
- Tokens con expiración configurable (default 60 min)

---

## 🧪 Pruebas

```bash
pytest -v
```

Corren contra una base SQLite descartable (no tocan tu Postgres real) y
contra una credencial de Firebase falsa generada al vuelo — no necesitás
tener `.env` ni `firebase-service-account.json` configurados para correrlas.
Cubren autenticación, CRUD de aceras (con control de rol admin) y el motor
de rutas (estabilidad del snapping, ruta directa en el mismo tramo, giros).

Se corren automáticamente en GitHub Actions en cada push/PR — ver
`.github/workflows/backend-tests.yml`.

---

## 📖 Documentación interactiva

Con el servidor corriendo:
- **Swagger:** `http://localhost:8000/docs`
- **Redoc:** `http://localhost:8000/redoc`

---

## 🚀 Desarrollo futuro

```
feature/yolo          → Detección de obstáculos en tiempo real (on-device, TFLite)
feature/segformer     → Segmentación de aceras desde la cámara (on-device)
feature/favorites     → Tabla real de favoritos (hoy los endpoints existen pero son stub)
feature/alerts        → Sistema de alertas en tiempo real
```

Ya no están en esta lista porque ya están implementados: cálculo de rutas
peatonales (`/api/navigation`), grafo de aceras (`/api/sidewalks`), panel de
administración con roles (`/admin` + `/api/admin/users`).