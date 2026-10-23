import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function StudentLogin() {
  const [sisId, setSisId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { studentLogin } = useAuth();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await studentLogin(sisId, password);
      navigate('/student');
    } catch (err) {
      setError('Invalid SIS ID or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="card login-card">
        <div className="kicker">Student Portal</div>
        <h1>Student Login</h1>
        <p className="sub">Sign in with your SIS ID and password.</p>

        {error && <div className="login-error show">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field" style={{ marginBottom: '16px' }}>
            <label>SIS ID</label>
            <input
              value={sisId}
              onChange={(event) => setSisId(event.target.value)}
              placeholder="e.g., A00123456"
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
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px' }}>
          Don't have an account? <Link to="/student/register">Register here</Link>
        </div>
      </div>
    </div>
  );
}
