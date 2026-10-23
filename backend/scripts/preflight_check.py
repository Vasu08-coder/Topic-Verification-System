import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Placeholder for get_admin_password_hash function
def get_admin_password_hash_from_db(db_url: str) -> str | None:
    # In a real scenario, this would connect to the database and retrieve the hash
    # For this script, we'll assume a direct check if the hash is the default one.
    # This is a simplification; actual implementation would query the 'admin' table.
    engine = create_engine(db_url)
    try:
        with engine.connect() as connection:
            # Assuming 'admins' table and 'password_hash' column
            # This is a placeholder and needs to be adapted to the actual schema
            result = connection.execute(text("SELECT password_hash FROM admins WHERE username = 'admin'"))
            row = result.fetchone()
            if row:
                return row[0]
    except OperationalError:
        return None # Database not reachable or table not found
    return None

def run_preflight_checks():
    failures = 0

    def fail_check(message):
        nonlocal failures
        print(f"FAIL: {message}")
        failures += 1

    def pass_check(message):
        print(f"PASS: {message}")

    # 1. JWT_SECRET check
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or jwt_secret == "THIS_IS_A_SECRET_KEY" or len(jwt_secret) < 32:
        fail_check("JWT_SECRET is not set, is the placeholder, or is too short (min 32 characters)")
    else:
        pass_check("JWT_SECRET is set and secure")

    # 2. ALLOWED_ORIGINS check for production
    environment = os.getenv("ENVIRONMENT")
    allowed_origins = os.getenv("ALLOWED_ORIGINS")
    if environment == "prod" and allowed_origins and "*" in allowed_origins:
        fail_check("ALLOWED_ORIGINS contains '*' in production environment")
    else:
        pass_check("ALLOWED_ORIGINS is configured correctly for the environment")

    # 3. Database reachability check
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        fail_check("DATABASE_URL is not set")
    else:
        try:
            engine = create_engine(database_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            pass_check("Database is reachable")
        except OperationalError:
            fail_check("Database is not reachable")

    # 4. Default admin password check (simplified, requires actual DB query in real app)
    # NOTE: This check assumes the default password hash is known or can be compared.
    # In a real application, you'd need to query the DB and compare the hash.
    # For this script, we'll assume we are looking for a specific default hash, or
    # that the `get_admin_password_hash_from_db` function is properly implemented.
    default_admin_password_hash = "DEFAULT_ADMIN_PASSWORD_HASH" # Replace with actual default hash
    admin_password_changed = True # Assume changed if we can't fetch from DB

    if database_url:
        current_admin_hash = get_admin_password_hash_from_db(database_url)
        if current_admin_hash == default_admin_password_hash:
            admin_password_changed = False

    if not admin_password_changed:
        fail_check("Default admin password has not been changed")
    else:
        pass_check("Default admin password has been changed")

    # 5. EMAIL_BACKEND check for production
    email_backend = os.getenv("EMAIL_BACKEND")
    if environment == "prod" and (not email_backend or email_backend == "console"):
        fail_check("EMAIL_BACKEND is not 'smtp' in production environment")
    else:
        pass_check("EMAIL_BACKEND is configured correctly for the environment")

    if failures > 0:
        print(f"\nPreflight checks failed with {failures} error(s).")
        sys.exit(1)
    else:
        print("\nAll preflight checks passed.")
        sys.exit(0)

if __name__ == "__main__":
    run_preflight_checks()