import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

INKWELL_VERSION = "1.0.0"
INKWELL_ENV = os.getenv("INKWELL_ENV", "sandbox")  # "sandbox" or "production"

# Database - Defaults to local SQLite database file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inkwell.db")

# Anthropic / Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# GoCardless
GC_ACCESS_TOKEN = os.getenv("GC_ACCESS_TOKEN", "sandbox_token_here")
GC_WEBHOOK_SECRET = os.getenv("GC_WEBHOOK_SECRET", "webhook_secret_here")
GC_API_BASE = (
    "https://api.gocardless.com"
    if INKWELL_ENV == "production"
    else "https://api-sandbox.gocardless.com"
)

# App Base URL
APP_URL = os.getenv("APP_URL", "http://localhost:56517")

# Redirect URIs for GoCardless Billing Request Flow
GC_SUCCESS_REDIRECT_URI = f"{APP_URL}/payment-complete"
GC_NOTIFY_URI = f"{APP_URL}/webhooks/gocardless"

# Plans config
PLAN_LIMITS = {
    "free": 4,
    "pro": 10,
    "elite": 999999,  # Unlimited
}

PLAN_PRICES = {
    "free": 0.0,
    "pro": 12.0,
    "elite": 29.0,
}

GC_PLAN_IDS = {
    "pro": os.getenv("GC_PLAN_ID_PRO", "YOUR_GC_PRO_PLAN_ID"),
    "elite": os.getenv("GC_PLAN_ID_ELITE", "YOUR_GC_ELITE_PLAN_ID"),
}

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET_MINIMUM_32_CHARS_LONG_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 30  # 30 days

# Admin
ADMIN_EMAIL = "admin@inkwell.ai"
# Setup standard admin hash (in database initialization)

# CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",
    "http://localhost:56517",
]

# File Storage settings
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "uploads")
