"""
AI Documentation Generation Platform — FastAPI Backend.
Handles REST API for job submission, progress tracking, and file download.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import threading

from backend.config import get_settings
from backend.database import init_database
from backend.routes import health, jobs, queue
from runner.main import main as run_runner_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup and start background queue worker."""
    init_database()
    print("[API] FastAPI server started")
    runner_thread = threading.Thread(target=run_runner_worker, daemon=True)
    runner_thread.start()
    print("[API] Background runner worker started")
    yield
    print("[API] FastAPI server shutting down")


app = FastAPI(
    title="AI Docs Generator API",
    description="REST API for the AI Documentation Generation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()

# CORS — restricted to configured trusted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    """Inject HTTP security headers into all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def disable_static_caching(request, call_next):
    """Disable browser 304 caching for CSS/JS static files so updates reflect immediately."""
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/css") or path.startswith("/js") or path in ("/", "/favicon.ico", "/favicon.svg", "/logo.png"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Mount routes
app.include_router(health.router, tags=["Health"])
app.include_router(jobs.router, tags=["Jobs"])
app.include_router(queue.router, tags=["Queue"])

# Paths to frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
CSS_DIR = os.path.join(FRONTEND_DIR, "css")
JS_DIR = os.path.join(FRONTEND_DIR, "js")

# Mount CSS & JS static directories
if os.path.exists(CSS_DIR):
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")


@app.get("/")
def read_root():
    """Serve the main frontend HTML file."""
    html_path = os.path.join(FRONTEND_DIR, "ai-docs-generator.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Frontend file not found", "docs": "/docs"}


@app.get("/logo.png")
def read_logo():
    """Serve the logo image file."""
    logo_path = os.path.join(FRONTEND_DIR, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    root_logo = os.path.join(os.path.dirname(FRONTEND_DIR), "logo.png")
    if os.path.exists(root_logo):
        return FileResponse(root_logo)
    return {"error": "Logo file not found"}


@app.get("/favicon.ico")
@app.get("/favicon.svg")
def read_favicon():
    """Serve the favicon file."""
    svg_path = os.path.join(FRONTEND_DIR, "favicon.svg")
    if os.path.exists(svg_path):
        return FileResponse(svg_path, media_type="image/svg+xml")
    ico_path = os.path.join(FRONTEND_DIR, "favicon.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path)
    return {"error": "Favicon file not found"}


