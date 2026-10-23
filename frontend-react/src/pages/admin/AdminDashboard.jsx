import React, { useEffect, useState } from 'react';
import { getDashboardStats } from '../../api/client';

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    pending: 0,
    approved: 0,
    flagged: 0,
    recent_items: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const response = await getDashboardStats();
        setStats({
          pending: response?.pending || 0,
          approved: response?.approved || 0,
          flagged: response?.flagged || 0,
          recent_items: response?.recent_items || response?.recent_submissions || [],
        });
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Unable to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div>
      <div className="a-page-head">
        <div>
          <h2>Dashboard</h2>
          <div className="a-desc">Review and manage topic submissions across the institution.</div>
        </div>
      </div>

      {loading ? (
        <div className="a-card a-empty">Loading dashboard…</div>
      ) : error ? (
        <div className="a-card a-error">{error}</div>
      ) : (
        <>
          <div className="a-stats">
            <div className="a-card a-stat pending">
              <div className="a-stat-icon">
                <svg className="icon" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 7v5l3 3" />
                </svg>
              </div>
              <div>
                <div className="a-stat-num">{stats?.pending ?? '—'}</div>
                <div className="a-stat-lbl">Pending Review</div>
              </div>
            </div>
            <div className="a-card a-stat approved">
              <div className="a-stat-icon">
                <svg className="icon" viewBox="0 0 24 24">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
              </div>
              <div>
                <div className="a-stat-num">{stats?.approved ?? '—'}</div>
                <div className="a-stat-lbl">Approved</div>
              </div>
            </div>
            <div className="a-card a-stat resub">
              <div className="a-stat-icon">
                <svg className="icon" viewBox="0 0 24 24">
                  <path d="M3 12a9 9 0 109-9" />
                </svg>
              </div>
              <div>
                <div className="a-stat-num">{stats?.needs_modification ?? '—'}</div>
                <div className="a-stat-lbl">Needs Resubmission</div>
              </div>
            </div>
            <div className="a-card a-stat flagged">
              <div className="a-stat-icon">
                <svg className="icon" viewBox="0 0 24 24">
                  <path d="M12 3l7 4v5c0 4.5-2.8 7.7-7 9-4.2-1.3-7-4.5-7-9V7l7-4z" />
                </svg>
              </div>
              <div>
                <div className="a-stat-num">{stats?.flagged ?? '—'}</div>
                <div className="a-stat-lbl">Flagged</div>
              </div>
            </div>
          </div>

          <div className="a-card a-queue">
            <h3>Recent Queue</h3>
            {stats.recent_items.length === 0 ? (
              <p className="a-muted">No recent submissions yet.</p>
            ) : (
              <div className="a-list">
                {stats.recent_items.map((item, index) => (
                  <div key={item.id || `${item.title}-${index}`} className="a-item">
                    <div>
                      <div className="a-item-title">{item.title || item.topic_title || 'Untitled Topic'}</div>
                      <div className="a-item-meta">{item.student_name || item.studentName || 'Student name unavailable'}</div>
                    </div>
                    <span className="a-pill">{item.status || 'Pending'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}