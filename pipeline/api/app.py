import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from db.models import (
    create_client,
    get_clients,
    get_lead_detail,
    get_leads,
    get_pipeline_stats,
    init_db,
    update_company_status,
    log_event,
    get_due_outreach,
)

load_dotenv()

DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "")
DASHBOARD_ORIGIN = os.getenv("DASHBOARD_ORIGIN", "http://localhost:3000")

init_db()

app = FastAPI(title="Brightwick Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[DASHBOARD_ORIGIN, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)


def _require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)):
    if not DASHBOARD_SECRET:
        return  # Auth disabled if no secret configured
    if credentials is None or credentials.credentials != DASHBOARD_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class MarkWonRequest(BaseModel):
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    monthly_value_gbp: Optional[float] = None
    notes: Optional[str] = None


class TriggerOutreachRequest(BaseModel):
    limit: Optional[int] = 10


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/pipeline/stats", dependencies=[Depends(_require_auth)])
def pipeline_stats():
    return get_pipeline_stats()


@app.get("/api/leads", dependencies=[Depends(_require_auth)])
def list_leads(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    leads = get_leads(status=status, limit=limit, offset=offset)
    return {"leads": leads, "count": len(leads)}


@app.get("/api/leads/{lead_id}", dependencies=[Depends(_require_auth)])
def get_lead(lead_id: int):
    lead = get_lead_detail(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.post("/api/leads/{lead_id}/mark-won", dependencies=[Depends(_require_auth)])
def mark_won(lead_id: int, body: MarkWonRequest):
    lead = get_lead_detail(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead["status"] in ("won",):
        raise HTTPException(status_code=400, detail="Lead is already won")

    client_id = create_client(
        company_id=lead_id,
        client_name=lead["company_name"],
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        monthly_value_gbp=body.monthly_value_gbp,
        notes=body.notes,
    )
    update_company_status(lead_id, "won")
    log_event(lead_id, "won", f"client_id={client_id}")
    return {"ok": True, "client_id": client_id}


@app.post("/api/leads/{lead_id}/mark-dead", dependencies=[Depends(_require_auth)])
def mark_dead(lead_id: int):
    lead = get_lead_detail(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    update_company_status(lead_id, "dead")
    log_event(lead_id, "dead", "manually marked dead via API")
    return {"ok": True}


@app.post("/api/outreach/trigger", dependencies=[Depends(_require_auth)])
def trigger_outreach(body: TriggerOutreachRequest):
    from outreach.sender import EmailSender

    due = get_due_outreach(limit=body.limit or 10)
    if not due:
        return {"ok": True, "sent": 0, "message": "No outreach due"}

    sender = EmailSender()
    sent = sender.run_batch(due)
    return {"ok": True, "sent": sent, "queued": len(due)}


@app.get("/api/clients", dependencies=[Depends(_require_auth)])
def list_clients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    clients = get_clients(limit=limit, offset=offset)
    return {"clients": clients, "count": len(clients)}
