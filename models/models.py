import uuid
from datetime import datetime, timezone
from flask_argon2 import Argon2
from app import db

# ============================================================
# User Model
# ============================================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True  # ✅ indexed for quick lookups
    )
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)  # ✅ fast login lookup
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)  # ✅ optional phone number

    role = db.Column(
        db.Enum("ADMIN", "STAFF", name="user_roles"),
        nullable=False,
        index=True  # ✅ allows filtering by role
    )
    department = db.Column(db.String(100), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )

    # Relationships
    credential = db.relationship(
        "Credential",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    biometrics = db.relationship(
        "Biometric",
        backref="user",
        cascade="all, delete-orphan"
    )

    attendance_records = db.relationship(
        "StaffAttendance",
        backref="user",
        cascade="all, delete-orphan"
    )


# ============================================================
# Credential Model
# ============================================================
class Credential(db.Model):
    __tablename__ = "credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    last_password_reset_at = db.Column(db.DateTime)


# ============================================================
# Biometric Model
# ============================================================
class Biometric(db.Model):
    __tablename__ = "biometrics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    fingerprint_template = db.Column(db.LargeBinary, nullable=True)
    face_template = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)


# ============================================================
# Student Model
# ============================================================
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        db.String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True
    )
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    role = db.Column(
        db.Enum("STUDENT", name="student_roles"),
        nullable=False,
        index=True  # ✅ allows filtering by role
    )
    department = db.Column(db.String(100), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )

    attendance_records = db.relationship(
        "StudentAttendance",
        backref="student",
        cascade="all, delete-orphan"
    )


# ============================================================
# Staff Attendance Model
# ============================================================
class StaffAttendance(db.Model):
    __tablename__ = "staff_attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    time_in = db.Column(db.DateTime, nullable=True)
    time_out = db.Column(db.DateTime, nullable=True)
    method = db.Column(db.String(20), nullable=True, index=True)
    status = db.Column(db.String(30), default="SIGNED_IN", index=True)


# ============================================================
# Student Attendance Model
# ============================================================
class StudentAttendance(db.Model):
    __tablename__ = "student_attendance"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)
    time_in = db.Column(db.DateTime, nullable=True)
    time_out = db.Column(db.DateTime, nullable=True)
    method = db.Column(db.String(20), nullable=True, index=True)
    status = db.Column(db.String(30), default="SIGNED_IN", index=True)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date(), index=True)

