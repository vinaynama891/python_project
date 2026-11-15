import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  RefreshCw
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
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
            <span>Alerts & Incident Center</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 font-mono font-bold">
              STATE-AWARE DEDUPLICATION
            </span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Real-time threshold breaches, missing heartbeats, and AI anomaly alerts.
          </p>
        </div>
        <button
          onClick={loadAlerts}
          className="flex items-center space-x-2 py-2 px-3 rounded-lg bg-[#0e0e0e] border border-[#222222] text-neutral-300 hover:text-yellow-400 hover:border-yellow-400/40 text-xs font-bold transition-colors self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Alerts</span>
        </button>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-3 bg-[#0a0a0a] p-3 rounded-xl border border-[#1f1f1f]">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-yellow-400" />
          <span className="text-xs text-neutral-400 font-semibold">Status:</span>
          <div className="flex bg-[#121212] p-0.5 rounded-lg border border-[#262626]">
            {['active', 'acknowledged', 'resolved', 'all'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 text-xs rounded-md capitalize font-extrabold transition-colors ${
                  statusFilter === st ? 'bg-yellow-400 text-black shadow' : 'text-neutral-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-2 ml-auto">
          <span className="text-xs text-neutral-400 font-semibold">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-[#121212] border border-[#262626] text-xs text-neutral-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-yellow-400"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
          </select>
        </div>
      </div>

      {/* Alerts Feed in Yellow and Black Styling */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-12 text-center text-neutral-400 text-xs font-mono">Loading incident feed...</div>
        ) : alerts.length === 0 ? (
          <div className="p-12 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] text-center">
            <CheckCircle2 className="w-10 h-10 text-yellow-400 mx-auto mb-2" />
            <h3 className="text-base font-bold text-white">All Infrastructure Systems Healthy</h3>
            <p className="text-xs text-neutral-400 mt-1">No active incidents matching the current filters.</p>
          </div>
        ) : (
          alerts.map((a) => (
            <div
              key={a.id}
              className={`p-4 rounded-xl border transition-all ${
                a.severity === 'critical'
                  ? 'bg-[#120505] border-rose-500/40'
                  : 'bg-[#0f0e04] border-yellow-500/40'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start space-x-3.5">
                  <div
                    className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                      a.severity === 'critical' ? 'bg-rose-500/20 text-rose-400' : 'bg-yellow-500/20 text-yellow-400'
                    }`}
                  >
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2.5">
                      <span
                        className={`text-[11px] font-mono font-black uppercase px-2 py-0.5 rounded-full ${
                          a.severity === 'critical'
                            ? 'bg-rose-500 text-white'
                            : 'bg-yellow-400 text-black'
                        }`}
                      >
                        {a.severity}
                      </span>
                      <span className="text-xs text-neutral-400 font-mono">
                        Server: <strong className="text-white">{a.server_name}</strong>
                      </span>
                      <span className="text-xs text-neutral-500 font-mono">
                        Metric: <span className="uppercase text-yellow-400 font-bold">{a.metric_type}</span>
                      </span>
                    </div>
                    <p className="text-sm font-bold text-white mt-1.5">{a.message}</p>
                    <div className="flex items-center space-x-4 text-xs text-neutral-400 mt-2 font-mono">
                      <span>Triggered: {new Date(a.created_at).toLocaleString()}</span>
                      {a.acknowledged_at && (
                        <span className="text-yellow-400">
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
                      className="px-3 py-1.5 rounded-lg bg-[#141414] hover:bg-[#1f1f1f] text-xs text-yellow-400 border border-yellow-500/40 font-bold transition-colors"
                    >
                      Acknowledge
                    </button>
                  )}
                  {a.status !== 'resolved' && (
                    <button
                      onClick={() => handleResolve(a.id)}
                      className="px-3 py-1.5 rounded-lg bg-yellow-400 hover:bg-yellow-300 text-xs text-black font-extrabold transition-colors shadow-md shadow-yellow-500/20"
                    >
                      Resolve Incident
                    </button>
                  )}
                  {a.status === 'resolved' && (
                    <span className="text-xs text-yellow-400 font-mono px-3 py-1 rounded bg-yellow-500/10 border border-yellow-500/30 font-bold">
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
