"""
Vercel serverless entry point
Dit bestand wordt gebruikt door Vercel om de Flask app te draaien
"""
import sys
import os

# Voeg de parent directory toe aan het Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, session, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
import stripe
from app.routes import routes
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel
import logging

# Configureer logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Laad .ENV-bestand
load_dotenv()
stripe.api_key = getenv('STRIPE_SECRET_KEY')

# Initialiseer Flask
app = Flask(__name__, template_folder="../app/templates", static_folder="../app/static")

# Database configuratie
database_url = getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Babel configuratie
app.config['BABEL_DEFAULT_LOCALE'] = 'nl'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = '../app/translations'
app.config['BABEL_SUPPORTED_LOCALES'] = ['nl', 'en', 'fr', 'es', 'de']


def get_locale():
    if 'lang' in request.args:
        language = request.args.get('lang')
        if language in ['nl', 'en', 'fr', 'es', 'de']:
            session['language'] = language
            return language
    if 'language' in session:
        return session['language']
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

# Registreer Blueprint-routes
app.register_blueprint(routes)


@app.route('/test')
def test():
    logging.info("Testroute aangeroepen")
    return "Hello, World! Vercel serverless is running."


@app.context_processor
def inject_user():
    return dict(user=session.get("Gebruiker"))


@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)


@app.context_processor
def inject_language():
    return {'language': str(get_locale())}


# BELANGRIJK: Geen database initialisatie hier!
# Voor Vercel moet de database al bestaan op een remote server (bijv. Supabase, Railway, etc.)
# Draai de database migraties handmatig of via een aparte script

# Vercel verwacht een 'app' variabele
# Deze wordt automatisch gebruikt als WSGI handler
