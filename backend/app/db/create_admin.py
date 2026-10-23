from app.db.session import SessionLocal
from app.models.admin import AdminUser
from app.core.security import hash_password

def create_first_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if existing:
            print("Admin user 'admin' already exists!")
            return

        # Create new admin user
        new_admin = AdminUser(
            username="admin",
            password_hash=hash_password("admin123"),  # Change this password as needed
            full_name="System Administrator",
        )
        db.add(new_admin)
        db.commit()
        print("Successfully created admin user: username='admin', password='admin123'")
    except Exception as e:
        print(f"Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_first_admin()