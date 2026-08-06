from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import os
import time
import uuid
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from db import ConfigRecord, TemplateRecord, UserRecord, VariableRecord, get_db, init_db
from seed import MASTER_DATA_KEY, seed_if_empty
from auth import create_access_token, get_current_user, require_roles, verify_password

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pixous")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

app = FastAPI(title="Pixous Template Engine API")

# CORS is restricted to explicitly configured origins. Set ALLOWED_ORIGINS to a
# comma-separated list of real frontend origin(s) in any non-local deployment.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:6262").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health_check():
    return {"status": "ok"}


# All non-health routes live under /api — this keeps them from colliding with
# the frontend's own client-side routes (e.g. GET /templates the API endpoint
# vs. the SPA's /templates page) when both are served from one origin/service.
api = APIRouter(prefix="/api")


@app.on_event("startup")
def on_startup():
    init_db()
    db = next(get_db())
    seed_if_empty(db)
    logger.info("Startup complete (environment=%s, allowed_origins=%s)", ENVIRONMENT, ALLOWED_ORIGINS)


# --- Simple in-memory rate limiting for login (per-process; fine for a single-instance deploy) ---
_LOGIN_ATTEMPTS: Dict[str, List[float]] = {}
LOGIN_RATE_LIMIT = 10
LOGIN_RATE_WINDOW_SECONDS = 60


def _check_login_rate_limit(ip: str):
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS.get(ip, []) if now - t < LOGIN_RATE_WINDOW_SECONDS]
    if len(attempts) >= LOGIN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again in a minute.")
    attempts.append(now)
    _LOGIN_ATTEMPTS[ip] = attempts


# --- Models ---
class BrandingConfig(BaseModel):
    logoEnabled: bool
    signatureEnabled: bool
    footerEnabled: bool
    letterheadEnabled: bool
    companyDetailsEnabled: bool

class ChannelData(BaseModel):
    enabled: bool
    subject: Optional[str] = ""
    content: str

class SectionData(BaseModel):
    id: str
    name: str
    type: str
    enabled: bool
    order: int
    required: bool
    defaultContent: Any

class ChecklistItem(BaseModel):
    id: str
    title: str
    description: str
    mandatory: bool
    ownerRole: str
    evidenceRequired: bool

class AudienceSelection(BaseModel):
    allEmployees: bool
    departments: List[str]
    locations: List[str]
    roles: List[str]

class NotificationBehavior(BaseModel):
    requireAcknowledgement: bool
    allowComments: bool
    pinToNoticeBoard: bool

class PublishingConfig(BaseModel):
    priority: str
    publishImmediately: bool
    effectiveDate: str
    expiryDate: str
    audience: AudienceSelection
    notificationBehavior: NotificationBehavior

class EventTrigger(BaseModel):
    enabled: bool
    eventType: str
    autoGenerate: bool
    autoPublish: bool
    leadTimeDays: int

class TemplateBase(BaseModel):
    name: str
    description: str
    department: str
    category: str
    status: str
    owner: str
    language: str
    visibility: str
    tags: List[str] = []
    branding: BrandingConfig
    channels: Dict[str, ChannelData] = {}
    allowed_attachments: List[str] = []
    sections: List[SectionData] = []
    checklistItems: List[ChecklistItem] = []
    signoffRole: str = ""
    publishing: PublishingConfig
    eventTrigger: EventTrigger
    banner: str = ""

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(TemplateBase):
    pass

class LoginRequest(BaseModel):
    email: str
    password: str

class MasterDataItem(BaseModel):
    id: str
    name: str
    active: bool = True
    parentId: Optional[str] = None

class PriorityItem(BaseModel):
    id: str
    name: str
    active: bool = True
    order: int
    badgeClass: str
    description: str = ""
    requiresAcknowledgementDefault: bool = False

class SimpleList(BaseModel):
    items: List[MasterDataItem]

class LanguageList(BaseModel):
    items: List[MasterDataItem]
    default: str

class PriorityList(BaseModel):
    items: List[PriorityItem]

class MasterDataLists(BaseModel):
    categories: SimpleList
    departments: SimpleList
    languages: LanguageList
    priorities: PriorityList

class MasterDataUpdate(BaseModel):
    lists: MasterDataLists


# --- Auth ---
@api.post("/auth/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    _check_login_rate_limit(request.client.host if request.client else "unknown")
    user = db.query(UserRecord).filter(UserRecord.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
    }


# --- Templates ---
@api.get("/templates")
def get_templates(db: Session = Depends(get_db), user: UserRecord = Depends(get_current_user)):
    return [r.payload for r in db.query(TemplateRecord).all()]

@api.get("/templates/{template_id}")
def get_template(template_id: str, db: Session = Depends(get_db), user: UserRecord = Depends(get_current_user)):
    record = db.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    return record.payload

@api.post("/templates")
def create_template(template: TemplateCreate, db: Session = Depends(get_db), user: UserRecord = Depends(require_roles("Admin", "Editor"))):
    new_id = str(uuid.uuid4())
    data = template.model_dump()
    data["id"] = new_id
    data["created_by"] = user.name
    data["updated_by"] = user.name
    data["version"] = 1
    db.add(TemplateRecord(id=new_id, payload=data))
    db.commit()
    return data

@api.put("/templates/{template_id}")
def update_template(template_id: str, template: TemplateUpdate, db: Session = Depends(get_db), user: UserRecord = Depends(require_roles("Admin", "Editor"))):
    record = db.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    updated_data = template.model_dump()
    updated_data["id"] = record.payload["id"]
    updated_data["created_by"] = record.payload["created_by"]
    updated_data["updated_by"] = user.name
    updated_data["version"] = record.payload["version"] + 1
    record.payload = updated_data
    db.commit()
    return updated_data

@api.delete("/templates/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db), user: UserRecord = Depends(require_roles("Admin", "Editor"))):
    record = db.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(record)
    db.commit()
    return {"deleted": True, "id": template_id}

@api.get("/categories")
def get_categories(db: Session = Depends(get_db), user: UserRecord = Depends(get_current_user)):
    record = db.query(ConfigRecord).filter(ConfigRecord.key == MASTER_DATA_KEY).first()
    if not record:
        return []
    return [i["name"] for i in record.payload["lists"]["categories"]["items"] if i.get("active", True)]

# --- Master Data (org-wide reference lists: categories, departments, languages, priorities) ---
@api.get("/master-data")
def get_master_data(db: Session = Depends(get_db), user: UserRecord = Depends(get_current_user)):
    record = db.query(ConfigRecord).filter(ConfigRecord.key == MASTER_DATA_KEY).first()
    if not record:
        raise HTTPException(status_code=404, detail="Master data not configured")
    return record.payload

@api.put("/master-data")
def update_master_data(body: MasterDataUpdate, db: Session = Depends(get_db), user: UserRecord = Depends(require_roles("Admin"))):
    record = db.query(ConfigRecord).filter(ConfigRecord.key == MASTER_DATA_KEY).first()
    if not record:
        raise HTTPException(status_code=404, detail="Master data not configured")
    payload = body.model_dump()
    payload["updatedBy"] = user.name
    payload["updatedAt"] = datetime.now(timezone.utc).isoformat()
    record.payload = payload
    db.commit()
    return payload

@api.get("/variables")
def get_variables(db: Session = Depends(get_db), user: UserRecord = Depends(get_current_user)):
    return [r.payload for r in db.query(VariableRecord).all()]

# AI Actions (Groq)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

AI_ACTION_INSTRUCTIONS = {
    "Improve": "Improve the clarity and quality of this text while keeping the same meaning and length.",
    "Professional": "Rewrite this text in a more professional tone.",
    "Friendly": "Rewrite this text in a warmer, more friendly tone.",
    "Formal": "Rewrite this text in a more formal tone.",
    "Shorter": "Make this text more concise without losing key information.",
    "Longer": "Expand this text with more detail while keeping the same intent.",
    "Grammar": "Fix any grammar and spelling mistakes in this text.",
    "Company Tone": "Rewrite this text to match a professional corporate company communication style.",
}

class AIActionRequest(BaseModel):
    action: str
    content: str
    targetLanguage: Optional[str] = None

@api.post("/ai/action")
def ai_action(req: AIActionRequest, user: UserRecord = Depends(require_roles("Admin", "Editor"))):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the server")

    if req.action == "Translate":
        instruction = f"Translate this text into {req.targetLanguage or 'Spanish'}."
    else:
        instruction = AI_ACTION_INSTRUCTIONS.get(req.action)
    if not instruction:
        raise HTTPException(status_code=400, detail=f"Unknown AI action: {req.action}")

    system_prompt = (
        "You edit HTML snippets used inside a message template editor. "
        "Preserve the existing HTML tags and structure. "
        "Preserve any {{VariableName}} placeholders exactly as written - never translate, rename, or remove them. "
        "Return only the rewritten HTML with no explanation, no markdown code fences, and no extra commentary."
    )

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{instruction}\n\nText:\n{req.content}"}
                ],
                "temperature": 0.4,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        return {"result": result}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Groq API request failed: {e}")


app.include_router(api)

# Optionally serve the built frontend from this same service (single-service
# deploy). Only activates when frontend/dist actually exists — i.e. the build
# command built it — so local dev (where the frontend runs on its own Vite
# dev server) is completely unaffected.
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    logger.info("Serving built frontend from %s", FRONTEND_DIST)
else:
    logger.info("frontend/dist not found — running API-only (normal for local dev)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True)
