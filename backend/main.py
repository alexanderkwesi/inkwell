import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.config import ALLOWED_ORIGINS, UPLOAD_DIR
from app.routers import auth, books, payments, users, files, webhooks

# Create tables in SQLite database if they don't exist
Base.metadata.create_all(bind=engine)

# Ensure UPLOAD_DIR exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app = FastAPI(
    title="Inkwell AI API",
    description="Python FastAPI backend migrating legacy PHP logic to modern REST services with SQLite storage.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount files uploads directory as static route
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")  # /api/webhooks/gocardless

@app.get("/")
def read_root():
    return {"message": "Inkwell AI API is running.", "status": "online"}
