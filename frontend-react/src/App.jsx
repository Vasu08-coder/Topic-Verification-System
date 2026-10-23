import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import StudentLayout from './layouts/StudentLayout';
import AdminLayout from './layouts/AdminLayout';
import StudentHome from './pages/student/StudentHome';
import StudentLogin from './pages/student/StudentLogin';
import StudentRegister from './pages/student/StudentRegister';
import PublicArchive from './pages/student/PublicArchive';
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminSubmissions from './pages/admin/AdminSubmissions';
import AdminSubmissionDetail from './pages/admin/AdminSubmissionDetail';
import AdminArchive from './pages/admin/AdminArchive';
import AdminLedger from './pages/admin/AdminLedger';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Student Portal Routes */}
          <Route element={<StudentLayout />}>
            <Route path="/" element={<StudentHome />} />
            <Route path="/student" element={<StudentHome />} />
            <Route path="/student/login" element={<StudentLogin />} />
            <Route path="/student/register" element={<StudentRegister />} />
            <Route path="/archive" element={<PublicArchive />} />
          </Route>

          {/* Admin Login Route */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* Admin Console Routes */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="submissions" element={<AdminSubmissions />} />
            <Route path="submissions/:id" element={<AdminSubmissionDetail />} />
            <Route path="archive" element={<AdminArchive />} />
            <Route path="ledger" element={<AdminLedger />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}