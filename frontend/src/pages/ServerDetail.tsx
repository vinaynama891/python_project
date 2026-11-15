import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import {
  Server as ServerIcon,
  Cpu,
  Database,
  HardDrive,
  Wifi,
  ArrowLeft,
  Terminal,
  Layers,
  RefreshCw
} from 'lucide-react';
import { serverApi, metricsApi, alertsApi } from '../services/api';
import { Server, ServerDetailedMetrics, MetricPoint, Alert } from '../types';
import { useWebSocket, WebSocketEvent } from '../hooks/useWebSocket';

export const ServerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [server, setServer] = useState<Server | null>(null);
  const [detailed, setDetailed] = useState<ServerDetailedMetrics | null>(null);
  const [history, setHistory] = useState<MetricPoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    if (!id) return;
    try {
      const [sData, dData, hData, aData] = await Promise.all([
        serverApi.getServer(id),
        metricsApi.getServerDetailedMetrics(id),
        metricsApi.getHistory(id, 1),
        alertsApi.getAlerts('all', undefined, id)
      ]);
      setServer(sData);
      setDetailed(dData);
      setHistory(hData);
      setAlerts(aData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 6000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Live WebSocket Telemetry Hook
  const handleWsUpdate = useCallback((event: WebSocketEvent) => {
    if (event.server_id === id) {
      setHistory((prev) => [
        ...prev.slice(-40),
        {
          timestamp: event.timestamp,
          cpu_percent: event.cpu_percent,
          ram_percent: event.ram_percent,
          disk_percent: event.disk_percent,
          net_upload_speed: event.net_upload_speed,
          net_download_speed: event.net_download_speed
        }
      ]);
      setServer((prev) => (prev ? { ...prev, latest_cpu: event.cpu_percent, latest_ram: event.ram_percent, status: 'online' } : null));
    }
  }, [id]);

  useWebSocket(handleWsUpdate);

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
    if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(0)} KB`;
    return `${bytes} B`;
  };

  const formatSpeed = (bytesPerSec: number) => {
    if (!bytesPerSec || bytesPerSec === 0) return '0 B/s';
    if (bytesPerSec >= 1024 * 1024) return `${(bytesPerSec / (1024 * 1024)).toFixed(2)} MB/s`;
    if (bytesPerSec >= 1024) return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
    return `${bytesPerSec.toFixed(0)} B/s`;
  };

  if (loading || !server) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-yellow-400 animate-spin" />
      </div>
    );
  }

  const latest = detailed?.latest;
  const processes = detailed?.processes || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1f1f1f]">
        <div className="flex items-center space-x-4">
          <Link
            to="/servers"
            className="p-2 rounded-lg bg-[#0e0e0e] border border-[#222222] text-neutral-400 hover:text-yellow-400 hover:border-yellow-400/40 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-black text-white tracking-tight">{server.name}</h1>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold font-mono uppercase ${
                  server.status === 'online'
                    ? 'bg-yellow-400/15 text-yellow-400 border border-yellow-400/30'
                    : 'bg-neutral-800 text-neutral-400 border border-neutral-700'
                }`}
              >
                {server.status}
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-1 font-mono">
              Hostname: <span className="text-yellow-400/90">{server.hostname || 'Unpaired'}</span> | IP: {server.ip_address || 'N/A'} | OS: {server.os} {server.os_version}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchAll}
            className="flex items-center space-x-2 py-2 px-3 rounded-lg bg-[#0e0e0e] border border-[#222222] text-neutral-300 hover:text-yellow-400 hover:border-yellow-400/40 text-xs font-bold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Real-time KPI Metric Gauges in Black & Yellow */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* CPU */}
        <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <div className="flex items-center justify-between text-xs text-neutral-400 mb-2">
            <span className="font-bold uppercase tracking-wider text-yellow-400">CPU Load</span>
            <Cpu className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {latest ? `${latest.cpu_percent.toFixed(1)}%` : '-'}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1 font-mono">
            {latest?.cpu_cores ? `${latest.cpu_cores} Cores` : ''} {latest?.cpu_frequency_current ? `@ ${latest.cpu_frequency_current} MHz` : ''}
          </p>
        </div>

        {/* Memory */}
        <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <div className="flex items-center justify-between text-xs text-neutral-400 mb-2">
            <span className="font-bold uppercase tracking-wider text-amber-400">RAM Load</span>
            <Database className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {latest ? `${latest.ram_percent.toFixed(1)}%` : '-'}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1 font-mono">
            {latest ? `${formatBytes(latest.ram_used)} / ${formatBytes(latest.ram_total)}` : '-'}
          </p>
        </div>

        {/* Disk */}
        <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <div className="flex items-center justify-between text-xs text-neutral-400 mb-2">
            <span className="font-bold uppercase tracking-wider text-yellow-300">Disk Capacity</span>
            <HardDrive className="w-4 h-4 text-yellow-300" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {latest ? `${latest.disk_percent.toFixed(1)}%` : '-'}
          </div>
          <p className="text-[11px] text-neutral-500 mt-1 font-mono">
            {latest ? `${formatBytes(latest.disk_used)} / ${formatBytes(latest.disk_total)}` : '-'}
          </p>
        </div>

        {/* Network */}
        <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <div className="flex items-center justify-between text-xs text-neutral-400 mb-2">
            <span className="font-bold uppercase tracking-wider text-yellow-400">Net Throughput</span>
            <Wifi className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-xs font-mono space-y-1">
            <div className="text-yellow-400 font-bold">Up: {formatSpeed(latest?.net_upload_speed || 0)}</div>
            <div className="text-amber-300 font-bold">Down: {formatSpeed(latest?.net_download_speed || 0)}</div>
          </div>
        </div>
      </div>

      {/* Live Charts in High-Contrast Yellow & Gold */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU Chart */}
        <div className="p-5 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-yellow-400" />
            <span>CPU Utilization History (%)</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="cpuYellowGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#facc15" stopOpacity={0.65} />
                    <stop offset="95%" stopColor="#facc15" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c1c1c" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(t) => new Date(t).toLocaleTimeString()}
                  stroke="#525252"
                  fontSize={10}
                />
                <YAxis domain={[0, 100]} stroke="#525252" fontSize={10} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#facc15', borderRadius: '8px', color: '#ffffff' }}
                  labelFormatter={(t) => new Date(t).toLocaleTimeString()}
                  formatter={(val: any) => [`${val}%`, 'CPU']}
                />
                <Area type="monotone" dataKey="cpu_percent" stroke="#facc15" strokeWidth={2.5} fill="url(#cpuYellowGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Memory Chart */}
        <div className="p-5 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center space-x-2">
            <Database className="w-4 h-4 text-amber-400" />
            <span>Memory Utilization History (%)</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="ramAmberGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.65} />
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c1c1c" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(t) => new Date(t).toLocaleTimeString()}
                  stroke="#525252"
                  fontSize={10}
                />
                <YAxis domain={[0, 100]} stroke="#525252" fontSize={10} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#eab308', borderRadius: '8px', color: '#ffffff' }}
                  labelFormatter={(t) => new Date(t).toLocaleTimeString()}
                  formatter={(val: any) => [`${val}%`, 'RAM']}
                />
                <Area type="monotone" dataKey="ram_percent" stroke="#fde047" strokeWidth={2.5} fill="url(#ramAmberGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top Consuming Processes */}
      <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] overflow-hidden shadow-xl">
        <div className="p-4 border-b border-[#1a1a1a] flex items-center justify-between bg-[#0e0e0e]">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-yellow-400" />
            <span>Top Resource-Consuming Processes (psutil Hardware Inspection)</span>
          </h3>
          <span className="text-xs text-yellow-500 font-mono font-bold">LIVE SNAPSHOT</span>
        </div>

        {processes.length === 0 ? (
          <div className="p-6 text-center text-xs text-neutral-500">
            No process telemetry records received yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#121212] text-neutral-400 uppercase tracking-wider border-b border-[#1c1c1c]">
                <tr>
                  <th className="py-2.5 px-4">PID</th>
                  <th className="py-2.5 px-4">Process Name</th>
                  <th className="py-2.5 px-4">Username</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">CPU %</th>
                  <th className="py-2.5 px-4">RAM %</th>
                  <th className="py-2.5 px-4">Memory RSS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a] font-mono">
                {processes.map((p, idx) => (
                  <tr key={idx} className="hover:bg-[#121212]">
                    <td className="py-2.5 px-4 text-neutral-500">{p.pid}</td>
                    <td className="py-2.5 px-4 font-bold text-white">{p.name}</td>
                    <td className="py-2.5 px-4 text-neutral-400 truncate max-w-xs">{p.username || 'SYSTEM'}</td>
                    <td className="py-2.5 px-4 text-neutral-300">{p.status}</td>
                    <td className="py-2.5 px-4">
                      <span className={p.cpu_percent > 10 ? 'text-yellow-400 font-black' : 'text-neutral-300'}>
                        {p.cpu_percent.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      <span className={p.memory_percent > 5 ? 'text-amber-400 font-black' : 'text-neutral-300'}>
                        {p.memory_percent.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-neutral-400">{formatBytes(p.memory_bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Hardware System Specs */}
      {latest?.raw_details?.system && (
        <div className="p-5 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-yellow-400" />
            <span>Host Hardware & Operating System Profile</span>
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-neutral-500 block">Hostname:</span>
              <span className="text-yellow-400 font-bold">{latest.raw_details.system.hostname}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Operating System:</span>
              <span className="text-white font-semibold">{latest.raw_details.system.os}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Kernel / Version:</span>
              <span className="text-white font-semibold">{latest.raw_details.system.os_version}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Architecture:</span>
              <span className="text-white font-semibold">{latest.raw_details.system.architecture}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Physical Cores:</span>
              <span className="text-white font-semibold">{latest.raw_details.system.cpu_cores_physical}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">Logical Cores:</span>
              <span className="text-white font-semibold">{latest.raw_details.system.cpu_cores_logical}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">System Boot Time:</span>
              <span className="text-white font-semibold">{new Date(latest.raw_details.system.boot_time).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-neutral-500 block">System Uptime:</span>
              <span className="text-white font-semibold">{(latest.raw_details.system.uptime_seconds / 3600).toFixed(1)} hours</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
