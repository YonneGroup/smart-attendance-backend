"""
📘 Smart Attendance System – Example Configuration

This is a sample config file to guide VPS deployment.
DO NOT use these values in production. 
Instead, replace them with secure environment variables.
"""

from datetime import timedelta
import os

class Config:
    # Flask Secret Key (for session signing, CSRF protection, etc.)
    # Replace with a long, random string in production.
    SECRET_KEY = os.getenv("SECRET_KEY", "replace-with-strong-secret")

    # Database connection string
    # Example: "postgresql://username:password@localhost:5432/smart_attendance"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        "postgresql://<user>:<password>@<host>:5432/smart_attendance"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Secret Key (for signing JWT tokens)
    # Replace with a different secure random string in production.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "replace-with-jwt-secret")

    # -----------------------
    # JWT – using cookies
    # -----------------------
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False       # Set to True if using HTTPS
    JWT_COOKIE_SAMESITE = "Lax"     # Options: "Strict", "Lax", "None"
    JWT_COOKIE_CSRF_PROTECT = False # Can be enabled later if needed
    JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
    JWT_REFRESH_COOKIE_NAME = "refresh_token_cookie"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)   # Adjust as needed
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # Refresh token expiry
