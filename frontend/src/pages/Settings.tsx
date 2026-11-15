import React, { useState, useEffect } from 'react';
import {
  User,
  Sliders,
  Cloud
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
        <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
          <span>System Settings & Governance</span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 font-mono font-bold">
            TENANT CONTROLS
          </span>
        </h1>
        <p className="text-xs text-neutral-400 mt-1">
          Configure multi-tenant organization policies, threshold rules, and external integrations.
        </p>
      </div>

      {/* User Profile in Black & Yellow */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] space-y-4 shadow-xl">
        <h2 className="text-base font-bold text-white flex items-center space-x-2">
          <User className="w-5 h-5 text-yellow-400" />
          <span>Administrator Profile</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div>
            <span className="text-neutral-500 block">Full Name:</span>
            <span className="text-white text-sm font-bold">{user?.full_name || 'Loading...'}</span>
          </div>
          <div>
            <span className="text-neutral-500 block">Email Address:</span>
            <span className="text-yellow-400 text-sm font-bold">{user?.email || 'Loading...'}</span>
          </div>
          <div>
            <span className="text-neutral-500 block">Assigned Role:</span>
            <span className="text-yellow-400 font-black uppercase">{user?.role || 'admin'}</span>
          </div>
          <div>
            <span className="text-neutral-500 block">Organization Tenant ID:</span>
            <span className="text-neutral-300 select-all font-mono">{user?.organization_id || 'Global'}</span>
          </div>
        </div>
      </div>

      {/* Alert Engine Threshold Rules in Black & Yellow */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] space-y-4 shadow-xl">
        <h2 className="text-base font-bold text-white flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-yellow-400" />
          <span>Configured Alert Engine Thresholds</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-[#121212] border border-[#1f1f1f] space-y-2">
            <span className="text-yellow-400 font-bold block">CPU Utilization</span>
            <div className="flex justify-between text-neutral-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 80.0%</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 90.0%</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#121212] border border-[#1f1f1f] space-y-2">
            <span className="text-amber-400 font-bold block">RAM Utilization</span>
            <div className="flex justify-between text-neutral-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 85.0%</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 95.0%</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#121212] border border-[#1f1f1f] space-y-2">
            <span className="text-yellow-300 font-bold block">Disk Capacity</span>
            <div className="flex justify-between text-neutral-300">
              <span>Warning:</span>
              <span className="font-bold text-amber-400">&ge; 85.0%</span>
            </div>
            <div className="flex justify-between text-neutral-300">
              <span>Critical:</span>
              <span className="font-bold text-rose-400">&ge; 95.0%</span>
            </div>
          </div>
        </div>
        <p className="text-xs text-neutral-500 font-mono">
          * Missing heartbeat timeout is set to 30 seconds before declaring nodes offline. Deduplication active.
        </p>
      </div>

      {/* Optional AWS CloudWatch Integration */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Cloud className="w-5 h-5 text-yellow-400" />
            <span>Optional AWS CloudWatch Integration</span>
          </h2>
          <span className="text-xs font-mono uppercase px-2.5 py-1 rounded bg-[#141414] text-yellow-400/80 border border-yellow-500/20 font-bold">
            DISCONNECTED (LOCAL HOST MODE)
          </span>
        </div>
        <p className="text-xs text-neutral-300 leading-relaxed">
          CloudPulse operates independently with authentic psutil host telemetry. If AWS CloudWatch monitoring is required for remote EC2 instances, supply read-only IAM credentials in the backend <code className="text-yellow-400">.env</code> file:
        </p>
        <pre className="p-3.5 rounded-xl bg-[#050505] border border-[#1f1f1f] text-xs font-mono text-yellow-300 select-all overflow-x-auto">
{`ENABLE_AWS_CLOUDWATCH=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1`}
        </pre>
        <p className="text-[11px] text-neutral-500 font-mono">
          Strict security policy: CloudPulse enforces read-only access (<code className="text-yellow-400">cloudwatch:GetMetricData</code>) and never stores plain secrets in database records.
        </p>
      </div>
    </div>
  );
};
