"""
Configuration Management for ConvoInsight Backend
Handles environment-based configuration with sensible defaults
"""

import os
from typing import Optional

# ============================================
# Deployment Mode Configuration
# ============================================
MODE = os.getenv("DEPLOYMENT_MODE", "cloud")  # "local" | "cloud" | "hybrid"

# ============================================
# Redis Configuration (Caching & Rate Limiting)
# ============================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "dataset_list": int(os.getenv("CACHE_TTL_DATASET_LIST", "60")),
    "dataset_content": int(os.getenv("CACHE_TTL_DATASET_CONTENT", "300")),
    "query_result": int(os.getenv("CACHE_TTL_QUERY_RESULT", "300")),
    "session_state": int(os.getenv("CACHE_TTL_SESSION_STATE", "1800")),
    "pg_connection": int(os.getenv("CACHE_TTL_PG_CONNECTION", "600")),
    "llm_models": int(os.getenv("CACHE_TTL_LLM_MODELS", "3600")),
    "prompt_suggestions": int(os.getenv("CACHE_TTL_PROMPT_SUGGESTIONS", "300")),
}

# Rate limit settings
RATE_LIMITS = {
    "default": os.getenv("RATE_LIMIT_DEFAULT", "100/hour"),
    "query": os.getenv("RATE_LIMIT_QUERY", "20/minute"),
    "upload": os.getenv("RATE_LIMIT_UPLOAD", "50/hour"),
    "dataset_ops": os.getenv("RATE_LIMIT_DATASET_OPS", "200/hour"),
    "auth": os.getenv("RATE_LIMIT_AUTH", "10/minute"),
}

# ============================================
# PostgreSQL Configuration
# ============================================
# Local development PostgreSQL
LOCAL_POSTGRES_URL = os.getenv(
    "LOCAL_POSTGRES_URL",
    "postgresql://convoinsight:dev_password_change_in_production@localhost:5432/convoinsight"
)

# Production/Supabase PostgreSQL (with connection pooler)
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Use local or production based on mode
def get_postgres_url() -> Optional[str]:
    """Get appropriate PostgreSQL URL based on deployment mode"""
    if MODE == "local":
        return LOCAL_POSTGRES_URL
    elif MODE in ["cloud", "hybrid"]:
        return POSTGRES_URL or LOCAL_POSTGRES_URL
    return None

# ============================================
# GCP Configuration (Cloud Storage & Firestore)
# ============================================
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET = os.getenv("GCS_BUCKET")
GCS_DATASETS_PREFIX = os.getenv("GCS_DATASETS_PREFIX", "datasets")
GCS_DIAGRAMS_PREFIX = os.getenv("GCS_DIAGRAMS_PREFIX", "diagrams")
GCS_SIGNED_URL_TTL_SECONDS = int(os.getenv("GCS_SIGNED_URL_TTL_SECONDS", "604800"))  # 7 days
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")

# Firestore collections
FIRESTORE_COLLECTION_SESSIONS = os.getenv("FIRESTORE_SESSIONS_COLLECTION", "convo_sessions")
FIRESTORE_COLLECTION_DATASETS = os.getenv("FIRESTORE_DATASETS_COLLECTION", "datasets_meta")
FIRESTORE_COLLECTION_PROVIDERS = os.getenv("FIRESTORE_PROVIDERS_COLLECTION", "convo_providers")
FIRESTORE_COLLECTION_PG = os.getenv("FIRESTORE_PG_COLLECTION", "pg_connections")

# ============================================
# Supabase Configuration (Storage)
# ============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_CHARTS = os.getenv("SUPABASE_BUCKET_CHARTS", "charts")
SUPABASE_SIGNED_TTL_SECONDS = int(os.getenv("SUPABASE_SIGNED_TTL_SECONDS", "604800"))

# ============================================
# Security Configuration
# ============================================
FERNET_KEY = os.getenv("FERNET_KEY")

# CORS origins
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://127.0.0.1:5500,http://localhost:5500,http://localhost:5173,http://127.0.0.1:5173,https://convoinsight.vercel.app"
).split(",")

# ============================================
# Storage Configuration
# ============================================
STORAGE_MODE = os.getenv("STORAGE_MODE", MODE)  # Which storage backend to use by default

# Local filesystem paths
DATASETS_ROOT = os.getenv("DATASETS_ROOT", os.path.abspath("./datasets"))
CHARTS_ROOT = os.getenv("CHARTS_ROOT", os.path.abspath("./charts"))

# ============================================
# LLM Configuration
# ============================================
# API Keys (optional, can be provided per-request)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Speech-to-Text
STT_MODEL_ID = os.getenv("STT_MODEL_ID", "groq/whisper-large-v3")
STT_API_KEY = os.getenv("GROQ_API_KEY")

# ============================================
# Server Configuration
# ============================================
PORT = int(os.getenv("PORT", "8080"))
FLASK_ENV = os.getenv("FLASK_ENV", "production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ============================================
# Feature Flags
# ============================================
FEATURES = {
    "cache": CACHE_ENABLED,
    "rate_limit": RATE_LIMIT_ENABLED,
    "postgres": bool(get_postgres_url()),
    "gcs": bool(GCS_BUCKET and GCP_PROJECT_ID),
    "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
    "local_storage": MODE in ["local", "hybrid"],
}

# ============================================
# Helper Functions
# ============================================
def is_local_mode() -> bool:
    """Check if running in local development mode"""
    return MODE == "local"

def is_cloud_mode() -> bool:
    """Check if running in cloud mode"""
    return MODE == "cloud"

def is_hybrid_mode() -> bool:
    """Check if running in hybrid mode"""
    return MODE == "hybrid"

def get_feature(name: str) -> bool:
    """Check if a feature is enabled"""
    return FEATURES.get(name, False)

# ============================================
# Validation
# ============================================
def validate_config():
    """Validate critical configuration on startup"""
    errors = []

    # Validate cache configuration
    if CACHE_ENABLED and not REDIS_URL:
        errors.append("CACHE_ENABLED is true but REDIS_URL is not set")

    # Validate rate limit configuration
    if RATE_LIMIT_ENABLED and not REDIS_URL:
        errors.append("RATE_LIMIT_ENABLED is true but REDIS_URL is not set")

    # Validate cloud mode requirements
    if is_cloud_mode():
        if not GCP_PROJECT_ID:
            errors.append("Cloud mode requires GCP_PROJECT_ID")
        if not GCS_BUCKET:
            errors.append("Cloud mode requires GCS_BUCKET")

    # Validate encryption key
    if FERNET_KEY:
        try:
            from cryptography.fernet import Fernet
            Fernet(FERNET_KEY.encode())
        except Exception as e:
            errors.append(f"Invalid FERNET_KEY: {e}")

    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))

# Run validation on import (optional, can be disabled)
if os.getenv("VALIDATE_CONFIG_ON_IMPORT", "true").lower() == "true":
    try:
        validate_config()
    except ValueError as e:
        import warnings
        warnings.warn(f"Configuration validation warning: {e}")
