from app.db.session import SessionLocal
from app.models.student import Student
from app.core.security import hash_password

db = SessionLocal()

# Create a test student for document download testing
test_student = Student(
    sis_id='A00999999',
    full_name='PDF Download Tester',
    branch_id=1,
    password_hash=hash_password('pdftest123')
)
db.add(test_student)
db.commit()
db.refresh(test_student)

print(f'Created student: sis_id={test_student.sis_id}, id={test_student.id}, password=pdftest123')
db.close()
