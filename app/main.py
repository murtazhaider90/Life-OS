from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from .db import init_db
from .routes import calendar, documents, evidence, planning, study, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Personal AI Life OS", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


for router in (tasks.router, calendar.router, study.router, planning.router, documents.router, evidence.router):
    app.include_router(router)
