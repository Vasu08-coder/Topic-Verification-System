import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAdminSubmissions } from '../../api/client';

export default function AdminSubmissions() {
  const [filters, setFilters] = useState({ status: '', branch: '' });
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSubmissions = async () => {
      setLoading(true);
      setError('');

      try {
        const response = await getAdminSubmissions(filters);
        const data = Array.isArray(response) ? response : response?.results || [];
        setRecords(data);
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Unable to load submissions.');
      } finally {
        setLoading(false);
      }
    };

    fetchSubmissions();
  }, [filters]);

  return (
    <div>
      <div className="a-page-head">
        <div>
          <h2>Submissions Queue</h2>
          <div className="a-desc">Review incoming topic submissions awaiting a decision.</div>
        </div>
      </div>

      <div className="a-card a-card-pad">
        <div className="a-filters">
          <div className="field">
            <label>Status</label>
            <select
              value={filters.status}
              onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>

          <div className="field">
            <label>Branch</label>
            <select
              value={filters.branch}
              onChange={(event) => setFilters((prev) => ({ ...prev, branch: event.target.value }))}
            >
              <option value="">All</option>
              <option value="CSE">CSE</option>
              <option value="ECE">ECE</option>
              <option value="MECH">MECH</option>
              <option value="CIVIL">CIVIL</option>
              <option value="EEE">EEE</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="a-empty">Loading submissions…</div>
        ) : error ? (
          <div className="a-error">{error}</div>
        ) : records.length === 0 ? (
          <div className="a-empty">No submissions to review</div>
        ) : (
          <table className="a-table">
            <thead>
              <tr>
                <th>Student Name</th>
                <th>SIS ID</th>
                <th>Topic</th>
                <th>Similarity</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {records.map((item, index) => (
                <tr key={item.id || `${item.title}-${index}`}>
                  <td>{item.student_name || item.studentName || '—'}</td>
                  <td className="mono">{item.sis_id || item.sisId || '—'}</td>
                  <td>{item.title || item.topic_title || 'Untitled'}</td>
                  <td>
                    <span className={`a-sim ${item.similarity_score >= 75 ? 'high' : item.similarity_score >= 45 ? 'mid' : 'low'}`}>
                      {item.similarity_score ?? '—'}%
                    </span>
                  </td>
                  <td className="mono" style={{ fontSize: '12px' }}>
                    {item.submitted_at || item.created_at || '—'}
                  </td>
                  <td>
                    <button className="abtn abtn-primary" onClick={() => window.location.assign(`/admin/submissions/${item.id}`)}>
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}