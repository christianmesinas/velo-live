from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from os import getenv
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Laad .env (alleen lokaal, niet op Vercel)
load_dotenv()

DATABASE_URL = getenv("DATABASE_URL")

# Fix voor Vercel: geen crash als DATABASE_URL niet bestaat
if DATABASE_URL:
    # Fix postgres:// naar postgresql:// voor SQLAlchemy
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    try:
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,             # 🔥 Vercel fix: geen persistent poolen
            connect_args={"sslmode": "require"}  # 🔥 Supabase vereist SSL
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        logger.info("✅ Database sessie geconfigureerd")

    except Exception as e:
        logger.error(f"❌ Fout bij database configuratie: {e}")
        engine = None
        SessionLocal = None
else:
    logger.warning("⚠️ DATABASE_URL niet gevonden - database functies zijn uitgeschakeld")
    engine = None
    SessionLocal = None
