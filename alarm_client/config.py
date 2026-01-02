"""Configuration management for the alarm client."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # VPS connection
    VPS_URL = os.getenv("VPS_URL", "ws://localhost:8000/ws")
    REST_API_URL = os.getenv("REST_API_URL", "http://localhost:8000/api")

    # Authentication
    USERNAME = os.getenv("ALARM_USERNAME", os.getenv("USERNAME", "admin"))
    PASSWORD = os.getenv("ALARM_PASSWORD", os.getenv("PASSWORD", "admin"))

    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

    # Paths
    CV_ALARM_ROOT = os.getenv("CV_ALARM_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RUN_ALARM_SCRIPT = os.getenv("RUN_ALARM_SCRIPT", "run_alarm.py")
    MODEL_PATH = os.getenv("MODEL_PATH", "models/shufflenet_pretrained_weights.pth")

    # Reconnection settings
    RECONNECT_INITIAL_DELAY = int(os.getenv("RECONNECT_INITIAL_DELAY", "1"))
    RECONNECT_MAX_DELAY = int(os.getenv("RECONNECT_MAX_DELAY", "60"))
    RECONNECT_MULTIPLIER = float(os.getenv("RECONNECT_MULTIPLIER", "2"))

    # Process management
    MAX_ALARM_DURATION = int(os.getenv("MAX_ALARM_DURATION", "1900"))  # 31 minutes

    # Platform-specific lock file path
    import platform
    import tempfile
    if platform.system() == "Windows":
        default_lock = os.path.join(tempfile.gettempdir(), "cv_alarm.lock")
    else:
        default_lock = "/tmp/cv_alarm.lock"
    LOCK_FILE_PATH = os.getenv("LOCK_FILE_PATH", default_lock)


config = Config()
