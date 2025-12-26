"""Configuration management for the alarm server."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""

    # Server settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/alarms.db")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

    # Admin user settings
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_TIMEOUT = int(os.getenv("WS_TIMEOUT", "90"))

    # JWT settings
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24


config = Config()
