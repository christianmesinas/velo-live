import os

class Config:
    # Fix: convert postgres:// → postgresql://
    raw_db_url = os.getenv("DATABASE_URL", "")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://")

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Babel languages
    LANGUAGES = ['nl', 'en', 'es', 'fr']
