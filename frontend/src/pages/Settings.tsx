import React, { useState, useEffect } from 'react';
import {
  User,
  Building,
  Shield,
  Sliders,
  Cloud,
  CheckCircle2,
  AlertTriangle,
  Info,
  Key
} from 'lucide-react';
import { authApi } from '../services/api';

export const Settings: React.FC = () => {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    authApi.getMe().then(setUser).catch(console.error);
  }, []);

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System Settings & Governance</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure multi-tenant organization policies, threshold rules, and external integrations.
        </p>
      </div>

      {/* User Profile */}
      <div className="p-6 rounded-2xl bg-[#0c1220] border border-slate-800 space-y-4 shadow-xl">
        <h2 className="text-base font-bold text-white flex items-center space-x-2">
          <User className="w-5 h-5 text-sky-400" />
          <span>Administrator Profile</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div>
            <span className="text-slate-500 block">Full Name:</span>
            <span className="text-white text-sm font-semibold">{user?.full_name || 'Loading...'}</span>
          </div>
          <div>
            <span className="text-slate-500 block">Email Address:</span>
            <span className="text-white text-sm font-semibold">{user?.email || 'Loading...'}</span>
          </div>
          <div>
            <span className="text-slate-500 block">Assigned Role:</span>
            <span className="text-emerald-400 font-bold uppercase">{user?.role || 'admin'}</span>
          </div>
          <div>
            <span className="text-slate-500 block">Organization Tenant ID:</span>
            <span className="text-slate-300 select-all">{user?.organization_id || 'Global'}</span>
          </div>
        </div>
      </div>

      {/* Alert Engine Threshold Rules */}
      <div className="p-6 rounded-2xl bg-[#0c1220] border border-slate-800 space-y-4 shadow-xl">
        <h2 className="text-base font-bold text-white flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-amber-400" />
          <span>Configured Alert Engine Thresholds</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-sky-400 font-bold block">CPU Utilization</span>
            <div className="flex justify-between text-slate-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 80.0%</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 90.0%</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-purple-400 font-bold block">RAM Utilization</span>
            <div className="flex justify-between text-slate-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 85.0%</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 95.0%</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-cyan-400 font-bold block">Disk Capacity</span>
            <div className="flex justify-between text-slate-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 85.0%</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 95.0%</span>
            </div>
          </div>
        </div>
        <p className="text-xs text-slate-500 font-mono">
          * Missing heartbeat timeout is set to 30 seconds before declaring nodes offline. Deduplication active.
        </p>
      </div>

      {/* Optional AWS CloudWatch Integration */}
      <div className="p-6 rounded-2xl bg-[#0c1220] border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Cloud className="w-5 h-5 text-amber-400" />
            <span>Optional AWS CloudWatch Integration</span>
          </h2>
          <span className="text-xs font-mono uppercase px-2.5 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
            DISCONNECTED (LOCAL HOST MODE)
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          CloudPulse operates independently with authentic psutil host telemetry. If AWS CloudWatch monitoring is required for remote EC2 instances, supply read-only IAM credentials in the backend <code>.env</code> file:
        </p>
        <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-400 select-all overflow-x-auto">
{`ENABLE_AWS_CLOUDWATCH=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1`}
        </pre>
        <p className="text-[11px] text-slate-500 font-mono">
          Strict security policy: CloudPulse enforces read-only access (<code>cloudwatch:GetMetricData</code>) and never stores plain secrets in database records.
        </p>
      </div>
    </div>
  );
};
