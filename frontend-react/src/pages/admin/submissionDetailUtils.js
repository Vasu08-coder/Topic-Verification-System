export function getSubmissionDisplayData(submission = null) {
  if (!submission) {
    return {
      studentName: '—',
      sisId: '—',
      branch: '—',
      submittedAt: '—',
    };
  }
  return {
    studentName:
      submission.student_full_name ??
      submission.student_name ??
      submission.studentName ??
      '—',
    sisId:
      submission.student_sis_id ??
      submission.sis_id ??
      submission.sisId ??
      '—',
    branch:
      submission.branch_name ??
      submission.branch ??
      '—',
    submittedAt:
      submission.submitted_at ??
      submission.created_at ??
      submission.submittedAt ??
      '—',
  };
}
