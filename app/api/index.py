from flask import Flask, jsonify
from wsgiref.simple_server import make_server
import json

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "ok"})

@app.route("/maps")
def maps():
    return jsonify({"route": "/maps werkt zonder mangum"})

# Vercel handler zonder extra packages
def handler(environ, start_response):
    # Flask verwacht een WSGI-app, die hebben we al (app)
    # We geven hem gewoon door aan Flask zelf
    response = app(environ, start_response)
    return response

# Voor lokale tests
if __name__ == "__main__":
    make_server("127.0.0.1", 8000, app).serve_forever()