import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Server,
  Activity,
  Cpu,
  Database,
  HardDrive,
  Wifi,
  AlertTriangle,
  ArrowUpRight,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock
} from 'lucide-react';
import { analyticsApi, serverApi } from '../services/api';
import { OverviewStats, Server as ServerType } from '../types';
import { useWebSocket, WebSocketEvent } from '../hooks/useWebSocket';

export const Overview: React.FC = () => {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [servers, setServers] = useState<ServerType[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = useCallback(async () => {
    try {
      const [overviewData, serverList] = await Promise.all([
        analyticsApi.getOverview(),
        serverApi.getServers()
      ]);
      setStats(overviewData);
      setServers(serverList);
      setLastRefreshed(new Date());
    } catch (e) {
      console.error('Failed to load overview data:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Live WebSocket updates
  const handleWsMetric = useCallback((event: WebSocketEvent) => {
    setServers((prev) =>
      prev.map((s) => {
        if (s.id === event.server_id) {
          return {
            ...s,
            status: 'online',
            latest_cpu: event.cpu_percent,
            latest_ram: event.ram_percent,
            latest_disk: event.disk_percent
          };
        }
        return s;
      })
    );
    // Refresh stats smoothly
    analyticsApi.getOverview().then(setStats).catch(() => {});
  }, []);

  useWebSocket(handleWsMetric);

  const formatSpeed = (bytesPerSec: number) => {
    if (!bytesPerSec || bytesPerSec === 0) return '0 B/s';
    if (bytesPerSec >= 1024 * 1024) return `${(bytesPerSec / (1024 * 1024)).toFixed(2)} MB/s`;
    if (bytesPerSec >= 1024) return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
    return `${bytesPerSec.toFixed(0)} B/s`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center space-y-3">
          <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
          <p className="text-sm text-slate-400">Loading infrastructure telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-3">
            <span>Fleet Overview</span>
            <span className="text-xs py-0.5 px-2.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
              Live Real-Time
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Centralized health monitoring across host machines, virtual nodes, and cloud instances.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchData}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/servers"
            className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors shadow-lg shadow-sky-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Register Server</span>
          </Link>
        </div>
      </div>

      {/* Primary Status Counter Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800/80">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Servers</p>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{stats?.total_servers ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Managed nodes</p>
        </div>
        <div className="p-4 rounded-xl bg-[#0c1220] border border-emerald-500/20">
          <p className="text-xs font-medium text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Online</span>
          </p>
          <p className="text-2xl font-bold text-emerald-400 mt-2 font-mono">{stats?.online_servers ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Heartbeat active</p>
        </div>
        <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800/80">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <XCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Offline</span>
          </p>
          <p className="text-2xl font-bold text-slate-300 mt-2 font-mono">{stats?.offline_servers ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Missing heartbeat</p>
        </div>
        <div className="p-4 rounded-xl bg-[#0c1220] border border-amber-500/20">
          <p className="text-xs font-medium text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Warning</span>
          </p>
          <p className="text-2xl font-bold text-amber-400 mt-2 font-mono">{stats?.warning_servers ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Load &gt; 80%</p>
        </div>
        <div className="p-4 rounded-xl bg-[#0c1220] border border-rose-500/20">
          <p className="text-xs font-medium text-rose-400 uppercase tracking-wider flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Active Alerts</span>
          </p>
          <p className="text-2xl font-bold text-rose-400 mt-2 font-mono">{stats?.active_alerts_count ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Require triage</p>
        </div>
      </div>

      {/* Aggregate Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        {/* Average CPU */}
        <div className="p-5 rounded-xl bg-gradient-to-b from-[#0f172a] to-[#0b1120] border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Fleet CPU Load</span>
            <Cpu className="w-5 h-5 text-sky-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">{stats?.avg_cpu_percent ?? 0}%</span>
            <span className="text-xs text-slate-500">average</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-2 mt-4 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                (stats?.avg_cpu_percent ?? 0) > 85 ? 'bg-rose-500' : (stats?.avg_cpu_percent ?? 0) > 70 ? 'bg-amber-500' : 'bg-sky-500'
              }`}
              style={{ width: `${Math.min(100, stats?.avg_cpu_percent ?? 0)}%` }}
            />
          </div>
        </div>

        {/* Average RAM */}
        <div className="p-5 rounded-xl bg-gradient-to-b from-[#0f172a] to-[#0b1120] border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Fleet RAM Load</span>
            <Database className="w-5 h-5 text-purple-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">{stats?.avg_ram_percent ?? 0}%</span>
            <span className="text-xs text-slate-500">average</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-2 mt-4 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                (stats?.avg_ram_percent ?? 0) > 90 ? 'bg-rose-500' : (stats?.avg_ram_percent ?? 0) > 80 ? 'bg-amber-500' : 'bg-purple-500'
              }`}
              style={{ width: `${Math.min(100, stats?.avg_ram_percent ?? 0)}%` }}
            />
          </div>
        </div>

        {/* Average Disk */}
        <div className="p-5 rounded-xl bg-gradient-to-b from-[#0f172a] to-[#0b1120] border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Fleet Storage</span>
            <HardDrive className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">{stats?.avg_disk_percent ?? 0}%</span>
            <span className="text-xs text-slate-500">capacity</span>
          </div>
          <div className="w-full bg-slate-800/80 rounded-full h-2 mt-4 overflow-hidden">
            <div
              className="h-2 rounded-full bg-cyan-500 transition-all duration-500"
              style={{ width: `${Math.min(100, stats?.avg_disk_percent ?? 0)}%` }}
            />
          </div>
        </div>

        {/* Network Throughput */}
        <div className="p-5 rounded-xl bg-gradient-to-b from-[#0f172a] to-[#0b1120] border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Network Throughput</span>
            <Wifi className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Up:</span>
              <span className="font-mono text-emerald-400 font-semibold">
                {formatSpeed(stats?.total_network_upload_speed ?? 0)}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Down:</span>
              <span className="font-mono text-sky-400 font-semibold">
                {formatSpeed(stats?.total_network_download_speed ?? 0)}
              </span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-3 pt-2 border-t border-slate-800">
            Combined interface telemetry
          </p>
        </div>
      </div>

      {/* Registered Servers Fleet Table */}
      <div className="rounded-xl bg-[#0c1220] border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Connected Server Fleet</h2>
            <p className="text-xs text-slate-400 mt-0.5">Real hardware counters reporting via CloudPulse Agent</p>
          </div>
          <Link
            to="/servers"
            className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center space-x-1"
          >
            <span>Manage All Servers</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {servers.length === 0 ? (
          <div className="p-12 text-center">
            <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No monitoring agents connected.</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Install the Python agent on your Windows or Linux workstation to start streaming authentic metrics.
            </p>
            <Link
              to="/servers"
              className="inline-flex items-center space-x-2 mt-4 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Register First Server</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-[11px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-5">Server Name</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5">OS & Architecture</th>
                  <th className="py-3 px-5">CPU</th>
                  <th className="py-3 px-5">RAM</th>
                  <th className="py-3 px-5">Disk</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {servers.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-5">
                      <div className="flex items-center space-x-3">
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
                        <div>
                          <Link to={`/servers/${s.id}`} className="font-semibold text-white hover:text-sky-400 transition-colors">
                            {s.name}
                          </Link>
                          <p className="text-xs text-slate-500 font-mono mt-0.5">{s.hostname || 'Unpaired'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase font-mono ${
                          s.status === 'online'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-700 text-slate-300'
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-xs text-slate-300 font-mono">
                      {s.os ? `${s.os} (${s.architecture || 'x64'})` : 'N/A'}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_cpu !== null && s.latest_cpu !== undefined ? (
                        <div className="flex items-center space-x-2">
                          <span className={s.latest_cpu > 80 ? 'text-amber-400 font-bold' : 'text-slate-200'}>
                            {s.latest_cpu.toFixed(1)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_ram !== null && s.latest_ram !== undefined ? (
                        <span className={s.latest_ram > 85 ? 'text-amber-400 font-bold' : 'text-slate-200'}>
                          {s.latest_ram.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_disk !== null && s.latest_disk !== undefined ? (
                        <span className="text-slate-200">{s.latest_disk.toFixed(1)}%</span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>
                    <td className="py-4 px-5 text-right">
                      <Link
                        to={`/servers/${s.id}`}
                        className="inline-flex items-center space-x-1 text-xs text-sky-400 hover:text-sky-300 font-medium py-1 px-2.5 rounded bg-sky-500/10 border border-sky-500/20"
                      >
                        <span>Telemetry</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
