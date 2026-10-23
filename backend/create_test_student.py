from app.db.session import SessionLocal
from app.models.student import Student
from app.core.security import hash_password

db = SessionLocal()

# Create a test student for document upload testing
test_student = Student(
    sis_id='A00888888',
    full_name='Document Test',
    branch_id=1,
    password_hash=hash_password('testpass123')
)
db.add(test_student)
db.commit()
db.refresh(test_student)

print(f'Created student: sis_id={test_student.sis_id}, id={test_student.id}')
db.close()
