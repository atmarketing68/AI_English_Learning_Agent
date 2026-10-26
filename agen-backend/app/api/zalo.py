"""G9 · Zalo OA webhook (link by code) and link status for the signed-in user."""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import zalo

router = APIRouter(prefix="/zalo", tags=["Zalo"])


class ZaloStatus(BaseModel):
    available: bool
    oa_link: str | None
    linked: bool
    link_code: str | None


def status_for(db: Session, user: User) -> ZaloStatus:
    available = zalo.enabled()
    return ZaloStatus(available=available, oa_link=zalo.oa_link(), linked=bool(user.zalo_user_id),
                      link_code=zalo.link_code_for(db, user) if available else None)


@router.get("/status", response_model=ZaloStatus)
def get_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return status_for(db, current_user)


@router.post("/unlink", response_model=ZaloStatus)
def unlink(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    zalo.unlink(db, current_user)
    return status_for(db, current_user)


@router.get("/webhook")
def webhook_check():
    """Zalo pings the URL when it is registered."""
    return {"ok": True}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db),
                  x_zevent_signature: str = Header(default=""), x_zevent_timestamp: str = Header(default="")):
    raw = await request.body()
    if not zalo.enabled():
        return {"ok": False, "reason": "zalo_disabled"}
    if not zalo.verify_signature(raw, x_zevent_timestamp, x_zevent_signature):
        raise HTTPException(status_code=403, detail="Bad signature")
    results = [zalo.handle_event(db, ev) for ev in zalo.parse_events(raw)]
    return {"ok": True, "handled": len(results), "actions": [r["action"] for r in results]}
