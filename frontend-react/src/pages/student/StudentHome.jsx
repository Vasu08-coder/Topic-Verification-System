import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { checkSimilarity, uploadAbstract } from '../../api/client';
import { BRANCH_OPTIONS } from '../../constants/branches';

const initialForm = {
  branch: 'CSE',
  module_type: 'seminar',
  title: '',
  abstract: '',
};

export default function StudentHome() {
  const { currentStudent, logout, userType } = useAuth();
  const navigate = useNavigate();
  const hasStudentSession = userType === 'student' || Boolean(sessionStorage.getItem('student_token') || currentStudent);

  // Redirect to login if not authenticated
  React.useEffect(() => {
    if (!hasStudentSession) {
      navigate('/student/login', { replace: true });
    }
  }, [hasStudentSession, navigate]);

  const [formData, setFormData] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [submissionId, setSubmissionId] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadError, setUploadError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setUploadMessage('');
    setUploadError('');
    setResult(null);
    setSubmissionId(null);

    try {
      const payload = {
        branch: formData.branch,
        module_type: formData.module_type,
        title: formData.title,
        abstract: formData.abstract,
      };

      const response = await checkSimilarity(payload);
      setResult(response);
      setSubmissionId(response?.submission_id || response?.id || null);
    } catch (err) {
      if (err?.response?.status === 401) {
        logout();
        navigate('/student/login');
        return;
      }
      const backendMessage = Array.isArray(err?.response?.data?.detail)
        ? err.response.data.detail[0]?.msg || JSON.stringify(err.response.data.detail)
        : err?.response?.data?.detail;

      setError(backendMessage || err?.message || 'Unable to verify your topic right now.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file || !submissionId) {
      setUploadError('Please select a file and ensure a submission ID is available.');
      return;
    }

    setUploading(true);
    setUploadError('');
    setUploadMessage('');

    try {
      await uploadAbstract(submissionId, file);
      setUploadMessage('Abstract uploaded successfully.');
    } catch (err) {
      if (err?.response?.status === 401) {
        logout();
        navigate('/student/login');
        return;
      }
      setUploadError(err?.response?.data?.detail || err?.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  if (!hasStudentSession) {
    return null; // Will redirect via useEffect
  }

  const match = result?.matches?.[0] || result?.similar_topics?.[0] || null;
  const similarityPercent =
    match?.similarity ?? match?.score ?? result?.best_similarity ?? result?.similarity_score ?? 0;

  return (
    <div className="card form-card">
      <div className="kicker">Student Portal · Topic Verification</div>
      <h1>Submit Your Seminar Topic</h1>
      <p className="sub">Welcome, {currentStudent.full_name}. Submit your proposal for AI-based originality review before final submission.</p>

      <form onSubmit={handleSubmit}>
        <div className="field-row">
          <div className="field">
            <label>Branch</label>
            <select
              name="branch"
              value={formData.branch}
              onChange={handleChange}
            >
              {BRANCH_OPTIONS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Module Type</label>
            <select
              name="module_type"
              value={formData.module_type}
              onChange={handleChange}
            >
              <option value="seminar">Seminar</option>
              <option value="project">Project</option>
            </select>
          </div>
        </div>

        <div className="field-row">
          <div className="field full">
            <label>Topic Title</label>
            <input
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="field-row">
          <div className="field full">
            <label>Abstract</label>
            <textarea
              name="abstract"
              rows="6"
              value={formData.abstract}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="field-row">
          <div className="field full">
            <label>Supporting Document (optional)</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              className="student-file-input"
            />
          </div>
        </div>

        <div className="student-form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Checking...' : 'Submit for Similarity Check'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}
      </form>

      {result && (
        <div className="result-panel">
          <div className={`stamp ${Number(result.best_similarity ?? 0) > 40 ? 'flagged' : 'cleared'}`}>
            <div className="stamp-text">
              {Number(result.best_similarity ?? 0) > 40 ? 'FLAGGED\nFOR REVIEW' : 'CLEARED\nNO MATCH'}
            </div>
          </div>
          <div className={`result-body ${Number(result.best_similarity ?? 0) > 40 ? 'flagged' : 'cleared'}`}>
            <div className="result-content">
              <h3>{Number(result.best_similarity ?? 0) > 40 ? 'Similar topic found' : 'No overlapping topic found'}</h3>
              <p>
                {Number(result.best_similarity ?? 0) > 40
                  ? 'The system detected a likely overlap with an existing topic.'
                  : 'Your topic passed the initial similarity review. Please upload the abstract to complete submission.'}
              </p>
            </div>
            <div className="match-box">
              <p className="match-title">
                <strong>{match?.title || 'No match details available'}</strong>
              </p>
              <p className="match-meta">Similarity score: {Math.round(Number(similarityPercent) || 0)}%</p>
              <div className="sim-bar">
                <div className="sim-bar-fill" style={{ width: `${Math.min(100, Math.round(Number(similarityPercent) || 0))}%` }} />
              </div>
            </div>
            {Number(result.best_similarity ?? 0) <= 40 && (
              <div className="match-box student-upload-box">
                <label className="upload-label">Upload Abstract (.pdf, .doc, .docx)</label>
                <div className="student-upload-row">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(event) => setFile(event.target.files?.[0] || null)}
                    className="student-file-input"
                  />

                  <button type="button" onClick={handleUpload} disabled={uploading || !file} className="btn btn-primary">
                    {uploading ? 'Uploading...' : 'Upload & Submit'}
                  </button>
                </div>

                {uploadMessage && <p className="success">{uploadMessage}</p>}
                {uploadError && <p className="error">{uploadError}</p>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}