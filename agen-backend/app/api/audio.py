"""
G2 · Audio API — server-side neural text-to-speech with cache.

GET /audio/tts?text=...&voice=female|male → audio bytes, or
  404 "tts_disabled"    no provider configured (client uses the browser voice)
  503 "tts_unavailable" provider failed or daily budget spent (client falls back)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.security import get_current_user
from app.models.user import User
from app.services import tts_service

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.get("/tts/status")
def tts_status(current_user: User = Depends(get_current_user)):
    return {"enabled": tts_service.is_enabled(), "providers": tts_service.providers()}


@router.get("/tts")
def text_to_speech(
    text: str = Query(min_length=1, max_length=tts_service.MAX_TEXT_CHARS),
    voice: str = Query(default="female"),
    lang: str = Query(default="en", pattern="^(en|vi)$"),     # G6 · "vi" for the mascot
    current_user: User = Depends(get_current_user),
):
    if not tts_service.is_enabled():
        raise HTTPException(status_code=404, detail="tts_disabled")
    result = tts_service.synthesize(text, voice, lang)
    if result is None:
        raise HTTPException(status_code=503, detail="tts_unavailable")
    return Response(
        content=result.data,
        media_type=result.mime,
        headers={
            "Cache-Control": "private, max-age=86400",
            "X-TTS-Provider": result.provider,
            "X-TTS-Cache": "hit" if result.cached else "miss",
        },
    )
