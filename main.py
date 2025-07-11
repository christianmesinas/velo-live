from flask import Flask, session, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
import stripe
from app.database.models import Base
from app.routes import routes
from app.simulation import simulation
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel, _
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ✅ Laad .ENV-bestand (alleen lokaal nodig, niet op Render)
load_dotenv()
stripe.api_key = getenv('STRIPE_SECRET_KEY')

# ✅ Initialiseer Flask
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
database_url = getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Render geeft soms postgres:// maar SQLAlchemy wil postgresql://
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'postgresql://admin:Velo123@db:5432/velo_community'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Babel configuratie
app.config['BABEL_DEFAULT_LOCALE'] = 'nl'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'app/translations'
app.config['BABEL_SUPPORTED_LOCALES'] = ['nl', 'en', 'fr', 'es', 'de']


def get_locale():
    if 'lang' in request.args:
        language = request.args.get('lang')
        if language in ['nl', 'en', 'fr', 'es', 'de']:
            session['language'] = language
            logging.debug(f"Set language from query param: {language}")
            return language
    if 'language' in session:
        language = session['language']
        logging.debug(f"Language from session: {language}")
        return language
    logging.debug("Using default language: nl")
    return 'nl'


# Initialiseer Babel
babel = Babel(app, locale_selector=get_locale)

# Stel de secret key in voor sessies
app.secret_key = getenv("SECRET_KEY", "fallback-secret")

# OAuth instellen
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=getenv("AUTH0_CLIENT_ID"),
    client_secret=getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "audience": "https://" + getenv("AUTH0_DOMAIN") + "/api/v2/"
    },
    server_metadata_url=f'https://{getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# ✅ Registreer je Blueprint-routes
app.register_blueprint(routes)


# Testroute om te controleren of de server draait
@app.route('/test')
def test():
    logging.info("Testroute aangeroepen")
    return "Hello, World! Server is running."


# Maak databasetabellen en voer initiële simulatie uit
with app.app_context():
    try:
        logging.info("Proberen databasetabellen aan te maken...")
        db.create_all()  # Maakt alle tabellen aan (Station, Fiets, Gebruiker, etc.)
        logging.info("✅ Tabellen succesvol aangemaakt bij opstart!")

        # Controleer of de fietsen-tabel leeg is voordat de simulatie wordt uitgevoerd
        if db.session.query(Base.metadata.tables['fietsen']).count() == 0:
            logging.info("Database is leeg, initiële simulatie wordt uitgevoerd...")
            simulation.sla_stations_op_in_db(simulation.stations)
            fietsen = simulation.genereer_fietsen(5800, simulation.stations)
            simulation.sla_fietsen_op_in_db(fietsen)
            gebruikers = simulation.genereer_gebruikers(50000)
            simulation.sla_gebruikers_op_in_db(gebruikers)
            geschiedenis = simulation.genereer_geschiedenis(gebruikers, fietsen, simulation.stations, dagen=30)
            simulation.sla_geschiedenis_op_in_db(geschiedenis)
            logging.info("✅ Initiële simulatie uitgevoerd: database gevuld met gebruikers, fietsen en geschiedenis")
        else:
            logging.info("Database bevat al gegevens, simulatie wordt overgeslagen")
    except Exception as e:
        logging.error(f"❌ Fout bij initialiseren database of simulatie: {str(e)}", exc_info=True)


@app.context_processor
def inject_user():
    return dict(user=session.get("Gebruiker"))


@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)


@app.context_processor
def inject_language():
    return {'language': str(get_locale())}


# Opstart app (alleen lokaal, Render gebruikt gunicorn)
if __name__ == "__main__":
    port = int(getenv('PORT', 8000))
    app.run(host="0.0.0.0", port=port, debug=True)