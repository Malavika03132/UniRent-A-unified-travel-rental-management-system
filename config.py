import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'unirent-heritage-secret-key-2026-kerala')
    
    # MySQL configurations
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DB = os.getenv('MYSQL_DB', 'unirent_db')
    
    # Determine DB URI: allow explicit DATABASE_URL, or build MySQL URI, or fallback to SQLite
    explicit_db = os.getenv('DATABASE_URL')
    if explicit_db:
        SQLALCHEMY_DATABASE_URI = explicit_db
    elif os.getenv('USE_MYSQL', 'false').lower() in ('true', '1', 'yes'):
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
        )
    else:
        # Default SQLite database for instant out-of-the-box evaluation without setup barriers
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'unirent.db')}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    } if 'mysql' in SQLALCHEMY_DATABASE_URI else {}
    
    SESSION_COOKIE_NAME = 'unirent_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day
