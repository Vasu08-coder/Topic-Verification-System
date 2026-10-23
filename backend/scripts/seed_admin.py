import os
import sys
from pathlib import Path

import bcrypt
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings


def main() -> None:
    password = os.getenv("SUPER_ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("SUPER_ADMIN_PASSWORD environment variable is required")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with psycopg.connect(settings.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admins (username, password_hash, name, role, branch, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    branch = EXCLUDED.branch
                """,
                ("super_admin", password_hash, "System Super Admin", "super_admin", None),
            )
        conn.commit()

    print("Seeded super admin account")


if __name__ == "__main__":
    main()
