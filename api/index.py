"""
Vercel serverless entry point
Dit bestand wordt gebruikt door Vercel om de Flask app te draaien
"""
import sys
import os

# Voeg de parent directory toe aan het Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging

# Configureer logging EERST
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from flask import Flask, session, request, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from os import getenv
    from datetime import datetime

    logger.info("✅ Flask imports succesvol")

    # Initialiseer Flask
    app = Flask(__name__, template_folder="../app/templates", static_folder="../app/static")

    # Secret key (VERPLICHT voor sessions)
    app.secret_key = getenv("SECRET_KEY", "vercel-fallback-secret-change-this")
    if app.secret_key == "vercel-fallback-secret-change-this":
        logger.warning("⚠️ Gebruik een echte SECRET_KEY in productie!")

    # Database configuratie
    database_url = getenv('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
        db = SQLAlchemy(app)
        logger.info("✅ Database configuratie succesvol")
    else:
        logger.error("❌ DATABASE_URL niet gevonden!")
        db = None

    # Optionele imports met error handling
    try:
        import stripe
        stripe_key = getenv('STRIPE_SECRET_KEY')
        if stripe_key:
            stripe.api_key = stripe_key
            logger.info("✅ Stripe geconfigureerd")
        else:
            logger.warning("⚠️ STRIPE_SECRET_KEY niet gevonden")
    except ImportError as e:
        logger.warning(f"⚠️ Stripe import mislukt: {e}")

    # Babel configuratie (optioneel)
    try:
        from flask_babel import Babel
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

        babel = Babel(app, locale_selector=get_locale)
        logger.info("✅ Babel geconfigureerd")
    except ImportError as e:
        logger.warning(f"⚠️ Babel import mislukt: {e}")

    # OAuth configuratie (optioneel)
    try:
        from authlib.integrations.flask_client import OAuth
        auth0_domain = getenv("AUTH0_DOMAIN")
        auth0_client_id = getenv("AUTH0_CLIENT_ID")
        auth0_client_secret = getenv("AUTH0_CLIENT_SECRET")

        if auth0_domain and auth0_client_id and auth0_client_secret:
            oauth = OAuth(app)
            oauth.register(
                "auth0",
                client_id=auth0_client_id,
                client_secret=auth0_client_secret,
                client_kwargs={
                    "scope": "openid profile email",
                    "audience": f"https://{auth0_domain}/api/v2/"
                },
                server_metadata_url=f'https://{auth0_domain}/.well-known/openid-configuration'
            )
            logger.info("✅ Auth0 geconfigureerd")
        else:
            logger.warning("⚠️ Auth0 environment variables niet volledig geconfigureerd")
            oauth = None
    except ImportError as e:
        logger.warning(f"⚠️ OAuth import mislukt: {e}")
        oauth = None

    # Importeer routes (optioneel)
    try:
        from app.routes import routes
        app.register_blueprint(routes)
        logger.info("✅ Routes geregistreerd")
    except ImportError as e:
        logger.error(f"❌ Routes import mislukt: {e}")
        logger.info("App draait in debug mode zonder routes")

    # Test routes
    @app.route('/')
    def index():
        return jsonify({
            "status": "ok",
            "message": "Velo Live API is running on Vercel",
            "database": "connected" if db else "not configured",
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route('/test')
    @app.route('/api/test')
    def test():
        logger.info("Test route aangeroepen")
        return jsonify({
            "status": "success",
            "message": "Vercel serverless is working!",
            "environment": {
                "DATABASE_URL": "configured" if getenv('DATABASE_URL') else "missing",
                "SECRET_KEY": "configured" if getenv('SECRET_KEY') else "using fallback",
                "STRIPE_SECRET_KEY": "configured" if getenv('STRIPE_SECRET_KEY') else "missing",
                "AUTH0_DOMAIN": "configured" if getenv('AUTH0_DOMAIN') else "missing",
            }
        })

    @app.route('/api/health')
    def health():
        health_status = {
            "status": "healthy",
            "database": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Test database connectie
        if db:
            try:
                db.session.execute('SELECT 1')
                health_status["database"] = "connected"
            except Exception as e:
                health_status["database"] = f"error: {str(e)}"
                health_status["status"] = "unhealthy"

        return jsonify(health_status)

    # Context processors
    @app.context_processor
    def inject_user():
        return dict(user=session.get("Gebruiker"))

    @app.context_processor
    def inject_datetime():
        return dict(datetime=datetime)

    @app.context_processor
    def inject_language():
        try:
            return {'language': str(get_locale())}
        except:
            return {'language': 'nl'}

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Error: {error}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(error)
        }), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found"
        }), 404

    logger.info("✅ Flask app volledig geïnitialiseerd")

except Exception as e:
    logger.error(f"❌ Kritieke fout bij initialisatie: {e}", exc_info=True)
    # Maak een minimale Flask app voor error reporting
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/')
    @app.route('/<path:path>')
    def error_page(path=''):
        return jsonify({
            "error": "Application failed to initialize",
            "message": str(e),
            "details": "Check Vercel logs for more information"
        }), 500

# Vercel verwacht een 'app' variabele
# Deze wordt automatisch gebruikt als WSGI handler
