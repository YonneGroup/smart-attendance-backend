import sys
from app import create_app, db, argon2
from models.models import User, Credential
from datetime import datetime

# Create an application instance
app = create_app()

def create_or_update_admin(firstname, lastname, email, password):
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if user:
            if user.role != "ADMIN":
                print(f"⚠️ A user with email {email} exists but is not an ADMIN. Aborting.")
                return

            # Update password in Credential
            if user.credential:
                user.credential.password_hash = argon2.generate_password_hash(password)
                user.credential.last_password_reset_at = datetime.utcnow()
            else:
                # In case the user exists but has no credential
                credential = Credential(
                    user_id=user.id,
                    password_hash=argon2.generate_password_hash(password),
                    last_password_reset_at=datetime.utcnow()
                )
                db.session.add(credential)

            db.session.commit()
            print(f"🔄 Admin {email}'s password was reset successfully.")
            return

        # If no admin exists with that email → create one
        admin = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            role="ADMIN",
            department="Administration"
        )
        db.session.add(admin)
        db.session.flush()  # ensures admin.id is generated

        credential = Credential(
            user_id=admin.id,
            password_hash=argon2.generate_password_hash(password),
            last_password_reset_at=datetime.utcnow()
        )
        db.session.add(credential)

        db.session.commit()
        print(f"✅ Admin {email} created successfully.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python create_admin.py <firstname> <lastname> <email> <password>")
        sys.exit(1)

    firstname, lastname, email, password = sys.argv[1:]
    create_or_update_admin(firstname, lastname, email, password)
