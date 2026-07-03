from pydantic import BaseModel, EmailStr

# ── Registro manual ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

# ── Login manual ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ── Google OAuth ─────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    id_token: str  # Token que Flutter recibe de Google y manda al backend

# ── Respuesta de autenticación ───────────────────────────────────────

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    auth_provider: str

    model_config = {"from_attributes": True}

AuthResponse.model_rebuild()