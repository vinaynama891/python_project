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
    <div className="flex h-screen bg-[#050505] text-neutral-200 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#0a0a0a] border-r border-[#1a1a1a] flex flex-col justify-between shrink-0">
        <div>
          {/* Brand */}
          <div className="h-16 px-6 border-b border-[#1a1a1a] flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-yellow-500 via-yellow-400 to-amber-300 flex items-center justify-center shadow-lg shadow-yellow-500/25">
                <Radio className="w-5 h-5 text-black animate-pulse" />
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-yellow-300 via-yellow-400 to-amber-400 bg-clip-text text-transparent">
                  CloudPulse
                </span>
                <span className="text-[10px] text-yellow-400/90 block -mt-1 font-mono tracking-wider font-bold">
                  INFRA PROFILER
                </span>
              </div>
            </div>
          </div>

          {/* Live Status Indicator */}
          <div className="px-6 py-2.5 bg-[#0e0e0e] border-b border-[#1a1a1a] flex items-center justify-between text-xs">
            <span className="text-neutral-400 font-medium">Telemetry Stream:</span>
            <div className="flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-yellow-400 shadow-sm shadow-yellow-400 animate-ping' : 'bg-neutral-600'}`} />
              <span className={`font-mono text-xs font-bold ${isConnected ? 'text-yellow-400' : 'text-neutral-500'}`}>
                {isConnected ? 'LIVE WS' : 'OFFLINE'}
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
                        ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/40 shadow-sm shadow-yellow-500/10 font-semibold'
                        : 'text-neutral-400 hover:text-yellow-300 hover:bg-[#141414]'
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
        <div className="p-4 border-t border-[#1a1a1a] bg-[#070707]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-500 to-amber-400 flex items-center justify-center font-black text-xs text-black shrink-0 shadow-sm shadow-yellow-500/20">
                {(user.full_name || user.email || 'A')[0].toUpperCase()}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-neutral-200 truncate">{user.full_name || 'Administrator'}</p>
                <p className="text-[11px] text-yellow-500/70 truncate font-mono">{user.email || 'admin@cloudpulse.io'}</p>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 py-1.5 px-3 rounded-md text-xs font-semibold text-neutral-400 hover:text-red-400 hover:bg-red-500/10 transition-colors border border-transparent hover:border-red-500/20"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-[#050505] p-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
