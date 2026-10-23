import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import AdminUser


def main() -> None:
    username = input("Admin username to reset: ").strip()
    if not username:
        print("Username cannot be empty.")
        raise SystemExit(1)

    new_password = secrets.token_urlsafe(12)

    with SessionLocal() as db:
        admin = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
        if admin is None:
            print(f"No admin account found for username: {username}")
            raise SystemExit(1)

        admin.password_hash = hash_password(new_password)
        db.commit()

    print("=" * 41)
    print(f"NEW ADMIN PASSWORD (save this now): {new_password}")
    print("=" * 41)


if __name__ == "__main__":
    main()
