from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base
from app.api.auth_router import router as auth_router
from app.api.profile_router import router as profile_router
from app.api.history_router import router as history_router
from app.api.locations_router import router as locations_router
from app.api.sidewalks_router import router as sidewalks_router
from app.api.navigation_router import router as navigation_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Importar modelos para que create_all los detecte
from app.models import (  # noqa
    user_model,
    place_history_model,
    location_model,
    sidewalk_model,
    navigation_route_model,
)

try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas/verificadas en la BD")
except Exception as e:
    print(f"⚠ No se pudo conectar a la BD: {e}")

app = FastAPI(
    title="PathAR API",
    description="Backend para navegación peatonal con AR e IA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/admin", StaticFiles(directory="app/admin", html=True), name="admin")

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(history_router)
app.include_router(locations_router)
app.include_router(sidewalks_router)
app.include_router(navigation_router)

@app.get("/")
def root():
    return {"message": "PathAR API funcionando ✓"}