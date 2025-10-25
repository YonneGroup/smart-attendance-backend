from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from models.models import User, Biometric
import base64
import json
import numpy as np

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    dot = np.dot(a, b)
    return dot / (np.linalg.norm(a) * np.linalg.norm(b))

biometric_bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")

@biometric_bp.route("/enroll", methods=["POST"])
@jwt_required()
def enroll_biometric():
    claims = get_jwt()
    role = claims.get("role")
    if role != "ADMIN":
        abort(403, description="Admins only")

    data = request.get_json(silent=True)
    if not data or "user_uuid" not in data:
        abort(400, description="Missing user_uuid")

    user = User.query.filter_by(uuid=data["user_uuid"]).first()
    if not user:
        abort(404, description="User not found")

    try:
        fingerprint_template = data.get("fingerprint_template")
        face_template = data.get("face_template")

        # Always normalize: store embedding array as JSON
        face_json = None
        if face_template:
            if isinstance(face_template, dict) and "embedding" in face_template:
                face_json = json.dumps(face_template["embedding"]).encode("utf-8")
            elif isinstance(face_template, list):
                face_json = json.dumps(face_template).encode("utf-8")

        bio = Biometric(
            user=user,
            fingerprint_template=base64.b64decode(fingerprint_template) if fingerprint_template else None,
            face_template=face_json
        )

        db.session.add(bio)
        db.session.commit()

        return jsonify({"message": "Biometric enrollment successful"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to enroll biometric data", "details": str(e)}), 500


@biometric_bp.route("/verify/face", methods=["POST"])
@jwt_required(optional=True)  # allow login attempt without session
def verify_face():
    data = request.get_json(silent=True)
    if not data or "embedding" not in data:
        return jsonify({"success": False, "message": "Missing embedding"}), 400

    embedding = data["embedding"]
    biometrics = Biometric.query.filter(Biometric.face_template.isnot(None)).all()
    if not biometrics:
        return jsonify({"success": False, "message": "No enrolled faces"}), 200

    best_match = None
    best_score = -1.0
    threshold = 0.65

    for bio in biometrics:
        try:
            stored_embedding = json.loads(bio.face_template.decode("utf-8"))
            score = cosine_similarity(embedding, stored_embedding)
            if score > best_score:
                best_match = bio.user
                best_score = score
        except Exception as e:
            continue

    if best_match and best_score >= threshold:
        return jsonify({
            "success": True,
            "user_uuid": best_match.uuid,
            "firstname": best_match.firstname,
            "lastname": best_match.lastname,
            "score": float(best_score)
        }), 200

    return jsonify({"success": False, "message": "No match found"}), 200
