"""Main FastAPI application entry point for alarm server."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database.database import init_db, get_db
from database.models import User, ConnectionStatus
from api import auth, alarms, websocket
from utils.security import hash_password
from utils.logger import logger
from config import config
import os

# Initialize FastAPI app
app = FastAPI(
    title="CV Alarm Server",
    description="Remote alarm management system with WebSocket synchronization",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(alarms.router)
app.include_router(websocket.router)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Serve index.html at root
from fastapi.responses import FileResponse


@app.get("/")
async def serve_index():
    """Serve the frontend index.html."""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CV Alarm Server is running. Frontend not found."}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database and create default admin user on startup."""
    logger.info("Starting CV Alarm Server...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Create default admin user if it doesn't exist
    db = next(get_db())
    try:
        admin_user = db.query(User).filter(User.username == config.ADMIN_USERNAME).first()

        if not admin_user:
            admin_user = User(
                username=config.ADMIN_USERNAME,
                password_hash=hash_password(config.ADMIN_PASSWORD)
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Created default admin user: {config.ADMIN_USERNAME}")

            # Create connection status entry
            connection_status = ConnectionStatus(user_id=admin_user.id, is_online=False)
            db.add(connection_status)
            db.commit()
        else:
            logger.info(f"Admin user already exists: {config.ADMIN_USERNAME}")

    finally:
        db.close()

    logger.info("CV Alarm Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down CV Alarm Server...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
