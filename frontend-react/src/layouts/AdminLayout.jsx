import React from 'react';
import { Link, Outlet, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import collegeLogo from '../assets/college-logo.png';

export default function AdminLayout() {
  const { currentAdmin, logout, userType } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const hasAdminSession = userType === 'admin' || Boolean(sessionStorage.getItem('admin_token') || currentAdmin);

  if (!hasAdminSession) {
    return <Navigate to="/admin/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/admin/login', { replace: true });
  };

  return (
    <div className="admin-app-shell">
      <header className="masthead">
        <div className="masthead-left">
          <img src={collegeLogo} alt="College logo" className="college-logo" />
          <div className="masthead-title">
            <h1>Shri Sant Gajanan Maharaj College of Engineering, Shegaon</h1>
            <div className="masthead-subtitle">Seminar Topic Records & Verification System</div>
          </div>
        </div>
        <div className="masthead-right">
          <span>Welcome, {currentAdmin?.full_name || currentAdmin?.name || 'Admin'}</span>
          <button onClick={handleLogout} className="btn">
            Logout
          </button>
        </div>
      </header>

      <div className="admin-shell" id="admin-console">
        <aside className="a-sidebar">
          <nav className="a-nav">
            <Link to="/admin/dashboard" className={location.pathname === '/admin/dashboard' ? 'active' : ''}>
              Dashboard
            </Link>
            <Link to="/admin/submissions" className={location.pathname.startsWith('/admin/submissions') ? 'active' : ''}>
              Submissions Queue
            </Link>
            <Link to="/admin/archive" className={location.pathname.startsWith('/admin/archive') ? 'active' : ''}>
              Archive & Datasets
            </Link>
            <Link to="/admin/ledger" className={location.pathname.startsWith('/admin/ledger') ? 'active' : ''}>
              Blockchain Ledger
            </Link>
          </nav>
        </aside>
        <main className="a-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
