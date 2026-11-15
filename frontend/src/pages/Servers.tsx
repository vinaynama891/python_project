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
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-2">
            <ServerIcon className="w-6 h-6 text-yellow-400" />
            <span>Server Fleet Management</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Provision agent registration tokens and monitor physical, virtual, and cloud nodes.
          </p>
        </div>
        <button
          onClick={() => {
            setRegisterResult(null);
            setNewServerName('');
            setNewServerDesc('');
            setModalOpen(true);
          }}
          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:to-amber-400 text-black text-xs font-extrabold transition-colors shadow-lg shadow-yellow-500/20"
        >
          <Plus className="w-4 h-4 text-black stroke-[3]" />
          <span>Register New Server</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-[#0a0a0a] p-3 rounded-xl border border-[#1f1f1f]">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by server name or hostname..."
            className="w-full bg-[#121212] border border-[#262626] rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-yellow-400"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-yellow-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#121212] border border-[#262626] text-xs text-neutral-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-yellow-400"
          >
            <option value="">All Statuses</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
          <button
            onClick={loadServers}
            className="p-1.5 rounded-lg bg-[#121212] border border-[#262626] text-neutral-400 hover:text-yellow-400"
            title="Refresh list"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Server List Table */}
      <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-neutral-400 text-xs font-mono">Loading server registry...</div>
        ) : servers.length === 0 ? (
          <div className="p-12 text-center">
            <ServerIcon className="w-10 h-10 text-neutral-700 mx-auto mb-2" />
            <p className="text-white font-bold text-sm">No servers found matching criteria.</p>
            <p className="text-xs text-neutral-500 mt-1">Register a machine using the button above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#121212] text-neutral-400 uppercase text-[11px] tracking-wider border-b border-[#1c1c1c]">
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
              <tbody className="divide-y divide-[#1a1a1a]">
                {servers.map((s) => (
                  <tr key={s.id} className="hover:bg-[#121212] transition-colors">
                    <td className="py-4 px-5">
                      <Link to={`/servers/${s.id}`} className="font-bold text-white hover:text-yellow-400 transition-colors">
                        {s.name}
                      </Link>
                      {s.description && <p className="text-xs text-neutral-500">{s.description}</p>}
                    </td>
                    <td className="py-4 px-5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold font-mono uppercase ${
                          s.status === 'online'
                            ? 'bg-yellow-400/15 text-yellow-400 border border-yellow-400/30'
                            : 'bg-neutral-800 text-neutral-400 border border-neutral-700'
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="py-4 px-5 text-xs font-mono text-neutral-300">
                      <div>{s.hostname || 'Unpaired'}</div>
                      <div className="text-neutral-500">{s.ip_address || '-'}</div>
                    </td>
                    <td className="py-4 px-5 text-xs text-neutral-300">
                      {s.os ? `${s.os} ${s.os_version || ''}` : 'Pending registration'}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_cpu !== null && s.latest_cpu !== undefined ? `${s.latest_cpu.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-4 px-5 font-mono text-xs">
                      {s.latest_ram !== null && s.latest_ram !== undefined ? `${s.latest_ram.toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-4 px-5 text-xs text-neutral-400 font-mono">
                      {s.last_heartbeat ? new Date(s.last_heartbeat).toLocaleTimeString() : 'Never'}
                    </td>
                    <td className="py-4 px-5 text-right space-x-2">
                      <Link
                        to={`/servers/${s.id}`}
                        className="inline-flex items-center px-2.5 py-1 text-xs rounded bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 hover:bg-yellow-400 hover:text-black font-bold transition-all"
                      >
                        Telemetry
                      </Link>
                      <button
                        onClick={() => handleDelete(s.id, s.name)}
                        className="p-1 rounded text-neutral-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-xl bg-[#0a0a0a] border border-[#262626] rounded-2xl p-6 shadow-2xl relative">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-neutral-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            {!registerResult ? (
              <form onSubmit={handleCreate} className="space-y-4">
                <h2 className="text-lg font-black text-white flex items-center space-x-2">
                  <ServerIcon className="w-5 h-5 text-yellow-400" />
                  <span>Register New Machine</span>
                </h2>
                <p className="text-xs text-neutral-400">
                  Generate an authenticated provisioning token for the host agent.
                </p>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Server Name *</label>
                  <input
                    type="text"
                    required
                    value={newServerName}
                    onChange={(e) => setNewServerName(e.target.value)}
                    placeholder="e.g. Production-Database-Node"
                    className="w-full bg-[#121212] border border-[#262626] rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-yellow-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-300 mb-1">Description (Optional)</label>
                  <input
                    type="text"
                    value={newServerDesc}
                    onChange={(e) => setNewServerDesc(e.target.value)}
                    placeholder="e.g. Primary host in AWS us-east-1"
                    className="w-full bg-[#121212] border border-[#262626] rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none focus:border-yellow-400"
                  />
                </div>

                <div className="pt-2 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-neutral-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 text-black text-xs font-extrabold shadow-md shadow-yellow-500/20"
                  >
                    Generate Agent Command
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-yellow-400">
                  <Check className="w-5 h-5" />
                  <h3 className="font-extrabold text-lg text-white">Server Provisioned Successfully!</h3>
                </div>
                <p className="text-xs text-neutral-400">
                  Run the following command in PowerShell or Bash on your target machine to connect the agent:
                </p>

                {/* Windows Command */}
                <div>
                  <div className="flex items-center justify-between text-xs text-neutral-300 mb-1">
                    <span className="font-bold text-yellow-400">Windows (PowerShell):</span>
                    <button
                      onClick={() => copyToClipboard(registerResult.registration_command_windows, true)}
                      className="text-xs text-yellow-400 hover:text-yellow-300 flex items-center space-x-1 font-bold"
                    >
                      {copiedWin ? <Check className="w-3 h-3 text-yellow-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedWin ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="p-3 rounded-lg bg-[#050505] border border-yellow-500/30 text-xs text-yellow-300 font-mono overflow-x-auto select-all">
                    {registerResult.registration_command_windows}
                  </pre>
                </div>

                {/* Linux Command */}
                <div>
                  <div className="flex items-center justify-between text-xs text-neutral-300 mb-1">
                    <span className="font-bold text-amber-400">Linux (Bash):</span>
                    <button
                      onClick={() => copyToClipboard(registerResult.registration_command_linux, false)}
                      className="text-xs text-amber-400 hover:text-amber-300 flex items-center space-x-1 font-bold"
                    >
                      {copiedLinux ? <Check className="w-3 h-3 text-amber-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedLinux ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="p-3 rounded-lg bg-[#050505] border border-amber-500/30 text-xs text-amber-300 font-mono overflow-x-auto select-all">
                    {registerResult.registration_command_linux}
                  </pre>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => {
                      setModalOpen(false);
                      loadServers();
                    }}
                    className="px-4 py-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 text-black text-xs font-extrabold"
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
