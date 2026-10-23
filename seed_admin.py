import os
import sys
from passlib.context import CryptContext

# Fix absolute environment workspace directory path routing maps
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import the database configuration
try:
    from app.database import SessionLocal
except ImportError:
    from database import SessionLocal

# -------------------------------------------------------------
# SPECIFIC MODEL FIX: Instead of guessing files, we manually 
# import your actual models to see which one works.
# -------------------------------------------------------------
try:
    # Option A: Look for Admin model inside your project files
    from app.models.admin import Admin as User
except ImportError:
    try:
        # Option B: Fallback to reading the global app initialization exports
        from app.models import Admin as User
    except ImportError:
        try:
            # Option C: Look inside your user authentication script layout
            from app.models.auth import Admin as User
        except ImportError:
            raise ImportError(
                "CRITICAL: Could not locate the 'Admin' database table model inside app/models/. "
                "Please check the folder contents of backend/app/models/ to see the actual filename."
            )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Admin@1234!"
DEFAULT_EMAIL = "admin@example.com"


def create_default_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == DEFAULT_USERNAME).first()

        if admin is None:
            admin = User(username=DEFAULT_USERNAME)
            db.add(admin)

        if hasattr(admin, "email"):
            admin.email = DEFAULT_EMAIL

        if hasattr(admin, "is_active"):
            admin.is_active = True

        if hasattr(admin, "is_admin"):
            admin.is_admin = True

        if hasattr(admin, "is_superuser"):
            admin.is_superuser = True

        if hasattr(admin, "hashed_password"):
            admin.hashed_password = pwd_context.hash(DEFAULT_PASSWORD)
        elif hasattr(admin, "password_hash"):
            admin.password_hash = pwd_context.hash(DEFAULT_PASSWORD)
        else:
            raise AttributeError(
                "Neither 'hashed_password' nor 'password_hash' exists on this database account model."
            )

        db.commit()
        db.refresh(admin)
        print(f"\n🚀 SUCCESS! Admin account is active inside your cloud database.")
        print(f"Username: {admin.username}")
        print(f"Password: {DEFAULT_PASSWORD}\n")
        return admin
    finally:
        db.close()


if __name__ == "__main__":
    create_default_admin()

