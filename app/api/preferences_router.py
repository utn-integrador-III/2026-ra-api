from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.models.user_model import User
from app.models.user_preference_model import UserPreference
from app.api.profile_router import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["Preferences"])


class PreferencesOut(BaseModel):
    voice_guidance_enabled: bool
    walking_speed_mps: float
    model_config = {"from_attributes": True}


class PreferencesUpdate(BaseModel):
    voice_guidance_enabled: Optional[bool] = None
    walking_speed_mps: Optional[float] = None


def _get_or_create(db: Session, user: User) -> UserPreference:
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesOut)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_or_create(db, current_user)


@router.put("", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = _get_or_create(db, current_user)
    if body.voice_guidance_enabled is not None:
        prefs.voice_guidance_enabled = body.voice_guidance_enabled
    if body.walking_speed_mps is not None:
        prefs.walking_speed_mps = body.walking_speed_mps
    db.commit()
    db.refresh(prefs)
    return prefs
