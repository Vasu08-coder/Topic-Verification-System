import React, { useEffect, useState } from 'react';
import { getPublicArchive } from '../../api/client';

export default function PublicArchive() {
  const [moduleType, setModuleType] = useState('seminar');
  const [branch, setBranch] = useState('');
  const [academicYear, setAcademicYear] = useState('');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchArchive = async () => {
      setLoading(true);
      setError('');

      try {
        const response = await getPublicArchive(moduleType, {
          branch: branch || undefined,
          year: academicYear || undefined,
        });

        const data = Array.isArray(response) ? response : response?.results || [];
        setRecords(data);
      } catch (err) {
        setError(err?.response?.data?.detail || err?.message || 'Unable to load archived topics.');
      } finally {
        setLoading(false);
      }
    };

    fetchArchive();
  }, [moduleType, branch, academicYear]);

  const archiveRows = (records || []).filter((item) => {
    const q = '';
    return true;
  });

  return (
    <div className="card" style={{ padding: '32px 36px' }}>
      <div className="section-heading">
        <div>
          <h2>Register of Approved Topics</h2>
          <div className="desc">Browse this list before drafting your title to avoid an overlap.</div>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <select value={branch} onChange={(event) => setBranch(event.target.value)}>
            <option value="">All Branches</option>
            <option value="CSE">CSE</option>
            <option value="ECE">ECE</option>
            <option value="MECH">MECH</option>
            <option value="CIVIL">CIVIL</option>
            <option value="EEE">EEE</option>
          </select>
          <select value={moduleType} onChange={(event) => setModuleType(event.target.value)}>
            <option value="">All Modules</option>
            <option value="seminar">Seminar</option>
            <option value="final_year_project">Project</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">Loading public archive…</div>
      ) : error ? (
        <div className="empty-state">{error}</div>
      ) : archiveRows.length === 0 ? (
        <div className="empty-state">No rows match this view.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{ width: '90px' }}>Year</th>
              <th style={{ width: '110px' }}>Module</th>
              <th style={{ width: '130px' }}>Branch</th>
              <th>Topic</th>
            </tr>
          </thead>
          <tbody>
            {archiveRows.map((item, index) => (
              <tr key={item.id || `${item.title}-${index}`}>
                <td className="mono">{item.academic_year || item.year || '—'}</td>
                <td>{item.module || (moduleType === 'seminar' ? 'Seminar' : 'Project')}</td>
                <td>{item.branch || '—'}</td>
                <td>{item.title || 'Untitled'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}