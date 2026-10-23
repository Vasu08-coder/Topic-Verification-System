import React, { createContext, useContext, useState } from 'react';
import { adminLogin as apiAdminLogin, studentLogin as apiStudentLogin, studentRegister as apiStudentRegister } from '../api/client';

const AuthContext = createContext(null);

const getStoredStudentData = () => {
  const studentData = sessionStorage.getItem('student_data');
  if (!studentData) {
    return null;
  }

  try {
    return JSON.parse(studentData);
  } catch {
    sessionStorage.removeItem('student_data');
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => sessionStorage.getItem('admin_token') || sessionStorage.getItem('student_token'));
  const [userType, setUserType] = useState(() => sessionStorage.getItem('user_type'));
  const [currentAdmin, setCurrentAdmin] = useState(() => {
    const name = sessionStorage.getItem('admin_name');
    return name ? { name } : null;
  });
  const [currentStudent, setCurrentStudent] = useState(() => getStoredStudentData());

  const isAuthenticated = userType === 'admin' || userType === 'student';

  const clearAdminSession = () => {
    sessionStorage.removeItem('admin_token');
    sessionStorage.removeItem('admin_name');
    setCurrentAdmin(null);
  };

  const clearStudentSession = () => {
    sessionStorage.removeItem('student_token');
    sessionStorage.removeItem('student_data');
    setCurrentStudent(null);
  };

  // Admin login
  const login = async (username, password) => {
    const data = await apiAdminLogin(username, password);
    const accessToken = data.access_token || data.token;
    const adminName = data.name || data.username || username;

    clearStudentSession();
    sessionStorage.setItem('admin_token', accessToken);
    sessionStorage.setItem('admin_name', adminName);
    sessionStorage.setItem('user_type', 'admin');

    setToken(accessToken);
    setUserType('admin');
    setCurrentAdmin({ name: adminName, full_name: adminName });
    return data;
  };

  // Student register
  const register = async (sisId, fullName, branch, password) => {
    const data = await apiStudentRegister(sisId, fullName, branch, password);
    const accessToken = data.access_token || data.token;
    const studentData = {
      id: data.student_id,
      sis_id: sisId,
      full_name: fullName,
    };

    clearAdminSession();
    sessionStorage.setItem('student_token', accessToken);
    sessionStorage.setItem('student_data', JSON.stringify(studentData));
    sessionStorage.setItem('user_type', 'student');

    setToken(accessToken);
    setUserType('student');
    setCurrentStudent(studentData);
    return data;
  };

  // Student login
  const studentLoginFunc = async (sisId, password) => {
    const data = await apiStudentLogin(sisId, password);
    const accessToken = data.access_token || data.token;
    const studentData = {
      id: data.student_id,
      sis_id: data.sis_id,
      full_name: data.full_name,
    };

    clearAdminSession();
    sessionStorage.setItem('student_token', accessToken);
    sessionStorage.setItem('student_data', JSON.stringify(studentData));
    sessionStorage.setItem('user_type', 'student');

    setToken(accessToken);
    setUserType('student');
    setCurrentStudent(studentData);
    return data;
  };

  const logout = () => {
    clearAdminSession();
    clearStudentSession();
    sessionStorage.removeItem('user_type');
    setToken(null);
    setUserType(null);
  };

  return (
    <AuthContext.Provider value={{ 
      currentAdmin, 
      currentStudent,
      isAuthenticated, 
      userType,
      login, 
      logout,
      register,
      studentLogin: studentLoginFunc,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
