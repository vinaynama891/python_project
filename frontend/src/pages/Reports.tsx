import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Server as ServerIcon,
  Activity,
  CheckCircle2,
  RefreshCw
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
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-3">
            <span>Executive Infrastructure Reports</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              Audit-Ready PDF / CSV
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Historical aggregation, SLA compliance metrics, and downloadable audits.
          </p>
        </div>

        <div className="flex items-center space-x-2 self-start">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center space-x-2 py-2 px-3.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:text-white text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center space-x-2 py-2 px-3.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium shadow-lg shadow-sky-600/20 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Download PDF</span>
          </button>
        </div>
      </div>

      {/* Period Selector Tabs */}
      <div className="flex items-center space-x-3 bg-[#0c1220] p-1.5 rounded-xl border border-slate-800 w-fit">
        <button
          onClick={() => setPeriod('daily')}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            period === 'daily' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Last 24 Hours (Daily)</span>
        </button>
        <button
          onClick={() => setPeriod('weekly')}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            period === 'weekly' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Last 7 Days (Weekly)</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">Compiling historical report...</div>
      ) : !report ? (
        <div className="p-12 text-center text-slate-400 text-xs">No report data generated.</div>
      ) : (
        <div className="space-y-6">
          {/* Executive Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-mono">Telemetry Data Points</span>
              <p className="text-2xl font-bold text-white font-mono mt-2">{report.metrics_analyzed}</p>
              <p className="text-xs text-slate-500 mt-1">Across {report.server_count} nodes</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-mono">Average CPU Load</span>
              <p className="text-2xl font-bold text-sky-400 font-mono mt-2">{report.avg_cpu}%</p>
              <p className="text-xs text-slate-500 mt-1">Peak: {report.max_cpu}%</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-mono">Average Memory Load</span>
              <p className="text-2xl font-bold text-purple-400 font-mono mt-2">{report.avg_ram}%</p>
              <p className="text-xs text-slate-500 mt-1">SLA target: &lt;85%</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0c1220] border border-slate-800">
              <span className="text-xs text-slate-400 uppercase font-mono">Total Alert Incidents</span>
              <p className="text-2xl font-bold text-rose-400 font-mono mt-2">{report.total_alerts}</p>
              <p className="text-xs text-emerald-400 mt-1">{report.resolved_alerts} resolved</p>
            </div>
          </div>

          {/* Node Breakdown Table */}
          <div className="rounded-xl bg-[#0c1220] border border-slate-800 overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">Server Fleet Performance Breakdown</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/60 text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Node Name</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Avg CPU %</th>
                    <th className="py-3 px-4">Avg RAM %</th>
                    <th className="py-3 px-4">Avg Disk %</th>
                    <th className="py-3 px-4">Ingested Samples</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {report.server_breakdown && report.server_breakdown.map((s: any) => (
                    <tr key={s.server_id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-white font-sans">{s.name}</td>
                      <td className="py-3 px-4 uppercase text-emerald-400">{s.status}</td>
                      <td className="py-3 px-4 text-slate-200">{s.avg_cpu}%</td>
                      <td className="py-3 px-4 text-slate-200">{s.avg_ram}%</td>
                      <td className="py-3 px-4 text-slate-200">{s.avg_disk}%</td>
                      <td className="py-3 px-4 text-slate-400">{s.data_points}</td>
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
