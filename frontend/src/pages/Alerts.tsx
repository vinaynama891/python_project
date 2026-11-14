import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Check,
  RefreshCw,
  Server as ServerIcon,
  ShieldAlert
} from 'lucide-react';
import { alertsApi } from '../services/api';
import { Alert } from '../types';

export const Alerts: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('active');
  const [severityFilter, setSeverityFilter] = useState('');

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await alertsApi.getAlerts(statusFilter, severityFilter);
      setAlerts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter]);

  const handleAcknowledge = async (id: string) => {
    try {
      await alertsApi.acknowledge(id);
      loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await alertsApi.resolve(id);
      loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-3">
            <span>Alerts & Incident Center</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono">
              Intelligent Deduplication Engine
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time threshold breaches, missing heartbeats, and AI anomaly alerts.
          </p>
        </div>
        <button
          onClick={loadAlerts}
          className="flex items-center space-x-2 py-2 px-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Alerts</span>
        </button>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-3 bg-[#0c1220] p-3 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">Status:</span>
          <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-700/80">
            {['active', 'acknowledged', 'resolved', 'all'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 text-xs rounded-md capitalize font-medium transition-colors ${
                  statusFilter === st ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-2 ml-auto">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
          </select>
        </div>
      </div>

      {/* Alerts Feed */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading incident feed...</div>
        ) : alerts.length === 0 ? (
          <div className="p-12 rounded-xl bg-[#0c1220] border border-slate-800 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <h3 className="text-base font-semibold text-white">All Infrastructure Systems Healthy</h3>
            <p className="text-xs text-slate-400 mt-1">No active incidents matching the current filters.</p>
          </div>
        ) : (
          alerts.map((a) => (
            <div
              key={a.id}
              className={`p-4 rounded-xl border transition-all ${
                a.severity === 'critical'
                  ? 'bg-rose-950/20 border-rose-500/30'
                  : 'bg-amber-950/15 border-amber-500/30'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start space-x-3.5">
                  <div
                    className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                      a.severity === 'critical' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                    }`}
                  >
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2.5">
                      <span
                        className={`text-[11px] font-mono font-bold uppercase px-2 py-0.5 rounded-full ${
                          a.severity === 'critical'
                            ? 'bg-rose-500 text-white'
                            : 'bg-amber-500 text-slate-950'
                        }`}
                      >
                        {a.severity}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Server: <strong className="text-white">{a.server_name}</strong>
                      </span>
                      <span className="text-xs text-slate-500 font-mono">
                        Metric: <span className="uppercase text-sky-400">{a.metric_type}</span>
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-white mt-1.5">{a.message}</p>
                    <div className="flex items-center space-x-4 text-xs text-slate-400 mt-2 font-mono">
                      <span>Triggered: {new Date(a.created_at).toLocaleString()}</span>
                      {a.acknowledged_at && (
                        <span className="text-sky-400">
                          Acknowledged by {a.acknowledged_by} ({new Date(a.acknowledged_at).toLocaleTimeString()})
                        </span>
                      )}
                      {a.resolved_at && (
                        <span className="text-emerald-400">
                          Resolved by {a.resolved_by} ({new Date(a.resolved_at).toLocaleTimeString()})
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end md:self-center">
                  {a.status === 'active' && (
                    <button
                      onClick={() => handleAcknowledge(a.id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-sky-400 border border-sky-500/20 font-medium transition-colors"
                    >
                      Acknowledge
                    </button>
                  )}
                  {a.status !== 'resolved' && (
                    <button
                      onClick={() => handleResolve(a.id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs text-white font-medium transition-colors"
                    >
                      Resolve Incident
                    </button>
                  )}
                  {a.status === 'resolved' && (
                    <span className="text-xs text-emerald-400 font-mono px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                      RESOLVED
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
