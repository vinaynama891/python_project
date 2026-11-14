import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  AlertOctagon,
  Sparkles,
  RefreshCw,
  Cpu,
  Database,
  Wifi,
  HardDrive,
  Info,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { aiApi } from '../services/api';
import { AnomalyLog, ModelStatus, Recommendation } from '../types';

export const AIAnalytics: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyLog[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [anomData, statusData, recData] = await Promise.all([
        aiApi.getAnomalies(),
        aiApi.getModelStatus(),
        aiApi.getRecommendations()
      ]);
      setAnomalies(anomData);
      setModelStatus(statusData);
      setRecommendations(recData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTrain = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const res = await aiApi.train(0.05);
      setTrainMessage(res.message);
      loadData();
    } catch (err: any) {
      setTrainMessage(err.response?.data?.message || 'Model training failed.');
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-3">
            <span>Machine Learning Anomaly Detection</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
              Scikit-Learn Isolation Forest
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Unsupervised outlier detection identifying non-linear multidimensional telemetry anomalies.
          </p>
        </div>

        <button
          onClick={handleTrain}
          disabled={training}
          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/20 transition-all disabled:opacity-50 self-start"
        >
          <Sparkles className="w-4 h-4" />
          <span>{training ? 'Training Model...' : 'Train / Retrain Model'}</span>
        </button>
      </div>

      {trainMessage && (
        <div className="p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-200 text-xs flex items-center space-x-2">
          <Info className="w-4 h-4 text-purple-400 shrink-0" />
          <span>{trainMessage}</span>
        </div>
      )}

      {/* Model State & Diagnostics Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#0c1220] via-[#0f172a] to-[#0c1220] border border-slate-800 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
              <BrainCircuit className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h3 className="text-base font-bold text-white">
                  {modelStatus?.model_name || 'IsolationForestAnomalyDetector'}
                </h3>
                <span
                  className={`text-[11px] font-mono uppercase px-2 py-0.5 rounded-full ${
                    modelStatus?.is_trained
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {modelStatus?.is_trained ? 'Active & Trained' : 'Cold Start / Awaiting Data'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Algorithm: {modelStatus?.algorithm || 'Isolation Forest (Scikit-learn)'} | Version: {modelStatus?.version || '1.0.0'}
              </p>
              <p className="text-xs text-slate-300 mt-2">
                {modelStatus?.status_message}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-6 text-xs font-mono">
            <div>
              <span className="text-slate-500 block uppercase">Training Samples</span>
              <span className="text-lg font-bold text-white">{modelStatus?.training_samples || 0}</span>
            </div>
            <div>
              <span className="text-slate-500 block uppercase">Last Calibration</span>
              <span className="text-sm font-semibold text-slate-300">
                {modelStatus?.last_trained ? new Date(modelStatus.last_trained).toLocaleDateString() : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Anomaly Detection History */}
      <div className="rounded-xl bg-[#0c1220] border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <AlertOctagon className="w-5 h-5 text-rose-400" />
            <span>Detected Outlier Logs & Metric Attribution</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">Real historical anomalies</span>
        </div>

        {anomalies.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-10 h-10 text-emerald-500/60 mx-auto mb-2" />
            <p className="text-slate-200 font-medium text-sm">No abnormal telemetry vectors detected.</p>
            <p className="text-slate-500 mt-1">Host telemetry metrics align within normal historical baseline.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider border-b border-slate-800 font-mono">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Server</th>
                  <th className="py-3 px-4">Anomaly Score</th>
                  <th className="py-3 px-4">CPU %</th>
                  <th className="py-3 px-4">RAM %</th>
                  <th className="py-3 px-4">Attribution / Root Cause</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {anomalies.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-4 text-slate-400">{new Date(a.timestamp).toLocaleString()}</td>
                    <td className="py-3 px-4 font-semibold text-white">{a.server_name}</td>
                    <td className="py-3 px-4">
                      <span className="text-rose-400 font-bold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                        {a.anomaly_score.toFixed(3)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-200">{a.cpu_val !== null && a.cpu_val !== undefined ? `${a.cpu_val.toFixed(1)}%` : '-'}</td>
                    <td className="py-3 px-4 text-slate-200">{a.ram_val !== null && a.ram_val !== undefined ? `${a.ram_val.toFixed(1)}%` : '-'}</td>
                    <td className="py-3 px-4 text-sky-300 font-sans">{a.explanation || 'Baseline divergence'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* AI Recommendations */}
      <div className="rounded-xl bg-[#0c1220] border border-slate-800 p-6 shadow-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-sky-400" />
          <span>Active Optimization Recommendations</span>
        </h3>
        {recommendations.length === 0 ? (
          <p className="text-xs text-slate-400">No tuning recommendations generated at this time.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((r) => (
              <div key={r.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    {r.category}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">Server: {r.server_name}</span>
                </div>
                <h4 className="text-sm font-semibold text-white">{r.title}</h4>
                <p className="text-xs text-slate-300">{r.description}</p>
                {r.suggested_action && (
                  <p className="text-xs text-emerald-400 bg-emerald-500/10 p-2 rounded border border-emerald-500/20 mt-2">
                    <strong>Suggested Action:</strong> {r.suggested_action}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
