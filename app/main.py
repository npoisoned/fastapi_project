from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.links import router as links_router
from app.db.base import *
from app.db.session import Base, engine
from app.tasks.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="Short Link Service")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


@app.get("/")
def root():
    return {"message": "Service is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(links_router)