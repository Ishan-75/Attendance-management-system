import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { SyncProvider } from './context/SyncContext';

// Layouts & Route guards
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';

// Pages
import { Login } from './pages/Login';
import { ForgotPassword } from './pages/ForgotPassword';
import { ResetPassword } from './pages/ResetPassword';
import { VerifyEmail } from './pages/VerifyEmail';
import { Dashboard } from './pages/Dashboard';
import { Attendance } from './pages/Attendance';
import { Employees } from './pages/Employees';
import { EmployeeDetail } from './pages/EmployeeDetail';
import { Leaves } from './pages/Leaves';
import { Departments } from './pages/Departments';
import { Holidays } from './pages/Holidays';
import { Reports } from './pages/Reports';
import { AuditLogs } from './pages/AuditLogs';
import { BackupRestore } from './pages/BackupRestore';
import { Settings } from './pages/Settings';
import { UsersPage } from './pages/Users';
import { SyncConflicts } from './pages/SyncConflicts';
import { RegisteredDevices } from './pages/RegisteredDevices';
import { NotFound } from './pages/NotFound';

export const App = () => {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <SyncProvider>
            <BrowserRouter>
              <Routes>
                {/* Public Authentication Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
                <Route path="/verify-email" element={<VerifyEmail />} />

                {/* Protected Application Routes */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <MainLayout />
                    </ProtectedRoute>
                  }
                >
                  {/* Workforce & Operations Routes */}
                  <Route index element={<Dashboard />} />
                  <Route path="attendance" element={<Attendance />} />
                  <Route path="employees" element={<Employees />} />
                  <Route path="employees/:id" element={<EmployeeDetail />} />
                  <Route path="leaves" element={<Leaves />} />
                  <Route path="departments" element={<Departments />} />
                  <Route path="holidays" element={<Holidays />} />
                  <Route path="reports" element={<Reports />} />
                  <Route path="sync-conflicts" element={<SyncConflicts />} />

                  {/* Administration Routes (Admin Only) */}
                  <Route
                    path="devices"
                    element={
                      <ProtectedRoute requireAdmin>
                        <RegisteredDevices />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="users"
                    element={
                      <ProtectedRoute requireAdmin>
                        <UsersPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="audit-logs"
                    element={
                      <ProtectedRoute requireAdmin>
                        <AuditLogs />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="backup-restore"
                    element={
                      <ProtectedRoute requireAdmin>
                        <BackupRestore />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="settings"
                    element={
                      <ProtectedRoute requireAdmin>
                        <Settings />
                      </ProtectedRoute>
                    }
                  />

                  {/* 404 Catch-all */}
                  <Route path="*" element={<NotFound />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </SyncProvider>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
};

export default App;
