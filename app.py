from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_argon2 import Argon2
from flask_jwt_extended import JWTManager
import os

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------
# Extensions (initialized later)
# ---------------------------------
db = SQLAlchemy()
migrate = Migrate()
argon2 = Argon2()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # ---------------------------------
    # Load Configurations
    # ---------------------------------
    app.config.from_object("config.config")

    # ---------------------------------
    # Environment-aware JWT cookie config
    # ---------------------------------
    ENV = os.getenv("FLASK_ENV", "production")

    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
    app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token_cookie"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # can enable later

    if ENV == "production":
        app.config["JWT_COOKIE_SECURE"] = True     # HTTPS only
        app.config["JWT_COOKIE_SAMESITE"] = "None" # required for cross-site
    else:
        app.config["JWT_COOKIE_SECURE"] = False    # local dev
        app.config["JWT_COOKIE_SAMESITE"] = "Lax"

    # ---------------------------------
    # CORS (allow Angular frontend)
    # ---------------------------------
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:4200", "https://attendance.yonnegroup.co"]}},
        supports_credentials=True,
        expose_headers=["Content-Type", "Authorization"],
        allow_headers=["Content-Type", "Authorization"]
    )

    # ---------------------------------
    # Initialize extensions
    # ---------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    argon2.init_app(app)
    jwt.init_app(app)

    # ---------------------------------
    # Register Blueprints
    # ---------------------------------
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.crypto_route import crypto_bp
    from routes.biometrics_routes import biometric_bp
    from routes.attendance_route import attendance_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(crypto_bp, url_prefix="/api/crypto")
    app.register_blueprint(biometric_bp, url_prefix="/api/biometrics")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
