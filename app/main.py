from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware 
from app.database.database import engine, Base
from app.api.auth_router import router as auth_router
from app.api.profile_router import router as profile_router
from app.models.place_history_model import PlaceHistory
from app.api.history_router import router as history_router
from app.models.location_model import Location
from app.api.locations_router import router as locations_router



# Crea las tablas automáticamente al iniciar
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas/verificadas en la BD")
except Exception as e:
    print(f"⚠ No se pudo conectar a la BD: {e}")
    print("⚠ El servidor arranca igual, pero los endpoints de BD fallarán")

app = FastAPI(
    title="PathAR API",
    description="Backend para navegación peatonal con AR e IA",
    version="1.0.0",
)

# CORS — permite peticiones desde Flutter (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(history_router)
app.include_router(locations_router)

@app.get("/")
def root():
    return {"message": "PathAR API funcionando ✓"}
