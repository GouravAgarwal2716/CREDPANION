"""
backend/main.py
Credpanion FastAPI server entrypoint.
"""
from __future__ import annotations
import os
import sys

# Ensure project root is on sys.path so all modules resolve correctly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api_routes import router

app = FastAPI(
    title="Credpanion — Agentic Credit Intelligence Platform",
    description="Multi-agent bank credit committee simulation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Credpanion API"}


@app.on_event("startup")
async def startup():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs",    exist_ok=True)
    print("✅ Credpanion API started — http://localhost:8000/docs")
