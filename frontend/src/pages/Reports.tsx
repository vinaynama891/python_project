import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Calendar
} from 'lucide-react';
import { reportsApi } from '../services/api';

export const Reports: React.FC = () => {
  const [period, setPeriod] = useState<'daily' | 'weekly'>('daily');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const data = period === 'daily' ? await reportsApi.getDaily() : await reportsApi.getWeekly();
      setReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [period]);

  const handleExport = (format: 'csv' | 'pdf') => {
    reportsApi.downloadExport(format, period === 'daily' ? 1 : 7);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
            <span>Executive Infrastructure Reports</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 font-mono font-bold">
              PDF & CSV AUDIT LOGS
            </span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Historical aggregation, SLA compliance metrics, and downloadable audits.
          </p>
        </div>

        <div className="flex items-center space-x-2 self-start">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center space-x-2 py-2 px-3.5 rounded-lg bg-[#0e0e0e] border border-[#262626] text-neutral-300 hover:text-yellow-400 hover:border-yellow-400/40 text-xs font-bold transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center space-x-2 py-2 px-3.5 rounded-lg bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:to-amber-400 text-black text-xs font-black shadow-lg shadow-yellow-500/20 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-black stroke-[2.5]" />
            <span>Download PDF</span>
          </button>
        </div>
      </div>

      {/* Period Selector Tabs */}
      <div className="flex items-center space-x-3 bg-[#0a0a0a] p-1.5 rounded-xl border border-[#1f1f1f] w-fit">
        <button
          onClick={() => setPeriod('daily')}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-black transition-all ${
            period === 'daily' ? 'bg-yellow-400 text-black shadow' : 'text-neutral-400 hover:text-white'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Last 24 Hours (Daily)</span>
        </button>
        <button
          onClick={() => setPeriod('weekly')}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-black transition-all ${
            period === 'weekly' ? 'bg-yellow-400 text-black shadow' : 'text-neutral-400 hover:text-white'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Last 7 Days (Weekly)</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-neutral-400 text-xs font-mono">Compiling historical report...</div>
      ) : !report ? (
        <div className="p-12 text-center text-neutral-400 text-xs">No report data generated.</div>
      ) : (
        <div className="space-y-6">
          {/* Executive Overview Cards in Black & Yellow */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
              <span className="text-xs text-neutral-400 uppercase font-mono font-bold">Telemetry Data Points</span>
              <p className="text-2xl font-black text-white font-mono mt-2">{report.metrics_analyzed}</p>
              <p className="text-xs text-neutral-500 mt-1">Across {report.server_count} nodes</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
              <span className="text-xs text-neutral-400 uppercase font-mono font-bold">Average CPU Load</span>
              <p className="text-2xl font-black text-yellow-400 font-mono mt-2">{report.avg_cpu}%</p>
              <p className="text-xs text-neutral-500 mt-1">Peak: {report.max_cpu}%</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
              <span className="text-xs text-neutral-400 uppercase font-mono font-bold">Average Memory Load</span>
              <p className="text-2xl font-black text-amber-400 font-mono mt-2">{report.avg_ram}%</p>
              <p className="text-xs text-neutral-500 mt-1">SLA target: &lt;85%</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0a0a0a] border border-[#1f1f1f]">
              <span className="text-xs text-neutral-400 uppercase font-mono font-bold">Total Alert Incidents</span>
              <p className="text-2xl font-black text-rose-400 font-mono mt-2">{report.total_alerts}</p>
              <p className="text-xs text-yellow-400 mt-1 font-mono">{report.resolved_alerts} resolved</p>
            </div>
          </div>

          {/* Node Breakdown Table */}
          <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] overflow-hidden shadow-xl">
            <div className="p-4 border-b border-[#1a1a1a] bg-[#0e0e0e]">
              <h3 className="text-sm font-bold text-white">Server Fleet Performance Breakdown</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#121212] text-neutral-400 uppercase border-b border-[#1c1c1c]">
                  <tr>
                    <th className="py-3 px-4">Node Name</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Avg CPU %</th>
                    <th className="py-3 px-4">Avg RAM %</th>
                    <th className="py-3 px-4">Avg Disk %</th>
                    <th className="py-3 px-4">Ingested Samples</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1a1a1a]">
                  {report.server_breakdown && report.server_breakdown.map((s: any) => (
                    <tr key={s.server_id} className="hover:bg-[#121212]">
                      <td className="py-3 px-4 font-bold text-white font-sans">{s.name}</td>
                      <td className="py-3 px-4 uppercase text-yellow-400 font-bold">{s.status}</td>
                      <td className="py-3 px-4 text-neutral-200">{s.avg_cpu}%</td>
                      <td className="py-3 px-4 text-neutral-200">{s.avg_ram}%</td>
                      <td className="py-3 px-4 text-neutral-200">{s.avg_disk}%</td>
                      <td className="py-3 px-4 text-neutral-500">{s.data_points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
