"""
main.py - FastAPI application entry point for BLS Invoice.
Initialises the database, seeds default data, mounts all routers,
and serves the React frontend static files in production.

Start with:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db, SessionLocal
from auth import ensure_default_user
from seed import seed_default_settings

# Import all routers
from routers.auth_router import router as auth_router
from routers.customers   import router as customers_router
from routers.items       import router as items_router
from routers.invoices    import router as invoices_router
from routers.reports     import router as reports_router

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BLS Invoice",
    description="Bluelight Invoice Management System",
    version="1.0.0",
)

# Allow the Vite dev server (port 5173) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers ──────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(items_router)
app.include_router(invoices_router)
app.include_router(reports_router)

# ── Serve React SPA in production ─────────────────────────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

if os.path.isdir(STATIC_DIR):
    # Serve hashed asset files (JS/CSS bundles)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_root():
        """Serve the SPA root."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Catch-all: return index.html so React Router handles client-side routing."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """
    Called automatically when the server starts:
      1. Create database tables
      2. Seed default admin user if none exists
      3. Seed default company/bank settings if none exist
    """
    init_db()
    db = SessionLocal()
    try:
        ensure_default_user(db)
        seed_default_settings(db)
    finally:
        db.close()
    print("BLS Invoice server ready.")
