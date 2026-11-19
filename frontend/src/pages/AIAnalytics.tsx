import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  AlertOctagon,
  Sparkles,
  Info,
  CheckCircle2
} from 'lucide-react';
import { aiApi } from '../services/api';
import { AnomalyLog, ModelStatus, Recommendation } from '../types';

import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  AlertOctagon,
  Sparkles,
  Info,
  CheckCircle2
} from 'lucide-react';
import { aiApi } from '../services/api';
import { AnomalyLog, ModelStatus, Recommendation } from '../types';
+import { serverApi } from '../services/api';
+
+// New state for server selection
+const [servers, setServers] = useState<Server[]>([]);
+const [selectedServer, setSelectedServer] = useState<string>('');
+
+// Load servers list on component mount
+useEffect(() => {
+  const loadServers = async () => {
+    try {
+      const srv = await serverApi.getServers();
+      setServers(srv);
+      if (srv.length > 0) setSelectedServer(srv[0].id);
+    } catch (e) {
+      console.error('Failed to load servers', e);
+    }
+  };
+  loadServers();
+}, []);

export const AIAnalytics: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyLog[]>([]);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
@@
   const loadData = async () => => {
@@
   };
@@
   const handleTrain = async () => => {
@@
   };
+
+  // New handler to run anomaly detection for the selected server
+  const handleDetect = async () => {
+    if (!selectedServer) return;
+    try {
+      // Default look‑back of 60 minutes
+      const res = await aiApi.detectAnomalies(selectedServer);
+      // Refresh the anomalies list after detection
+      await loadData();
+    } catch (err: any) {
+      console.error('Detection failed', err);
+    }
+  };
@@
   return (
     <div className="space-y-8">
@@
-      {/* Header */}
+      {/* Header */}
@@
-        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
+        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
@@
-          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
+          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
@@
-          </h1>
-          <p className="text-xs text-neutral-400 mt-1">
-            Unsupervised outlier detection identifying non-linear multidimensional telemetry anomalies.
-          </p>
-        </div>
-
-        <button
-          onClick={handleTrain}
-          disabled={training}
-          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:to-amber-400 text-black text-xs font-black shadow-lg shadow-yellow-500/20 transition-all disabled:opacity-50 self-start"
-        >
-          <Sparkles className="w-4 h-4 text-black stroke-[2.5]" />
-          <span>{training ? 'Training Model...' : 'Train / Retrain Model'}</span>
-        </button>
+          </h1>
+          <p className="text-xs text-neutral-400 mt-1">
+            Unsupervised outlier detection identifying non-linear multidimensional telemetry anomalies.
+          </p>
+        </div>
+
+        {/* Server selector */}
+        <select
+          value={selectedServer}
+          onChange={(e) => setSelectedServer(e.target.value)}
+          className="rounded-md bg-[#1a1a1a] text-white px-2 py-1"
+        >
+          {servers.map((s) => (
+            <option key={s.id} value={s.id}>
+              {s.name}
+            </option>
+          ))}
+        </select>
+
+        {/* Detect button */}
+        <button
+          onClick={handleDetect}
+          disabled={!selectedServer}
+          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-green-600 hover:bg-green-500 text-white text-xs font-bold transition-all disabled:opacity-50"
+        >
+          Detect Anomalies
+        </button>
+
+        {/* Train button */}
+        <button
+          onClick={handleTrain}
+          disabled={training}
+          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:to-amber-400 text-black text-xs font-black shadow-lg shadow-yellow-500/20 transition-all disabled:opacity-50 self-start"
+        >
+          <Sparkles className="w-4 h-4 text-black stroke-[2.5]" />
+          <span>{training ? 'Training Model...' : 'Train / Retrain Model'}</span>
+        </button>
*** End Patch
*** End Patch {
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
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center space-x-3">
            <span>Machine Learning Anomaly Detection</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-yellow-400/10 text-yellow-400 border border-yellow-400/30 font-mono font-bold">
              SCIKIT-LEARN ISOLATION FOREST
            </span>
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Unsupervised outlier detection identifying non-linear multidimensional telemetry anomalies.
          </p>
        </div>

        <button
          onClick={handleTrain}
          disabled={training}
          className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:to-amber-400 text-black text-xs font-black shadow-lg shadow-yellow-500/20 transition-all disabled:opacity-50 self-start"
        >
          <Sparkles className="w-4 h-4 text-black stroke-[2.5]" />
          <span>{training ? 'Training Model...' : 'Train / Retrain Model'}</span>
        </button>
      </div>

      {trainMessage && (
        <div className="p-3.5 rounded-xl bg-[#0f0e04] border border-yellow-500/40 text-yellow-200 text-xs flex items-center space-x-2 font-mono">
          <Info className="w-4 h-4 text-yellow-400 shrink-0" />
          <span>{trainMessage}</span>
        </div>
      )}

      {/* Model State & Diagnostics Card in Black & Yellow */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-xl bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center shrink-0">
              <BrainCircuit className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h3 className="text-base font-bold text-white">
                  {modelStatus?.model_name || 'IsolationForestAnomalyDetector'}
                </h3>
                <span
                  className={`text-[11px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
                    modelStatus?.is_trained
                      ? 'bg-yellow-400/15 text-yellow-400 border border-yellow-400/40'
                      : 'bg-neutral-800 text-neutral-400 border border-neutral-700'
                  }`}
                >
                  {modelStatus?.is_trained ? 'Active & Trained' : 'Cold Start / Awaiting Data'}
                </span>
              </div>
              <p className="text-xs text-neutral-400 mt-1 font-mono">
                Algorithm: <span className="text-yellow-400">{modelStatus?.algorithm || 'Isolation Forest (Scikit-learn)'}</span> | Version: {modelStatus?.version || '1.0.0'}
              </p>
              <p className="text-xs text-neutral-300 mt-2">
                {modelStatus?.status_message}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 border-t lg:border-t-0 lg:border-l border-[#1f1f1f] pt-4 lg:pt-0 lg:pl-6 text-xs font-mono">
            <div>
              <span className="text-neutral-500 block uppercase">Training Samples</span>
              <span className="text-lg font-black text-yellow-400">{modelStatus?.training_samples || 0}</span>
            </div>
            <div>
              <span className="text-neutral-500 block uppercase">Last Calibration</span>
              <span className="text-sm font-semibold text-neutral-300">
                {modelStatus?.last_trained ? new Date(modelStatus.last_trained).toLocaleDateString() : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Anomaly Detection History */}
      <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] overflow-hidden shadow-xl">
        <div className="p-4 border-b border-[#1a1a1a] flex items-center justify-between bg-[#0e0e0e]">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <AlertOctagon className="w-5 h-5 text-yellow-400" />
            <span>Detected Outlier Logs & Metric Attribution</span>
          </h3>
          <span className="text-xs text-neutral-400 font-mono">Historical anomalies</span>
        </div>

        {anomalies.length === 0 ? (
          <div className="p-12 text-center text-neutral-400 text-xs">
            <CheckCircle2 className="w-10 h-10 text-yellow-400 mx-auto mb-2" />
            <p className="text-white font-bold text-sm">No abnormal telemetry vectors detected.</p>
            <p className="text-neutral-500 mt-1">Host telemetry metrics align within normal baseline parameters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#121212] text-neutral-400 uppercase tracking-wider border-b border-[#1c1c1c] font-mono">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Server</th>
                  <th className="py-3 px-4">Anomaly Score</th>
                  <th className="py-3 px-4">CPU %</th>
                  <th className="py-3 px-4">RAM %</th>
                  <th className="py-3 px-4">Attribution / Root Cause</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a] font-mono">
                {anomalies.map((a) => (
                  <tr key={a.id} className="hover:bg-[#121212]">
                    <td className="py-3 px-4 text-neutral-400">{new Date(a.timestamp).toLocaleString()}</td>
                    <td className="py-3 px-4 font-bold text-white">{a.server_name}</td>
                    <td className="py-3 px-4">
                      <span className="text-yellow-400 font-black bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/30">
                        {a.anomaly_score.toFixed(3)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-neutral-200">{a.cpu_val !== null && a.cpu_val !== undefined ? `${a.cpu_val.toFixed(1)}%` : '-'}</td>
                    <td className="py-3 px-4 text-neutral-200">{a.ram_val !== null && a.ram_val !== undefined ? `${a.ram_val.toFixed(1)}%` : '-'}</td>
                    <td className="py-3 px-4 text-yellow-300 font-sans">{a.explanation || 'Baseline divergence'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* AI Recommendations */}
      <div className="rounded-xl bg-[#0a0a0a] border border-[#1f1f1f] p-6 shadow-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-yellow-400" />
          <span>Active Optimization Recommendations</span>
        </h3>
        {recommendations.length === 0 ? (
          <p className="text-xs text-neutral-400">No tuning recommendations generated at this time.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((r) => (
              <div key={r.id} className="p-4 rounded-xl bg-[#121212] border border-[#1f1f1f] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 font-bold">
                    {r.category}
                  </span>
                  <span className="text-xs text-neutral-500 font-mono">Server: {r.server_name}</span>
                </div>
                <h4 className="text-sm font-bold text-white">{r.title}</h4>
                <p className="text-xs text-neutral-300">{r.description}</p>
                {r.suggested_action && (
                  <p className="text-xs text-yellow-300 bg-yellow-500/10 p-2 rounded border border-yellow-500/30 mt-2 font-mono">
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
