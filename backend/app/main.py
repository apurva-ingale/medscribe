import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from .auth import hash_pw, user_from_token
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Consultation, User
from .routes import auth_router, router
from .ws import hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub.loop = asyncio.get_running_loop()
    for _ in range(30):  # wait for Postgres to accept connections
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            time.sleep(1)
    with SessionLocal() as db:
        email = settings.admin_email.lower()
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(email=email, name="Admin", password_hash=hash_pw(settings.admin_password), role="admin"))
            db.commit()
    yield


app = FastAPI(title="MedScribe", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(router)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.websocket("/ws/consultations/{cid}")
async def consultation_ws(websocket: WebSocket, cid: str, token: str = Query(...)):
    with SessionLocal() as db:
        user = user_from_token(token, db)
        c = db.get(Consultation, cid)
        if not user or not c or (user.role != "admin" and c.doctor_id != user.id):
            await websocket.close(code=4401)
            return
        snapshot = {"status": c.status, "stage": c.stage}
    await hub.connect(cid, websocket)
    await websocket.send_json(snapshot)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(cid, websocket)
