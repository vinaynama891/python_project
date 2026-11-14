import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Server as ServerIcon,
  Plus,
  Search,
  Filter,
  Trash2,
  Copy,
  Check,
  Terminal,
  Activity,
  ArrowRight,
  RefreshCw,
  X
} from 'lucide-react';
import { serverApi } from '../services/api';
import { Server, ServerRegisterToken } from '../types';

export const Servers: React.FC = () => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [newServerName, setNewServerName] = useState('');
  const [newServerDesc, setNewServerDesc] = useState('');
  const [registerResult, setRegisterResult] = useState<ServerRegisterToken | null>(null);
  const [copiedWin, setCopiedWin] = useState(false);
  const [copiedLinux, setCopiedLinux] = useState(false);

  const loadServers = async () => {
    try {
      setLoading(true);
      const data = await serverApi.getServers(statusFilter, search);
      setServers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServers();
  }, [statusFilter, search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newServerName) return;
    try {
      const res = await serverApi.createServer(newServerName, newServerDesc);
      setRegisterResult(res);
      loadServers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to deregister server '${name}'?`)) return;
    try {
      await serverApi.deleteServer(id);
      loadServers();
    } catch (e) {
      console.error(e);
    }
  };

  const copyToClipboard = (text: string, isWin: boolean) => {
    navigator.clipboard.writeText(text);
    if (isWin) {
      setCopiedWin(true);
      setTimeout(() => setCopiedWin(false), 2000);
    } else {
      setCopiedLinux(true);
      setTimeout(() => setCopiedLinux(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Server Fleet Management</h1>
          <p className="text-sm text-slate-400 mt-1">
            Provision agent registration tokens and monitor hardware nodes.
          </p>
        </div>
        <button
          onClick={() => {
            setRegisterResult(null);
            setNewServerName('');
            setNewServerDesc('');
            setModalOpen(true);
          }}
          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition-colors shadow-lg shadow-sky-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Server</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-[#0c1220] p-3 rounded-xl border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by server name or hostname..."
            className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Statuses</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
          <button
            onClick={loadServers}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-400 hover:text-white"
            title="Refresh list"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Server List Table */}
      <div className="rounded-xl bg-[#0c1220] border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading servers...</div>
        ) : servers.length === 0 ? (
          <div className="p-12 text-center">
            <ServerIcon className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-white font-medium text-sm">No servers found matching criteria.</p>
            <p className="text-xs text-slate-500 mt-1">Register a machine using the button above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-[11px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-5">Server</th>
                  <th className="py-3 px-5">Status</th>
                  <th className="py-3 px-5">Hostname / IP</th>
                  <th className="py-3 px-5">OS Details</th>
                  <th className="py-3 px-5">CPU Load</th>
                  <th className="py-3 px-5">RAM Load</th>
                  <th className="py-3 px-5">Last Heartbeat</th>
                  <th className="py-3 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {servers.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-5">
                      <Link to={`/servers/${s.id}`} className="font-semibold text-white hover:text-sky-400">
                        {s.name}
                      </Link>
                      {s.description && <p className="text-xs text-slate-400">{s.description}</p>}
                    </td>
                    <td className="py-4 px-5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium font-mono uppercase ${
                          s.status === 'online'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-700 text-slate-300'
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-xs font-mono text-slate-300">
                      <div>{s.hostname || 'Unpaired'}</div>
                      <div className="text-slate-500">{s.ip_address || '-'}</div>
                    </td>
                    <td className="py-4 px-5 text-xs text-slate-300">
                      {s.os ? `${s.os} ${s.os_version || ''}` : 'Pending registration'}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_cpu !== null && s.latest_cpu !== undefined ? `${s.latest_cpu.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_ram !== null && s.latest_ram !== undefined ? `${s.latest_ram.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-4 px-5 text-xs text-slate-400 font-mono">
                      {s.last_heartbeat ? new Date(s.last_heartbeat).toLocaleTimeString() : 'Never'}
                    </td>
                    <td className="py-4 px-5 text-right space-x-2">
                      <Link
                        to={`/servers/${s.id}`}
                        className="inline-flex items-center px-2.5 py-1 text-xs rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 hover:bg-sky-500/20"
                      >
                        Details
                      </Link>
                      <button
                        onClick={() => handleDelete(s.id, s.name)}
                        className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        title="Deregister server"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Registration Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-xl bg-[#0e1626] border border-slate-800 rounded-2xl p-6 shadow-2xl relative">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            {!registerResult ? (
              <form onSubmit={handleCreate} className="space-y-4">
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <ServerIcon className="w-5 h-5 text-sky-400" />
                  <span>Register New Machine</span>
                </h2>
                <p className="text-xs text-slate-400">
                  Generate an authenticated provisioning token for the host agent.
                </p>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Server Name *</label>
                  <input
                    type="text"
                    required
                    value={newServerName}
                    onChange={(e) => setNewServerName(e.target.value)}
                    placeholder="e.g. Production-Database-Node"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
                  <input
                    type="text"
                    value={newServerDesc}
                    onChange={(e) => setNewServerDesc(e.target.value)}
                    placeholder="e.g. Primary host in AWS us-east-1"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="pt-2 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium"
                  >
                    Generate Agent Command
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <Check className="w-5 h-5" />
                  <h3 className="font-bold text-lg text-white">Server Provisioned Successfully!</h3>
                </div>
                <p className="text-xs text-slate-400">
                  Run the following command in PowerShell or Bash on your target machine to connect the agent:
                </p>

                {/* Windows Command */}
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-300 mb-1">
                    <span className="font-semibold text-sky-400">Windows (PowerShell):</span>
                    <button
                      onClick={() => copyToClipboard(registerResult.registration_command_windows, true)}
                      className="text-xs text-sky-400 hover:text-sky-300 flex items-center space-x-1"
                    >
                      {copiedWin ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedWin ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-emerald-400 font-mono overflow-x-auto select-all">
                    {registerResult.registration_command_windows}
                  </pre>
                </div>

                {/* Linux Command */}
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-300 mb-1">
                    <span className="font-semibold text-amber-400">Linux (Bash):</span>
                    <button
                      onClick={() => copyToClipboard(registerResult.registration_command_linux, false)}
                      className="text-xs text-amber-400 hover:text-amber-300 flex items-center space-x-1"
                    >
                      {copiedLinux ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedLinux ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-emerald-400 font-mono overflow-x-auto select-all">
                    {registerResult.registration_command_linux}
                  </pre>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => {
                      setModalOpen(false);
                      loadServers();
                    }}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
