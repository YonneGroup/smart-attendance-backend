from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.models import User, Credential, Student
from app import db, argon2

# Blueprint with url_prefix and no strict slash issues
user_bp = Blueprint("users", __name__, url_prefix="/api/users")

# ---------------------------
# Constants
# ---------------------------
VALID_ROLES = {"ADMIN", "STAFF", "STUDENT"}


# ---------------------------
# Enroll Staff (Admin only)
# ---------------------------
@user_bp.route("/enroll/staff", methods=["POST"])
@jwt_required()
def enroll_staff():
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(uuid=current_user_id).first()

    if not current_user or current_user.role != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    required_fields = ["firstname", "lastname", "email", "password", "role", "department"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        abort(400, description=f"Missing required fields: {', '.join(missing)}")

    if User.query.filter_by(email=data["email"]).first():
        abort(400, description="Email already exists")

    role = data.get("role", "").upper()
    if role not in VALID_ROLES:
        abort(400, description=f"Invalid role: {role}. Must be one of {', '.join(VALID_ROLES)}")

    try:
        # Create user and credentials
        new_user = User(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            role=role,
            department=data["department"]
        )

        password_hash = argon2.generate_password_hash(data["password"])
        cred = Credential(password_hash=password_hash, user=new_user)

        db.session.add_all([new_user, cred])
        db.session.commit()

        return jsonify({"message": "User enrolled successfully"}), 201

    except Exception as e:
        db.session.rollback()
        # Show friendly error in production
        return jsonify({"error": "Failed to enroll user"}), 500
    
    
# ---------------------------
# Enroll Student (Admin only)
# ---------------------------
@user_bp.route("/enroll/student", methods=["POST"])
@jwt_required()
def enroll_student():
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(uuid=current_user_id).first()

    if not current_user or current_user.role != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    required_fields = ["firstname", "lastname", "email", "role", "department"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        abort(400, description=f"Missing required fields: {', '.join(missing)}")

    if Student.query.filter_by(email=data["email"]).first():
        abort(400, description="Email already exists")

    role = data.get("role", "").upper()
    if role not in VALID_ROLES:
        abort(400, description=f"Invalid role: {role}. Must be one of {', '.join(VALID_ROLES)}")

    try:
        # Create student credentials
        new_student = Student(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            role=role,
            department=data["department"]
        )


        db.session.add_all([new_student])
        db.session.commit()

        return jsonify({"message": "Student enrolled successfully"}), 201

    except Exception as e:
        db.session.rollback()
        # Show friendly error in production
        return jsonify({"error": "Failed to enroll student"}), 500


# ---------------------------
# Get All Staff (Admin only)
# ---------------------------
@user_bp.route("/staff", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_all_staff():
    claims = get_jwt()
    role = claims.get("role")

    if role != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    users = User.query.all()
    user_data = [
        {
            "uuid": u.uuid,
            "firstname": u.firstname,
            "lastname": u.lastname,
            "email": u.email,
            "role": u.role,
            "department": u.department
        }
        for u in users
    ]

    return jsonify(user_data), 200

# ---------------------------
# Get All Students (Admin only)
# ---------------------------
@user_bp.route("/students", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_all_students():
    claims = get_jwt()
    role = claims.get("role")

    if role != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    students = Student.query.all()
    student_data = [
        {
            "uuid": s.uuid,
            "firstname": s.firstname,
            "lastname": s.lastname,
            "email": s.email,
            "role": s.role,
            "department": s.department
        }
        for s in students
    ]

    return jsonify(student_data), 200