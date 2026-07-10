import os
from dotenv import load_dotenv

# Load variables from .env into the environment (local dev only —
# on Render/Railway, env vars are injected directly by the platform)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalized_db_uri():
    """
    Render/Railway/Heroku give you a DATABASE_URL like:
        postgres://user:pass@host/dbname
    but SQLAlchemy 1.4+/2.x requires:
        postgresql://user:pass@host/dbname
    This fixes that automatically. Falls back to local SQLite if no
    DATABASE_URL is set (i.e. when you're developing on your own laptop).
    """
    url = os.environ.get('DATABASE_URL', '').strip()
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    return 'sqlite:///' + os.path.join(BASE_DIR, 'skilltribe.db')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-ME')

    SQLALCHEMY_DATABASE_URI = _normalized_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True} 
     # avoids stale Postgres connections
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
    # Uploads
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 2 MB max upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Pagination
    TEACHERS_PER_PAGE = 9

    # Environment flags
    FLASK_ENV   = os.environ.get('FLASK_ENV', 'development')
    IS_PRODUCTION = FLASK_ENV == 'production'
    SEED_DEMO   = os.environ.get('SEED_DEMO', 'false').lower() == 'true'

    # Cookie security — only force HTTPS-only cookies in production
    SESSION_COOKIE_SECURE   = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
