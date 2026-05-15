"""
Dream Recorder - FastAPI Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.api.routes import auth, dreams, generate, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init database tables
    await init_db()
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="Dream Recorder API",
    description="AI-powered dream visualization - 梦境记录器",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001", "http://147.139.134.10"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(dreams.router)
app.include_router(generate.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {
        "name": "Dream Recorder API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
