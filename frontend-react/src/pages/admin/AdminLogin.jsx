import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(username, password);
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="card login-card">
        <div className="kicker">Faculty & Admin Access</div>
        <h1>Sign in to Admin Console</h1>
        <p className="sub">Use your assigned administrator credentials.</p>

        {error && <div className="login-error show">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field" style={{ marginBottom: '16px' }}>
            <label>Username</label>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>
          <div className="field" style={{ marginBottom: '16px' }}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%' }}>
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}