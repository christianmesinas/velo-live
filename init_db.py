"""
Database initialisatie en migratie script voor Velo Live

Dit script kan worden gebruikt om:
1. Database tabellen aan te maken
2. Database te seeden met initiële simulatie data
3. Database status te controleren

Gebruik:
    python init_db.py --create-tables     # Maak alleen tabellen aan
    python init_db.py --seed              # Maak tabellen + seed data
    python init_db.py --check             # Controleer database status
    python init_db.py --reset             # VOORZICHTIG: Drop en hermaak alles
"""

import argparse
import sys
from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Laad environment variables
load_dotenv()

# Import models en simulatie
try:
    from app.database.models import Base, Station, Fiets, Gebruiker, Geschiedenis, Usertable, Pas, ContactBericht, Defect
    from app.simulation import simulation
except ImportError as e:
    logger.error(f"Fout bij importeren: {e}")
    logger.error("Zorg dat je dit script draait vanuit de root directory van het project")
    sys.exit(1)


def get_database_url():
    """Haal database URL op uit environment variables"""
    database_url = getenv('DATABASE_URL')

    if not database_url:
        logger.error("DATABASE_URL niet gevonden in environment variables")
        logger.info("Zorg dat je .env bestand correct is geconfigureerd")
        sys.exit(1)

    # Fix voor Render/Heroku postgres:// URLs
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("Database URL aangepast: postgres:// -> postgresql://")

    return database_url


def create_tables(engine):
    """Maak alle database tabellen aan"""
    try:
        logger.info("Bezig met aanmaken van database tabellen...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Alle tabellen succesvol aangemaakt!")
        return True
    except Exception as e:
        logger.error(f"❌ Fout bij aanmaken tabellen: {e}")
        return False


def drop_tables(engine):
    """Drop alle database tabellen (VOORZICHTIG!)"""
    try:
        logger.warning("⚠️  WAARSCHUWING: Alle tabellen worden verwijderd...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Alle tabellen verwijderd")
        return True
    except Exception as e:
        logger.error(f"❌ Fout bij verwijderen tabellen: {e}")
        return False


def check_table_exists(engine, table_name):
    """Controleer of een tabel bestaat"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
            ))
            return result.scalar()
    except Exception as e:
        logger.error(f"Fout bij controleren tabel {table_name}: {e}")
        return False


def get_table_count(engine, table_name):
    """Haal aantal rijen op uit een tabel"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception as e:
        logger.error(f"Fout bij tellen rijen in {table_name}: {e}")
        return 0


def check_database_status(engine):
    """Controleer status van de database"""
    logger.info("📊 Database status:")
    logger.info("=" * 50)

    tables = [
        'stations',
        'fietsen',
        'gebruikers',
        'geschiedenis',
        'inlog_gegevens',
        'passen',
        'contact_berichten',
        'defecten'
    ]

    for table in tables:
        exists = check_table_exists(engine, table)
        if exists:
            count = get_table_count(engine, table)
            logger.info(f"✅ {table:20} - {count:,} rijen")
        else:
            logger.info(f"❌ {table:20} - Bestaat niet")

    logger.info("=" * 50)


def seed_database():
    """Vul database met initiële simulatie data"""
    logger.info("🌱 Bezig met seeden van database...")

    try:
        # Controleer of database al data bevat
        from app.database.session import SessionLocal
        session = SessionLocal()

        try:
            fiets_count = session.query(Fiets).count()
            if fiets_count > 0:
                logger.warning(f"⚠️  Database bevat al {fiets_count} fietsen")
                response = input("Wil je de database opnieuw seeden? (ja/nee): ")
                if response.lower() not in ['ja', 'j', 'yes', 'y']:
                    logger.info("Seeding geannuleerd")
                    return False

                logger.info("Bestaande data wordt overschreven...")
        finally:
            session.close()

        # Genereer en sla simulatie data op
        logger.info("Genereren van stations...")
        simulation.sla_stations_op_in_db(simulation.stations)

        logger.info("Genereren van 5800 fietsen...")
        fietsen = simulation.genereer_fietsen(5800, simulation.stations)
        simulation.sla_fietsen_op_in_db(fietsen)

        logger.info("Genereren van 50.000 gebruikers...")
        gebruikers = simulation.genereer_gebruikers(50000)
        simulation.sla_gebruikers_op_in_db(gebruikers)

        logger.info("Genereren van 30 dagen geschiedenis (dit kan even duren)...")
        geschiedenis = simulation.genereer_geschiedenis(
            gebruikers,
            fietsen,
            simulation.stations,
            dagen=30
        )
        simulation.sla_geschiedenis_op_in_db(geschiedenis)

        logger.info("✅ Database succesvol geseeded!")
        return True

    except Exception as e:
        logger.error(f"❌ Fout bij seeden database: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Velo Live Database Migratie Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python init_db.py --create-tables    # Maak alleen tabellen aan
  python init_db.py --seed             # Maak tabellen + voeg seed data toe
  python init_db.py --check            # Controleer database status
  python init_db.py --reset            # Drop en hermaak alles (VOORZICHTIG!)
        """
    )

    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Maak database tabellen aan'
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Maak tabellen aan en vul met seed data'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Controleer database status'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='⚠️  Drop alle tabellen en maak opnieuw aan (VOORZICHTIG!)'
    )

    args = parser.parse_args()

    # Als geen argumenten, toon help
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)

    # Maak database connectie
    database_url = get_database_url()
    logger.info(f"Verbinden met database...")

    try:
        engine = create_engine(database_url)
        # Test connectie
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database verbinding succesvol!")
    except Exception as e:
        logger.error(f"❌ Kon niet verbinden met database: {e}")
        sys.exit(1)

    # Voer gevraagde acties uit
    if args.reset:
        logger.warning("⚠️  RESET MODE - Alle data zal worden verwijderd!")
        response = input("Weet je het zeker? Type 'RESET' om te bevestigen: ")
        if response == 'RESET':
            drop_tables(engine)
            create_tables(engine)
            logger.info("✅ Database gereset")
        else:
            logger.info("Reset geannuleerd")

    if args.create_tables:
        create_tables(engine)

    if args.seed:
        # Zorg dat tabellen bestaan
        if not check_table_exists(engine, 'fietsen'):
            logger.info("Tabellen bestaan nog niet, aanmaken...")
            create_tables(engine)

        seed_database()

    if args.check:
        check_database_status(engine)

    logger.info("✅ Klaar!")


if __name__ == "__main__":
    main()
