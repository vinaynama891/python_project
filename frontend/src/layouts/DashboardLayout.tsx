import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  Activity,
  Server,
  AlertTriangle,
  BrainCircuit,
  Zap,
  FileText,
  Settings,
  LogOut,
  Radio,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';

export const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const { isConnected } = useWebSocket();
  const user = JSON.parse(localStorage.getItem('cp_user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('cp_token');
    localStorage.removeItem('cp_user');
    navigate('/login');
  };

  const navItems = [
    { to: '/', label: 'Overview', icon: Activity },
    { to: '/servers', label: 'Server Fleet', icon: Server },
    { to: '/alerts', label: 'Alerts Center', icon: AlertTriangle },
    { to: '/ai', label: 'AI Analytics', icon: BrainCircuit },
    { to: '/profiler', label: 'Performance Profiler', icon: Zap },
    { to: '/reports', label: 'Executive Reports', icon: FileText },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-[#070b14] text-slate-200 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#0d1322] border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div>
          {/* Brand */}
          <div className="h-16 px-6 border-b border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
                <Radio className="w-5 h-5 text-white animate-pulse" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-sky-300 bg-clip-text text-transparent">
                  CloudPulse
                </span>
                <span className="text-[10px] text-sky-400 block -mt-1 font-mono tracking-wider font-semibold">
                  INFRA PROFILER
                </span>
              </div>
            </div>
          </div>

          {/* Live Status Indicator */}
          <div className="px-6 py-3 bg-slate-900/40 border-b border-slate-800/50 flex items-center justify-between text-xs">
            <span className="text-slate-400">Stream Status:</span>
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
              <span className={`font-mono font-medium ${isConnected ? 'text-emerald-400' : 'text-amber-400'}`}>
                {isConnected ? 'LIVE WS' : 'CONNECTING'}
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 opacity-40" />
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer / User Profile */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-sky-400 shrink-0">
                {(user.full_name || user.email || 'A')[0].toUpperCase()}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-200 truncate">{user.full_name || 'Administrator'}</p>
                <p className="text-[11px] text-slate-500 truncate">{user.email || 'admin@cloudpulse.io'}</p>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 py-1.5 px-3 rounded-md text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-[#070b14] p-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
