import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { Button } from '../components/common/Button';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState('loading'); // 'loading', 'success', 'error'
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error');
        setErrorMsg('Verification token is missing.');
        return;
      }
      try {
        await authApi.verifyEmail(token);
        setStatus('success');
      } catch (err) {
        setStatus('error');
        setErrorMsg(err.response?.data?.message || 'Invalid or expired verification link.');
      }
    };
    verify();
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 dark:bg-slate-950 p-4">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl shadow-xl p-8 text-center">
        {status === 'loading' && (
          <div className="py-8">
            <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Verifying account...</h3>
            <p className="text-sm text-slate-500 mt-1">Please hold on while we activate your account.</p>
          </div>
        )}

        {status === 'success' && (
          <div className="py-6">
            <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">Email Verified!</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 mb-6">
              Your email has been verified successfully. You can now log into your account.
            </p>
            <Link to="/login">
              <Button variant="primary" size="lg" className="w-full">
                Proceed to Login
              </Button>
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="py-6">
            <div className="w-14 h-14 bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">Verification Failed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 mb-6">
              {errorMsg}
            </p>
            <Link to="/login">
              <Button variant="outline" size="md" className="w-full">
                Return to Login
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
