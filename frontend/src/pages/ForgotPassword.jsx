import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../api/authApi';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSubmitted(true);
      toast.success('Reset link dispatched if account exists.');
    } catch (err) {
      toast.error('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 dark:bg-slate-950 p-4">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-3xl shadow-xl p-8">
        <Link
          to="/login"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>

        {submitted ? (
          <div className="text-center py-4">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Check your email</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
              If an account with <strong className="text-slate-700 dark:text-slate-300">{email}</strong> exists, we've sent password reset instructions.
            </p>
          </div>
        ) : (
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
              Reset Password
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              Enter the email address associated with your account.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email Address"
                type="email"
                required
                icon={Mail}
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <Button type="submit" variant="primary" size="lg" loading={loading} className="w-full">
                Send Reset Link
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
