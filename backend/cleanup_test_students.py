from app.db.session import SessionLocal
from app.models.activity_log import ActivityLog
from app.models.student import Student
from app.models.submission import Submission

sis_ids = ['A99999999', 'A99999998']

db = SessionLocal()
try:
    student_ids = [row[0] for row in db.query(Student.id).filter(Student.sis_id.in_(sis_ids)).all()]
    if student_ids:
        submission_ids = [row[0] for row in db.query(Submission.id).filter(Submission.student_id.in_(student_ids)).all()]
        if submission_ids:
            db.query(ActivityLog).filter(ActivityLog.submission_id.in_(submission_ids)).delete(synchronize_session=False)
            db.query(Submission).filter(Submission.student_id.in_(student_ids)).delete(synchronize_session=False)
        db.query(Student).filter(Student.sis_id.in_(sis_ids)).delete(synchronize_session=False)
        db.commit()
    print('cleaned')
finally:
    db.close()
