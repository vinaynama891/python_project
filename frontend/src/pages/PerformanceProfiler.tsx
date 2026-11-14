import React, { useState, useEffect } from 'react';
import {
  Zap,
  Cpu,
  Database,
  HardDrive,
  Terminal,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Sliders,
  Sparkles
} from 'lucide-react';
import { serverApi, profilerApi } from '../services/api';
import { Server } from '../types';

export const PerformanceProfiler: React.FC = () => {
  const [servers, setServers] = useState<Server[]>([]);
  const [selectedServerId, setSelectedServerId] = useState<string>('');
  const [profileData, setProfileData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    serverApi.getServers().then((list) => {
      setServers(list);
      if (list.length > 0) {
        setSelectedServerId(list[0].id);
      }
    });
  }, []);

  const runProfiler = async () => {
    if (!selectedServerId) return;
    setLoading(true);
    try {
      const data = await profilerApi.profileServer(selectedServerId);
      setProfileData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedServerId) {
      runProfiler();
    }
  }, [selectedServerId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-3">
            <span>Performance Tuning Profiler</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
              cProfile & perf_counter
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Deep bottleneck inspection, execution duration profiling, and non-destructive optimization techniques.
          </p>
        </div>

        {/* Server Selector */}
        <div className="flex items-center space-x-3 self-start">
          <label className="text-xs text-slate-400">Target Node:</label>
          <select
            value={selectedServerId}
            onChange={(e) => setSelectedServerId(e.target.value)}
            className="bg-[#0c1220] border border-slate-700 text-xs text-white rounded-lg px-3 py-2 focus:outline-none focus:border-sky-500 font-mono"
          >
            {servers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.status})
              </option>
            ))}
          </select>
          <button
            onClick={runProfiler}
            disabled={loading}
            className="p-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors"
            title="Re-run profiler"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Running diagnostic profiling engine...</div>
      ) : !profileData ? (
        <div className="p-12 text-center text-slate-400 text-xs">Select a server to run performance profiler.</div>
      ) : (
        <div className="space-y-6">
          {/* Bottlenecks Found */}
          <div className="p-5 rounded-xl bg-[#0c1220] border border-slate-800 shadow-xl">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <span>Detected Subsystem Bottlenecks</span>
            </h3>

            {profileData.bottlenecks && profileData.bottlenecks.length > 0 ? (
              <div className="space-y-2">
                {profileData.bottlenecks.map((b: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/30 flex items-center justify-between"
                  >
                    <div>
                      <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold mr-2">
                        {b.component}
                      </span>
                      <span className="text-xs text-slate-200">{b.description}</span>
                    </div>
                    <span className="text-xs font-mono text-amber-400 font-bold uppercase">{b.severity}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span className="text-xs text-emerald-300">
                  No critical resource bottlenecks detected on server '{profileData.server_name}'. Utilization is within balanced tolerances.
                </span>
              </div>
            )}
          </div>

          {/* Practical Tuning Recommendations */}
          <div className="rounded-xl bg-[#0c1220] border border-slate-800 p-6 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-sky-400" />
              <span>Tailored Optimization Recommendations</span>
            </h3>

            {profileData.recommendations && profileData.recommendations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profileData.recommendations.map((r: any) => (
                  <div key={r.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-sky-500/15 text-sky-400 border border-sky-500/25">
                        {r.category}
                      </span>
                      <span className="text-xs text-amber-400 font-mono capitalize">Impact: {r.impact}</span>
                    </div>
                    <h4 className="text-sm font-semibold text-white">{r.title}</h4>
                    <p className="text-xs text-slate-300">{r.description}</p>
                    {r.suggested_action && (
                      <div className="text-xs text-emerald-400 bg-emerald-500/10 p-2.5 rounded border border-emerald-500/20 mt-2 font-mono">
                        <strong className="text-white block mb-0.5">Recommended Tuning:</strong>
                        {r.suggested_action}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                Operating parameters optimal. System will automatically generate suggestions if CPU, memory, or disk loads exceed thresholds.
              </p>
            )}
          </div>

          {/* Python Execution Profiling Architecture Details */}
          <div className="p-5 rounded-xl bg-[#0c1220] border border-slate-800 space-y-2 font-mono text-xs text-slate-400">
            <span className="text-sky-400 font-bold block">Python Runtime Profiler Integration:</span>
            <p>
              Decorators measuring wall-clock duration with <code>time.perf_counter</code> and call-graph statistics with <code>cProfile</code> are instrumented on critical ingestion and query pipelines. Non-destructive operational policy enforced.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
