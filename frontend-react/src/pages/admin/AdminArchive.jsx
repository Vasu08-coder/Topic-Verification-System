import React, { useEffect, useState } from 'react';
import { getArchive } from '../../api/client';

export default function AdminArchive() {
  const [moduleType, setModuleType] = useState('seminar');
  const [branch, setBranch] = useState('');
  const [year, setYear] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchArchive = async () => {
      setLoading(true);
      setError('');

      try {
        const response = await getArchive(moduleType, {
          branch: branch || undefined,
          year: year || undefined,
        });
        const data = Array.isArray(response) ? response : response?.results || [];
        setRecords(data);
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Unable to load archive data.');
      } finally {
        setLoading(false);
      }
    };

    fetchArchive();
  }, [moduleType, branch, year]);

  const archiveRows = (records || []).filter((item) => {
    const q = searchQuery.trim().toLowerCase();
    return !q || `${item.title || ''} ${item.branch || ''} ${item.student_name || item.studentName || ''}`.toLowerCase().includes(q);
  });

  return (
    <div>
      <div className="a-page-head">
        <div>
          <h2>Topic Archive</h2>
          <div className="a-desc">Master record of all approved seminar and project topics.</div>
        </div>
      </div>

      <div className="a-card a-card-pad" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <select value={moduleType} onChange={(event) => setModuleType(event.target.value)}>
            <option value="seminar">Seminar</option>
            <option value="project">Project</option>
          </select>
          <select value={branch} onChange={(event) => setBranch(event.target.value)}>
            <option value="">All Branches</option>
            <option value="CSE">CSE</option>
            <option value="ECE">ECE</option>
            <option value="MECH">MECH</option>
            <option value="CIVIL">CIVIL</option>
            <option value="EEE">EEE</option>
          </select>
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            <option value="">All Years</option>
            <option value="2022">2022</option>
            <option value="2023">2023</option>
            <option value="2024">2024</option>
            <option value="2025">2025</option>
          </select>
          <input
            type="text"
            placeholder="Search archived topics..."
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            style={{ padding: '8px 12px', border: '1px solid var(--adm-line)', borderRadius: '7px', flex: 1, minWidth: '200px' }}
          />
        </div>
      </div>

      <div className="a-card a-card-pad">
        {loading ? (
          <div className="a-empty">Loading archive…</div>
        ) : error ? (
          <div className="a-error">{error}</div>
        ) : archiveRows.length === 0 ? (
          <div className="a-empty">No records match this search</div>
        ) : (
          <table className="a-table">
            <thead>
              <tr>
                <th style={{ width: '90px' }}>Year</th>
                <th style={{ width: '110px' }}>Module</th>
                <th style={{ width: '130px' }}>Branch</th>
                <th>Topic Title</th>
              </tr>
            </thead>
            <tbody>
              {archiveRows.map((item, index) => (
                <tr key={item.id || `${item.title}-${index}`}>
                  <td className="mono">{item.academic_year || item.year || '—'}</td>
                  <td>
                    <span className="apill approved">{item.module || (moduleType === 'seminar' ? 'Seminar' : 'Project')}</span>
                  </td>
                  <td>{item.branch || '—'}</td>
                  <td>{item.title || 'Untitled'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}