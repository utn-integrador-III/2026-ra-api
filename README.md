# 2026-ra-api
# PathAR API
Backend desarrollado para el proyecto PathAR, un sistema inteligente de navegación peatonal asistida mediante visión computacional, inteligencia artificial y realidad aumentada.

## Tecnologías

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- YOLOv8 (futuro)
- SegFormer (futuro)

## Instalación

### Crear entorno virtual

python -m venv .venv

### Crear entorno virtual

### Windows:

.venv\Scripts\activate

### Linux:

source .venv/bin/activate

### Instalar dependencias

pip install -r requirements.txt

### Ejecutar proyecto

uvicorn app.main:app --reload

## Documentación

### Swagger:

http://localhost:8000/docs

### Redoc:

http://localhost:8000/redoc

## Estructura

app/
├── api/
├── core/
├── database/
├── models/
├── schemas/
├── services/
├── utils/

### Estado actual

MVP inicial en desarrollo.

### Desarrollo a futuro

feature/navigation
feature/yolo
feature/database
feature/auth