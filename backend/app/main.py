from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal, migrate_schema
from .models import models
from .config import settings
from .api.routes import router
from .services.core import seed

app=FastAPI(title="CreatorShield AI — Guidewire-Inspired Insurance Core", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(',')], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)
migrate_schema()
with SessionLocal() as db: seed(db)
app.include_router(router, prefix="/api")

@app.get("/")
def root(): return {"service":"CreatorShield AI","architecture":"Guidewire-inspired PolicyCenter / ClaimCenter / BillingCenter simulator","status":"running"}
@app.get("/health")
def health(): return {"status":"ok"}
