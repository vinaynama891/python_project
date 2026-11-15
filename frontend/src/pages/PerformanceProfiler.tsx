import React, { useState, useEffect } from 'react';
import {
  Zap,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
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
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
            <span>Performance Tuning Profiler</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 font-mono font-bold">
              cProfile & perf_counter
            </span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Deep bottleneck inspection, execution duration profiling, and non-destructive optimization techniques.
          </p>
        </div>

        {/* Server Selector */}
        <div className="flex items-center space-x-3 self-start">
          <label className="text-xs font-semibold text-neutral-400">Target Node:</label>
          <select
            value={selectedServerId}
            onChange={(e) => setSelectedServerId(e.target.value)}
            className="bg-[#121212] border border-[#262626] text-xs text-white rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-400 font-mono"
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
            className="p-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 text-black transition-colors"
            title="Re-run profiler"
          >
            <RefreshCw className={`w-4 h-4 text-black stroke-[2.5] ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-neutral-400 text-xs font-mono">Running diagnostic profiling engine...</div>
      ) : !profileData ? (
        <div className="p-12 text-center text-neutral-400 text-xs">Select a server to run performance profiler.</div>
      ) : (
        <div className="space-y-6">
          {/* Bottlenecks Found */}
          <div className="p-5 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] shadow-xl">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-yellow-400" />
              <span>Detected Subsystem Bottlenecks</span>
            </h3>

            {profileData.bottlenecks && profileData.bottlenecks.length > 0 ? (
              <div className="space-y-2">
                {profileData.bottlenecks.map((b: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-[#0f0e04] border border-yellow-500/30 flex items-center justify-between"
                  >
                    <div>
                      <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-yellow-400 text-black font-black mr-2">
                        {b.component}
                      </span>
                      <span className="text-xs text-neutral-200">{b.description}</span>
                    </div>
                    <span className="text-xs font-mono text-yellow-400 font-extrabold uppercase">{b.severity}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center space-x-3">
                <CheckCircle2 className="w-5 h-5 text-yellow-400 shrink-0" />
                <span className="text-xs text-yellow-300">
                  No critical resource bottlenecks detected on server '{profileData.server_name}'. Utilization is within balanced tolerances.
                </span>
              </div>
            )}
          </div>

          {/* Practical Tuning Recommendations */}
          <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] p-6 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span>Tailored Optimization Recommendations</span>
            </h3>

            {profileData.recommendations && profileData.recommendations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profileData.recommendations.map((r: any) => (
                  <div key={r.id} className="p-4 rounded-xl bg-[#121212] border border-[#1f1f1f] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 font-bold">
                        {r.category}
                      </span>
                      <span className="text-xs text-yellow-400/80 font-mono capitalize">Impact: {r.impact}</span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{r.title}</h4>
                    <p className="text-xs text-neutral-300">{r.description}</p>
                    {r.suggested_action && (
                      <div className="text-xs text-yellow-300 bg-yellow-500/10 p-2.5 rounded border border-yellow-500/30 mt-2 font-mono">
                        <strong className="text-white block mb-0.5">Recommended Tuning:</strong>
                        {r.suggested_action}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-neutral-400">
                Operating parameters optimal. System will automatically generate suggestions if CPU, memory, or disk loads exceed thresholds.
              </p>
            )}
          </div>

          {/* Python Execution Profiling Architecture Details */}
          <div className="p-5 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] space-y-2 font-mono text-xs text-neutral-400">
            <span className="text-yellow-400 font-bold block">Python Runtime Profiler Integration:</span>
            <p>
              Decorators measuring wall-clock duration with <code className="text-yellow-300">time.perf_counter</code> and call-graph statistics with <code className="text-yellow-300">cProfile</code> are instrumented on critical ingestion and query pipelines. Non-destructive operational policy enforced.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
