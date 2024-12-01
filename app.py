"""This module creates a flask app by registering routes."""

from flask import Flask
from esg_app.api.routes.routes import all_routes


def create_app():
    """Create a Flask Application with default parameters and a name."""
    app = Flask(__name__)

    # Register routes
    all_routes(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
