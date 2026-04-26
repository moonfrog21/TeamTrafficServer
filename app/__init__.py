from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Instantiate the db extension here so it can be imported by both
# models.py and routes.py without causing circular imports.
db = SQLAlchemy()


def create_app():
    """Application factory — configure and return the Flask app instance."""
    app = Flask(__name__, instance_relative_config=True)

    # SQLite database stored in the instance/ folder (git-ignored)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///telemetry.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Bind the db extension to this app
    db.init_app(app)

    # Register routes blueprint
    from app.routes import main
    app.register_blueprint(main)

    return app
