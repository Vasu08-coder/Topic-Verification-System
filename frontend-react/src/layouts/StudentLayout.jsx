import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import collegeLogo from '../assets/college-logo.png';

export default function StudentLayout() {
  const { currentStudent, userType, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const hasStudentSession = userType === 'student' || Boolean(sessionStorage.getItem('student_token') || currentStudent);

  const handleLogout = () => {
    logout();
    navigate('/student/login', { replace: true });
  };

  return (
    <div>
      <header className="masthead">
        <div className="masthead-left">
          <img src={collegeLogo} alt="College logo" className="college-logo" />
          <div className="masthead-title">
            <h1>Shri Sant Gajanan Maharaj College of Engineering, Shegaon</h1>
            <div className="masthead-subtitle">Seminar Topic Records & Verification System</div>
          </div>
        </div>
        <div className="masthead-right">
          {hasStudentSession && currentStudent ? (
            <div style={{ marginRight: '20px', display: 'flex', alignItems: 'center' }}>
              <span>Hi, {currentStudent.full_name}</span>
              <button onClick={handleLogout} className="btn" style={{ marginLeft: '10px' }}>
                Logout
              </button>
            </div>
          ) : (
            <div className="portal-toggle">
              <Link
                to="/student"
                className={location.pathname.startsWith('/student') || location.pathname === '/' ? 'active' : ''}
              >
                Student Portal
              </Link>
            </div>
          )}
        </div>
      </header>

      <main className="wrap">
        <Outlet />
      </main>
    </div>
  );
}
