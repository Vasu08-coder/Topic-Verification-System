import React, { useCallback, useEffect, useState } from 'react';
import apiClient from '../../api/client';

const short = (hash) => (hash ? `${hash.slice(0, 10)}…${hash.slice(-6)}` : '');

export default function AdminLedger() {
  const [ledger, setLedger] = useState({ total_blocks: 0, rejected_logged_off_chain: 0, blocks: [] });
  const [check, setCheck] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await apiClient.get('/api/admin/ledger');
      setLedger(data);
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Unable to load the ledger.');
    } finally {
      setLoading(false);
    }
  }, []);

  const validate = async () => {
    setError('');
    try {
      const { data } = await apiClient.get('/api/admin/ledger/validate');
      setCheck(data);
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Validation failed to run.');
    }
  };

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="a-page-head">
        <div>
          <h2>Blockchain Ledger</h2>
          <div className="a-desc">Tamper-evident record of admin-approved topics. Each block is linked to the previous one with SHA-256.</div>
        </div>
        <button className="btn" onClick={validate}>Validate Chain</button>
      </div>

      {error && <div className="a-card a-card-pad" style={{ marginBottom: '16px' }}>{error}</div>}

      <div className="a-card a-card-pad" style={{ marginBottom: '16px', display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        <div><strong>{ledger.total_blocks}</strong> blocks (incl. genesis)</div>
        <div><strong>{ledger.rejected_logged_off_chain}</strong> rejected topics logged separately (not on chain)</div>
        {check && (
          <div role="status">
            Integrity:{' '}
            <strong>{check.valid ? 'VALID – no tampering detected' : `TAMPERED at block ${check.broken_at_index}`}</strong>
            {!check.valid && <div>{check.reason}</div>}
          </div>
        )}
      </div>

      <div className="a-card">
        <table className="a-table">
          <thead>
            <tr><th>#</th><th>Topic</th><th>Student</th><th>AI similarity</th><th>Timestamp (UTC)</th><th>Block hash</th><th>Previous hash</th></tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan="7">Loading…</td></tr>}
            {!loading && ledger.blocks.length === 0 && <tr><td colSpan="7">No blocks yet. Approve a topic to create the first block.</td></tr>}
            {ledger.blocks.map((b) => (
              <tr key={b.block_index} style={check && !check.valid && b.block_index === check.broken_at_index ? { outline: '2px solid #b42318' } : undefined}>
                <td>{b.block_index}</td>
                <td>{b.data?.topic_title || (b.block_index === 0 ? 'Genesis block' : '')}</td>
                <td>{b.data?.student_name || ''}</td>
                <td>{b.data?.similarity_score ?? ''}</td>
                <td>{b.timestamp}</td>
                <td title={b.block_hash}><code>{short(b.block_hash)}</code></td>
                <td title={b.previous_hash}><code>{short(b.previous_hash)}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
