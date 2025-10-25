from datetime import timedelta
import os

class config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # for signing JWTs

    # -----------------------
    # JWT – using cookies
    # -----------------------
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False       # True only if using HTTPS
    JWT_COOKIE_SAMESITE = "Lax"     # Options: "Strict", "Lax", "None"
    JWT_COOKIE_CSRF_PROTECT = False # can enable later if needed
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"   # default
    JWT_REFRESH_COOKIE_NAME = "refresh_token_cookie" # default
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)  # adjust as needed
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30) # refresh token expiry