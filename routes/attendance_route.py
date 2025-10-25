from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import datetime, date, time as dtime, timezone
from models.models import Student, User, Biometric, StaffAttendance, StudentAttendance
from app import db
import json
import numpy as np

# ---------------------------
# Office Hours Configuration
# ---------------------------
OFFICE_OPEN = dtime(8, 0, 0)     # 08:00 AM
OFFICE_CLOSE = dtime(16, 59, 0)  # 04:59 PM

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")

# ---------------------------
# Utility Functions
# ---------------------------
def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    dot = np.dot(a, b)
    return dot / (np.linalg.norm(a) * np.linalg.norm(b))


def match_face(embedding, threshold=0.65):
    """Return best matching user from face embeddings."""
    biometrics = Biometric.query.filter(Biometric.face_template.isnot(None)).all()
    best_match, best_score = None, -1

    for bio in biometrics:
        try:
            stored_embedding = json.loads(bio.face_template.decode("utf-8"))
            score = cosine_similarity(embedding, stored_embedding)
            if score > best_score:
                best_match, best_score = bio.user, score
        except Exception:
            continue

    if best_match and best_score >= threshold:
        return best_match, "face", best_score
    return None, None, None


def match_fingerprint(fingerprint_template):
    """Stub fingerprint matcher (replace with SDK)."""
    biometrics = Biometric.query.filter(Biometric.fingerprint_template.isnot(None)).all()
    for bio in biometrics:
        # TODO: Replace with actual fingerprint matcher SDK
        if bio.fingerprint_template == fingerprint_template.encode("utf-8"):
            return bio.user, "fingerprint"
    return None, None


def has_signed_in_today(user_id):
    """Check if staff has already signed in today."""
    today = date.today()
    return (
        StaffAttendance.query.filter(
            StaffAttendance.user_id == user_id,
            StaffAttendance.timestamp >= datetime(today.year, today.month, today.day)
        ).first()
        is not None
    )


def get_today_attendance_record(user_id):
    """Return today's staff attendance record."""
    today = date.today()
    start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    return (
        StaffAttendance.query.filter(
            StaffAttendance.user_id == user_id,
            StaffAttendance.created_at >= start
        ).order_by(StaffAttendance.id.desc()).first()
    )


def has_student_signed_in_today(user_id):
    """Check if student has already signed in today."""
    today = date.today()
    return (
        StudentAttendance.query.filter(
            StudentAttendance.user_id == user_id,
            StudentAttendance.timestamp >= datetime(today.year, today.month, today.day)
        ).first()
        is not None
    )


def get_today_student_attendance_record(user_id):
    """Return today's student attendance record."""
    today = date.today()
    start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    return (
        StudentAttendance.query.filter(
            StudentAttendance.user_id == user_id,
            StudentAttendance.created_at >= start
        ).order_by(StudentAttendance.id.desc()).first()
    )

# ---------------------------
# Routes
# ---------------------------

@attendance_bp.route("/signin", methods=["POST"])
def signin():
    """Biometric sign-in (face or fingerprint)."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid request"}), 400

    embedding = data.get("face_embedding")
    fingerprint = data.get("fingerprint_template")

    if not embedding and not fingerprint:
        return jsonify({"success": False, "message": "No biometric provided"}), 400

    matched_user, method_used, score = None, None, None

    if embedding:
        matched_user, method_used, score = match_face(embedding)
    if not matched_user and fingerprint:
        matched_user, method_used = match_fingerprint(fingerprint)

    if not matched_user:
        return jsonify({"success": False, "message": "No match found"}), 200

    if has_signed_in_today(matched_user.id):
        return jsonify({
            "success": True,
            "message": "Already signed in today",
            "user_uuid": matched_user.uuid,
            "firstname": matched_user.firstname,
            "lastname": matched_user.lastname,
            "method": method_used
        }), 200

    record = StaffAttendance(
        user=matched_user,
        timestamp=datetime.utcnow(),
        method=method_used,
        status="SIGNED_IN"
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Attendance recorded",
        "user_uuid": matched_user.uuid,
        "firstname": matched_user.firstname,
        "lastname": matched_user.lastname,
        "method": method_used,
        "score": float(score) if score else None,
        "time": record.timestamp.isoformat()
    }), 200


# ---------------------------
# Admin: List Users / Students
# ---------------------------

@attendance_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users_for_admin():
    """Return minimal user list for admin dropdown."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    users = User.query.order_by(User.firstname).all()
    payload = [
        {
            "id": u.id,
            "uuid": u.uuid,
            "firstname": u.firstname,
            "lastname": u.lastname,
            "role": u.role,
            "department": u.department
        } for u in users
    ]
    return jsonify({"success": True, "users": payload}), 200


@attendance_bp.route("/students", methods=["GET"])
@jwt_required()
def list_students_for_admin():
    """Return minimal student list for admin dropdown."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    students = Student.query.order_by(Student.firstname).all()
    payload = [
        {
            "id": s.id,
            "uuid": s.uuid,
            "firstname": s.firstname,
            "lastname": s.lastname,
            "role": s.role,
            "department": s.department
        } for s in students
    ]
    return jsonify({"success": True, "students": payload}), 200


# ---------------------------
# Manual Staff Attendance
# ---------------------------

@attendance_bp.route("/manual/staff", methods=["POST"])
@jwt_required()
def manual_staff_attendance():
    """Admin manual sign in/out for staff."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    if not request.is_json:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    data = request.get_json()
    user_id = data.get("user_id")
    user_uuid = data.get("user_uuid")
    action = (data.get("action") or "").lower()
    ts = data.get("timestamp")

    if not (user_id or user_uuid) or action not in ("sign_in", "sign_out"):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    user = User.query.filter_by(id=user_id).first() if user_id else User.query.filter_by(uuid=user_uuid).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    try:
        dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc) if ts else datetime.now(timezone.utc)
    except Exception:
        return jsonify({"success": False, "message": "Invalid timestamp format"}), 400

    record = get_today_attendance_record(user.id)

    if action == "sign_in":
        if record and record.time_in:
            return jsonify({
                "success": True,
                "message": "User already signed in today",
                "attendance": {
                    "id": record.id,
                    "time_in": record.time_in.isoformat() if record.time_in else None,
                    "time_out": record.time_out.isoformat() if record.time_out else None,
                    "status": record.status
                }
            }), 200

        if not record:
            record = StaffAttendance(user_id=user.id, created_at=datetime.now(timezone.utc))
            db.session.add(record)

        record.time_in = dt
        record.method = "manual"
        record.status = "ON_TIME" if dt.time() <= OFFICE_OPEN else "LATE"

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Manual sign-in recorded",
            "attendance": {
                "id": record.id,
                "time_in": record.time_in.isoformat(),
                "time_out": record.time_out.isoformat() if record.time_out else None,
                "status": record.status
            }
        }), 200

    if action == "sign_out":
        if not record:
            record = StaffAttendance(user_id=user.id, created_at=datetime.now(timezone.utc))
            db.session.add(record)

        record.time_out = dt
        record.method = "manual"
        record.status = "EARLY_SIGNOUT" if dt.time() < OFFICE_CLOSE else "SIGNED_OUT"

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Manual sign-out recorded",
            "attendance": {
                "id": record.id,
                "time_in": record.time_in.isoformat() if record.time_in else None,
                "time_out": record.time_out.isoformat(),
                "status": record.status
            }
        }), 200


# ---------------------------
# Manual Student Attendance
# ---------------------------

@attendance_bp.route("/manual/student", methods=["POST"])
def manual_student_attendance():
    """
    Manually record student attendance (sign_in / sign_out).
    Uses frontend timestamp if provided; otherwise, server time.
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON"}), 400

        data = request.get_json()
        print("📩 Received data:", data)

        student_id = data.get("student_id")
        action = (data.get("action") or "").lower()
        ts = data.get("timestamp")

        if not student_id or action not in ("sign_in", "sign_out"):
            return jsonify({"success": False, "message": "Missing student_id or invalid action"}), 400

        student = Student.query.get(student_id)
        if not student:
            return jsonify({"success": False, "message": "Student not found"}), 404

        # Use frontend timestamp if provided; else use server time
        try:
            dt = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc) if ts else datetime.now(timezone.utc)
        except Exception:
            return jsonify({"success": False, "message": "Invalid timestamp format"}), 400

        today = datetime.now(timezone.utc).date()

        # Try to find today's attendance record
        record = StudentAttendance.query.filter_by(user_id=student.id, date=today).first()

        # --- SIGN IN ---
        if action == "sign_in":
            if record and record.time_in:
                return jsonify({
                    "success": True,
                    "message": "Student already signed in today",
                    "attendance": {
                        "id": record.id,
                        "sign_in": record.time_in.isoformat() if record.time_in else None,
                        "sign_out": record.time_out.isoformat() if record.time_out else None
                    }
                }), 200

            if not record:
                record = StudentAttendance(
                    user_id=student.id,
                    date=today,
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(record)

            record.time_in = dt
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Manual sign-in recorded",
                "attendance": {
                    "id": record.id,
                    "sign_in": record.time_in.isoformat(),
                    "sign_out": record.time_out.isoformat() if record.time_out else None
                }
            }), 201

        # --- SIGN OUT ---
        elif action == "sign_out":
            if not record or not record.time_in:
                return jsonify({"success": False, "message": "Student has not signed in today"}), 400

            if record.time_out:
                return jsonify({
                    "success": True,
                    "message": "Student already signed out today",
                    "attendance": {
                        "id": record.id,
                        "sign_in": record.time_in.isoformat() if record.time_in else None,
                        "sign_out": record.time_out.isoformat() if record.time_out else None
                    }
                }), 200

            record.time_out = dt
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Manual sign-out recorded",
                "attendance": {
                    "id": record.id,
                    "sign_in": record.time_in.isoformat() if record.time_in else None,
                    "sign_out": record.time_out.isoformat()
                }
            }), 200

        else:
            return jsonify({"success": False, "message": "Invalid action"}), 400

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Internal Server Error: {str(e)}"}), 500


# ---------------------------
# Admin: View Attendance (Today + All)
# ---------------------------

@attendance_bp.route("/today/staff", methods=["GET"])
@jwt_required()
def get_today_attendance():
    """Get today's attendance record for all staff."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    today = date.today()
    start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)

    records = StaffAttendance.query.filter(
        StaffAttendance.created_at >= start,
        StaffAttendance.created_at <= end
    ).order_by(StaffAttendance.user_id).all()

    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.user.firstname} {r.user.lastname}" if r.user else None,
            "time_in": r.time_in.isoformat() if r.time_in else None,
            "time_out": r.time_out.isoformat() if r.time_out else None,
            "status": r.status,
            "method": r.method
        } for r in records
    ]
    return jsonify({"success": True, "data": data}), 200


@attendance_bp.route("/today/students", methods=["GET"])
@jwt_required()
def get_today_student_attendance():
    """Get today's attendance record for all students."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    today = date.today()
    start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)

    records = StudentAttendance.query.filter(
        StudentAttendance.created_at >= start,
        StudentAttendance.created_at <= end
    ).order_by(StudentAttendance.user_id).all()

    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.student.firstname} {r.student.lastname}" if r.student else None,
            "time_in": r.time_in.isoformat() if r.time_in else None,
            "time_out": r.time_out.isoformat() if r.time_out else None,
            "status": r.status,
            "method": r.method
        } for r in records
    ]
    return jsonify({"success": True, "data": data}), 200


@attendance_bp.route("/all/staff", methods=["GET"])
@jwt_required()
def get_all_staff_attendance():
    """Get all staff attendance records."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    records = StaffAttendance.query.order_by(StaffAttendance.created_at.desc()).all()

    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.user.firstname} {r.user.lastname}" if r.user else None,
            "time_in": r.time_in.isoformat() if r.time_in else None,
            "time_out": r.time_out.isoformat() if r.time_out else None,
            "status": r.status,
            "method": r.method
        } for r in records
    ]
    return jsonify({"success": True, "data": data}), 200


@attendance_bp.route("/all/students", methods=["GET"])
@jwt_required()
def get_all_student_attendance():
    """Get all student attendance records."""
    claims = get_jwt()
    if claims.get("role") != "ADMIN":
        abort(403, description="Access forbidden: Admins only")

    records = StudentAttendance.query.order_by(StudentAttendance.created_at.desc()).all()

    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_name": f"{r.student.firstname} {r.student.lastname}" if r.student else None,
            "time_in": r.time_in.isoformat() if r.time_in else None,
            "time_out": r.time_out.isoformat() if r.time_out else None,
            "status": r.status,
            "method": r.method
        } for r in records
    ]
    return jsonify({"success": True, "data": data}), 200
