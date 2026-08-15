import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { Compass, Home } from 'lucide-react';

export const NotFound = () => {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center p-6">
      <div className="w-16 h-16 rounded-3xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mb-6">
        <Compass className="w-8 h-8" />
      </div>
      <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
        404 - Page Not Found
      </h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mt-2 mb-8">
        The page you are looking for does not exist or has been relocated.
      </p>
      <Link to="/">
        <Button variant="primary" size="lg" icon={Home}>
          Back to Dashboard
        </Button>
      </Link>
    </div>
  );
};
