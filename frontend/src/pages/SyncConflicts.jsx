import React, { useState, useEffect } from 'react';
import { syncApi } from '../api/syncApi';
import { useSync } from '../context/SyncContext';
import { useToast } from '../context/ToastContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { SkeletonLoader } from '../components/common/SkeletonLoader';
import { EmptyState } from '../components/common/EmptyState';
import { AlertTriangle, CheckCircle2, RefreshCw, ArrowRight, ShieldCheck } from 'lucide-react';

export const SyncConflicts = () => {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);

  const { refreshConflictsCount } = useSync();
  const toast = useToast();

  const fetchConflicts = async () => {
    setLoading(true);
    try {
      const res = await syncApi.getConflicts();
      if (res.success) {
        setConflicts(res.data);
      }
    } catch (err) {
      toast.error('Failed to load pending sync conflicts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConflicts();
  }, []);

  const handleResolve = async (conflictId, strategy) => {
    setResolvingId(conflictId);
    try {
      const res = await syncApi.resolveConflict(conflictId, strategy, `Resolved via dashboard with ${strategy}`);
      if (res.success) {
        toast.success(`Conflict resolved using ${strategy}`);
        fetchConflicts();
        refreshConflictsCount();
      }
    } catch (err) {
      toast.error('Failed to resolve sync conflict');
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Sync Conflict Resolution Center
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Review concurrent offline modifications from distributed devices and choose an authorized resolution strategy
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchConflicts}
          icon={RefreshCw}
        >
          Refresh Conflicts
        </Button>
      </div>

      {loading ? (
        <SkeletonLoader rows={3} type="cards" />
      ) : conflicts.length === 0 ? (
        <Card bodyClassName="p-8">
          <EmptyState
            icon={CheckCircle2}
            title="All synchronized records are consistent"
            description="Zero data conflicts detected across web and mobile client devices."
          />
        </Card>
      ) : (
        <div className="space-y-6">
          {conflicts.map((c) => {
            let serverData = {};
            let clientData = {};
            try {
              serverData = JSON.parse(c.server_payload);
            } catch (e) {}
            try {
              clientData = JSON.parse(c.client_payload);
            } catch (e) {}

            return (
              <Card key={c.id} bodyClassName="p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        {c.entity_type} Conflict on Entity #{c.entity_id}
                      </h3>
                      <span className="text-xs text-slate-400 font-mono">
                        Device: {c.device_id} | Detected: {new Date(c.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    PENDING RESOLUTION
                  </span>
                </div>

                <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl text-xs text-slate-700 dark:text-slate-300 border border-slate-200/60 dark:border-slate-700/60">
                  <strong className="text-slate-900 dark:text-white">Discrepancy Note: </strong>
                  {c.conflict_reason}
                </div>

                {/* Side-by-Side Payload Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
                  {/* Server State */}
                  <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/30 dark:border-blue-900/60 dark:bg-blue-950/20">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-400">
                        Current Server State (MySQL)
                      </span>
                      <Badge variant={serverData.status || 'PRESENT'} size="sm">
                        {serverData.status || 'PRESENT'}
                      </Badge>
                    </div>

                    <pre className="text-[11px] font-mono bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 overflow-x-auto text-slate-800 dark:text-slate-200">
                      {JSON.stringify(serverData, null, 2)}
                    </pre>

                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full mt-3"
                      loading={resolvingId === c.conflict_id}
                      onClick={() => handleResolve(c.conflict_id, 'SERVER_WINS')}
                    >
                      Keep Server State
                    </Button>
                  </div>

                  {/* Client Offline State */}
                  <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 dark:border-emerald-900/60 dark:bg-emerald-950/20">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                        Offline Client Attempt
                      </span>
                      <Badge variant={clientData.status || 'PRESENT'} size="sm">
                        {clientData.status || 'PRESENT'}
                      </Badge>
                    </div>

                    <pre className="text-[11px] font-mono bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 overflow-x-auto text-slate-800 dark:text-slate-200">
                      {JSON.stringify(clientData, null, 2)}
                    </pre>

                    <Button
                      variant="primary"
                      size="sm"
                      className="w-full mt-3"
                      loading={resolvingId === c.conflict_id}
                      onClick={() => handleResolve(c.conflict_id, 'CLIENT_WINS')}
                    >
                      Accept Client Version
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
