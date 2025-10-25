from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
)
from models.models import User
from app import db, argon2

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.credential and argon2.check_password_hash(user.credential.password_hash, password):
        # ✅ Add extra claims (role, department)
        additional_claims = {
            "role": user.role,
            "department": user.department,
        }

        access_token = create_access_token(identity=str(user.uuid), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.uuid))

        resp = make_response(
            jsonify({
                "message": "Login successful",
                "user": {
                    "uuid": user.uuid,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "role": user.role,
                    "department": user.department,
                    "email": user.email,
                },
            })
        )

        # ✅ Store tokens in HttpOnly cookies
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)

        return resp, 200

    return jsonify({"error": "Invalid email or password"}), 401


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)

    resp = make_response(jsonify({"message": "Token refreshed"}))
    set_access_cookies(resp, new_access_token)

    return resp, 200
