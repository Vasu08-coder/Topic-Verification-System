from app.db.session import SessionLocal
from app.models.admin import AdminUser

db = SessionLocal()
admins = db.query(AdminUser).all()
for admin in admins:
    print(f'ID={admin.id}, Username={admin.username}, FullName={admin.full_name}')
    # Check if the model has branch attribute
    print(f'  Has branch attr: {hasattr(admin, "branch")}')
db.close()
