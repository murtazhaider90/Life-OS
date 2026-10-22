import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import get_settings
from .db import SessionLocal, init_db
from .routes import activity, briefing, calendar, context, documents, evidence, focus, learning, planning, reviews, state, study, tasks, weekly
from .services.adguard import AdGuardNotConfigured, AdGuardRequestError, adguard_configured
from .services.focus import reconcile_expired_focus_mode


async def _focus_expiry_loop() -> None:
    while True:
        await asyncio.sleep(60)
        if not adguard_configured():
            continue
        try:
            with SessionLocal() as db:
                await asyncio.to_thread(reconcile_expired_focus_mode, db)
        except (AdGuardNotConfigured, AdGuardRequestError):
            # A filtering outage must never bring down the Life OS server.
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(_focus_expiry_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Personal AI Life OS", version="0.5.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "version": "0.5.0",
        "adguard_configured": bool(settings.adguard_base_url and settings.adguard_username and settings.adguard_password),
    }


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


for router in (
    tasks.router,
    calendar.router,
    study.router,
    planning.router,
    weekly.router,
    learning.router,
    reviews.router,
    briefing.router,
    documents.router,
    evidence.router,
    activity.router,
    state.router,
    context.router,
    focus.router,
):
    app.include_router(router)
