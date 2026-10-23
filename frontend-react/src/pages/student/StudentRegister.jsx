import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { BRANCH_OPTIONS } from '../../constants/branches';

export default function StudentRegister() {
  const [sisId, setSisId] = useState('');
  const [fullName, setFullName] = useState('');
  const [branch, setBranch] = useState('CSE');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const MIN_PASSWORD_LENGTH = 8;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    // Client-side validation
    if (!sisId || !fullName || !password || !confirmPassword) {
      setError('All fields are required.');
      return;
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long.`);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await register(sisId, fullName, branch, password);
      navigate('/student');
    } catch (err) {
      const backendMessage = err?.response?.data?.detail;
      if (backendMessage && backendMessage.includes('already registered')) {
        setError(
          <>
            This SIS ID is already registered. <Link to="/student/login">Sign in instead</Link>
          </>
        );
      } else {
        setError(backendMessage || err?.message || 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="card login-card">
        <div className="kicker">Student Portal</div>
        <h1>Create Your Account</h1>
        <p className="sub">Register to submit your seminar or project topic.</p>

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
            <label>Full Name</label>
            <input
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="e.g., John Doe"
              required
            />
          </div>

          <div className="field" style={{ marginBottom: '16px' }}>
            <label>Branch</label>
            <select value={branch} onChange={(event) => setBranch(event.target.value)}>
              {BRANCH_OPTIONS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </div>

          <div className="field" style={{ marginBottom: '16px' }}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={`Minimum ${MIN_PASSWORD_LENGTH} characters`}
              required
            />
          </div>

          <div className="field" style={{ marginBottom: '16px' }}>
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Re-enter your password"
              required
            />
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%' }}>
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px' }}>
          Already have an account? <Link to="/student/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
