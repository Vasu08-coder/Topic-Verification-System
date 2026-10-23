import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getAdminSubmissionDetail, submitDecision, downloadSubmissionDocument } from '../../api/client';
import { getSubmissionDisplayData } from './submissionDetailUtils';

export default function AdminSubmissionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [showNotesInput, setShowNotesInput] = useState(false);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const [notesError, setNotesError] = useState('');
  const notesInputRef = useRef(null);

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const response = await getAdminSubmissionDetail(id);
        setSubmission(response);
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Unable to load submission details.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  useEffect(() => {
    if (showNotesInput) {
      notesInputRef.current?.focus();
    }
  }, [showNotesInput]);

  const handleDecision = async (action) => {
    if (action === 'approve') {
      setShowNotesInput(false);
      setDecisionNotes('');
      setPendingAction(null);
      setNotesError('');
      setDecisionLoading(true);
      try {
        await submitDecision(id, action, '');
        navigate('/admin/submissions');
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Decision submission failed.');
      } finally {
        setDecisionLoading(false);
      }
      return;
    }

    setPendingAction(action);
    setShowNotesInput(true);
    setNotesError('');
  };

  const handleConfirmDecision = async () => {
    if (!pendingAction) {
      return;
    }

    const trimmedNotes = decisionNotes.trim();
    if (!trimmedNotes) {
      setNotesError('Feedback is required for reject or modification requests.');
      return;
    }

    setDecisionLoading(true);
    try {
      await submitDecision(id, pendingAction, trimmedNotes);
      navigate('/admin/submissions');
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Decision submission failed.');
    } finally {
      setDecisionLoading(false);
    }
  };

  const handleDownloadDocument = async () => {
    try {
      const response = await downloadSubmissionDocument(id);
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'] || '';
      let filename = `submission_${id}.pdf`;
      const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
      // Create blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to download document.');
    }
  };

  const submissionDisplay = getSubmissionDisplayData(submission);
  const similarityScore = Number(submission?.similarity_score ?? submission?.score ?? 0);
  const gaugeColor = similarityScore >= 75 ? 'var(--adm-red)' : similarityScore >= 45 ? 'var(--adm-amber)' : 'var(--adm-green)';

  return (
    <div>
      <button className="abtn" onClick={() => navigate('/admin/submissions')} style={{ marginBottom: '18px' }}>
        ← Back to Submissions Queue
      </button>

      <div className="a-review-head">
        <div>
          <h2>{submission?.title || submission?.topic_title || 'Submission Review'}</h2>
          <div className="a-desc">
            Submitted by {submissionDisplay.studentName} · {submissionDisplay.branch} · {submissionDisplay.submittedAt}
          </div>
        </div>
        <span className={`apill ${similarityScore >= 45 ? 'flagged' : 'pending'}`}>
          {similarityScore >= 45 ? 'Flagged' : 'Pending Review'}
        </span>
      </div>

      {loading ? (
        <div className="a-empty">Loading submission details…</div>
      ) : error ? (
        <div className="a-error">{error}</div>
      ) : submission ? (
        <>
          <div className="a-review-grid">
            <div className="a-review-column">
              <div className="a-card a-card-pad">
                <div className="a-card-title">
                  <h3>Student Details</h3>
                </div>
                <div className="a-detail-list">
                  <div className="a-detail-row">
                    <span className="a-detail-label">Full Name</span>
                    <span className="a-detail-value">{submissionDisplay.studentName}</span>
                  </div>
                  <div className="a-detail-row">
                    <span className="a-detail-label">SIS ID</span>
                    <span className="a-detail-value mono">{submissionDisplay.sisId}</span>
                  </div>
                  <div className="a-detail-row">
                    <span className="a-detail-label">Branch</span>
                    <span className="a-detail-value">{submissionDisplay.branch}</span>
                  </div>
                  <div className="a-detail-row">
                    <span className="a-detail-label">Submitted</span>
                    <span className="a-detail-value">{submissionDisplay.submittedAt}</span>
                  </div>
                </div>
              </div>

              <div className="a-card a-card-pad">
                <div className="a-card-title">
                  <h3>Submitted Topic & Abstract</h3>
                </div>
                <div className="a-topic-title">
                  {submission.title || submission.topic_title || '—'}
                </div>
                <div className="a-abstract">{submission.abstract || submission.description || submission.abstract_text || 'No abstract provided.'}</div>
              </div>

              <div className="a-card a-card-pad">
                <div className="a-card-title">
                  <h3>Uploaded Document</h3>
                </div>
                {submission.document_filename ? (
                  <div className="a-upload-row">
                    <span className="a-detail-value">{submission.document_filename}</span>
                    <button className="abtn" onClick={handleDownloadDocument}>View</button>
                  </div>
                ) : (
                  <p className="a-empty-text">
                    No document uploaded yet.
                  </p>
                )}
              </div>
            </div>

            <div className="a-review-column">
              <div className="a-card a-card-pad">
                <div className="a-card-title">
                  <h3>Similarity</h3>
                </div>
                <div className="gauge-wrap">
                  <div className="gauge" style={{ background: `conic-gradient(${gaugeColor} ${similarityScore}%, #E5E7EB 0)` }}>
                    <div className="gauge-inner">
                      <div className="gnum" style={{ color: gaugeColor }}>
                        {similarityScore}%
                      </div>
                      <div className="glbl">Similarity</div>
                    </div>
                  </div>
                  <div className="a-help-text">
                    Highest match against departmental records
                  </div>
                </div>
              </div>

              <div className="a-card a-card-pad">
                <div className="a-card-title">
                  <h3>Top Similar Topics</h3>
                </div>
                <ul className="a-match-list">
                  {(submission.matches || submission.matched_topics || []).map((m, i) => (
                    <li key={i}>
                      <div className="myr">{m.year}</div>
                      <div className="mtop">
                        <span>{m.title}</span>
                        <span>{m.similarity_pct}%</span>
                      </div>
                      <div className="mini-bar">
                        <div className="mini-bar-fill" style={{ width: `${m.similarity_pct}%` }}></div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {submission.ai_recommendation && (
                <div className="ai-box">
                  <p>
                    <strong>AI Recommendation:</strong> {submission.ai_recommendation}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="a-actions-row">
            <button className="abtn abtn-approve" onClick={() => handleDecision('approve')} disabled={decisionLoading}>
              Approve
            </button>
            <button className="abtn abtn-modify" onClick={() => handleDecision('needs_modification')} disabled={decisionLoading}>
              Ask for Modification
            </button>
            <button className="abtn abtn-reject" onClick={() => handleDecision('reject')} disabled={decisionLoading}>
              Reject
            </button>
          </div>

          {showNotesInput ? (
            <div className="a-card a-card-pad" style={{ marginTop: '16px' }}>
              <label htmlFor="admin-feedback" className="a-detail-label" style={{ display: 'block', marginBottom: '8px' }}>
                Add feedback for the student (required)
              </label>
              <textarea
                id="admin-feedback"
                ref={notesInputRef}
                value={decisionNotes}
                onChange={(e) => {
                  setDecisionNotes(e.target.value);
                  if (notesError) {
                    setNotesError('');
                  }
                }}
                rows={5}
                placeholder="Enter feedback for the student..."
                style={{ width: '100%', resize: 'vertical' }}
              />
              {notesError ? (
                <div className="a-error" style={{ marginTop: '8px' }}>{notesError}</div>
              ) : null}
              <div className="a-actions-row" style={{ marginTop: '12px', justifyContent: 'flex-start' }}>
                <button className="abtn abtn-approve" onClick={handleConfirmDecision} disabled={decisionLoading}>
                  Submit Decision
                </button>
              </div>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}