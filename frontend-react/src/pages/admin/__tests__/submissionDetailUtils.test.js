import test from 'node:test';
import assert from 'node:assert/strict';

import { getSubmissionDisplayData } from '../submissionDetailUtils.js';

test('maps the admin submission detail response fields from the backend contract', () => {
  const submission = {
    student_full_name: 'Ada Lovelace',
    student_sis_id: 'SIS-1001',
    branch_name: 'Computer Science',
    submitted_at: '2025-01-15T10:00:00Z',
  };

  const result = getSubmissionDisplayData(submission);

  assert.equal(result.studentName, 'Ada Lovelace');
  assert.equal(result.sisId, 'SIS-1001');
  assert.equal(result.branch, 'Computer Science');
  assert.equal(result.submittedAt, '2025-01-15T10:00:00Z');
});

test('falls back to older UI field names when present', () => {
  const submission = {
    student_name: 'Grace Hopper',
    sis_id: 'SIS-2002',
    branch: 'Software Engineering',
    created_at: '2025-01-16T10:00:00Z',
  };

  const result = getSubmissionDisplayData(submission);

  assert.equal(result.studentName, 'Grace Hopper');
  assert.equal(result.sisId, 'SIS-2002');
  assert.equal(result.branch, 'Software Engineering');
  assert.equal(result.submittedAt, '2025-01-16T10:00:00Z');
});
